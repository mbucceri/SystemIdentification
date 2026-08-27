# PSDM System Identification Workflow (Student Guide)

> Proposed revision. This guide integrates actuator-to-joint coordinate conversion, prismatic-axis conventions, joint-local direction semantics, and URDF-to-DH automation boundaries.

## Purpose and scope

This is the student-oriented companion to `workflow_detailed_proposed_revised.md`. Both documents use the same phase structure.


| This guide                                                    | Engineering guide                                                 |
| ------------------------------------------------------------- | ----------------------------------------------------------------- |
| Explains why each activity is required and provides examples. | Defines required inputs, outputs, gates, and acceptance evidence. |
| Includes small MATLAB and configuration snippets.             | Avoids training material unless required to execute the process.  |
| Adds supporting appendices.                                   | Assumes the reader already knows the underlying mathematics.      |




### What you are building

You are building a numerical digital twin that predicts generalized joint effort from **link-side joint motion**:

```text
tau_i = yp(q, qdot, qddot) * P_i * theta_b
```


| Symbol               | Meaning                                                                                                                  |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `q`, `qdot`, `qddot` | Link-side generalized position, velocity, and acceleration. `q` is rad for a revolute joint and m for a prismatic joint. |
| `yp`                 | PSDM basis-function row evaluated at a joint state.                                                                      |
| `P_i`                | PSDM reduction matrix for joint `i`.                                                                                     |
| `theta_b`            | Base inertial parameter vector.                                                                                          |
| `tau_i`              | Generalized effort. Nm for a revolute joint and N for a prismatic joint.                                                 |


The raw motor-drive encoder count is **not** PSDM `q`.

### The coordinate path you must implement

```text
raw drive count c  ->  motor coordinate phi  ->  link-side q  ->  PSDM
raw motor current i ->  generalized effort tau_meas           ->  regression
```

The PSDM toolbox derives `E` and `P` from robot kinematics. Your work is to make the physical data and the kinematic model use the same joint coordinate definition before fitting `theta_b`.

**In scope:** rigid serial chains, revolute and prismatic joints, current-derived effort labels, and the sequential calibration structure used in the Denso PSDM study.

**Out of scope:** flexible joints, backlash, compliance, unmodeled cable forces, and contact/process forces.

### Why the new distinction matters

A gearbox may rotate the motor 100 revolutions while the robot link rotates one revolution. Feeding the motor angle to PSDM would make PSDM evaluate `sin(phi)` where the robot geometry requires `sin(q)`. No choice of DH sign `s_i = +1` or `-1` can correct that scale error. The raw telemetry must first become the link-side coordinate.

## Authoritative sources

Use the sources in this order:

1. **PSDM-README.pdf**, for the MATLAB calling syntax and PSDM DH convention.
2. **Lloyd et al. Denso application preprint**, for the experimental calibration sequence.
3. **Lloyd et al. (2021)**, for the PSDM theory and the treatment of revolute and prismatic coordinates.
4. `critical_ambiguities.md`, for existing decision gates around effort scaling and time derivatives.
5. **The checked-out** `CarletonABL/PSDM` **source**, for function behavior and dimensions.

The examples in this guide are implementation illustrations. Values such as sign, ratio, encoder reference, and ball-screw lead must come from the robot evidence, not from the example.

## Prerequisites



### Software setup

**Step 1: install MATLAB** R2018a or newer.

**Step 2: clone PSDM and add it to the MATLAB path.**

```bash
git clone https://github.com/CarletonABL/PSDM.git
```

```matlab
addpath(genpath('/path/to/PSDM'));
help PSDM.deriveModel
```

**Step 3, optional:** compile PSDM MEX functions when MATLAB Coder and a supported compiler are available.

```matlab
PSDM.make();
```

**Step 4:** install Python only if you will implement the proposed URDF-chain and FK-validation helper. A URDF library selection is a separate implementation decision.

### Hardware evidence checklist

Before logging data, collect:

- [ ] URDF matching the selected physical robot and tool configuration.
- [ ] Encoder scale for each actuator.
- [ ] Gearbox definition, including which side is numerator and which side is denominator.
- [ ] Ball-screw lead for every prismatic axis.
- [ ] Encoder count at the selected physical kinematic zero.
- [ ] Motor torque constant and signed-current convention.
- [ ] Joint position, velocity, acceleration, and effort limits.
- [ ] Robot base orientation and gravity direction.



### Project files to create

```text
project/
  conventions_sheet.md
  actuator_to_joint_map.yaml
  actuator_effort_conversion_notes.md
  dh_table.csv
  dh_table.mat
  fk_validation_report.md
  raw_logs/
  processed_data/
  matlab/
```

`actuator_to_joint_map.yaml` is required because `conventions_sheet.md` is readable by people but does not by itself provide the exact numeric telemetry transformation.

