# PSDM System Identification Workflow (Student Guide)

This document is the **student-oriented companion** to `workflow_detailed.md`. Both guides share the same chapter structure so you can cross-reference them section by section.

| This guide (`workflow_detailed_student.md`) | Engineer guide (`workflow_detailed.md`) |
|---------------------------------------------|----------------------------------------|
| Explains *why* and *how* with examples | States *what* must be done concisely |
| Includes MATLAB/Python snippets | Lists outputs and gates |
| Appendices teach prerequisite math | Assumes familiarity |

**How to use this document:** Read each phase in order. Do not skip Phase 0. When you see a box labeled **Practical procedure**, follow it literally before moving on. When you see **Cross-reference**, open the matching section in `workflow_detailed.md` for the formal requirement list.

---

## Purpose and scope

### What you are building

You are building a **digital twin**: a numerical model that predicts joint torques from joint motion. The twin is expressed in **regressor form**:

```
tau_i = yp(q, qdot, qddot) * P_i * theta_b
```

| Symbol | Meaning |
|--------|---------|
| `q`, `qdot`, `qddot` | Joint position, velocity, acceleration (vectors, size `n x 1`) |
| `yp` | Row vector of basis functions evaluated at the current motion state (size `1 x p`) |
| `P_i` | Reduction matrix for joint `i` (size `p x l`) |
| `theta_b` | Base inertial parameters to identify (size `l x 1`) |
| `tau_i` | Predicted torque at joint `i` |

The PSDM toolbox computes `E` and `P` from robot kinematics. Your job in Phases 3 and 4 is to collect data and solve for `theta_b`.

### What PSDM does vs what you do

```
  YOU provide                    PSDM provides              YOU identify
  ---------                      -------------              --------------
  URDF, DH table, g      -->     E, P matrices      -->     theta_b
  Robot logs (q, i)      -->     (regressor eval)   -->     from regression
```

**Cross-reference:** `workflow_detailed.md`, Purpose and scope.

**In scope:** serial chains, motor-current torque measurement, four-step calibration from the Denso application paper.

**Out of scope:** flexible joints, backlash, unmodeled cable effects.

---

## Authoritative sources

Read these in this order when learning:

1. **PSDM-README.pdf** (start here for MATLAB usage).
2. **Lloyd et al. application preprint** (Denso robot, experimental calibration walkthrough).
3. **Lloyd et al. (2021)** (full PSDM theory; read Section 3 when you need deeper understanding).
4. **`critical_ambiguities.md`** (before touching real data).

Keep PDFs open while working in MATLAB. Use `help PSDM.deriveModel` for function-level documentation.

---

## Prerequisites

### Software setup (first-time install)

**Step 1: Install MATLAB** (R2018a or newer).

**Step 2: Clone PSDM and add to path.**

```bash
git clone https://github.com/CarletonABL/PSDM.git
```

In MATLAB:

```matlab
addpath(genpath('/path/to/PSDM'));
savepath;   % optional: persist across sessions
help PSDM.deriveModel   % should print help text, not error
```

**Step 3 (optional but recommended):** Compile MEX files for speed.

```matlab
PSDM.make();
% Edit +PSDM/config.m: set use_mex = true;
```

**Step 4: Install Python 3** with `numpy`, `scipy`, and `yourdfpy` or `urdfpy` for URDF parsing in Phase 1.

### Hardware checklist

Before any experiment, confirm you have:

- [ ] URDF file matching the physical robot.
- [ ] Motor datasheet `Kt` values (units: Nm/A at motor shaft).
- [ ] Gear ratio per joint (motor revolutions per joint revolution).
- [ ] Sign convention documentation from the drive firmware team.
- [ ] Safe joint/velocity/torque limits from the robot manual.

### Required artifacts before Phase 3

**Cross-reference:** `workflow_detailed.md`, Prerequisites.

Create a project folder:

```
project/
  conventions_sheet.md
  dh_table.mat
  kt_conversion_notes.md      (after Checkpoint A)
  derivative_filter_config.yaml (after Checkpoint B)
  raw_logs/
  processed_data/
  matlab/
```

---

## Phase 0: Scope and conventions lock

**Goal:** Every later step fails if frames and signs are inconsistent. This phase prevents silent errors (wrong torque sign, inverted gear ratio, gravity pointing the wrong way).

**Cross-reference:** `workflow_detailed.md`, Phase 0.

### Step 0.1: Define coordinate conventions

#### What you need to understand

A **reference frame** is an origin plus three orthogonal axes. The URDF, DH table, telemetry, and PSDM model must all describe the same physical robot using compatible frames.

**Gravity in PSDM:** `g` is a **unit vector** (length 1) pointing **upward**, opposite to gravity. If your base frame has `+Z` pointing up, use:

```matlab
g = [0; 0; 1];
```

PSDM multiplies this direction by `9.806132 m/s^2` internally when evaluating gravity terms (`utilities.g` in the toolbox).

#### Practical procedure

Create `conventions_sheet.md` using this template:

