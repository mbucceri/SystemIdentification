# PSDM System Identification Workflow (Detailed)

This document is the detailed, step-by-step execution guide for building and validating a PSDM-based inverse dynamics model of a robot manipulator. It expands the approved outline in `workflow_outline.md` and incorporates resolution procedures from `critical_ambiguities.md`.

## Purpose and scope

The workflow produces a calibrated digital twin expressed in PSDM regressor form:

```
tau_i = yp(q, qdot, qddot) * P_i * theta_b
```

where `E` and `P` come from `PSDM.deriveModel`, and `theta_b` is identified from real-robot telemetry. Optional fast code generation and forward dynamics follow PSDM-README Sections 3.2 to 3.4.

**In scope:** serial rigid-body chains, revolute and prismatic joints, motor-current torque proxy, sequential calibration structure validated in the Lloyd et al. application preprint.

**Out of scope (unless explicitly added later):** flexible joints, backlash models, cable harness effects, tool/process forces not modeled in URDF.

## Authoritative sources

| Source | Role |
|--------|------|
| Lloyd et al. (2021), *Mechanism and Machine Theory* | PSDM theory, regressor structure, sample selection (Section 3.3), additional effects (Section 3.5) |
| PSDM-README.pdf | MATLAB API, DH table format, `deriveModel`, `inverseDynamics`, code generation |
| Lloyd et al. application preprint (Denso VS-6556G) | Four-step experimental calibration: motor, gravity, friction, inertial |
| GitHub `CarletonABL/PSDM` | Reference implementation and examples |
| `critical_ambiguities.md` | Execution-time resolution for `Kt` conversion and derivative filtering |

Claims below are tied to these sources. Items marked **[Needs confirmation]** require robot-specific verification before identification runs.

---

## Prerequisites

### Software

| Component | Requirement |
|-----------|-------------|
| MATLAB | R2018a or newer (PSDM-README Section 1) |
| PSDM toolbox | Clone or add `CarletonABL/PSDM` to MATLAB path |
| Optional: Symbolic Toolbox | Examples only |
| Optional: MATLAB Coder | `PSDM.make()`, `makeInverseDynamics`, MEX compilation |
| Optional: Parallel Computing Toolbox | Faster derivation (`use_par` in `+PSDM/config.m`) |
| Python 3 | URDF parsing and FK validation scripts (Phase 1) |

### Hardware and measurement

- Robot URDF (joint axes, link transforms, limits).
- EtherCAT telemetry on QNX, nominal 1 ms sample period.
- Logged signals: timestamps, `q`, `qdot` (or derivable from `q`), motor current `i`.
- Motor plate data: `Kt_motor` per joint at motor reference.
- Transmission data per joint: gear ratio, direction/sign convention.
- Gravity direction in base frame (unit vector pointing upward, PSDM-README Eq. (6) convention).

### Required artifacts before Phase 3

Create and version-control these files:

1. `conventions_sheet.md` (frames, joint signs, units, `Kt` policy).
2. `dh_table.mat` or `dh_table.csv` (approved after Gate 1).
3. `kt_conversion_notes.md` (after Checkpoint A).
4. `derivative_filter_config.yaml` (after Checkpoint B).

---

## Phase 0: Scope and conventions lock

**Goal:** Freeze reference frames, sign conventions, and data contracts so URDF, DH, telemetry, and regression datasets are mutually consistent.

### Step 0.1: Define coordinate conventions

1. Document base frame orientation and gravity vector `g` (unit vector, upward).
2. Document joint position sign convention for each joint (positive rotation direction).
3. Document current sign convention (motor current positive direction vs joint torque positive direction).
4. Document tool frame and any fixed payload included in URDF vs treated as known `tau_ee`.

**Output:** `conventions_sheet.md` with one row per joint for sign, units, and limits.

### Step 0.2: Lock URDF-to-DH policy

1. Choose **standard DH** or **modified DH** (Spong and Vidyasagar, 2008, per PSDM-README Section 2.1).
2. State joint indexing: base (joint 1) to tool (joint n).
3. State how fixed URDF joint origins map into `d_i` and `theta_i` offsets.
4. State how `t_i` (0 = revolute, 1 = prismatic) and `s_i` (+1 or -1) are assigned from URDF axis direction.