## Phase 0: Coordinate, sign, and telemetry contract lock

**Goal:** define one canonical coordinate system that is shared by the URDF comparison, the DH table, and the PSDM regression dataset.

### Step 0.1: Understand the three coordinate layers

For every axis, keep these names separate:


| Layer           | Symbol  | Example unit   | Meaning                                            |
| --------------- | ------- | -------------- | -------------------------------------------------- |
| Drive telemetry | `c_i`   | encoder counts | What the motor drive reports.                      |
| Motor shaft     | `phi_i` | rad            | Motor angle after count-to-angle conversion.       |
| Kinematic joint | `q_i`   | rad or m       | Link-side generalized coordinate supplied to PSDM. |


A motor-side count is only equal to a kinematic joint coordinate when there is no transmission and the units already match. Your robot has transmissions, therefore you must implement the conversion.

### Step 0.2: Define frames, gravity, and the reference posture

A reference frame is an origin and three orthogonal axes. The URDF, DH table, telemetry conversion, and PSDM model must all use compatible definitions.

PSDM `g` is a unit vector pointing upward, opposite gravity. If the base frame has `+Z` upward:

```matlab
g = [0; 0; 1];
```

Define and record `q_ref`, the kinematic reference posture. This is normally the posture represented by URDF and DH zero coordinates. Also record encoder counts at that posture.

### Step 0.3: Fill `conventions_sheet.md`

Use a joint-local direction. Do not use an end-effector direction in this table.

```markdown
# Robot conventions

## Base frame
- Origin: [physical description]
- +X: [description]
- +Y: [description]
- +Z: [description]
- Gravity vector g, unit and upward: [gx, gy, gz]
- Reference posture q_ref: [q1_ref, ..., qn_ref]

## Joint conventions
| Joint | Type | q unit | +q direction, local physical meaning | Direction frame | q=0 definition | t_i | s_i | Lower | Upper | Positive generalized effort |
|---|---|---|---|---|---|---:|---:|---:|---:|---|
| J1 | revolute | rad | Right-hand rotation about +Z_J1 | J1 | [description] | 0 | [±1] | [value] | [value] | [torque convention] |
| P3 | prismatic | m | Child link translates along +Z_P3 | P3 | [description] | 1 | [±1] | [value] | [value] | [force convention] |
```



#### What `+q direction` means

For a revolute joint, `+q` is the positive right-hand rotation about the local joint axis.

For a prismatic joint, `+q` is positive translation of the child link relative to the parent link along the local joint axis.

For the vertical-slide example, write `child link translates along +Z_P3`. You may add `at q_ref, +Z_P3 aligns with +Z_base`, but only as an optional reference-pose note.

#### Why not use an end-effector direction?

The direction of end-effector motion caused by a joint depends on the robot configuration. For a downstream prismatic joint, the base-frame direction of its local axis depends on preceding joints. You do not need to set other joints to zero to define `+q`. Define it locally. Use `q_ref` only when you want to report an illustrative base-frame direction.

### Step 0.4: Build `actuator_to_joint_map.yaml`

Example schema:

```yaml
J1:
  joint_type: revolute
  encoder_counts_per_motor_rev: 1048576
  motor_revs_per_output_rev: 100
  encoder_count_at_q_zero: 123456
  q_offset_at_reference: 0.0
  encoder_to_q_sign: 1

P3:
  joint_type: prismatic
  encoder_counts_per_motor_rev: 1048576
  motor_revs_per_output_rev: 50
  screw_lead_m_per_output_rev: 0.005
  encoder_count_at_q_zero: 654321
  q_offset_at_reference: 0.0
  encoder_to_q_sign: -1
```

With:

- `C` = encoder counts per motor revolution,
- `R` = motor revolutions per output-shaft revolution,
- `L` = screw lead in m per output-shaft revolution,
- `sigma_enc` = `encoder_to_q_sign`,

use:

```text
revolute:  q = q_offset + sigma_enc * 2*pi*(c-c_ref)/(C*R)
prismatic: q = q_offset + sigma_enc * L*(c-c_ref)/(C*R)
```

Differentiate the converted `q`, not encoder counts, unless you first apply exactly the same conversion to the derivative signal.

Put the encoder-reference offset in this map. Put a fixed URDF/DH transform offset in the DH constants. Do not put the same physical offset in both places.

**[Needs confirmation]** Verify `R` from the hardware/firmware definition. Some documentation uses the reciprocal ratio.

### Step 0.5: Understand `s_i` versus encoder sign

PSDM uses `s_i = +1` or `-1` inside its DH row. It determines whether an increasing canonical `q_i` increases the DH `theta_i` or `d_i` variable.

Your telemetry map uses `encoder_to_q_sign`. It determines whether increasing raw encoder count creates increasing physical canonical `q_i`.