```markdown
# Robot conventions

## Base frame
- Origin: [describe, e.g. robot base mounting surface center]
- +X: [forward / per drawing]
- +Y: [left / per drawing]
- +Z: [up]
- Gravity vector g (unit, upward): [0, 0, 1]

## Joint table
| Joint | Type | q unit | +q direction (physical) | i>0 torque direction | Lower | Upper |
|-------|------|--------|-------------------------|----------------------|-------|-------|
| 1     | rev  | rad    | CCW when viewed from +Z | CCW                  | -pi   | pi    |
| ...   |      |        |                         |                      |       |       |

## Tool / payload
- Tool mass in URDF: [yes/no, value]
- External tau_ee model: [none / separate wrench]
```

**Checkpoint:** For each joint, physically move it in the **positive** direction and verify that logged `q` increases.

### Step 0.2: Lock URDF-to-DH policy

#### Background (see also Appendix A)

Denavit-Hartenberg (DH) parameters describe each link with four numbers: `a_i`, `alpha_i`, `d_i`, `theta_i`. PSDM adds two columns:

| Column | Name | Value |
|--------|------|-------|
| 5 | `t_i` | `0` = revolute, `1` = prismatic |
| 6 | `s_i` | `+1` or `-1` (joint sign) |

Effective joint coordinate (PSDM-README Eq. (5)):

```
d_i_star    = d_i + t_i * s_i * q_i
theta_i_star = theta_i + (1 - t_i) * s_i * q_i
```

#### Practical procedure

1. Choose **standard** or **modified** DH. Pick one and never mix them. PSDM follows Spong and Vidyasagar (2008) as cited in PSDM-README.
2. List joints from base (index 1) to tool (index n).
3. Write the rule for mapping URDF `<origin xyz rpy>` and `<axis xyz>` into DH rows.
4. Set acceptance tolerance: position error < 1 mm, orientation error < 0.1 deg in FK check (Phase 1).

**Common mistake:** Putting a constant URDF joint offset into `q_i` instead of into fixed `theta_i` or `d_i`. Offsets belong in the DH constants; `q_i` is the measured joint variable.

### Step 0.3: Define data contract for logs

Every log file must contain synchronized columns. Example CSV header:

```
t, q1, q2, ..., qn, qdot1, ..., qdotn, i1, ..., in
```

If `qdot` is not logged, document that you will compute it in Phase 3 from `q`.

Store **raw** logs unchanged. Never overwrite them.

### Step 0.4: Execution checklist

**Cross-reference:** `workflow_detailed.md`, Step 0.4.

Run in MATLAB:

```matlab
assert(exist('PSDM.deriveModel', 'file') == 2, 'PSDM not on path');
```

**Gate 0:** `conventions_sheet.md` reviewed by someone who knows the physical robot.

---

## Phase 1: URDF to PSDM kinematics

**Goal:** Produce `DH` (`n x 6`) and `g` for `PSDM.deriveModel(DH, g)`.

**Cross-reference:** `workflow_detailed.md`, Phase 1.

### Step 1.1: Parse URDF joint chain

#### What is URDF?

URDF (Unified Robot Description Format) is an XML file. Each movable connection is a `<joint>` with:

- `type` (`revolute`, `prismatic`, `fixed`, ...),
- `parent` / `child` link names,
- `<origin xyz="..." rpy="..."/>` (transform from parent to joint frame),
- `<axis xyz="..."/>` (rotation or translation axis),
- `<limit lower="..." upper="..."/>`.

#### Practical procedure

1. Open the URDF in a text editor or URDF viewer.
2. Build a table from base link to tool link. Skip `fixed` joints but remember their transforms.
3. Export `urdf_kinematics.json` (or equivalent) with one record per actuated joint.

Example Python sketch (adapt to your parser library):

```python
import json
# from yourdfpy import URDF  # example library

# robot = URDF.load("robot.urdf")
# chain = robot.actuated_joints  # library-specific

joints = []
# for j in chain:
#     joints.append({
#         "name": j.name,
#         "type": j.type,
#         "axis": list(j.axis),
#         "origin_xyz": list(j.origin.xyz),
#         "origin_rpy": list(j.origin.rpy),
#         "lower": j.limit.lower,
#         "upper": j.limit.upper,
#     })

# with open("urdf_kinematics.json", "w") as f:
#     json.dump(joints, f, indent=2)
```

### Step 1.2: Build PSDM DH table

#### Worked concept (one revolute joint)

Suppose joint 1 rotates about the parent `Z` axis, with no offset. A common assignment is:

```
a_1 = 0,  alpha_1 = 0,  d_1 = link_length,  theta_1 = 0,  t_1 = 0,  s_1 = 1
```

If telemetry `q` increases in the opposite direction to the DH convention, set `s_1 = -1` (do not change the measured `q` in logs).

#### Practical procedure

1. For each joint `i`, fill one row of `DH`.
2. Use radians for angles and meters for lengths.
3. Save both human-readable and MATLAB formats:

```matlab
% Example 2-DOF planar arm (illustrative only)
DH = [
    0,  0,     0.3,  0,  0,  1;   % joint 1: a, alpha, d, theta, t, s
    0.2, 0,    0,    0,  0,  1    % joint 2
];
save('dh_table.mat', 'DH');
```

### Step 1.3: Define gravity vector

```matlab
g = [0; 0; 1];   % if +Z is up in base frame
```

Verify `norm(g) == 1`. PSDM requires a unit vector.

### Step 1.4: Forward kinematics validation

#### Why this matters

