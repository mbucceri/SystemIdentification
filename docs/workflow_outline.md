# PSDM System Identification Workflow Outline

This outline is intended for approval before detailed implementation. It summarizes phase structure, required inputs, and expected outputs.

## Objective

Build and validate a PSDM-based inverse dynamics model for a robot manipulator using URDF, telemetry, and motor current measurements.

## Inputs (Required)

- Robot URDF with joint definitions and link structure.
- Gravity direction in robot base frame.
- Real robot logs with timestamps, joint position `q`, velocity `qdot`, and motor current `i`.
- Motor torque constants (`Kt_motor`) from motor plates/datasheets.
- Transmission information per joint (gear ratio and sign convention).

## Outputs (Primary Deliverables)

- DH-based kinematic parameter table compatible with PSDM.
- PSDM model matrices `E` and `P`.
- Identified base parameter vector `theta_b`.
- Validated inverse dynamics model:
  - `tau_hat = yp(q, qdot, qddot) * P_i * theta_b`
- Optional generated fast code for inverse/forward dynamics.

## Phase Structure

### Phase 0 - Scope and Conventions Lock

- Confirm reference frames, sign conventions, and coordinate definitions.
- Lock URDF-to-DH convention and acceptance checks.
- Define data logging and preprocessing assumptions.

**Outputs:** conventions sheet, execution checklist, data contract.

### Phase 1 - URDF to PSDM Kinematics

- Parse URDF joint chain and transforms.
- Build PSDM-compatible DH table `[a_i, alpha_i, d_i, theta_i, t_i, s_i]`.
- Validate FK agreement between URDF and DH models.

**Outputs:** approved DH table and gravity vector `g`.

### Phase 2 - PSDM Model Derivation

- Run `PSDM.deriveModel(DH, g)` to obtain `E` and `P`.
- Apply optional simplification masks and complexity reduction if needed.

**Outputs:** `E`, `P`, and derivation metadata.

### Phase 3 - Real-Robot Data Collection and Preprocessing

- Execute excitation trajectories under safety limits.
- Log synchronized telemetry (`q`, `qdot`, `i`, timestamps).
- Convert current to torque labels using joint-side constants.
- Resample/filter data and estimate `qddot`.

**Outputs:** cleaned train/validation datasets with `q`, `qdot`, `qddot`, `tau_meas`.

### Phase 4 - Base Parameter Identification

- Evaluate regressor terms from `E`, then apply `P_i`.
- Solve for `theta_b` with least squares (and regularization if required).
- Assess conditioning and residual structure.

**Outputs:** identified `theta_b`, fit diagnostics, residual/error reports.

### Phase 5 - Validation and Digital Twin Packaging

- Validate torque prediction on held-out trajectories.
- Export reusable inverse dynamics function.
- Optionally generate optimized code artifacts.

**Outputs:** validated model package and deployment-ready functions.

### Phase 6 - Iteration Loop

- Repeat collection/identification under new trajectories or payloads.
- Re-tune preprocessing and model complexity when required.

**Outputs:** versioned model improvements and updated validation metrics.

## Approval Gates

- **Gate 1:** Kinematics consistency accepted (URDF vs DH FK checks).
- **Gate 2:** Data quality accepted (timestamp stability and derivative settings).
- **Gate 3:** Identification accepted (fit quality and generalization metrics).
- **Gate 4:** Packaging accepted (runtime and interface requirements met).

## Notes for Detailed Specification

- Keep a clear separation between fixed conventions and tunable preprocessing choices.
- Track all phase decisions in reproducible scripts/config files.
- Promote any unresolved ambiguity to an explicit gate blocker before identification runs.