These are not interchangeable. Do not put a gearbox ratio in `s_i`, because `s_i` can only be `+1` or `-1`.

### Step 0.6: Data contract

**Raw file example:**

```text
t, c1, c2, ..., cn, current1, current2, ..., currentn
```

**Processed PSDM file example:**

```text
t, q1, q2, ..., qn, qdot1, ..., qdotn, qddot1, ..., qddotn, tau_meas1, ..., tau_measn
```

Store raw files unchanged. Add conversion configuration and processed results separately.

### Step 0.7: Gate 0

Before proceeding, verify for each axis:

1. At the reference posture, converted `q` equals the documented reference coordinate.
2. A small physical positive joint movement produces an increase in canonical `q`.
3. A positive current produces the documented positive generalized-effort direction, or the opposite relationship is explicitly recorded.

Do not continue while any sign is inferred rather than checked.

## Phase 1: URDF to PSDM kinematics

**Goal:** produce a validated standard-DH table that consumes the canonical link-side `q` from Phase 0.

### Step 1.1: Parse the selected URDF chain

A URDF describes a tree. PSDM requires the selected serial chain from a base link to a tool link.

For every actuated joint on that path, extract:

- name,
- type,
- parent and child links,
- origin transform,
- local axis,
- limits.

Fixed joints are not ignored. Their transforms must be folded into the adjacent kinematic relationship and listed in the mapping report.

**Output:** `urdf_kinematics.json`.

### Step 1.2: What a URDF parser can and cannot generate

A parser can generate a candidate:

```text
urdf_kinematics.json
conventions_sheet.draft.md
dh_candidate.csv
dh_candidate.mat
dh_mapping_report.md
```

It cannot finalize the physical conventions because a typical URDF does not know your encoder scale, gearbox ratio, screw lead, encoder reference count, drive current sign, or firmware coordinate conversion.

Therefore, the script is a draft generator and FK test tool. It is not an authority that can approve a DH table automatically.

### Step 1.3: Build the PSDM standard-DH table

PSDM uses the six-column input:

```text
[a_i, alpha_i, d_i, theta_i, t_i, s_i]
```

with:

```text
d_i_star     = d_i     + t_i       * s_i * q_i
theta_i_star = theta_i + (1 - t_i) * s_i * q_i
```

- `t_i = 0` for revolute joints.
- `t_i = 1` for prismatic joints.
- `s_i` is a sign only. It does not contain the gearbox ratio or ball-screw lead.

Use the standard-DH convention expected by PSDM. Do not put a modified-DH table directly into `PSDM.deriveModel`.

### Step 1.4: Candidate-generation procedure

1. Select DH frames from the ordered serial chain.
2. Encode fixed geometry in `a`, `alpha`, `d`, and `theta`.
3. Assign `t_i` from joint type.
4. Choose `s_i` so canonical positive `q_i` produces the same local physical joint motion in URDF FK and DH FK.
5. Do not copy the encoder-reference offset into `d_i` or `theta_i` a second time.
6. Save the candidate table with joint-name to row mapping.



### Step 1.5: Validate FK

URDF-to-DH conversion is not unique. The proof that the selected table is usable is an FK comparison performed with the same canonical `q` values.

1. Check the reference posture.
2. Check planned calibration poses.
3. Check random valid poses.
4. Compare tool-frame position and orientation.
5. Investigate mismatch in this order: coordinate offset, encoder map sign, DH sign `s_i`, fixed transforms, frame assignment.

Write results to `fk_validation_report.md`.

### Step 1.6: MATLAB import check

```matlab
S = load('dh_table.mat', 'DH');
DH = S.DH;

assert(size(DH, 2) == 6);
assert(all(DH(:,5) == 0 | DH(:,5) == 1));
assert(all(abs(DH(:,6)) == 1));
```

**Gate 1:** FK validation passed. Do not derive a PSDM model before this result exists.

## Phase 2: PSDM model derivation

**Goal:** derive `E` and `P` from the approved DH table.

### Step 2.1: Confirm the PSDM installation

```matlab
which PSDM.deriveModel
help PSDM.deriveModel
```

Record the checked-out repository commit hash with every model derivation.

### Step 2.2: Optional inertial-structure mask `X`

`X` is a structural mask. A zero means that the corresponding inertial term is treated as absent in the derivation. It is not a fitted parameter vector.

```matlab
n = size(DH, 1);
X = ones(n, 10);
X(:, 8:10) = 0;  % Use only when justified by independent evidence.
```

An optional eleventh column may represent drive inertia or drive mass. Use it only after confirming how it is reflected into the output-joint coordinate.

### Step 2.3: Derive the model

