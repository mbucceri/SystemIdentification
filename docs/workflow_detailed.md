# PSDM System Identification Workflow (Detailed)

> Proposed revision. This version integrates actuator-to-joint coordinate mapping, prismatic-axis conventions, local joint-direction semantics, and URDF-to-DH automation boundaries.

## Purpose and scope

This document is the detailed, step-by-step execution guide for building and validating a PSDM-based inverse-dynamics digital twin of a rigid serial robot. It expands the approved outline and incorporates `critical_ambiguities.md`.

The resulting PSDM model is expressed in regressor form:

```text
tau_i = yp(q, qdot, qddot) * P_i * theta_b
```

`q`, `qdot`, and `qddot` in this expression are **link-side generalized coordinates**. They are expressed in rad, rad/s, rad/s² for revolute joints and m, m/s, m/s² for prismatic joints. They are not raw motor encoder counts, motor-shaft angles, or their derivatives.

For a mixed revolute-prismatic chain, `tau_i` denotes generalized effort. Its unit is Nm for a revolute joint and N for a prismatic joint. The notation follows the PSDM documentation, which uses `tau` for the complete generalized-effort vector.

**In scope:** rigid serial chains, revolute and prismatic joints, actuator-current-based generalized-effort proxy, sequential calibration following the Denso PSDM application paper, and optional real-time PSDM code generation.

**Out of scope unless separately added:** flexible transmissions, backlash, compliance, unmodeled cable effects, contact/process forces, and force-control behavior.

### Revision scope

This revision resolves four implementation-critical points:

1. The mandatory actuator-to-joint coordinate transformation from encoder telemetry to PSDM coordinates.
2. The meaning of `+q direction` for both revolute and prismatic joints.
3. The distinction between a joint-local `+q` direction and configuration-dependent end-effector motion.
4. The role and limitations of an automated URDF-to-DH conversion tool.

Items marked **[Needs confirmation]** require robot-specific evidence before identification proceeds. Items marked **[Inference]** are mechanically derived implementation rules rather than statements provided by PSDM itself.

## Authoritative sources

| Source | Role in this workflow |
|---|---|
| Lloyd et al. (2021), *A numeric derivation for fast regressive modeling of manipulator dynamics* | PSDM theory, regressor representation, base inertial parameters, and the treatment of revolute and prismatic generalized coordinates. |
| `PSDM-README.pdf` | MATLAB API, PSDM DH matrix, `t_i` and `s_i` conventions, gravity convention, optional drive inertia, inverse and forward dynamics, code generation. |
| Lloyd et al., Denso VS-6556G application preprint | Sequential motor, gravity, friction, and inertial calibration procedure. |
| `CarletonABL/PSDM` repository | Reference MATLAB implementation. The workflow code snippets must match the checked-out repository revision. |
| `critical_ambiguities.md` | Existing conversion and signal-quality decision gates. |

The workflow does not treat the URDF, the controller telemetry definition, or a motor datasheet as mutually consistent by assumption. Their consistency is established by Gates 0 and 1.

## Prerequisites

### Software

| Component | Requirement |
|---|---|
| MATLAB | R2018a or newer. |
| PSDM toolbox | Checked-out `CarletonABL/PSDM` revision recorded in the identification run log. |
| Optional: MATLAB Coder | Required for `PSDM.make` and generated-code compilation. |
| Optional: Parallel Computing Toolbox | Used only when the checked-out PSDM configuration supports parallel derivation. |
| Python 3 | Used only for a proposed URDF-chain extraction and FK comparison helper. |

### Hardware and measurement evidence

Collect the following before any experiment:

- URDF representing the physical robot configuration, including the selected tool state.
- EtherCAT logs containing raw drive-side position telemetry and motor current.
- Encoder scale for every motor, expressed as counts per motor revolution or an equivalent unambiguous scale.
- Transmission definition for every axis. This includes gearbox ratio direction, mechanical sign, ball-screw lead for prismatic axes, and any belt or additional reduction stage.
- Encoder reference count and the physical configuration corresponding to the selected kinematic zero.
- Motor torque constant at the motor reference.
- Current sign definition from drive firmware.
- Joint position, velocity, acceleration, and generalized-effort limits.
- Gravity direction in the PSDM base frame, expressed as a unit vector pointing upward.

### Required artifacts before Phase 3

Create and version-control the following artifacts:

