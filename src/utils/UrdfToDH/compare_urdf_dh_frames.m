function result = compare_urdf_dh_frames(urdfPath, dhCsvPath, kinematicsJsonPath, q, varargin)
%COMPARE_URDF_DH_FRAMES Visually compare URDF and generated standard-DH frames.
%
% result = compare_urdf_dh_frames(urdfPath, dhCsvPath, jsonPath, q, ...
%     'BaseLink', baseLink, 'ToolLink', toolLink)
%
% Required inputs
%   urdfPath            Source URDF file.
%   dhCsvPath           Generated dh_table.csv.
%   kinematicsJsonPath  Generated urdf_kinematics.json.
%   q                   Canonical joint coordinates in CSV row order.
%
% Name-value options
%   BaseLink   Selected URDF base link (required).
%   ToolLink   Selected URDF tool link (required).
%   FrameScale Length of plotted frame axes in metres (default 0.08).
%   ShowVisuals Show URDF visual meshes (default true).
%
% Example for Luna DB3.5
%   root = fullfile('src', 'Identification_Luna_DB3.5');
%   result = compare_urdf_dh_frames( ...
%       fullfile(root, 'RobotDescription', 'urdf', 'arm_with_None.urdf'), ...
%       fullfile(root, 'dh_table.csv'), ...
%       fullfile(root, 'urdf_kinematics.json'), zeros(1, 7), ...
%       'BaseLink', 'starman_arm_link_cart', ...
%       'ToolLink', 'starman_arm_ids');
%
% The DH frames are evaluated explicitly using
%   A_i = RotZ(theta_i*) TransZ(d_i*) TransX(a_i) RotX(alpha_i),
% where theta_i* = theta_i + (1-t_i)s_i q_i and
% d_i* = d_i + t_i s_i q_i. No rigidBodyTree DH conversion is used.
%
% Standard-DH indexing reminder: URDF joint i should be compared with the
% axis z_(i-1), not z_i. Body frames need not coincide with DH frames.

    parser = inputParser;
    parser.FunctionName = mfilename;
    addParameter(parser, 'BaseLink', '', @(x) ischar(x) || isstring(x));
    addParameter(parser, 'ToolLink', '', @(x) ischar(x) || isstring(x));
    addParameter(parser, 'FrameScale', 0.08, ...
        @(x) isnumeric(x) && isscalar(x) && isfinite(x) && x > 0);
    addParameter(parser, 'ShowVisuals', true, ...
        @(x) islogical(x) && isscalar(x));
    parse(parser, varargin{:});

    baseLink = char(parser.Results.BaseLink);
    toolLink = char(parser.Results.ToolLink);
    frameScale = double(parser.Results.FrameScale);
    showVisuals = parser.Results.ShowVisuals;
    if isempty(baseLink) || isempty(toolLink)
        error('compare_urdf_dh_frames:MissingFrames', ...
            ['BaseLink and ToolLink are required because a URDF can contain ' ...
             'branches and fixed frames outside the selected DH chain.']);
    end

    validateFile(urdfPath, 'URDF');
    validateFile(dhCsvPath, 'DH CSV');
    validateFile(kinematicsJsonPath, 'kinematics JSON');

    dhTable = readtable(dhCsvPath, 'TextType', 'string');
    requiredColumns = {'joint', 'a_m', 'alpha_rad', 'd_m', ...
        'theta_rad', 't', 's'};
    missingColumns = setdiff(requiredColumns, dhTable.Properties.VariableNames);
    if ~isempty(missingColumns)
        error('compare_urdf_dh_frames:BadCsv', ...
            'DH CSV is missing columns: %s', strjoin(missingColumns, ', '));
    end

    jointNames = string(dhTable.joint);
    DH = [dhTable.a_m, dhTable.alpha_rad, dhTable.d_m, ...
          dhTable.theta_rad, dhTable.t, dhTable.s];
    q = double(q(:));
    n = height(dhTable);
    if numel(q) ~= n || any(~isfinite(q))
        error('compare_urdf_dh_frames:BadConfiguration', ...
            'q must contain %d finite values in DH CSV row order.', n);
    end
    if any(~ismember(DH(:, 5), [0, 1])) || any(~ismember(DH(:, 6), [-1, 1]))
        error('compare_urdf_dh_frames:BadDhSelectors', ...
            'Every DH t value must be 0 or 1 and every s value must be -1 or +1.');
    end

    jsonData = jsondecode(fileread(kinematicsJsonPath));
    TBaseDh0 = requireTransform(jsonData, 'T_urdf_base_to_dh_base');
    TDhNTool = requireTransform(jsonData, 'T_dh_last_to_urdf_tool');
    if isfield(jsonData, 'joint_order') && ...
            ~isequal(string(jsonData.joint_order(:)), jointNames)
        error('compare_urdf_dh_frames:JointOrderMismatch', ...
            'Joint order differs between the DH CSV and kinematics JSON.');
    end

    fullRobot = importrobot(urdfPath);
    fullRobot.DataFormat = 'struct';
    assertBodyExists(fullRobot, baseLink, 'base');
    viewRobot = subtree(fullRobot, baseLink);
    viewRobot.DataFormat = 'struct';
    assertBodyExists(viewRobot, toolLink, 'tool');

    urdfConfig = homeConfiguration(viewRobot);
    urdfJointNames = string({urdfConfig.JointName});
    for i = 1:n
        match = find(urdfJointNames == jointNames(i));
        if numel(match) ~= 1
            error('compare_urdf_dh_frames:JointNotFound', ...
                'DH joint "%s" was not found exactly once in the URDF subtree.', jointNames(i));
        end
        urdfConfig(match).JointPosition = q(i);
    end

    % Evaluate D0...Dn in the selected URDF base frame.
    TDhFrames = zeros(4, 4, n + 1);
    TDhFrames(:, :, 1) = TBaseDh0;
    for i = 1:n
        a = DH(i, 1);
        alpha = DH(i, 2);
        d = DH(i, 3) + DH(i, 5) * DH(i, 6) * q(i);
        theta = DH(i, 4) + (1 - DH(i, 5)) * DH(i, 6) * q(i);
        TDhFrames(:, :, i + 1) = TDhFrames(:, :, i) * ...
            standardDhTransform(a, alpha, d, theta);
    end
    TDhTool = TDhFrames(:, :, end) * TDhNTool;
    TUrdfTool = getTransform(viewRobot, urdfConfig, toolLink);

    [urdfAxisOrigins, urdfAxisDirections] = getUrdfJointAxes( ...
        viewRobot, urdfConfig, jointNames);
    axisAngleErrorDeg = zeros(n, 1);
    axisLineDistance = zeros(n, 1);
    for i = 1:n
        dhOrigin = TDhFrames(1:3, 4, i);
        dhAxis = TDhFrames(1:3, 3, i);
        axisCosine = max(-1, min(1, dot(dhAxis, urdfAxisDirections(:, i))));
        axisAngleErrorDeg(i) = rad2deg(acos(axisCosine));
        axisLineDistance(i) = norm(cross( ...
            urdfAxisOrigins(:, i) - dhOrigin, dhAxis));
    end

    positionError = norm(TUrdfTool(1:3, 4) - TDhTool(1:3, 4));
    relativeRotation = TUrdfTool(1:3, 1:3)' * TDhTool(1:3, 1:3);
    cosine = max(-1, min(1, (trace(relativeRotation) - 1) / 2));
    orientationErrorDeg = rad2deg(acos(cosine));

    figureHandle = figure('Name', 'URDF versus standard-DH frames', ...
        'Color', 'white');
    visualsSetting = ternary(showVisuals, 'on', 'off');

    axUrdf = subplot(1, 3, 1, 'Parent', figureHandle);
    show(viewRobot, urdfConfig, 'Parent', axUrdf, 'Frames', 'on', ...
        'Visuals', visualsSetting, 'PreservePlot', false);
    prepareAxes(axUrdf, 'URDF model and body frames');
    drawUrdfJointAxes(axUrdf, urdfAxisOrigins, urdfAxisDirections, frameScale);

    axDh = subplot(1, 3, 2, 'Parent', figureHandle);
    hold(axDh, 'on');
    drawDhChain(axDh, TDhFrames, TDhTool, frameScale);
    prepareAxes(axDh, 'Generated standard-DH frames');

    axOverlay = subplot(1, 3, 3, 'Parent', figureHandle);
    show(viewRobot, urdfConfig, 'Parent', axOverlay, 'Frames', 'on', ...
        'Visuals', visualsSetting, 'PreservePlot', false);
    hold(axOverlay, 'on');
    if showVisuals
        meshPatches = findobj(axOverlay, 'Type', 'Patch');
        set(meshPatches, 'FaceAlpha', 0.25, 'EdgeAlpha', 0.15);
    end
    drawUrdfJointAxes(axOverlay, urdfAxisOrigins, urdfAxisDirections, frameScale);
    drawDhChain(axOverlay, TDhFrames, TDhTool, frameScale);
    plot3(axOverlay, TUrdfTool(1, 4), TUrdfTool(2, 4), TUrdfTool(3, 4), ...
        'ko', 'MarkerSize', 9, 'LineWidth', 2, 'DisplayName', 'URDF tool');
    prepareAxes(axOverlay, sprintf(['Aligned overlay\nposition error %.3g m, ' ...
        'orientation error %.3g deg'], positionError, orientationErrorDeg));
    linkprop([axUrdf, axDh, axOverlay], {'CameraPosition', 'CameraTarget', ...
        'CameraUpVector', 'CameraViewAngle', 'XLim', 'YLim', 'ZLim'});

    fprintf('URDF/DH comparison at q = [%s]\n', sprintf(' %.8g', q));
    fprintf('Tool position error:    %.12g m\n', positionError);
    fprintf('Tool orientation error: %.12g deg\n', orientationErrorDeg);
    fprintf('\nJoint-axis comparison (URDF J_i versus DH z_(i-1)):\n');
    fprintf('  %-28s  %14s  %16s\n', 'joint', 'angle (deg)', 'line distance (m)');
    for i = 1:n
        fprintf('  %-28s  %14.6g  %16.6g\n', jointNames(i), ...
            axisAngleErrorDeg(i), axisLineDistance(i));
    end
    fprintf(['Interpretation: URDF joint i aligns with DH z_(i-1); ' ...
             'URDF body frames need not coincide with DH frames.\n']);

    result = struct( ...
        'joint_names', jointNames, ...
        'q', q, ...
        'T_urdf_tool', TUrdfTool, ...
        'T_dh_tool', TDhTool, ...
        'T_dh_frames', TDhFrames, ...
        'joint_axis_angle_error_deg', axisAngleErrorDeg, ...
        'joint_axis_line_distance_m', axisLineDistance, ...
        'position_error_m', positionError, ...
        'orientation_error_deg', orientationErrorDeg, ...
        'figure', figureHandle);