```matlab
[E, P] = PSDM.deriveModel(DH, g);

% With a justified structural mask:
% [E, P] = PSDM.deriveModel(DH, g, X);

% Gravity-only model for sequential calibration:
% [E_grav, P_grav] = PSDM.deriveModel(DH, g, [], ...
%     'gravity_only', true);
```

The useful dimensions are:

```matlab
p = size(E, 2);     % retained PSDM basis functions
ell = size(P, 2);   % full-model base parameters
```

`P` is a page matrix of size `p x ell x DOF`.

### Step 2.4: Nominal parameter sanity check

When URDF inertial properties are trustworthy enough to use as a nominal reference:

```matlab
% Theta_nom = PSDM.X2Theta(E, P, DH, g, X_nominal);
```

This does not identify the real robot. It only gives a compatible PSDM parameter vector for a known hypothetical model.

### Step 2.5: Optional complexity reduction

```matlab
% [Eh, Ph] = PSDM.reduceModelComplexity(E, P, DH, g, X, ...
%     'mode', 'rel_error', 'max_relative_error', 0.001);
```

For prismatic axes, supply appropriate meter-based limits to any reduction study. Do not use angular default limits blindly.

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

**Gate 2A:** the model evaluates with link-side coordinates in the correct dimensions.

## Phase 3: Convert telemetry, collect data, and preprocess

**Goal:** produce clean PSDM inputs `q`, `qdot`, `qddot` and a current-derived generalized-effort label `tau_meas`.

### Step 3.1: Convert encoder counts to canonical `q`

Use `actuator_to_joint_map.yaml` before filtering or regression.

```matlab
% Illustrative conversion for a revolute axis.
q = q_offset + encoder_to_q_sign * ...
    2*pi*(c - c_ref)/(counts_per_motor_rev*motor_revs_per_output_rev);
```

For a prismatic ball-screw axis:

```matlab
q = q_offset + encoder_to_q_sign * ...
    screw_lead_m_per_output_rev*(c - c_ref) / ...
    (counts_per_motor_rev*motor_revs_per_output_rev);
```

Use the same scale and sign when converting a drive-provided count-rate signal. Prefer filtering and numerical differentiation after `q` is in rad or m.

#### Required checks

- At the reference posture, `q` matches the documented value.
- At a small positive physical motion, `q` increases.
- The signal stays within the documented link-side limits.



### Step 3.2: Convert current to generalized effort, Checkpoint A

The Denso paper uses a joint-side effective torque constant. Generalize the notation so it remains correct for a prismatic axis:

```text
tau_meas_i = Keff_i * i_i
```


| Joint type | `Keff_i` | `tau_meas_i` |
| ---------- | -------- | ------------ |
| Revolute   | Nm/A     | Nm           |
| Prismatic  | N/A      | N            |


For a prismatic axis, `Keff` combines motor torque constant, gearbox effect, ball-screw lead, signs, and the documented efficiency policy.

**[Inference]** Under an ideal direct ball-screw transmission, the force scale is proportional to motor torque divided by lead and multiplied by the motor-to-output reduction ratio. The exact equation depends on the ratio definition and mechanical loss policy.

Calibrate or validate the effort scale using a known mass and the equation from the Denso paper:

```text
diag(Keff) * (i_with_mass - i_nominal) = J(q)^T * f_weight
```

The Jacobian transpose returns a torque for a revolute row and a force for a prismatic row.

### Step 3.3: Design trajectories


| Activity                 | Required trajectory property                               |
| ------------------------ | ---------------------------------------------------------- |
| Effort-scale calibration | Slow forward and reverse motion, known added mass.         |
| Gravity fit              | Slow motion, low inertial effect, outside static friction. |
| Friction fit             | One-axis sinusoids, multiple amplitudes and speeds.        |
| Inertial fit             | Rich coordinated acceleration and velocity excitation.     |


All trajectory limits must be applied after conversion to canonical rad/m units.

### Step 3.4: Log raw data

1. Log raw timestamps, counts, and signed current at the EtherCAT rate.
2. Preserve the raw data unchanged.
3. Verify that current and position use a shared clock. If not, state the interpolation policy.



### Step 3.5: Check timestamps, Checkpoint B

```matlab
dt = diff(t);
fprintf('mean %.6g, std %.6g, min %.6g, max %.6g
', ...
    mean(dt), std(dt), min(dt), max(dt));
```

Select uniform-grid resampling only when the measured timing quality and derivative bandwidth justify it. Record the decision in `timing_quality_report.md`.

### Step 3.6: Filter and estimate derivatives

Filter link-side `q` or `qdot`, then estimate derivatives. Do not tune a cutoff in encoder-count units.

```matlab
fs = 1000;        % Example only.
fc = 40;          % Must be selected from actual signal bandwidth.
[b, a] = butter(4, fc/(fs/2));
q_filt = filtfilt(b, a, q, [], 2);
qdot = gradient(q_filt, 1/fs);
qddot = gradient(qdot, 1/fs);
```