1. `conventions_sheet.md`, the human-readable frame, joint, sign, and reference-pose record.
2. `actuator_to_joint_map.yaml`, the machine-readable actuator-coordinate to PSDM-coordinate mapping.
3. `actuator_effort_conversion_notes.md`, the generalized-effort-per-ampere derivation and validation record. This replaces the narrower term `kt_conversion_notes.md`.
4. `dh_table.csv` and `dh_table.mat`, approved only after Gate 1.
5. `fk_validation_report.md`.
6. `timing_quality_report.md`.
7. `derivative_filter_config.yaml`.

The raw logs and processed PSDM datasets are separate immutable artifact classes. Raw logs are never overwritten.

## Phase 0: Coordinate, sign, and telemetry contract lock

**Goal:** establish a single, testable coordinate chain from the motor drive to the rigid-link coordinate used by PSDM.

### Step 0.1: Define frames and the kinematic reference posture

1. Document the PSDM base frame and its orientation with respect to the robot installation.
2. Document the gravity vector `g` in that base frame. PSDM requires a unit vector that points upward, against gravity.
3. Define one kinematic reference posture `q_ref`. It is normally the vector represented by the adopted DH offsets and URDF zero coordinates.
4. Document the tool frame and state whether the tool inertia is included in the rigid-body model or handled as a separate known wrench `tau_ee`.

**Output:** base-frame and reference-posture sections in `conventions_sheet.md`.

### Step 0.2: Define the canonical PSDM joint coordinate

For every actuated joint, define the canonical link-side coordinate `q_i` that will be supplied to PSDM.

- Revolute joint: `q_i` is in rad.
- Prismatic joint: `q_i` is in m.
- `q_i = 0` is the selected kinematic zero, not necessarily the controller home-count value.
- Positive `q_i` is a local physical joint motion. It is not an end-effector direction.

Use three distinct variable names throughout the project:

| Layer | Symbol | Unit | Meaning |
|---|---|---|---|
| Raw telemetry | `c_i` | counts | Motor-drive encoder position. |
| Optional motor coordinate | `phi_i` | rad | Motor-shaft coordinate derived from `c_i`. |
| PSDM coordinate | `q_i` | rad or m | Link-side generalized coordinate. |

Do not use the raw drive telemetry under the name `q` in processed PSDM data.

### Step 0.3: Populate `conventions_sheet.md`

The joint table records the local generalized-coordinate convention. It does not record a global end-effector direction.

```markdown
## Joint conventions
| Joint | Type | q unit | +q direction, local physical meaning | Direction frame | q=0 definition | PSDM t_i | PSDM s_i | Lower | Upper | Positive generalized effort |
|---|---|---|---|---|---|---:|---:|---:|---:|---|
| J1 | revolute | rad | Right-hand rotation about +Z_J1 | J1 | [reference description] | 0 | [±1] | [value] | [value] | [see definition below] |
| P3 | prismatic | m | Child link translates along +Z_P3 | P3 | [reference description] | 1 | [±1] | [value] | [value] | [see definition below] |
```

#### Column definitions: `PSDM t_i`, `PSDM s_i`, and `Positive generalized effort`

These columns serve different purposes. Do not encode gearbox ratios or encoder corrections in `s_i` or in the effort column.

##### `PSDM t_i` (joint-type selector)

Fifth column of the PSDM DH row (PSDM-README Section 2.1). It selects which DH variable receives `q_i`:

| Value | Joint type | PSDM combination (README Eq. (5)) |
| --- | --- | --- |
| `0` | Revolute | `theta_i* = theta_i + s_i * q_i` |
| `1` | Prismatic | `d_i* = d_i + s_i * q_i` |

Set from joint type only.

##### `PSDM s_i` (DH sign)

Sixth column; must be `+1` or `-1`. It defines whether increasing canonical link-side `q_i` increases (`+1`) or decreases (`-1`) the active DH variable (`theta_i` or `d_i`).

Distinct from `encoder_to_q_sign` in `actuator_to_joint_map.yaml`. Assign after canonical `+q` is fixed; verify with FK validation.

##### `Positive generalized effort`

`tau_i` denotes generalized effort: Nm for revolute joints, N for prismatic joints (axial force). This column states how **positive** `tau_meas_i = Keff_i * i_i` relates to the local `+q` direction (for example, whether positive current produces torque or force that tends to increase `q_i`). Document any sign inversion relative to `+q` explicitly so regression labels stay consistent.

For the example prismatic joint `P3`, write `+Z_P3`, not only `+Z`. Write `+Z_base` only when the axis is fixed in the base frame for every reachable preceding-joint configuration.

