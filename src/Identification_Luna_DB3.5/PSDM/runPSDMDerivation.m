% This is a script to run the PSDM derivation for the Luna DB3.5 dataset. 
% It sets up the necessary parameters and calls the appropriate functions 
% to perform the derivation process.
%
% To run it, move to the root of the project (which is SystemIdentification) 
% and execute:
%   run('src/Identification_Luna_DB3.5/PSDM/runPSDMDerivation')

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
rootSysId = fullfile('..');
rootDH = fullfile(rootSysId, 'RobotDescription', 'DH');

% load the DH table and the join_names, which are saved in the dh_table.mat
load(fullfile(rootDH, 'dh_table.mat'));

% `X` is a structural mask. A zero means that the corresponding inertial term is treated as absent in the derivation.
% the menaing of the 10 colums are:
%   [ m, rx, ry ,rz, Ixx, Iyy, Izz, Ixy, Ixz, Iyz, Im ]
% where:
%   - m is the mass of link;
%   - rx, ry, rz are the (x,y,z) position of the center of gravity of the link;
%   - Ixx, Iyy, Izz, Ixy, Ixz, Iyz are the principle and cross inertia terms of the link,
%       centered at the center of gravity and aligned with the main coordinate system of the link.
%   - Im is the equivalent moment of inertias of the motor armatures and drives
n = size(DH, 1);
X = ones(n, 11);

% Since we do not want to identify the cross inertia temr of the mass and 
% the armature moment of innertia, we set the 8th to 10th column of X to zero
X(:, 2:11) = 0
X(1,:) = 1
X(2,:) = 1
X(3,:) = 1
X(4,:) = 1
X(5,:) = 1
X(6,:) = 1

X(7, 1) = 1; % m --> OK
X(7, 2) = 1; % Rx --> OK
% X(7, 3) = 1; % Ry --> cause accel derivation on J2 to not converge
X(7, 4) = 1; % Rz --> OK
% X(7, 5) = 1; % Ixx --> cause coriolis derivation on J2/J5 to not converge
X(7, 6) = 1; % Iyy --> OK
% X(7, 7) = 1; % Izz --> KO cause coriolis derivation on joint J2/J5 to not converge
X(7, 8) = 1; % Ixy --> OK
% X(7, 9) = 1; % Ixz --> cause accel derivation on J5 to not converge
X(7, 10) = 1; % Iyz --> OK

% Drop off the armature motor inertia
X(:,11)=0

% Gravity vector: aligned with +Z axis
g = [0, 0, 1]';

% Derive the model:
[E, P] = PSDM.deriveModel(DH, g, X);
% [E, P] = PSDM.deriveModel(DH, g);