Trim endpoint and filter-transient samples before fitting.

### Step 3.7: Split train and validation trajectories

Keep complete held-out trajectories. Do not allow samples from the same highly correlated motion record to appear in both fitting and final acceptance datasets.

**Gate 2B:** coordinate conversion, `Keff`, timing, filtering, and derivative policy are documented and accepted.

## Phase 4: Parameter identification

**Goal:** identify the full PSDM base parameter vector and any separate friction or actuator-effort parameters.

### Helper function: build the full PSDM regressor

Save as `matlab/build_psdm_regressor.m`:

```matlab
function Y_stack = build_psdm_regressor(E, P, Q, Qd, Qdd)
% Q, Qd, Qdd are DOF x N canonical link-side arrays.

    Yp = PSDM.generateYp(Q, Qd, Qdd, E);   % N x p
    Yb = utilities.blockprod(Yp, P);        % N x ell x DOF
    Y_stack = utilities.vertStack(Yb);      % (N*DOF) x ell
end
```

If `tau` is stored as `DOF x N`, use:

```matlab
tau_vec = reshape(tau, [], 1);
```

This has the same sample-then-joint ordering as `utilities.vertStack(Yb)`.

### Mode A: Sequential calibration, recommended

Use the physical decomposition:

```text
tau_meas = tau_psdm + tau_fric + tau_ee
tau_psdm = tau_grav + tau_iner
```

All these terms have per-joint generalized-effort units. They are not all torques in a mixed chain.

#### Step 4A.1: Actuator-effort calibration

1. Use low-speed sweeps, forward and reverse, with and without a known tool mass.
2. Fit or validate `Keff`.
3. Store values in the same joint order as the DH table.
4. Validate signs and magnitudes on held-out known-load data.



#### Step 4A.2: Gravity calibration

Derive a gravity-only PSDM model:

```matlab
[E_grav, P_grav] = PSDM.deriveModel(DH, g, [], ...
    'gravity_only', true);
```

Build and fit its regressor from slow data:

```matlab
Y_grav = build_psdm_regressor(E_grav, P_grav, q, ...
    zeros(size(q)), zeros(size(q)));

tau_target = tau_meas - tau_ee;
theta_grav = Y_grav \ reshape(tau_target, [], 1);
tau_grav_hat = reshape(Y_grav * theta_grav, size(tau_meas));
```

The gravity-only parameter vector is not guaranteed to use the same base-parameter coordinates as the complete model. Use it to predict gravity and isolate friction, not to fill entries of `Theta_full` by hand.

#### Step 4A.3: Friction calibration

```matlab
tau_fric_meas = tau_meas - tau_grav_hat - tau_ee;
```

Fit LuGre friction as in the preprint, or justify a simpler model by held-out residual behavior. Store friction outside PSDM.

#### Step 4A.4: Inertial assessment and full-model fit

First inspect the inertia-dominant residual:

```matlab
tau_iner_meas = tau_meas - tau_grav_hat - tau_fric_hat - tau_ee;
```

Use it to evaluate excitation and conditioning. Then fit one full PSDM parameter vector compatible with the original `E, P`:

```matlab
Y_full = build_psdm_regressor(E, P, q, qdot, qddot);
tau_psdm_target = tau_meas - tau_fric_hat - tau_ee;
Theta_full = Y_full \ reshape(tau_psdm_target, [], 1);
```

The full fit includes both gravity and inertial PSDM terms. This avoids incorrectly combining two parameter vectors that were derived in different reduced parameter spaces.

### Mode B: Direct identification

Use only when the target effort excludes separately modeled friction and known external wrench, or when their omission has been accepted.

```matlab
Y_full = build_psdm_regressor(E, P, q, qdot, qddot);
Theta_full = Y_full \ reshape(tau_psdm_target, [], 1);
```

Inspect `cond(Y_full)` and validate on held-out trajectories. A very large condition number means the fitted parameter values may be unstable even when training residuals are small.

### Step 4.3: Optional reflected drive inertia

The PSDM implementation allows an optional eleventh `X` column for drive inertia or drive mass. For a geared or ball-screw axis, the correct reflected quantity depends on the canonical output coordinate. Keep it out of the first model unless its reference and scaling are known.

**Gate 3:** accept the fitted model only after held-out generalized-effort validation.

## Phase 5: Validation and digital-twin packaging

**Goal:** show that the model predicts held-out generalized effort in the correct joint coordinates and units.

### Step 5.1: Predict held-out effort

```matlab
tau_psdm_hat = PSDM.inverseDynamics(E, P, Theta_full, q, qdot, qddot);
tau_hat = tau_psdm_hat + tau_fric_hat + tau_ee;
```