For a downstream joint, do not assume all preceding joints are zero to define `+q`. Define `+q` in the joint or parent-link frame. An optional note may state the base-frame direction at `q_ref`, for example, `at q_ref, +Z_P3 aligns with +Z_base`.

### Step 0.4: Define the actuator-to-joint coordinate map

For each joint, create one entry in `actuator_to_joint_map.yaml` with the following minimum fields:

```yaml
J1:
  joint_type: revolute
  encoder_counts_per_motor_rev: [value]
  motor_revs_per_output_rev: [value]
  encoder_count_at_q_zero: [value]
  q_offset_at_reference: 0.0
  encoder_to_q_sign: 1
P3:
  joint_type: prismatic
  encoder_counts_per_motor_rev: [value]
  motor_revs_per_output_rev: [value]
  screw_lead_m_per_output_rev: [value]
  encoder_count_at_q_zero: [value]
  q_offset_at_reference: 0.0
  encoder_to_q_sign: 1
```

With `C_i` defined as encoder counts per motor revolution and `R_i` defined as motor revolutions per output-shaft revolution, the nominal map is:

```text
phi_i   = 2*pi * (c_i - c_ref_i) / C_i

revolute:  q_i = q_offset_i + sigma_enc_i * phi_i / R_i
prismatic: q_i = q_offset_i + sigma_enc_i * lead_i * phi_i / (2*pi*R_i)
```

Equivalently:

```text
revolute:  q_i = q_offset_i + sigma_enc_i * 2*pi*(c_i-c_ref_i)/(C_i*R_i)
prismatic: q_i = q_offset_i + sigma_enc_i * lead_i*(c_i-c_ref_i)/(C_i*R_i)
```

`qdot_i` and `qddot_i` are obtained from the same physical map. Apply the conversion before engineering-limit checks and before PSDM regression. Prefer filtering and numerical differentiation in canonical joint units.

A constant encoder-reference offset belongs in this actuator-to-joint map. A fixed kinematic offset between URDF/DH frames belongs in the DH constants. Do not encode the same physical offset in both locations.

**[Needs confirmation]** Ratio direction, sign, and ball-screw lead definition must be verified against mechanics and firmware. A ratio defined as output revolutions per motor revolution requires the reciprocal of `R_i` above.

### Step 0.5: Separate telemetry sign from DH sign

`encoder_to_q_sign` and the PSDM DH sign `s_i` are distinct quantities:

- `encoder_to_q_sign` maps raw increasing encoder count to the canonical physical `+q_i` convention.
- `s_i` maps canonical `+q_i` into the DH row's increasing `theta_i` or `d_i` direction.

Do not use both signs to compensate the same reversal. The required FK check verifies their combined effect.

### Step 0.6: Define the raw and processed data contracts

**Raw drive-side log contract:**

| Field | Unit | Description |
|---|---|---|
| `t` | s | Monotonic timestamp. |
| `c_1..c_n` | counts | Raw encoder positions at motor drive. |
| `cdot_1..cdot_n` | counts/s, optional | Raw drive velocity if exported. |
| `i_1..i_n` | A | Signed motor current. |
| `cycle_dt_nominal` | s | Nominal cycle period. |
| `cycle_dt_measured` | s | Measured `t[k] - t[k-1]`. |

**Processed PSDM dataset contract:**

| Field | Unit | Description |
|---|---|---|
| `t` | s | Timestamp after any documented resampling. |
| `q_1..q_n` | rad or m | Canonical link-side coordinates. |
| `qdot_1..qdot_n` | rad/s or m/s | Canonical link-side velocities. |
| `qddot_1..qddot_n` | rad/s² or m/s² | Canonical link-side accelerations. |
| `tau_meas_1..tau_meas_n` | Nm or N | Current-derived generalized effort. |

### Step 0.7: Execution checklist

Confirm before Phase 1:

- [ ] URDF chain, selected base link, and selected tool link are fixed.
- [ ] The physical reference posture and corresponding encoder counts are known.
- [ ] The direction of positive encoder count, positive motor current, and positive physical joint motion is documented per axis.
- [ ] Prismatic-axis ball-screw lead and transmission direction are documented.
- [ ] The PSDM toolbox loads without error (`help PSDM.deriveModel`).

**Gate 0:** `conventions_sheet.md` and `actuator_to_joint_map.yaml` are reviewed by a person with access to the mechanism and drive-firmware conventions. Do not proceed using inferred signs only.