URDF-to-DH is **not unique**. Different textbooks place frame `i` on different links. The only proof your DH table is correct is that it produces the same end-effector pose as the URDF for many `q` samples.

#### Practical procedure

1. Sample `N` configurations (at least 100 random poses within limits).
2. Compute FK from URDF and from DH (use Robotics Toolbox, Pinocchio, or your own script).
3. Compare position norm error and orientation error (angle of rotation difference).
4. If a joint fails repeatedly, fix `s_i` or offset in that row first.

Document results in `fk_validation_report.md`:

```
Max position error: 0.3 mm
Max orientation error: 0.05 deg
Status: PASS (Gate 1)
```

### Step 1.5: MATLAB import check

```matlab
load('dh_table.mat', 'DH');
g = [0; 0; 1];

assert(size(DH, 2) == 6, 'DH must have 6 columns');
assert(all(DH(:, 5) == 0 | DH(:, 5) == 1), 't_i must be 0 or 1');
assert(all(abs(DH(:, 6)) == 1), 's_i must be +1 or -1');
fprintf('DH is %d joints, ready for PSDM.\n', size(DH, 1));
```

**Gate 1:** FK check passed. Stop if it did not pass.

---

## Phase 2: PSDM model derivation

**Goal:** Obtain `E` and `P` from kinematics alone (no robot logs needed yet).

**Cross-reference:** `workflow_detailed.md`, Phase 2. Theory in **Appendix E**.

### Step 2.1: Install and configure PSDM

Already done in Prerequisites. Confirm:

```matlab
which PSDM.deriveModel
```

### Step 2.2: Optional inertial parameter mask `X`

If you **know** some inertial parameters are zero (e.g. negligible products of inertia), build `X` (`n x 10`):

```matlab
n = size(DH, 1);
X = ones(n, 10);      % start with all parameters "present"
X(:, 8:10) = 0;       % example: zero all Ixy, Ixz, Iyz
```

Only **exact zeros** matter. Random nonzero placeholders are fine.

### Step 2.3: Derive the model

```matlab
load('dh_table.mat', 'DH');
g = [0; 0; 1];

[E, P] = PSDM.deriveModel(DH, g);
% With mask:
% [E, P] = PSDM.deriveModel(DH, g, X);

DOF = size(DH, 1);
p = size(E, 2);
l = size(P, 2);
fprintf('Derived model: p=%d basis terms, l=%d base parameters.\n', p, l);

save('psdm_model.mat', 'E', 'P', 'DH', 'g', ...
     'derivation_date', 'datetime("now")', ...
     'matlab_version', 'version');
```

**What happens inside `deriveModel`:** The toolbox separately derives gravity, acceleration, and velocity submodels, then combines them (see `deriveModel.m` in the PSDM repository). This is why you can later extract gravity-only models from the same kinematics.

Derivation may take seconds to minutes depending on DOF and whether MEX/parallel is enabled.

### Step 2.4: Determine base parameter count

```matlab
fprintf('Base parameter count l = %d (theoretical max 10*n = %d)\n', l, 10*DOF);
```

Optional: if URDF has nominal masses/inertias, compare structure:

```matlab
% X_nominal = ... from URDF
% Theta_nom = PSDM.X2Theta(E, P, DH, g, X_nominal);
```

`Theta_nom` is useful for sanity checks, not as final identified values.

### Step 2.5: Optional complexity reduction

```matlab
% [Eh, Ph] = PSDM.reduceModelComplexity(E, P, DH, g, X);
```

Use only if you need faster runtime and accept some approximation. Keep the full model for identification.

### Sanity test (partial Gate 2)

```matlab
Q   = zeros(DOF, 10);
Qd  = zeros(DOF, 10);
Qdd = zeros(DOF, 10);
Theta_test = ones(l, 1);
tau = PSDM.inverseDynamics(E, P, Theta_test, Q, Qd, Qdd);
assert(all(size(tau) == [DOF, 10]), 'inverseDynamics size mismatch');
disp('PSDM inverseDynamics OK.');
```

---

## Phase 3: Real-robot data collection and preprocessing

**Goal:** Clean datasets with `q`, `qdot`, `qddot`, `tau_meas`.

**Cross-reference:** `workflow_detailed.md`, Phase 3. Numerical methods in **Appendices C, D, F, G**.

### Step 3.1: Resolve `Kt_motor` to `Kt_joint` (Checkpoint A)

#### Physical meaning

Motor current `i` (Amps) is proportional to motor torque `tau_motor`:

```
tau_motor = Kt_motor * i
```

The joint feels a transformed torque through the gearbox:

```
tau_joint = eta * N * tau_motor    (common pattern; verify for your robot)
```

where `N` is the gear ratio (motor side to joint side) and `eta` is efficiency.

**Cross-reference:** `critical_ambiguities.md`, Ambiguity 1. Worked gear explanation in **Appendix G**.

#### Practical procedure

1. Write the equation your firmware uses (ask the controls team).
2. Compute `Kt_joint` per joint.
3. Bench test: hold a known pose, apply small constant velocity, compare gravity trend sign.

```matlab
Kt_joint = [K1; K2; K3; ...];   % Nm/A at joint
tau_meas = diag(Kt_joint) * i;    % i is n x N matrix of currents
```

Document in `kt_conversion_notes.md` with numeric example per joint.

### Step 3.2: Design excitation trajectories