For each joint, report:

- RMSE,
- R²,
- peak error,
- residual spectrum or time-history plot,
- output unit, Nm or N.

A prismatic joint can have excellent validation even though its values are not comparable numerically to a revolute joint's Nm residual.

### Step 5.2: Optional forward-dynamics check

```matlab
Qdd_sim = PSDM.forwardDynamics(E, P, Theta_full, q, qdot, tau_psdm_target);
```

Compare `Qdd_sim` with processed canonical `qddot`. This checks internal consistency. It does not replace effort validation.

### Step 5.3: Export model package

```text
model_v1.0.0/
  psdm_model.mat
  theta_b.mat
  conventions_sheet.md
  actuator_to_joint_map.yaml
  actuator_effort_conversion_notes.md
  friction_model.*
  fk_validation_report.md
  derivative_filter_config.yaml
  validation_report.md
```



### Step 5.4: Optional fast code generation

```matlab
PSDM.makeInverseDynamics('robot_id', E, P, Theta_full);
PSDM.makeForwardDynamics('robot_fd', E, P, Theta_full);
```

Generated PSDM code covers the rigid-body term. Add the separately identified friction and external-wrench models in the deployment wrapper when required.

### Step 5.5: Deployment interface

```text
tau_hat = robot_inverse_dynamics(q, qdot, qddot, model_state)
```

Document joint order, units, `q=0` definition, included friction/tool effects, valid state limits, and output units.

**Gate 4:** a clean environment reproduces the validation result from the versioned package.

## Phase 6: Iteration loop

Repeat affected steps when a payload, tool, encoder reference, gearbox convention, ball-screw lead, current scaling, friction behavior, filter policy, or kinematic model changes.

A kinematic-coordinate change invalidates the raw-to-joint mapping and requires a new FK validation. A current-to-effort change requires a new Checkpoint A. Do not treat these as minor regression retunes.

## Approval gates summary


| Gate        | Student check                                                                                  |
| ----------- | ---------------------------------------------------------------------------------------------- |
| **Gate 0**  | Physical signs, canonical `q`, reference counts, and local joint directions are documented.    |
| **Gate 1**  | URDF and DH FK agree for the same canonical `q` test poses.                                    |
| **Gate 2A** | PSDM derives and evaluates with the approved DH table.                                         |
| **Gate 2B** | Coordinate conversion, effort conversion, timing, and derivative configuration are documented. |
| **Gate 3**  | Held-out generalized-effort prediction meets per-joint target metrics.                         |
| **Gate 4**  | Versioned model package and deployment interface reproduce validation results.                 |




## Reproducibility checklist

- [ ] Raw encoder counts and currents are preserved unchanged.
- [ ] `actuator_to_joint_map.yaml` produces the `q` used in URDF FK, DH FK, PSDM, and regression.
- [ ] `+q` is written in a joint-local frame, not as an end-effector motion direction.
- [ ] `s_i` does not duplicate the encoder-sign correction.
- [ ] `Keff` units are Nm/A for revolute joints and N/A for prismatic joints.
- [ ] All derivative and resampling settings are versioned.
- [ ] Held-out trajectories are not used to tune parameters.
- [ ] The model package identifies which effects PSDM includes and which it adds separately.



## Planned companion artifacts

- `urdf_to_dh.py`, candidate DH and conventions generator.
- FK validation helper using the same canonical `q` as PSDM.
- Raw telemetry conversion helper driven by `actuator_to_joint_map.yaml`.
- MATLAB regressor, calibration, and validation helpers.
- Templates for the three convention and conversion artifacts.

The URDF helper must generate a draft and validation report. It must not invent missing mechanics or firmware information.

## References

1. Lloyd, S., Irani, R., Ahmadi, M. (2021). *A numeric derivation for fast regressive modeling of manipulator dynamics*. Mechanism and Machine Theory, 156, 104149.
2. `PSDM-README.pdf`.
3. Lloyd et al., Denso VS-6556G PSDM application preprint.
4. `critical_ambiguities.md`.
5. CarletonABL/PSDM MATLAB implementation, recorded commit hash required for a reproducible run.



# Appendices



## Appendix A: Denavit-Hartenberg parameters and joint directions



### Purpose

DH parameters encode the rigid geometry from base to tool. The PSDM table uses one row per actuated joint and expects standard-DH parameters.

### Standard DH transform

```text
T_i = Rot_z(theta_i) * Trans_z(d_i) * Trans_x(a_i) * Rot_x(alpha_i)
```



### PSDM extensions


| Parameter          | Meaning                                                               |
| ------------------ | --------------------------------------------------------------------- |
| `t_i = 0`          | Revolute joint. `q_i` enters `theta_i`.                               |
| `t_i = 1`          | Prismatic joint. `q_i` enters `d_i`.                                  |
| `s_i = +1` or `-1` | Sign between canonical physical `q_i` and the increasing DH variable. |