## Phase 1: URDF to PSDM kinematics

**Goal:** produce a validated six-column standard-DH matrix and gravity vector for `PSDM.deriveModel(DH, g)`.

### Step 1.1: Extract the selected serial URDF chain

1. Select an explicit `base_link` and `tool_link`.
2. Resolve the unique actuated chain between them.
3. Record every actuated joint's name, type, parent link, child link, local axis, origin transform, and limits.
4. Fold fixed joints into the adjacent kinematic transform, while retaining a report of every folded transform.

**Output:** `urdf_kinematics.json`.

### Step 1.2: Generate a candidate standard-DH representation

PSDM documents the DH input order:

```text
DH = [a_i, alpha_i, d_i, theta_i, t_i, s_i]
```

where `t_i = 0` for revolute joints and `t_i = 1` for prismatic joints. The effective variable is:

```text
d_i_star     = d_i     + t_i       * s_i * q_i
theta_i_star = theta_i + (1 - t_i) * s_i * q_i
```

Use the standard-DH convention expected by PSDM. Do not pass a modified-DH table directly to PSDM without a documented conversion.

The candidate DH generator must:

1. Construct DH frames from the selected serial chain.
2. Put fixed geometric offsets into constant `a_i`, `alpha_i`, `d_i`, and `theta_i` values.
3. Set `t_i` from joint type.
4. Set `s_i` from the relationship between the already-defined canonical `+q_i` and the increasing DH variable.
5. Do not insert the encoder-reference offset into `d_i` or `theta_i` a second time.
6. Preserve the explicit mapping from URDF joint name to DH row.

**Output:** `dh_candidate.csv`, `dh_candidate.mat`, and `dh_mapping_report.md`.

### Step 1.3: State automation boundaries

A URDF parser can reliably produce a draft of the chain, joint axes, limits, and fixed transforms. It cannot complete the physical convention set because a URDF normally does not provide encoder counts, gearbox definitions, ball-screw lead, firmware current sign, or the physical encoder value at kinematic zero.

Therefore, `urdf_to_dh.py` is a candidate-generation and validation tool. It must not automatically approve `conventions_sheet.md` or `dh_table.mat`.

Its expected outputs are:

```text
urdf_kinematics.json
conventions_sheet.draft.md
dh_candidate.csv
dh_candidate.mat
dh_mapping_report.md
fk_validation_report.md
```

### Step 1.4: Define gravity vector

1. Express `g` in the PSDM base frame.
2. Normalize it to unit length.
3. Use `g = [0; 0; 1]` only when the PSDM base `+Z` axis is upward.

**Output:** `g` recorded beside the approved DH matrix.

### Step 1.5: Validate URDF FK against DH FK

Use the same canonical `q` values for both models.

1. Evaluate the reference posture.
2. Evaluate representative poses planned for calibration.
3. Evaluate random valid joint configurations. Use the URDF joint limits after mapping them into the canonical coordinate definition.
4. Compare the selected tool-frame position and orientation.
5. If a mismatch occurs, investigate in this order: reference offset, `encoder_to_q_sign`, `s_i`, DH frame placement, fixed-transform folding.

**[Needs confirmation]** Position and orientation tolerances must reflect the geometric quality of the URDF and the intended model fidelity. The earlier values of 1 mm and 0.1 deg remain reasonable starting criteria only when the URDF is intended to be geometrically accurate.

**Output:** `fk_validation_report.md` with test poses, maximum errors, and pass/fail result.

### Step 1.6: MATLAB import check

```matlab
S = load('dh_table.mat', 'DH');
DH = S.DH;

g = [0; 0; 1];  % Replace with the approved unit gravity vector.

assert(size(DH, 2) == 6, 'DH must have six columns.');
assert(all(DH(:, 5) == 0 | DH(:, 5) == 1), 't_i must be 0 or 1.');
assert(all(abs(DH(:, 6)) == 1), 's_i must be +1 or -1.');
assert(abs(norm(g) - 1) < 1e-12, 'g must be a unit vector.');
```

**Gate 1:** the approved `dh_table` reproduces URDF FK at the selected tool frame. Do not derive or calibrate a PSDM model before this gate passes.

## Phase 2: PSDM model derivation

**Goal:** derive the PSDM exponent matrix `E` and page matrix `P` from approved kinematics.

### Step 2.1: Install and record the PSDM implementation