**Output:** written convention plus acceptance tolerance for FK cross-check (recommended: position error < 1 mm, orientation error < 0.1 deg at test poses).

### Step 0.3: Define data contract for logs

Minimum columns per sample:

| Field | Description |
|-------|-------------|
| `t` | Monotonic timestamp (s) |
| `q_1..q_n` | Joint position (rad or m) |
| `qdot_1..qdot_n` | Joint velocity (if not logged, derive consistently) |
| `i_1..i_n` | Motor current (A) |
| `cycle_dt_nominal` | Nominal sample period (e.g. 0.001 s) |
| `cycle_dt_measured` | `t[k] - t[k-1]` for jitter analysis |

**Output:** data contract section in `conventions_sheet.md`.

### Step 0.4: Execution checklist

Confirm before Phase 1:

- [ ] URDF matches physical robot configuration (including tool mass if modeled).
- [ ] All joint limits in URDF match controller limits.
- [ ] Motor `Kt` datasheets collected for every actuated joint.
- [ ] Gear ratios and sign conventions confirmed with drive firmware documentation.
- [ ] PSDM toolbox loads without error (`help PSDM.deriveModel`).

**Gate 0 (internal):** conventions sheet reviewed and frozen.

---

## Phase 1: URDF to PSDM kinematics

**Goal:** Produce `DH` (`n x 6`) and gravity vector `g` for `PSDM.deriveModel(DH, g)`.

### Step 1.1: Parse URDF joint chain

1. Extract ordered joint list from base to tool.
2. For each joint, record:
   - type (revolute / prismatic),
   - axis vector in parent frame,
   - origin transform (parent to child),
   - limits (`lower`, `upper`).
3. Ignore fixed joints except as static transforms folded into link geometry.

**Tool:** `urdf_to_dh.py` (to be implemented in a later task) or equivalent parser.

**Output:** intermediate `urdf_kinematics.json` with joint chain metadata.

### Step 1.2: Build PSDM DH table

Construct `DH` with columns `[a_i, alpha_i, d_i, theta_i, t_i, s_i]` per PSDM-README Eq. (4) and Eq. (5):

```
d_i_star = d_i + t_i * s_i * q_i
theta_i_star = theta_i + (1 - t_i) * s_i * q_i
```

Procedure:

1. Walk the joint chain using the convention locked in Phase 0.
2. Convert each URDF joint origin + axis into DH parameters for link `i`.
3. Set `t_i = 0` for revolute, `t_i = 1` for prismatic.
4. Set `s_i = +1` or `-1` so that positive telemetry `q_i` matches positive URDF joint motion under the locked sign convention.
5. Encode fixed offsets from URDF into constant `d_i` or `theta_i` terms (not into `q_i`).

**Output:** `dh_table.csv` and `dh_table.mat`.

### Step 1.3: Define gravity vector

1. Express gravity as a unit vector in the PSDM base frame, pointing upward (against gravity).
2. Default if Z is up: `g = [0, 0, 1]^T` (PSDM-README Eq. (6)).
3. If omitted in `deriveModel`, PSDM assumes this default.

**Output:** `g` vector recorded alongside `DH`.

### Step 1.4: Forward kinematics validation

1. Implement or use URDF FK and DH FK with the same `q` samples.
2. Sample joint configurations:
   - joint limits corners (if safe offline),
   - at least 100 random poses within limits,
   - poses planned for later experiments.
3. Compare end-effector position and orientation (or last link frame) between models.
4. If error exceeds tolerance, revise mapping at the failing joint and repeat.

**Output:** `fk_validation_report.md` with max error statistics and test poses.

### Step 1.5: MATLAB import check

```matlab
DH = load('dh_table.mat');  % n x 6
g  = [0; 0; 1];             % adjust per conventions
assert(size(DH, 2) == 6);
assert(all(DH(:, 5) == 0 | DH(:, 5) == 1));
assert(all(abs(DH(:, 6)) == 1));
```

**Gate 1:** FK consistency accepted. Do not proceed to identification until this gate passes.

---