### Why DH sign is not encoder scaling

Suppose a motor encoder requires 100 motor revolutions for one output-joint revolution. The conversion from counts to output angle belongs in `actuator_to_joint_map.yaml`. `s_i` cannot represent this 100:1 scale because it only has the values `+1` and `-1`.

### Assignment recipe

1. Define canonical physical `+q` locally for the joint.
2. Create the standard-DH frame assignment.
3. Determine whether a positive canonical `q` increases or decreases the DH variable.
4. Set `s_i` accordingly.
5. Verify by FK comparison against URDF.

For a prismatic joint, `+q` is positive local translation. For example, `child link translates along +Z_P3`. The direction may rotate in the base frame as earlier joints move, but its local definition remains unchanged.

## Appendix B: Least squares regression (primer)



### Linear model

```
y = Y * theta
```

- `Y`: `N x l` regressor matrix (stacked samples).
- `theta`: `l x 1` parameters to find.
- `y`: `N x 1` measured generalized effort values (stacked).



### MATLAB solution

```matlab
theta = Y \ y;                    % QR-based, preferred
% equivalent: theta = pinv(Y) * y;
```



### When it fails

- **Too few samples:** `N < l` (underdetermined). Collect more data.
- **Collinear columns:** `cond(Y)` very large (see Appendix C).
- **Wrong signs in** `y`**:** fix conventions before tuning `lambda`.

---



## Appendix C: Condition number and regularization



### Condition number

```matlab
c = cond(Y);
```


| Value     | Interpretation                                     |
| --------- | -------------------------------------------------- |
| `c < 1e4` | Usually well-conditioned                           |
| `c > 1e8` | Ill-conditioned; parameters not reliably separable |


Improve conditioning by:

- Richer excitation trajectories (especially for inertial ID).
- Removing redundant samples.
- Sequential calibration (Mode A).



### Ridge regression

```matlab
lambda = 1e-4;   % tune
theta = (Y'*Y + lambda*eye(l)) \ (Y'*y);
```

Plot `||theta||` vs `||Y*theta - y||` for several `lambda` (L-curve) to pick a compromise.

---



## Appendix D: Numerical differentiation and filtering in canonical units



### Why conversion comes before filtering

Differentiation amplifies noise. Convert counts into link-side rad or m first, then tune filters and check limits in meaningful physical units.

### Zero-phase filtering (`filtfilt`)

```matlab
[b, a] = butter(order, fc/(fs/2));
q_smooth = filtfilt(b, a, q, [], 2);
```



### Central difference

On a uniform grid with spacing `dt`:

```text
qdot(t)  ~= (q(t+dt) - q(t-dt)) / (2*dt)
qddot(t) ~= (qdot(t+dt) - qdot(t-dt)) / (2*dt)
```

Endpoints require a one-sided method or removal from the fitting set.

### Resampling to a uniform rate

```matlab
t_uniform = t(1) : mean(diff(t)) : t(end);
q_uniform = interp1(t, q', t_uniform, 'pchip')';
```

Validate resampling and filter choices by checking physical limits, excitation bandwidth, regressor conditioning, and held-out residuals.

## Appendix E: PSDM regressor structure



### Generator vector

PSDM builds basis functions from canonical joint coordinates:

```text
gamma = [q; sin(q); cos(q); qdot; qddot]
```

For a revolute coordinate, trigonometric terms are physically meaningful because `q` is an angle. For a prismatic coordinate, PSDM treats the coordinate through the prismatic multiplier functions described in the PSDM paper. In both cases the input must be the link-side generalized coordinate, not motor counts.

### Exponent matrix `E`

Each column of `E` stores exponents for the generator factors in one PSDM basis function. `PSDM.generateYp(Q, Qd, Qdd, E)` evaluates them for a set of samples.

### Reduction matrix `P`

`P` has size `p x ell x DOF`. Page `P(:,:,i)` maps the base parameter vector to the coefficient vector for joint `i`:

```text
tau_i = yp * P_i * theta_b
```



### Gravity and dynamic columns


| Term type          | Relevant state dependence |
| ------------------ | ------------------------- |
| Gravity            | `q` only.                 |
| Velocity terms     | `q` and `qdot`.           |
| Acceleration terms | `q`, `qdot`, and `qddot`. |




### Evaluate torque in one line

```matlab
tau = PSDM.inverseDynamics(E, P, Theta, Q, Qd, Qdd);
```

`Q`, `Qd`, and `Qdd` must all be `DOF x N` matrices in canonical joint units.

## Appendix F: RMSE and R² metrics



### RMSE, root mean square error