Each calibration step needs different motion:

| Step | Speed | What it excites |
|------|-------|-----------------|
| Motor `Kt` | Very slow | Current difference with added mass |
| Gravity | Slow | Gravity regressor columns |
| Friction | Low to high | Friction vs velocity |
| Inertial | Fast, rich | `qddot`, Coriolis, centrifugal terms |

**Safety:** Every trajectory must respect joint position, velocity, acceleration, and torque limits.

For inertial data, the Denso paper optimizes multi-sine trajectories to minimize `cond(Y_iner)`. A simpler student approach: use several sinusoids per joint with incommensurate frequencies, then check `cond(Y_iner)` before collecting hours of data.

### Step 3.3: Data logging

1. Log raw `t`, `q`, `i` at full rate.
2. Log `qdot` if the controller provides it (often cleaner than differentiating `q`).
3. Never modify raw files.

### Step 3.4: Characterize timing (Checkpoint B)

```matlab
% dt = diff(t);
% fprintf('dt: mean=%.6f, std=%.6f, min=%.6f, max=%.6f\n', ...
%     mean(dt), std(dt), min(dt), max(dt));

% Rule of thumb: if std(dt) > 10% of mean(dt), resample to uniform grid.
```

See **Appendix D** for resampling and filtering.

### Step 3.5: Resample and filter

Example: zero-phase Butterworth low-pass before differentiation (used in the Denso paper):

```matlab
fs = 1000;          % Hz, example
fc = 40;            % Hz cutoff (adjust per experiment type)
[b, a] = butter(4, fc/(fs/2));
q_filt = filtfilt(b, a, q, [], 2);   % filter along time (dim 2)
```

Record `fc`, filter order, and rationale in `derivative_filter_config.yaml`.

Suggested starting cutoffs from the application preprint:

| Experiment | Cutoff (indicative) |
|------------|---------------------|
| Motor / gravity | 4 Hz |
| Inertial | 15 Hz |
| Friction | 40 Hz |

### Step 3.6: Estimate `qdot` and `qddot`

**Central difference** (second-order accurate, used in Denso friction paper):

```matlab
dt = mean(diff(t));
qdot  = gradient(q, dt);                    % or use logged qdot
qddot = gradient(qdot, dt);                 % simple option

% Explicit central difference on uniform grid:
% qdot(:,k)  = (q(:,k+1) - q(:,k-1)) / (2*dt);
% qddot(:,k) = (qdot(:,k+1) - qdot(:,k-1)) / (2*dt);
```

Avoid using raw `diff(qdot)/dt` without filtering on noisy data.

Compare two methods, plot spectra, pick the one that gives lower validation error on held-out data.

### Step 3.7: Segment train and validation

```matlab
N = size(q, 2);
idx_train = 1:floor(0.85*N);
idx_val   = (floor(0.85*N)+1):N;

save('processed_data/train.mat', 't', 'q', 'qdot', 'qddot', 'tau_meas', 'idx_train');
save('processed_data/val.mat',   't', 'q', 'qdot', 'qddot', 'tau_meas', 'idx_val');
```

Label which file is for gravity, friction, or inertial calibration in `dataset_manifest.md`.

**Gate 2:** Timing report and filter config complete.

---

## Phase 4: Base parameter identification

**Goal:** Solve for `theta_b` (and optional friction/`Kt` parameters).

**Cross-reference:** `workflow_detailed.md`, Phase 4. Regression math in **Appendix B**. PSDM regressor details in **Appendix E**.

### Helper function: build the full regressor matrix

Save as `matlab/build_psdm_regressor.m`. You will reuse this in Steps 4A.2, 4A.4, and Mode B.

```matlab
function [Y_stack, Yb] = build_psdm_regressor(E, P, Q, Qd, Qdd)
% BUILD_PSDM_REGRESSOR  Stack joint regressors for least-squares ID.
%
%   Y_stack: (N*DOF) x l  matrix for tau_vec = Y_stack * theta_b
%   Yb:      DOF x l x N   joint-wise regressor (same as inverseDynamics)

    DOF = size(Q, 1);
    N   = size(Q, 2);
    l   = size(P, 2);

    Yp = PSDM.generateYp(Q, Qd, Qdd, E);       % N x p
    Yb = utilities.blockprod(Yp, P);            % N x l x DOF

    Y_stack = zeros(N * DOF, l);
    for i = 1:DOF
        Yi = Yb(:, :, i);                        % N x l
        rows = i:DOF:(N*DOF);
        Y_stack(rows, :) = Yi;
    end
end
```

Usage:

```matlab
load('psdm_model.mat', 'E', 'P');
load('processed_data/train.mat', 'q', 'qdot', 'qddot', 'tau_meas');

[Y_stack, ~] = build_psdm_regressor(E, P, q, qdot, qddot);
tau_vec = reshape(tau_meas, [], 1);
theta_b = Y_stack \ tau_vec;   % see Appendix B
```

---

### Mode A: Sequential calibration (recommended)

Full decomposition (application preprint Eq. (15)):

```
tau = diag(Kt_joint) * i = tau_grav + tau_fric + tau_iner + tau_ee
```

Calibrate in order: motor, gravity, friction, inertial. Later steps subtract what earlier steps explain.

---

#### Step 4A.1: Motor calibration (preprint Section 3.1)