## Phase 2: PSDM model derivation

**Goal:** Obtain exponent matrix `E` and reduction matrices `P` (stored as `P_i` per joint in the toolbox).

### Step 2.1: Install and configure PSDM

1. Clone `https://github.com/CarletonABL/PSDM`.
2. Add repository root to MATLAB path.
3. Optional: run `PSDM.make()` and set `use_mex = true` in `+PSDM/config.m`.
4. Optional: set `use_par = true` if Parallel Computing Toolbox is available.

### Step 2.2: Optional inertial parameter mask `X`

If some inertial parameters are known zero (e.g. negligible off-diagonal inertia, negligible link mass), supply mask matrix `X` per PSDM-README Section 2.2 and Lloyd (2021) Section 3.3:

- Numerical values in `X` are not used.
- Entries set to exactly zero are implicitly removed from the derived model.

If no simplification is desired, omit `X`.

### Step 2.3: Derive the model

```matlab
[E, P] = PSDM.deriveModel(DH, g);
% With optional simplification mask:
% [E, P] = PSDM.deriveModel(DH, g, X);
```

Record derivation options if used:

- `tolerance` (default `1e-10`, PSDM-README Section 2.4),
- `verbose`,
- `gravity_only` (diagnostic only).

**Output:** `psdm_model.mat` containing `E`, `P`, `DH`, `g`, derivation timestamp, MATLAB version.

### Step 2.4: Determine base parameter count

1. Inspect dimensions of `P` and derived `theta_b` structure.
2. Record `l = length(theta_b)` (base parameter count, `l <= 10n` per Lloyd 2021).
3. Optional: map to physical interpretation using `PSDM.X2Theta` if URDF inertias are available as a starting guess.

```matlab
% If URDF inertias are available:
% Theta = PSDM.X2Theta(DH, g, X);
```

### Step 2.5: Optional complexity reduction

If runtime is critical:

```matlab
[Eh, Ph] = PSDM.reduceModelComplexity(DH, g, X, E, P, options);
```

Trade accuracy vs evaluation speed (PSDM-README Section 3.4). Keep both full and reduced models if comparison is needed.

**Gate 2 (partial):** `psdm_model.mat` loads and `PSDM.inverseDynamics` runs on random `(Q, Qd, Qdd)` without error.

---

## Phase 3: Real-robot data collection and preprocessing

**Goal:** Produce cleaned train and validation datasets with `q`, `qdot`, `qddot`, and `tau_meas`.

### Step 3.1: Resolve `Kt_motor` to `Kt_joint` (Checkpoint A)

Follow `critical_ambiguities.md`, Ambiguity 1.

1. Write the canonical conversion equation from motor reference to joint reference using power/torque balance and the gearbox definition used in firmware.
2. Document ratio direction and sign for each joint in `kt_conversion_notes.md`.
3. **[Needs confirmation]** First-pass policy: use plate `Kt` with fixed conversion; defer efficiency to a refinement step unless bench tests show systematic bias.
4. Bench validation: low-velocity sweeps, compare predicted static torque trend vs current-derived torque.
5. Lock joint-side constants `Kt_joint` (vector, Nm/A).

Torque proxy (preprint Eq. (11), joint-side constants):

```
tau_meas = diag(Kt_joint) * i
```

### Step 3.2: Design excitation trajectories

Use trajectory types aligned with the calibration step that will consume the data (preprint Section 3):

| Calibration step | Trajectory intent |
|------------------|-------------------|
| Motor (`Kt`) | Slow constant-velocity sweeps, forward and reverse, with and without known end-effector mass |
| Gravity | Slow joint motion, velocity high enough to escape static friction, low enough to neglect inertia |
| Friction | Per-joint sinusoids, small to large amplitude, varying speed |
| Inertial | Multi-sine excitation across joints, optimized for regressor conditioning |

For inertial identification, optimize trajectory parameters to minimize `cond(Y_iner)` subject to position, velocity, and acceleration limits (preprint Section 3.4, Eq. (22) to (23)). Lloyd (2021) Section 3.3 recommends uniformly random `q` within limits and `qdot`, `qddot` in `[-1, 1]` for synthetic derivation; experimental trajectories should still avoid regressor collinearity.

