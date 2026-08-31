% this script launch the compare_urdf_dh_frames function, given 
% the following parameters:
% - the source urdf file
% - the DH table to be verified
% - the urdf_kinematics.json 
% - the base link
% - the tool link (aka the end-effector link)
% it generates three diagrams showing the reference frames labeled as D frames (through the DH table),
% UK frames (through the urdf description), and a superposition of both,
% using the given robot pose 'qpose'.


% addpath('src/utils/UrdfToDH');

qpose=zeros(1,7);

result = compare_urdf_dh_frames( ...
    fullfile(root, 'urdf', 'arm_with_None.urdf'), ...
    fullfile(root, 'DH', 'dh_table.csv'), ...
    fullfile(root, 'DH', 'urdf_kinematics.json'), ...
    qpose, ...
    'BaseLink', 'starman_arm_link_cart', ...
    'ToolLink', 'starman_arm_ids');