end


function T = standardDhTransform(a, alpha, d, theta)
    ct = cos(theta); st = sin(theta);
    ca = cos(alpha);  sa = sin(alpha);
    T = [ct, -st*ca,  st*sa, a*ct; ...
         st,  ct*ca, -ct*sa, a*st; ...
          0,     sa,     ca,    d; ...
          0,      0,      0,    1];
end


function drawDhChain(ax, frames, toolTransform, scale)
    origins = squeeze(frames(1:3, 4, :));
    plot3(ax, origins(1, :), origins(2, :), origins(3, :), 'k--', ...
        'LineWidth', 1.5, 'DisplayName', 'DH chain');
    for i = 1:size(frames, 3)
        drawFrame(ax, frames(:, :, i), scale, '--', 1.8);
        p = frames(1:3, 4, i);
        text(ax, p(1), p(2), p(3), sprintf('  D%d', i - 1), ...
            'Color', [0.1, 0.1, 0.1], 'FontWeight', 'bold');
    end
    drawFrame(ax, toolTransform, 1.15 * scale, ':', 2.5);
    p = toolTransform(1:3, 4);
    plot3(ax, p(1), p(2), p(3), 'md', 'MarkerSize', 9, ...
        'LineWidth', 2, 'DisplayName', 'DH reconstructed tool');
    text(ax, p(1), p(2), p(3), '  DH tool', 'Color', 'm', ...
        'FontWeight', 'bold');