1. Add the repository root to the MATLAB path.
2. Record the repository commit hash in the identification run log.
3. Run `help PSDM.deriveModel` and retain the command output with the run artifacts.
4. Run `PSDM.make()` only when MATLAB Coder and a supported compiler are available.

### Step 2.2: Optional inertial-structure mask `X`

The PSDM README defines `X` as a DOF-by-10 inertial-structure matrix. Entries that are exactly zero are omitted during derivation. An optional eleventh column represents drive inertia or drive mass, depending on joint type.

Use `X` only for parameters independently justified as structurally zero or negligible. Do not set uncertain entries to zero merely to obtain a smaller regressor.

### Step 2.3: Derive full and gravity-only models

```matlab
[E, P] = PSDM.deriveModel(DH, g);

% Optional structural simplification:
% [E, P] = PSDM.deriveModel(DH, g, X);

% Optional gravity-only model for sequential calibration:
% [E_grav, P_grav] = PSDM.deriveModel(DH, g, [], ...
%     'gravity_only', true);
```

Record all inputs and options. `E` has `5*n` rows and one column per retained basis function. `P` has dimensions `p x ell x n`, where `P(:,:,i)` is the reduction matrix for joint `i`.

**Output:** `psdm_model.mat`, containing `E`, `P`, `DH`, `g`, optional `X`, MATLAB version, PSDM commit hash, and derivation options.

### Step 2.4: Determine model dimensions and nominal reference vector

```matlab
p   = size(E, 2);
ell = size(P, 2);
```

If reliable link inertial data are available, obtain a nominal parameter vector only for a model-structure and magnitude sanity check:

```matlab
% Theta_nom = PSDM.X2Theta(E, P, DH, g, X_nominal);
```

Do not use URDF inertial values as identified values unless their provenance supports that use.

### Step 2.5: Optional complexity reduction

Use complexity reduction only after a full model has been retained and validated.

```matlab
% [Eh, Ph] = PSDM.reduceModelComplexity(E, P, DH, g, X, ...
%     'mode', 'rel_error', 'max_relative_error', 0.001);
```

For mixed joint types, provide explicit `qlim`, `qd_lim`, and `qdd_lim` values in consistent rad/m units when using a reduction study. Do not rely on revolute-joint defaults for prismatic axes.

### Step 2.6: Sanity test

```matlab
n = size(DH, 1);
Q   = zeros(n, 10);
Qd  = zeros(n, 10);
Qdd = zeros(n, 10);
Theta_test = ones(size(P, 2), 1);

tau = PSDM.inverseDynamics(E, P, Theta_test, Q, Qd, Qdd);
assert(isequal(size(tau), [n, 10]));
```

**Gate 2A:** `psdm_model.mat` loads, dimensions are consistent, and the inverse-dynamics evaluator runs for canonical link-side coordinates.

## Phase 3: Real-robot data conversion, collection, and preprocessing

**Goal:** produce train and validation datasets with canonical `q`, `qdot`, `qddot`, and generalized-effort labels `tau_meas`.

### Step 3.1: Convert raw drive telemetry into PSDM coordinates

Apply the approved `actuator_to_joint_map.yaml` to every raw log.

1. Convert counts `c` to canonical link-side `q` using Step 0.4.
2. Apply the same conversion to drive-provided velocity only when its signal is demonstrably derived from the same encoder and timestamp base.
3. Filter and differentiate canonical `q` when drive velocity or acceleration does not meet the signal-quality requirement.
4. Retain raw signals in the processed dataset only as traceability fields. Do not feed them to PSDM.
5. Verify each converted coordinate against position limits and known reference poses.

**Acceptance evidence:** one static reference check and one slow positive-direction motion check per axis. For each check, the recorded canonical `q_i` must change in the documented positive direction.

### Step 3.2: Resolve current to generalized effort, Checkpoint A

Define `Keff_i` as generalized effort per ampere:

| Joint type | `tau_meas_i` unit | `Keff_i` unit |
|---|---|---|
| Revolute | Nm | Nm/A |
| Prismatic | N | N/A |

The measured generalized-effort vector is:

```text
tau_meas_i = Keff_i * i_i
```

For a revolute axis, `Keff_i` includes motor torque constant, transmission ratio, sign, and any accepted efficiency policy. For a ball-screw prismatic axis, it also includes the screw torque-to-force conversion and lead.

**[Inference]** With `R_i = motor revolutions / output-shaft revolution`, a directly driven ball screw with lead `L_i` has an ideal signed scale proportional to `2*pi*R_i*Kt_motor_i/L_i`. Actual loss and sign policies must be established from mechanics and firmware evidence, not inferred from this relation alone.