**Output:** `trajectory_manifest.md` listing each log file, its purpose, and safety limits.

### Step 3.3: Data logging

1. Log at EtherCAT rate with raw timestamps.
2. Record nominal and measured `dt` per sample.
3. Ensure `q` and `i` share the same clock (or document interpolation policy if not).
4. Store raw logs immutable; derive processed sets in separate files.

**Output:** `raw_logs/` directory.

### Step 3.4: Characterize timing (Checkpoint B)

Follow `critical_ambiguities.md`, Ambiguity 2.

1. Compute `dt` statistics: mean, std, min, max, outlier rate.
2. Produce `timing_quality_report.md` with plots of `dt` and cumulative time error.
3. Choose preprocessing policy:
   - if jitter is small: keep native samples,
   - if jitter exceeds threshold **[Needs confirmation: set threshold from first logs]**: resample to uniform grid (e.g. 1 kHz).

### Step 3.5: Resample and filter

1. Apply chosen resampling method to obtain uniform `dt`.
2. Filter positions or velocities as needed before differentiation (record cutoff frequencies and filter type).
3. Preprint examples use zero-phase Butterworth (`filtfilt`): 4 Hz for slow calibrations, 15 to 40 Hz for friction and inertial steps. Adapt cutoffs to your sample rate and noise floor.

**Output:** `derivative_filter_config.yaml` with filter type, order, cutoff, and rationale.

### Step 3.6: Estimate `qdot` and `qddot`

1. Prefer central-difference or higher-order smoothed differentiators on uniformly sampled data.
2. Avoid bare first-order backward difference for production `qddot` except as a diagnostic.
3. Compare candidate methods on spectral content and noise gain; select the trade-off that preserves inertial bandwidth while limiting noise (Checkpoint B acceptance criteria).
4. Verify `qddot` plausibility against commanded motion and joint acceleration limits.

### Step 3.7: Segment train and validation

1. Split by trajectory or by time (preprint uses 85/15 train/validation).
2. Keep held-out trajectories for final model acceptance (not used during any parameter fit).
3. Label each segment with its calibration purpose (motor, gravity, friction, inertial, combined).

**Output:** `processed_data/train.mat`, `processed_data/val.mat` (or equivalent), plus `dataset_manifest.md`.

**Gate 2:** Data quality accepted (timestamp stability documented, derivative settings validated on representative logs).

---

## Phase 4: Base parameter identification

**Goal:** Solve for `theta_b` and optional actuator/friction parameters.

Two execution modes are supported:

- **Mode A (recommended for first robot):** Sequential four-step calibration from the application preprint.
- **Mode B:** Direct single-step least squares on full `tau_meas` if friction is negligible and `Kt_joint` is trusted.

### Mode A: Sequential calibration (preprint Section 3)

Full dynamic decomposition:

```
tau = diag(Kt_joint) * i = tau_grav + tau_fric + tau_iner + tau_ee
```

#### Step 4A.1: Motor calibration (preprint Section 3.1)

1. Use slow velocity sweeps with and without known calibration mass.
2. Average forward and reverse currents to cancel friction (symmetric friction assumption).
3. Solve preprint Eq. (16):

```
diag(Kt_joint) * (i_w - i_nom) = J(q)^T * f_w
```

where `f_w` is the wrench from the known mass (preprint Eq. (17)).
4. Validate with R² and RMSE on held-out segments.

**Output:** refined `Kt_joint` (if plate values are adjusted) in `identified_joint_parameters.mat`.

#### Step 4A.2: Gravity calibration (preprint Section 3.2)

1. From PSDM model, extract gravity columns of the regressor to form `Y_grav(q)` (acceleration function `a = g` only).
2. Identify `theta_b_grav` subset using slow-motion data and preprint Eq. (18):

```
diag(Kt_joint) * i = Y_grav(q) * theta_b_grav + J(q)^T * f_ee
```

3. Subtract known end-effector wrench if tool inertias are modeled separately.
4. Validate on held-out slow trajectories.

#### Step 4A.3: Friction calibration (preprint Section 3.3)