##### Idea

At very low speed, friction cancels when averaging forward and reverse motion. With and without a known mass on the tool, gravity difference isolates the motor constant.

##### Practical procedure

1. Attach known mass `m_w` at known position on the tool.
2. Move joint `j` slowly from limit to limit, forward then reverse, with and without mass.
3. Average currents to remove friction.
4. Solve Eq. (16) per joint or globally.

```matlab
% Per-sample wrench from calibration mass (preprint Eq. (17)):
% f_w = [m_w * g_world; R(q) * r_w x (m_w * g_world)]
% delta_tau = diag(Kt_joint) * (i_with - i_nom);
% J = geometricJacobian(...);  % from Robotics Toolbox or custom FK
% delta_tau = J' * f_w;
% Kt_joint_j = (J' * f_w) / (i_with - i_nom);  % scalar per sample, median over samples
```

Validate on held-out poses. Target R² near 1.0 on training data (see **Appendix F**).

**Output:** `identified_joint_parameters.mat` with field `Kt_joint`.

---

#### Step 4A.2: Gravity calibration (preprint Section 3.2)

This is the step that often confuses beginners. Below are **two equivalent approaches**.

##### What "gravity columns" means in PSDM

Each column of `E` is one basis function. Gravity-only functions depend on `q` (through `sin(q)` and `cos(q)` terms) but **not** on `qdot` or `qddot`.

In code (see `generateYp.m`), gravity columns are those with **zero exponents** in the velocity and acceleration rows of `E`:

```matlab
DOF = size(DH, 1);
vel_acc_rows = (3*DOF + 1) : (5*DOF);
grav_col_mask = ~any(E(vel_acc_rows, :) > 0, 1);
E_grav = E(:, grav_col_mask);
P_grav = P(grav_col_mask, :, :);   % subset rows of P to match E_grav
```

##### Method 1 (recommended for students): derive a gravity-only model

```matlab
[E_grav, P_grav] = PSDM.deriveModel(DH, g, [], 'gravity_only', true);
l_grav = size(P_grav, 2);
fprintf('Gravity-only model has l_grav = %d parameters.\n', l_grav);
```

This calls `deriveGravityModel` inside the toolbox and is the cleanest path.

##### Method 2: extract from the full model

Use the `grav_col_mask` code above on your saved full `E` and `P`. Method 1 and Method 2 should produce the same observable gravity subspace if kinematics match.

##### Build `Y_grav` and identify `theta_b_grav`

Use **slow** motion data where velocity and acceleration torques are negligible. You may set `Qd = 0` and `Qdd = 0` when building the regressor, or use actual small derivatives from slow logs.

```matlab
load('processed_data/gravity_train.mat', 'q', 'qdot', 'qddot', 'tau_meas', 'i');
load('identified_joint_parameters.mat', 'Kt_joint');

% Measured torque at joint
tau_meas = diag(Kt_joint) * i;

% Gravity regressor (Method 1 example)
[Y_stack_grav, Yb_grav] = build_psdm_regressor(E_grav, P_grav, q, zeros(size(q)), zeros(size(q)));

% Subtract known end-effector wrench mapped to joints (if applicable):
% tau_net = tau_meas - tau_ee;
tau_net = tau_meas;
tau_vec = reshape(tau_net, [], 1);

theta_b_grav = Y_stack_grav \ tau_vec;

% Predicted gravity torque
tau_grav_hat = reshape(Y_stack_grav * theta_b_grav, size(tau_meas));
```

##### Map `theta_b_grav` into the full `theta_b` vector

The gravity-only model uses a **subset** of base parameters. The full model has `l` parameters. After identifying gravity parameters:

1. Derive the **full** model `[E, P] = PSDM.deriveModel(DH, g)`.
2. Identify which full-model columns of `P` correspond to gravity parameters (compare `rank` and physical consistency, or fit full model with non-gravity `theta` fixed to zero).
3. **Practical student shortcut:** keep `theta_b_grav` from the gravity-only derivation. For inertial calibration (Step 4A.4), subtract `tau_grav_hat` from measurements before fitting inertial terms, rather than merging parameter vectors manually.

The Denso paper uses the subtraction approach (Eq. (19) and (21)), which avoids index bookkeeping errors.

##### Validate

```matlab
rmse = sqrt(mean((tau_net(:) - tau_grav_hat(:)).^2));
r2 = 1 - sum((tau_net(:) - tau_grav_hat(:)).^2) / sum((tau_net(:) - mean(tau_net(:))).^2);
fprintf('Gravity fit: RMSE=%.3f Nm, R2=%.4f\n', rmse, r2);
```

Plot `tau_net` vs `tau_grav_hat` per joint on validation trajectories.

---

#### Step 4A.3: Friction calibration (preprint Section 3.3)

##### Idea

Move one joint at a time with sinusoidal motion. Subtract gravity and known tool torque. What remains is mostly friction.

##### Practical procedure

```matlab
% Isolate friction torque (preprint Eq. (19)):
tau_fric_meas = tau_meas - tau_grav_hat - tau_ee;

% Per joint i, fit LuGre parameters (Appendix H) or simpler Coulomb+viscous:
% High |qdot|: tau_fric ≈ Fc*sign(qdot) + Fv*|qdot|^dv*sign(qdot)
```