Record per-axis derivation, units, signs, ratios, lead, and validation result in `actuator_effort_conversion_notes.md`.

Use the Denso-paper known-mass procedure to validate or calibrate the scale:

```text
diag(Keff) * (i_w - i_nom) = J(q)^T * f_w
```

`J(q)^T*f_w` yields Nm rows for revolute joints and N rows for prismatic joints.

**Checkpoint A:** signs and magnitudes of `tau_meas` are consistent with known loads for every joint. A global least-squares identification must not begin before this checkpoint passes.

### Step 3.3: Design excitation trajectories

Use trajectories that correspond to the intended calibration step:

| Calibration step | Trajectory intent |
|---|---|
| Actuator-effort scale | Slow forward and reverse sweeps, with and without a known tool mass. |
| Gravity | Slow motion outside the static-friction regime and with negligible inertial contribution. |
| Friction | Per-joint sinusoids covering small and large displacement and a range of speeds. |
| Inertia | Coordinated rich trajectories that excite accelerations and velocity products without violating all axis limits. |

All limits must be expressed in canonical joint units. For prismatic axes, use m, m/s, and m/s². Record every trajectory's purpose, limits, payload state, and input files in `trajectory_manifest.md`.

### Step 3.4: Log raw data

1. Log at EtherCAT rate with raw timestamps.
2. Log raw encoder counts and signed current rather than only a controller-transformed position.
3. Ensure position and current records share a clock. If they do not, define and validate a time-alignment policy.
4. Store raw logs immutably.

### Step 3.5: Characterize timing, Checkpoint B

1. Compute the mean, standard deviation, minimum, maximum, and outlier rate of `dt`.
2. Produce `timing_quality_report.md` with timing plots and time-alignment evidence.
3. Select native-time processing or resampling to a uniform grid. The threshold is **[Needs confirmation]** and must be justified from observed jitter and the required inertial bandwidth.

### Step 3.6: Filter, differentiate, and validate canonical state signals

1. Resample if required by Step 3.5.
2. Filter canonical `q` or `qdot` using a recorded method, order, and cutoff.
3. Estimate `qdot` and `qddot` in canonical units.
4. Trim filter-transient samples from regression sets.
5. Validate position, velocity, and acceleration against independent limits and commanded motion.

The application preprint uses zero-phase Butterworth filtering for experimental datasets. Its cutoffs are examples, not universal defaults. The selected configuration belongs in `derivative_filter_config.yaml`.

### Step 3.7: Split datasets

1. Split train and validation data by trajectory where possible. Avoid random sample splitting of a single correlated trajectory.
2. Preserve held-out trajectories for final acceptance only.
3. Label each dataset by calibration purpose and payload state.

**Output:** `processed_data/` with canonical state signals, `tau_meas`, manifests, and reproducible conversion configuration.

**Gate 2B:** Checkpoints A and B are complete, and all regression input units are link-side physical units.

## Phase 4: Parameter identification

**Goal:** identify the PSDM base parameter vector and any separate actuator or friction parameters.

### Identification modes

- **Mode A, recommended for a first robot:** sequential calibration following the Denso application preprint.
- **Mode B:** direct full-model least squares only when friction is demonstrably negligible or has already been removed and `tau_meas` is trusted.

### Mode A: Sequential calibration

Use the decomposition:

```text
tau_meas = tau_psdm + tau_fric + tau_ee
tau_psdm = tau_grav + tau_iner
```

For a mixed chain, every component is generalized effort with per-joint Nm or N units.

#### Step 4A.1: Actuator-effort calibration

1. Use slow forward and reverse sweeps with and without a known end-effector mass.
2. Average forward and reverse current only after verifying the friction symmetry assumption for the relevant range.
3. Fit or validate `Keff` with the known-wrench equation in Step 3.2.
4. Store resulting `Keff`, units, validation metrics, and payload data.

#### Step 4A.2: Gravity calibration

1. Derive or extract a gravity-only PSDM regressor.
2. Use slow-motion data and current-derived `tau_meas`.
3. Subtract the known end-effector wrench if it is treated separately.
4. Fit `theta_grav` and validate gravity prediction on held-out slow trajectories.

The gravity-only parameter vector is used to predict `tau_grav_hat`. Do not assume it is index-compatible with the base-parameter vector of the full PSDM model.

#### Step 4A.3: Friction calibration

