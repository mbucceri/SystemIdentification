# Utilities

This folder contains support tools used by the robot system-identification workflow.

## URDF to standard DH

[`UrdfToDH/urdf_to_standard_dh.py`](UrdfToDH/urdf_to_standard_dh.py) extracts a selected serial chain from a URDF model and generates a PSDM-compatible standard Denavit--Hartenberg (DH) representation. It reads the base/tool selection and validation settings from YAML, accounts for fixed transforms along the chain, writes the DH table and residual base/tool transforms, and validates the result by comparing URDF and DH forward kinematics.

For usage, configuration, mathematical conventions, generated files, and limitations, see the [complete manual (PDF)](UrdfToDH/urdf_to_standard_dh_manual.pdf) or its [LaTeX source](UrdfToDH/urdf_to_standard_dh_manual.tex).

## URDF/DH frame comparison in MATLAB

[`UrdfToDH/compare_urdf_dh_frames.m`](UrdfToDH/compare_urdf_dh_frames.m) visually and numerically compares the frames reconstructed from the generated standard-DH table with the corresponding URDF model at a specified joint configuration. It displays the URDF model, the DH chain, and an aligned overlay; reports joint-axis alignment and tool-pose errors; and returns the evaluated transforms, errors, and figure handle in a MATLAB structure.

The function requires MATLAB with Robotics System Toolbox and the files produced by `urdf_to_standard_dh.py` (`dh_table.csv` and `urdf_kinematics.json`). See the [concise MATLAB-function manual](UrdfToDH/compare_urdf_dh_frames_manual.tex) for its interface, options, example, and guidance on interpreting the comparison.