High-speed fit (linear in parameters once `dv` is fixed):

```matlab
% Example: joint 1, high-speed samples
idx = abs(qdot(1,:)) > 0.5;   % rad/s threshold, tune per robot
y = tau_fric_meas(1, idx)';
X = [sign(qdot(1,idx))', (abs(qdot(1,idx)).^0.5 .* sign(qdot(1,idx)))'];  % example
params = X \ y;
```

Low-speed / pre-sliding: simulate LuGre state `z` (Eq. (12)) and use `fminsearch` to minimize sum of squared errors (as in the preprint).

**Output:** friction coefficients in `identified_joint_parameters.mat`.

---

#### Step 4A.4: Inertial calibration (preprint Section 3.4)

##### Idea

After removing gravity, friction, and tool torque, the residual should be explained by inertial regressor columns (those involving `qddot` and velocity products).

##### Extract inertial columns from full model

```matlab
DOF = size(DH, 1);
vel_acc_rows = (3*DOF + 1) : (5*DOF);
iner_col_mask = any(E(vel_acc_rows, :) > 0, 1);
E_iner = E(:, iner_col_mask);
P_iner = P(iner_col_mask, :, :);
```

Alternatively, use velocity/acceleration-only derivation flags inside the toolbox (`deriveAccelModel`, `deriveVelocityModel`) for advanced users. Column masking on the full model is sufficient for coursework.

##### Practical procedure

```matlab
load('processed_data/inertial_train.mat', 'q', 'qdot', 'qddot', 'tau_meas', 'i');

tau_meas = diag(Kt_joint) * i;
tau_iner_meas = tau_meas - tau_grav_hat - tau_fric_hat - tau_ee;

[Y_stack_iner, ~] = build_psdm_regressor(E_iner, P_iner, q, qdot, qddot);
tau_vec = reshape(tau_iner_meas, [], 1);

% Check conditioning before solving
c = cond(Y_stack_iner);
fprintf('cond(Y_iner) = %.2e\n', c);
if c > 1e8
    warning('Ill-conditioned regressor. Use regularization (Appendix C).');
    lambda = 1e-4;   % tune via L-curve
    theta_b_iner = (Y_stack_iner' * Y_stack_iner + lambda*eye(size(Y_stack_iner,2))) \ (Y_stack_iner' * tau_vec);
else
    theta_b_iner = Y_stack_iner \ tau_vec;
end
```

##### Assemble complete `theta_b`

For simulation using `PSDM.inverseDynamics`, you need one `Theta` vector of length `l` matching the **full** `P` from `deriveModel`:

```matlab
[E, P] = PSDM.deriveModel(DH, g);
l = size(P, 2);

% Build full Theta: use X2Theta structure or full regression on combined data
[Y_full, ~] = build_psdm_regressor(E, P, q, qdot, qddot);
tau_residual = tau_meas - tau_fric_hat - tau_ee;  % if gravity terms inside Theta
Theta = Y_full \ reshape(tau_residual, [], 1);

save('theta_b.mat', 'Theta', 'theta_b_grav', 'theta_b_iner');
```

**Student tip:** The cleanest validation is torque prediction, not parameter vector equality. Always compare `tau_hat` vs `tau_meas` on held-out data.

---

### Mode B: Direct identification

Use when friction is negligible and `Kt_joint` is trusted.

#### Step 4B.1: Build regression matrix

```matlab
[Y_stack, ~] = build_psdm_regressor(E, P, q, qdot, qddot);
tau_vec = reshape(tau_meas, [], 1);
Theta = Y_stack \ tau_vec;
```

#### Step 4B.2: Solve and diagnose

```matlab
fprintf('cond(Y) = %.2e\n', cond(Y_stack));
tau_hat_vec = Y_stack * Theta;
residual = tau_vec - tau_hat_vec;
rmse = sqrt(mean(residual.^2));
```

Compare `Theta` to `PSDM.X2Theta(E, P, DH, g, X_urdf)` if URDF inertias exist.

---

### Step 4.3: Optional motor inertia in PSDM model

If motor reflected inertia `Im_i` should appear in `theta_b` (Lloyd 2021 Section 3.5):

```matlab
X = ones(n, 11);   % 11th column = Im_i
[E, P] = PSDM.deriveModel(DH, g, X);
```

Friction **cannot** be embedded in standard PSDM; model it separately (Mode A).

**Gate 3:** Held-out torque error meets your targets.

---

## Phase 5: Validation and digital twin packaging

**Goal:** Prove the model works on new data and package it for reuse.

**Cross-reference:** `workflow_detailed.md`, Phase 5.

### Step 5.1: Torque prediction validation

```matlab
load('psdm_model.mat', 'E', 'P');
load('theta_b.mat', 'Theta');
load('processed_data/val.mat', 'q', 'qdot', 'qddot', 'tau_meas', 'i');
load('identified_joint_parameters.mat', 'Kt_joint');

tau_hat = PSDM.inverseDynamics(E, P, Theta, q, qdot, qddot);

% If friction modeled separately:
% load friction model and compute tau_fric_hat
% tau_hat_total = tau_hat + tau_fric_hat;

for j = 1:size(q, 1)
    e = tau_meas(j,:) - tau_hat(j,:);
    rmse_j = sqrt(mean(e.^2));
    ss_res = sum(e.^2);
    ss_tot = sum((tau_meas(j,:) - mean(tau_meas(j,:))).^2);
    r2_j = 1 - ss_res/ss_tot;
    fprintf('Joint %d: RMSE=%.3f Nm, R2=%.4f\n', j, rmse_j, r2_j);
end
```