1. Compute the friction residual:

```text
tau_fric_meas = tau_meas - tau_grav_hat - tau_ee
```

2. Fit the selected friction model per axis. The Denso preprint uses LuGre friction. A simpler model is acceptable only when validation demonstrates that it is sufficient for the intended use.
3. Store `tau_fric_hat` as a separate model output.

#### Step 4A.4: Inertial-regressor and full-model fit

1. Use `tau_iner_meas = tau_meas - tau_grav_hat - tau_fric_hat - tau_ee` to assess inertial excitation and fit the inertia-only contribution.
2. Monitor regressor conditioning in the trajectory design and after data selection.
3. Use regularization only with a recorded selection rationale and validation comparison.
4. Obtain the final full PSDM parameter vector by fitting the complete `E, P` model to effort after subtracting separately modeled friction and known external wrench:

```text
tau_psdm_target = tau_meas - tau_fric_hat - tau_ee
Theta_full = argmin ||Y_full * Theta_full - tau_psdm_target||^2
```

This final full-model fit retains gravity and inertial terms in one parameter vector compatible with `PSDM.inverseDynamics(E, P, Theta_full, ...)`.

### Mode B: Direct identification

Use Mode B only when the target generalized effort already excludes friction and known external effects, or when their omission has been accepted against validation data.

For each sample, evaluate `yp(q, qdot, qddot)` using canonical link-side data, form `yp*P_i`, and stack joint rows into `Y_full`. Solve against the matching stacked generalized-effort vector.

```matlab
Yp = PSDM.generateYp(Q, Qd, Qdd, E);
Y_full = utilities.vertStack(utilities.blockprod(Yp, P));
tau_vec = reshape(tau_psdm_target, [], 1);
Theta_full = Y_full \ tau_vec;
```

Report conditioning, residuals by joint, and validation performance. Compare with a nominal `PSDM.X2Theta` result only as a structural sanity reference when trustworthy inertial data exist.

### Step 4.3: Optional reflected drive inertia

The PSDM implementation accepts an optional eleventh `X` column for drive inertia or drive mass. Include it only when the effect is both physically relevant and represented in the chosen joint-side coordinate convention.

For a geared axis, reflected motor inertia is affected by the transmission coordinate map. **[Needs confirmation]** Its treatment must be consistent with whether `q` is an output-joint angle or a linear ball-screw displacement.

Friction remains external to the standard rigid-body PSDM regressor and must be added or subtracted as a separate model component.

**Gate 3:** a candidate `Theta_full`, `Keff`, and friction model are accepted only when held-out generalized-effort prediction meets documented per-joint targets.

## Phase 5: Validation and digital-twin packaging

**Goal:** demonstrate prediction accuracy on held-out data and package a reproducible joint-side model.

### Step 5.1: Validate generalized-effort prediction

```matlab
tau_psdm_hat = PSDM.inverseDynamics(E, P, Theta_full, Q, Qd, Qdd);
tau_hat = tau_psdm_hat + tau_fric_hat + tau_ee;
```

1. Compare `tau_hat` with `tau_meas` on held-out trajectories.
2. Report RMSE, R², maximum error, and residual spectral evidence per joint.
3. Report units per joint. Do not label prismatic-axis residuals as Nm.
4. Separate slow gravity-dominant and high-excitation inertial results.
5. Confirm that all inputs are canonical joint-side state variables.

### Step 5.2: Forward-dynamics check, optional

```matlab
Qdd_sim = PSDM.forwardDynamics(E, P, Theta_full, Q, Qd, tau_psdm_target);
```

Compare `Qdd_sim` to processed canonical `qddot`. This is a consistency check, not a replacement for held-out effort validation.

### Step 5.3: Export the model package

| File | Content |
|---|---|
| `psdm_model.mat` | `E`, `P`, `DH`, `g`, optional `X`, derivation metadata. |
| `theta_b.mat` | `Theta_full` and fit metadata. |
| `actuator_to_joint_map.yaml` | Encoder-to-canonical-coordinate mapping. |
| `actuator_effort_conversion_notes.md` | Current-to-generalized-effort conversion evidence. |
| `friction_model.*` | Separate friction parameters and implementation, if used. |
| `conventions_sheet.md` | Frames, local `+q` directions, reference posture, limits, and signs. |
| `fk_validation_report.md` | URDF-to-DH validation evidence. |
| `derivative_filter_config.yaml` | Preprocessing configuration. |
| `validation_report.md` | Held-out validation metrics and plots. |