```text
RMSE = sqrt( mean( (tau_meas - tau_hat).^2 ) )
```

Report RMSE separately for each joint. Its unit is Nm for a revolute joint and N for a prismatic joint. Do not aggregate mixed-unit joint errors into one unqualified RMSE.

### R², coefficient of determination

```text
R2 = 1 - SS_res / SS_tot
SS_res = sum( (tau_meas - tau_hat).^2 )
SS_tot = sum( (tau_meas - mean(tau_meas)).^2 )
```

`R2 = 1` is a perfect fit. `R2 = 0` means the model is no better than predicting that joint's mean effort.

MATLAB for one joint:

```matlab
SS_res = sum((tau_meas_i - tau_hat_i).^2);
SS_tot = sum((tau_meas_i - mean(tau_meas_i)).^2);
R2_i = 1 - SS_res/SS_tot;
```



## Appendix G: From motor current to generalized effort



### Symbols


| Symbol     | Unit                 | Meaning                                               |
| ---------- | -------------------- | ----------------------------------------------------- |
| `c`        | counts               | Raw motor encoder position.                           |
| `C`        | counts/motor rev     | Encoder scale.                                        |
| `R`        | motor rev/output rev | Transmission reduction definition used in this guide. |
| `L`        | m/output rev         | Ball-screw lead.                                      |
| `Kt_motor` | Nm/A                 | Motor-shaft torque constant.                          |
| `Keff`     | Nm/A or N/A          | Current-to-generalized-effort scale.                  |




### Position conversion

```text
revolute:  q = q_offset + sigma_enc * 2*pi*(c-c_ref)/(C*R)
prismatic: q = q_offset + sigma_enc * L*(c-c_ref)/(C*R)
```



### Generalized effort conversion

```text
tau_meas = Keff * i
```

For a revolute axis, `tau_meas` is a torque. For a prismatic axis, it is a force.

### Ball-screw interpretation

**[Inference]** In an ideal screw, mechanical power relates screw torque and axial force. The force scale therefore depends on motor torque constant, all transmission stages, screw lead, sign, and loss assumptions. Use a known-load calibration to resolve the final scale and sign. Do not transfer a revolute torque-scale formula to a prismatic axis without the screw conversion.

### Sign check

Run a slow known-load test. The converted effort must have the expected polarity and a plausible magnitude. If it does not, inspect the ratio definition, current convention, mechanical inversion, screw lead direction, and reference-pose coordinate definition before fitting PSDM parameters.

## Appendix H: LuGre friction model (summary)

From the application preprint (Eq. (12) to (14)).

### State equation

```
zdot_i = qdot_i - (qdot_i / g_i(qdot_i)) * z_i
```



### Friction generalized effort

```
tau_fric_i = sigma0_i * z_i + sigma1_i * zdot_i + Fv_i * |qdot_i|^dv_i * sign(qdot_i)
```

The Denso preprint expresses this quantity as torque because its joints are revolute. For a prismatic axis, use the equivalent friction force in N. **[Inference]** The parameterization and its suitability for a prismatic transmission must be validated experimentally.

### Stribeck function

```
g_i(qdot_i) = Fc_i + (Fs_i - Fc_i) * exp(-(qdot_i/vs_i)^2)
```



### Identification strategy (two steps)

1. **High speed:** fit `Fc`, `Fv`, `dv` with simplified model (Eq. (20)).
2. **All speeds:** fit `Fs`, `vs`, `sigma0`, `sigma1` by simulating `z` forward in time and minimizing squared error.

LuGre is **nonlinear** in parameters. Use `lsqnonlin` or `fminsearch` rather than `\`.

---



## Appendix I: Glossary


| Term                           | Definition                                                                                    |
| ------------------------------ | --------------------------------------------------------------------------------------------- |
| Canonical joint coordinate `q` | Link-side generalized coordinate supplied to URDF FK, DH FK, PSDM, and regression.            |
| Drive count `c`                | Raw motor encoder count. It is not automatically a joint coordinate.                          |
| `encoder_to_q_sign`            | Sign mapping raw count increase to physical canonical `+q`.                                   |
| DH sign `s_i`                  | Sign mapping canonical `+q` to increasing `theta_i` or `d_i` in the DH row.                   |
| Generalized effort `tau`       | Torque for revolute joint, force for prismatic joint.                                         |
| `Keff`                         | Current-to-generalized-effort scale, Nm/A or N/A depending on joint type.                     |
| Base parameters `theta_b`      | Minimal PSDM inertial combinations identified from motion.                                    |
| DH table                       | PSDM standard-DH kinematic input with columns `[a, alpha, d, theta, t, s]`.                   |
| Held-out data                  | Validation trajectory not used to fit or tune the model.                                      |
| URDF                           | XML robot description used here as a source for a candidate kinematic chain and FK reference. |