end


function drawFrame(ax, T, scale, lineStyle, lineWidth)
    colors = [0.85, 0.10, 0.10; 0.10, 0.60, 0.10; 0.10, 0.25, 0.90];
    p = T(1:3, 4);
    for k = 1:3
        endpoint = p + scale * T(1:3, k);
        plot3(ax, [p(1), endpoint(1)], [p(2), endpoint(2)], ...
            [p(3), endpoint(3)], 'Color', colors(k, :), ...
            'LineStyle', lineStyle, 'LineWidth', lineWidth, ...
            'HandleVisibility', 'off');
    end
end


function drawUrdfJointAxes(ax, origins, directions, scale)
    hold(ax, 'on');
    for i = 1:size(origins, 2)
        p = origins(:, i);
        axisDirection = directions(:, i);
        endpoints = [p - scale * axisDirection, p + scale * axisDirection];
        plot3(ax, endpoints(1, :), endpoints(2, :), endpoints(3, :), ...
            '-', 'Color', [0.1, 0.1, 0.1], 'LineWidth', 2.2, ...
            'HandleVisibility', 'off');
        text(ax, p(1), p(2), p(3), sprintf('  UJ%d', i), ...
            'Color', [0.05, 0.05, 0.05]);
    end
end


function [origins, directions] = getUrdfJointAxes(robot, config, jointNames)
    origins = zeros(3, numel(jointNames));
    directions = zeros(3, numel(jointNames));
    for i = 1:numel(jointNames)
        body = bodyForJoint(robot, jointNames(i));
        if isempty(body)
            error('compare_urdf_dh_frames:JointBodyNotFound', ...
                'Cannot find the child body associated with joint "%s".', jointNames(i));
        end
        if strcmp(body.Parent.Name, robot.BaseName)
            TBaseParent = eye(4);
        else
            TBaseParent = getTransform(robot, config, body.Parent.Name);
        end
        TBaseJoint = TBaseParent * body.Joint.JointToParentTransform;
        direction = TBaseJoint(1:3, 1:3) * body.Joint.JointAxis(:);
        origins(:, i) = TBaseJoint(1:3, 4);
        directions(:, i) = direction / norm(direction);
    end