1. Per-joint sinusoidal excitation; isolate friction via preprint Eq. (19):

```
tau_fric = diag(Kt_joint) * i - Y_grav(q) * theta_b_grav - J(q)^T * f_ee
```

2. Fit LuGre parameters (preprint Eq. (12) to (14)) or a simpler friction model if appropriate.
3. High-velocity subset: fit Coulomb and viscous terms (preprint Eq. (20)) with nonlinear least squares.
4. Low/pre-sliding regime: fit remaining LuGre parameters with simulation-based cost (preprint uses `fminsearch` on simulated LuGre dynamics).

**Output:** friction parameters per joint in `identified_joint_parameters.mat`.

#### Step 4A.4: Inertial calibration (preprint Section 3.4)

1. Compute residual dynamic torque:

```
tau_iner_meas = tau_meas - tau_grav_hat - tau_fric_hat - tau_ee
```

2. Form `Y_iner(q, qdot, qddot)` from remaining PSDM regressor columns.
3. Solve preprint Eq. (21):

```
tau_iner_meas = Y_iner(q, qdot, qddot) * theta_b_iner
```

4. Monitor `cond(Y_iner)` during trajectory design and after sample selection.
5. Use regularized least squares if conditioning remains poor:

```
theta_b_iner = argmin ||Y_iner * theta - tau_iner_meas||^2 + lambda * ||theta||^2
```

Choose `lambda` by cross-validation or L-curve analysis.

**Output:** complete `theta_b` assembled from `theta_b_grav` and `theta_b_iner`.

### Mode B: Direct identification

Use when friction is negligible and `Kt_joint` is fixed from datasheets.

#### Step 4B.1: Build regression matrix

For each sample `k` and joint `i`:

1. Evaluate `yp(q_k, qdot_k, qddot_k)` from `E` (PSDM-README Eq. (2), (3)).
2. Form joint regressor row: `y_row_i = yp_k * P_i`.
3. Stack into `Y_full` of size `(N*n) x l`.

```matlab
% Conceptual structure; use PSDM API for yp evaluation
% Y_full(row_i, :) = yp(qk, qdk, qddk) * P{i};
% tau_vec = reshape(tau_meas, [], 1);
% theta_b = Y_full \ tau_vec;
```

#### Step 4B.2: Solve and diagnose

1. Solve least squares for `theta_b`.
2. Report `cond(Y_full)`, parameter covariance estimate, and per-joint residual RMS.
3. Compare against optional URDF-based `PSDM.X2Theta` prior if available.

### Step 4.3: Optional motor inertia in PSDM model

If motor inertias should be inside `theta_b` (Lloyd 2021 Section 3.5, Eq. (52)):

1. Include `Im_i` column in `X` mask when calling `deriveModel`.
2. Ensure sampling dynamics during derivation include `tau_m_i = Im_i * qddot_i`.
3. Re-derive or confirm existing `E`, `P` capture motor inertia terms.

Friction cannot be embedded in standard PSDM form (Lloyd 2021 Section 3.5); keep friction outside the PSDM regressor and subtract it before inertial fits, as in Mode A.

**Gate 3:** Identification accepted when held-out torque prediction meets project thresholds (set per joint RMSE and R² targets; preprint reports R² from 0.81 to 1.00 depending on joint and effect).

---

## Phase 5: Validation and digital twin packaging

**Goal:** Package a reusable simulation model with documented accuracy.

### Step 5.1: Torque prediction validation

1. On held-out trajectories, compute:

```
tau_hat = PSDM.inverseDynamics(E, P, Theta, Q, Qd, Qdd)
```

2. If friction and gravity subsets were identified separately, add `tau_fric_hat` and verify decomposition consistency.
3. Report per-joint RMSE, R², max error, and residual spectra.
4. Compare slow-speed (gravity-dominated) vs high-speed (inertial-dominated) segments separately.

**Output:** `validation_report.md`.

### Step 5.2: Forward dynamics check (optional)

```matlab
Qdd_sim = PSDM.forwardDynamics(E, P, Theta, Q, Qd, tau_meas);
```

Compare simulated accelerations to measured `qddot` for model sanity (not a substitute for torque validation).

### Step 5.3: Export model package