Report slow-speed and high-speed segments separately.

### Step 5.2: Forward dynamics check (optional)

```matlab
Qdd_sim = PSDM.forwardDynamics(E, P, Theta, q, qdot, tau_meas);
% Compare Qdd_sim to qddot (expect qualitative agreement, not perfect match)
```

### Step 5.3: Export model package

Copy these into `model_v1.0.0/`:

- `psdm_model.mat`
- `theta_b.mat`
- `identified_joint_parameters.mat`
- `conventions_sheet.md`
- `kt_conversion_notes.md`
- `derivative_filter_config.yaml`
- `validation_report.md`

### Step 5.4: Fast code generation (optional)

```matlab
PSDM.makeInverseDynamics('robot_id', E, P, Theta);
% Generates optimized C/MATLAB code for real-time use
```

### Step 5.5: Simulink or external integration

Wrap a single function:

```matlab
function tau = robot_inverse_dynamics(q, qdot, qddot)
% q, qdot, qddot: n x 1, units rad and rad/s
    persistent E P Theta
    if isempty(E)
        s = load('psdm_model.mat');
        t = load('theta_b.mat');
        E = s.E; P = s.P; Theta = t.Theta;
    end
    tau = PSDM.inverseDynamics(E, P, Theta, q, qdot, qddot);
end
```

Document joint order and units in the file header.

**Gate 4:** Interface and runtime requirements met.

---

## Phase 6: Iteration loop

**Cross-reference:** `workflow_detailed.md`, Phase 6.

When the tool changes:

1. Update URDF and `tau_ee`.
2. Re-run gravity calibration (Step 4A.2) and inertial calibration (Step 4A.4).
3. Keep the same `DH` if kinematics unchanged.
4. Bump version to `model_v1.1.0` and re-run all validation trajectories.

---

## Approval gates summary

| Gate | Student check |
|------|---------------|
| **Gate 1** | `fk_validation_report.md` shows PASS |
| **Gate 2** | `timing_quality_report.md` + `derivative_filter_config.yaml` exist |
| **Gate 3** | `validation_report.md` meets RMSE/R² targets on held-out data |
| **Gate 4** | `robot_inverse_dynamics()` runs in target environment within time budget |

---

## Reproducibility checklist

**Cross-reference:** `workflow_detailed.md`, Reproducibility checklist.

Work through every box before calling the project done.

---

## Planned companion artifacts (later tasks)

- `urdf_to_dh.py` and FK validation script.
- `matlab/build_psdm_regressor.m` (provided inline in this guide).
- Example `derivative_filter_config.yaml` template.

---

## References