### Step 5.4: Fast code generation, optional

```matlab
PSDM.makeInverseDynamics('id_psdm', E, P, Theta_full);
PSDM.makeForwardDynamics('fd_psdm', E, P, Theta_full);
```

The generated PSDM function models only the rigid-body term. Wrap it with the separate friction and external-wrench components when those are part of the deployed twin.

### Step 5.5: Define the deployment interface

```text
tau_hat = robot_inverse_dynamics(q, qdot, qddot, model_state)
```

The interface contract must state:

- joint order,
- input units per joint,
- reference coordinate definition,
- whether friction and tool wrench are included,
- output units per joint,
- valid state limits.

**Gate 4:** the package reproduces the held-out result using only versioned artifacts and meets runtime requirements.

## Phase 6: Iteration loop

Repeat affected phases when any of the following changes:

- tool or payload state,
- transmission ratio, ball-screw lead, encoder reference, or firmware sign convention,
- actuator-current scaling,
- friction behavior due to wear or temperature,
- derivative configuration,
- PSDM structural mask `X`, or
- kinematic model and DH table.

The iteration record must state whether the change affects raw-to-joint conversion, effort labels, kinematics, or only dynamic fitting. Re-run Gate 1 whenever the kinematic coordinate definition changes. Re-run Checkpoint A whenever the effort conversion changes.

## Approval gates summary

| Gate | Criterion | Blocking point |
|---|---|---|
| **Gate 0** | Canonical coordinate definitions, local `+q` conventions, and actuator-to-joint map reviewed. | Before DH conversion. |
| **Gate 1** | URDF FK and DH FK agree using the same canonical `q`. | Before `deriveModel`. |
| **Gate 2A** | PSDM model derives and evaluates with canonical input dimensions. | Before real-data regression. |
| **Gate 2B** | Current-to-effort conversion and timing/differentiation policies validated. | Before regression. |
| **Gate 3** | Held-out generalized-effort prediction meets defined per-joint targets. | Before model release. |
| **Gate 4** | Package and deployment interface are reproducible and meet runtime requirements. | Before deployment. |

## Reproducibility checklist

- [ ] `conventions_sheet.md` defines all local `+q` directions and does not use an end-effector direction as a joint convention.
- [ ] `actuator_to_joint_map.yaml` maps raw counts to link-side rad or m coordinates for every axis.
- [ ] Encoder sign and DH `s_i` have been verified independently and jointly through FK validation.
- [ ] `dh_table` passed Gate 1 with the selected tool frame.
- [ ] `psdm_model.mat` was derived from approved `DH`, `g`, and optional `X`.
- [ ] `actuator_effort_conversion_notes.md` records `Keff` in Nm/A or N/A as applicable.
- [ ] `timing_quality_report.md` and `derivative_filter_config.yaml` are complete.
- [ ] Train and validation trajectories are documented and held-out data were not used in fitting.
- [ ] `theta_b.mat`, friction model, and validation report share one model version identifier.
- [ ] Deployment interface declares joint order, units, and included model components.

## Planned companion artifacts

The following implementation artifacts are deliberately separate from this workflow:

- `urdf_to_dh.py`, which extracts a selected URDF chain and produces candidate DH and convention artifacts.
- `validate_fk.py` or equivalent, which compares URDF and standard-DH FK using canonical joint coordinates.
- `convert_raw_telemetry.m` or equivalent, which applies `actuator_to_joint_map.yaml` before preprocessing.
- MATLAB helper functions for PSDM regressor stacking, sequential calibration, and held-out validation.
- Example templates for `actuator_to_joint_map.yaml`, `actuator_effort_conversion_notes.md`, and `derivative_filter_config.yaml`.

The URDF helper must fail clearly when required mechanics or firmware data are absent. It must not manufacture encoder, transmission, or current-sign information.

## References

1. Lloyd, S., Irani, R., Ahmadi, M. (2021). *A numeric derivation for fast regressive modeling of manipulator dynamics*. Mechanism and Machine Theory, 156, 104149.
2. `PSDM-README.pdf`, Carleton ABL PSDM MATLAB package documentation.
3. Lloyd, S., Irani, R., Ahmadi, M. *Application of Pseudo-Symbolic Dynamic Modeling in the Modeling and Calibration of a 6-DOF Articulated Robot*, Denso VS-6556G preprint.
4. `critical_ambiguities.md`.
5. CarletonABL/PSDM reference repository, recorded commit hash required for each identification run.