end


function body = bodyForJoint(robot, jointName)
    body = [];
    for i = 1:numel(robot.Bodies)
        candidate = robot.Bodies{i};
        if strcmp(candidate.Joint.Name, char(jointName))
            body = candidate;
            return;
        end
    end
end


function prepareAxes(ax, titleText)
    grid(ax, 'on');
    axis(ax, 'equal');
    xlabel(ax, 'X (m)'); ylabel(ax, 'Y (m)'); zlabel(ax, 'Z (m)');
    title(ax, titleText, 'Interpreter', 'none');
    view(ax, 3);
end


function T = requireTransform(data, fieldName)
    if ~isfield(data, fieldName)
        error('compare_urdf_dh_frames:BadJson', ...
            'Kinematics JSON has no field "%s".', fieldName);
    end
    T = double(data.(fieldName));
    if ~isequal(size(T), [4, 4]) || any(~isfinite(T), 'all')
        error('compare_urdf_dh_frames:BadJsonTransform', ...
            'JSON field "%s" must be a finite 4-by-4 transform.', fieldName);
    end
end


function assertBodyExists(robot, bodyName, role)
    if strcmp(robot.BaseName, bodyName)
        return;
    end
    if ~any(strcmp(robot.BodyNames, bodyName))
        error('compare_urdf_dh_frames:BodyNotFound', ...
            'Selected URDF %s link "%s" was not found.', role, bodyName);
    end
end


function validateFile(path, description)
    if ~(ischar(path) || isstring(path)) || ~isfile(path)
        error('compare_urdf_dh_frames:FileNotFound', ...
            '%s file does not exist: %s', description, string(path));
    end
end


function value = ternary(condition, whenTrue, whenFalse)
    if condition
        value = whenTrue;
    else
        value = whenFalse;
    end
end