1. Lloyd, S., Irani, R., Ahmadi, M. (2021). *Mechanism and Machine Theory*, 156, 104149. [doi:10.1016/j.mechmachtheory.2020.104149](https://doi.org/10.1016/j.mechmachtheory.2020.104149)
2. PSDM-README.pdf
3. Lloyd et al., Denso VS-6556G application preprint (MECC supplementary material).
4. Spong, M. W., Vidyasagar, M. (2008). *Robot Dynamics and Control*.
5. [https://github.com/CarletonABL/PSDM](https://github.com/CarletonABL/PSDM)

---

# Appendices

## Appendix A: Denavit-Hartenberg parameters (primer)

### Purpose

DH parameters encode link geometry so forward kinematics can chain transforms from base to tool.

### Standard DH transform (conceptual)

From frame `i-1` to frame `i`:

```
T_i = Rot_z(theta_i) * Trans_z(d_i) * Trans_x(a_i) * Rot_x(alpha_i)
```

### PSDM extensions

| Parameter | Role |
|-----------|------|
| `t_i = 0` | Revolute: `q` enters in `theta_i` |
| `t_i = 1` | Prismatic: `q` enters in `d_i` |
| `s_i = +/-1` | Flips sign if encoder positive direction disagrees with DH |

### Assignment recipe (revolute joint)

1. Place `z_{i-1}` along the joint rotation axis.
2. Place `x_i` along the common normal to `z_{i-1}` and `z_i` (or perpendicular to both if axes intersect).
3. Read off `a_i`, `alpha_i`, `d_i`, `theta_i` from geometry.
4. Compare FK output to URDF/CAD at 3 known poses.

---

## Appendix B: Least squares regression (primer)

### Linear model

```
y = Y * theta
```

- `Y`: `N x l` regressor matrix (stacked samples).
- `theta`: `l x 1` parameters to find.
- `y`: `N x 1` measured torques (stacked).

### MATLAB solution

```matlab
theta = Y \ y;                    % QR-based, preferred
% equivalent: theta = pinv(Y) * y;
```

### When it fails

- **Too few samples:** `N < l` (underdetermined). Collect more data.
- **Collinear columns:** `cond(Y)` very large (see Appendix C).
- **Wrong signs in `y`:** fix conventions before tuning `lambda`.

---

## Appendix C: Condition number and regularization

### Condition number

```matlab
c = cond(Y);
```

| Value | Interpretation |
|-------|----------------|
| `c < 1e4` | Usually well-conditioned |
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

## Appendix D: Numerical differentiation and filtering

### Why filtering comes first

Differentiation amplifies noise. Always low-pass filter position (or velocity) before estimating higher derivatives.

### Zero-phase filtering (`filtfilt`)

`filtfilt` applies a filter forward and backward so phase delay cancels. Used in the Denso calibration paper.

```matlab
[b, a] = butter(order, fc/(fs/2));
q_smooth = filtfilt(b, a, q, [], 2);
```

### Central difference

On uniform grid with spacing `dt`:

```
qdot(t)  ≈ (q(t+dt) - q(t-dt)) / (2*dt)
qddot(t) ≈ (qdot(t+dt) - qdot(t-dt)) / (2*dt)
```

Endpoints need one-sided formulas or trim them from the dataset.

### Resampling to uniform rate

If `std(dt)` is large:

```matlab
t_uniform = t(1) : mean(dt) : t(end);
q_uniform = interp1(t, q', t_uniform, 'pchip')';
```

Use `pchip` or `spline` to avoid overshoot on sharp moves.

---

## Appendix E: PSDM regressor structure (primer)

### Generator vector

PSDM bundles joint variables into:

```
gamma = [q; sin(q); cos(q); qdot; qddot]    % size 5n x 1
```

### Exponent matrix `E`

Each column `E(:, j)` stores exponents for gamma factors. Example for one term resembling `sin(q2)*qddot1`:

- Exponent on `sin(q2)` is 1.
- Exponent on `qddot1` is 1.
- All other exponents are 0.

Evaluation (PSDM-README Eq. (2)):

```
yp_j = prod( gamma_k ^ E(k,j) )
```

`PSDM.generateYp(Q, Qd, Qdd, E)` performs this for `N` samples.

### Reduction matrix `P`

Not all lumped parameters are independent. `P_i` maps base parameters to joint-`i` lumped coefficients:

```
tau_i = yp * P_i * theta_b
```

`P` has size `p x l x n` (page matrix: one `P_i` per joint).

### Gravity vs inertial columns (key insight)

| Term type | Nonzero exponents in rows of `E` |
|-----------|----------------------------------|
| Gravity | `q`, `sin(q)`, `cos(q)` only (rows `1:3n`) |
| Velocity | `qdot` rows (`3n+1:4n`) |
| Acceleration | `qddot` rows (`4n+1:5n`) |

Gravity torque magnitude includes `9.806132 * g_direction` applied inside `generateYp`.

### Evaluate torque in one line

```matlab
tau = PSDM.inverseDynamics(E, P, Theta, Q, Qd, Qdd);
% Internally: Yp = generateYp(...); Yb = blockprod(Yp,P); tau = Yb * Theta
```

---

## Appendix F: RMSE and R² metrics

### RMSE (root mean square error)

```
RMSE = sqrt( mean( (tau_meas - tau_hat).^2 ) )
```

Units: Nm. Lower is better.

### R² (coefficient of determination)

```
R2 = 1 - SS_res / SS_tot
SS_res = sum( (tau_meas - tau_hat).^2 )
SS_tot = sum( (tau_meas - mean(tau_meas)).^2 )
```

`R2 = 1` is perfect; `R2 = 0` means the model is no better than predicting the mean.

MATLAB:

```matlab
SS_res = sum((tau_meas(:) - tau_hat(:)).^2);
SS_tot = sum((tau_meas(:) - mean(tau_meas(:))).^2);
R2 = 1 - SS_res/SS_tot;
```

---

## Appendix G: Motor torque and gear ratio conversion

### Symbols

| Symbol | Typical unit | Meaning |
|--------|--------------|---------|
| `Kt_motor` | Nm/A | Torque constant at motor shaft |
| `N` | - | Gear ratio (motor revs per joint rev) |
| `eta` | - | Efficiency (0 to 1) |
| `Kt_joint` | Nm/A | Effective constant at joint |

### Power balance (ideal gearbox)

```
tau_joint * qdot_joint = tau_motor * qdot_motor
qdot_motor = N * qdot_joint
=> tau_joint = tau_motor / N = (Kt_motor * i) / N
```

So:

```
Kt_joint = Kt_motor / N        (verify direction with firmware team)
```

### Sign

If positive motor current produces negative joint torque under your convention:

```
Kt_joint = -abs(Kt_motor / N)
```

Always confirm with a slow static test: hold pose, command small `+q` motion, check whether `i` sign matches expected gravity torque sign.

---

## Appendix H: LuGre friction model (summary)

From the application preprint (Eq. (12) to (14)).

### State equation

```
zdot_i = qdot_i - (qdot_i / g_i(qdot_i)) * z_i
```

### Friction torque

```
tau_fric_i = sigma0_i * z_i + sigma1_i * zdot_i + Fv_i * |qdot_i|^dv_i * sign(qdot_i)
```

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

| Term | Definition |
|------|------------|
| Base parameters `theta_b` | Minimal set of inertial combinations identifiable from motion |
| DH table | `n x 6` kinematic parameters for PSDM |
| Digital twin | Simulation model calibrated to match real robot |
| Regressor `Y` | Matrix multiplying parameter vector to predict torque |
| URDF | XML robot description format |
| Held-out data | Validation set never used during parameter fitting |