Minimum package contents:

| File | Content |
|------|---------|
| `psdm_model.mat` | `E`, `P`, `DH`, `g` |
| `theta_b.mat` | Identified base parameters |
| `identified_joint_parameters.mat` | `Kt_joint`, friction params if used |
| `conventions_sheet.md` | Frames, signs, units |
| `kt_conversion_notes.md` | Torque conversion documentation |
| `derivative_filter_config.yaml` | Preprocessing reproducibility |
| `validation_report.md` | Metrics and plots |

### Step 5.4: Fast code generation (optional)

```matlab
PSDM.makeInverseDynamics('id_psdm', E, P, Theta);
PSDM.makeForwardDynamics('fd_psdm', E, P, Theta);
```

Compile MEX if Coder is available (PSDM-README Section 3.3 and 4).

### Step 5.5: Simulink or external integration

1. Wrap generated MEX or MATLAB functions behind a single interface:

```
tau = robot_inverse_dynamics(q, qdot, qddot)
```

2. Document input units and joint ordering explicitly in the interface header.
3. Version the package (`model_v1.0.0`, date, git hash of scripts).

**Gate 4:** Packaging accepted when runtime, interface, and accuracy requirements are met.

---

## Phase 6: Iteration loop

Repeat Phases 3 to 5 when:

- new trajectories improve excitation of poorly observed parameters,
- payload or tool changes (update URDF/`tau_ee` or re-run gravity and inertial steps),
- `Kt_joint` or friction parameters drift with temperature or wear,
- model complexity trade-off changes (apply `reduceModelComplexity`).

Iteration checklist:

1. Bump model version.
2. Re-run only the calibration steps affected by the change.
3. Re-validate on all held-out trajectories, not only new logs.
4. Append to identification run log referencing Checkpoint A/B decisions.

---

## Approval gates summary

| Gate | Criterion | Blocking if failed |
|------|-----------|-------------------|
| **Gate 1** | URDF vs DH FK within tolerance | Yes, before `deriveModel` |
| **Gate 2** | Timestamp jitter quantified; derivative filter validated | Yes, before regression |
| **Gate 3** | Held-out torque fit meets thresholds | Yes, before release |
| **Gate 4** | Runtime and API requirements met | Yes, before deployment |

---

## Reproducibility checklist

Before declaring the workflow complete for a robot instance:

- [ ] `conventions_sheet.md` matches firmware and URDF.
- [ ] `dh_table` passed Gate 1 FK validation.
- [ ] `psdm_model.mat` derived from approved `DH` and `g`.
- [ ] `kt_conversion_notes.md` completed (Checkpoint A).
- [ ] `timing_quality_report.md` and `derivative_filter_config.yaml` completed (Checkpoint B).
- [ ] Train/validation split documented; held-out set never used in fitting.
- [ ] `theta_b` and optional friction/`Kt` parameters stored with version metadata.
- [ ] `validation_report.md` attached to model package.
- [ ] Identification run log references all checkpoint decisions.

---

## Planned companion artifacts (later tasks)

These items are referenced by this workflow but created in separate implementation tasks:

- `urdf_to_dh.py` and FK validation script (Phase 1).
- MATLAB helper scripts for regressor assembly and sequential calibration (Phase 4).
- Example config templates for `derivative_filter_config.yaml`.

---

## References

1. Lloyd, S., Irani, R., Ahmadi, M. (2021). A numeric derivation for fast regressive modeling of manipulator dynamics. *Mechanism and Machine Theory*, 156, 104149. doi: [10.1016/j.mechmachtheory.2020.104149](https://doi.org/10.1016/j.mechmachtheory.2020.104149)
2. PSDM-README.pdf (MATLAB toolbox documentation, Carleton ABL).
3. Lloyd, S., Irani, R., Ahmadi, M. Application of PSDM in the modeling and calibration of a 6-DOF articulated robot (preprint, Denso VS-6556G).
4. Spong, M. W., Vidyasagar, M. (2008). *Robot Dynamics and Control*. John Wiley and Sons.
5. GitHub repository: [https://github.com/CarletonABL/PSDM](https://github.com/CarletonABL/PSDM)
