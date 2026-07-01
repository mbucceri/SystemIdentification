# Critical Ambiguities and Resolution Plan

This document captures the remaining high-impact ambiguities for PSDM-based system identification and defines how each one will be resolved during execution.

## Scope

- Applies to data collection, preprocessing, and parameter identification phases.
- Assumes URDF-to-DH mapping, torque measurement path through motor current telemetry, and frame consistency decisions are already fixed.

## Ambiguity 1: `Kt_motor` to `Kt_joint` conversion model

### Why this matters

- A wrong conversion model creates a systematic scale/sign bias in torque labels, which directly corrupts identified dynamic parameters.
- The exact ratio direction and sign convention can differ between motor, transmission, and joint references.

### Open questions

- Should gear ratio be applied as `Kt_joint = Kt_motor * N` or `Kt_joint = Kt_motor / N` under the adopted variable definitions?
- How is transmission sign represented (mechanical inversion, software sign, or both)?
- Should transmission efficiency be included in the first-pass conversion or deferred to a refinement/calibration step?

### Resolution procedure

1. **Freeze conventions**
   - Record reference frames, positive rotation direction, and current sign conventions for each joint in a small parameter sheet.
2. **Derive conversion equation from first principles**
   - Use power/torque balance and gearbox definition used by controls firmware to derive one canonical equation.
3. **Cross-check against hardware and firmware**
   - Verify against motor datasheet notation, gearbox ratio definition, and existing drive-side implementation.
4. **Bench validation**
   - Run low-velocity tests on selected joints and compare predicted joint torque from current vs expected static/gravity load trend.
5. **Decision gate**
   - If residual bias is small and stable, keep plate-based `Kt` with fixed conversion.
   - If residual bias is systematic, introduce a bounded calibration factor per joint in the identification workflow.

### Acceptance criteria

- Sign and magnitude of `tau = diag(Kt_joint) * i` are consistent with known motion/load direction for all joints.
- Gravity-dominant segments show expected torque polarity and relative scaling.

## Ambiguity 2: EtherCAT/QNX timestamp jitter and derivative filter tuning

### Why this matters

- Acceleration estimation is sensitive to timestamp irregularity and high-frequency noise.
- Poor filter tuning can suppress inertial excitation or amplify noise, degrading regression conditioning and model validity.

### Open questions

- What are actual timestamp jitter bounds during representative robot operation?
- Which differentiator/filter configuration preserves inertial bandwidth while limiting noise amplification?
- Is current telemetry and kinematics logging synchronized tightly enough for regression-quality samples?

### Resolution procedure

1. **Characterize timing**
   - Compute sample interval statistics from logged timestamps: mean, standard deviation, min/max, and outlier rate.
2. **Set preprocessing policy**
   - Resample to a uniform grid when jitter exceeds threshold; otherwise keep native samples with robust differentiator.
3. **Tune differentiator**
   - Compare candidate filters (for example, Savitzky-Golay or higher-order FIR differentiators) on:
     - noise gain,
     - phase delay,
     - retained excitation bandwidth.
4. **Validate acceleration quality**
   - Confirm `qddot` plausibility and spectral content against commanded/observed motion.
5. **Regression impact check**
   - Evaluate condition number trends and validation residuals across filter settings, selecting the best trade-off.

### Acceptance criteria

- Timestamp jitter is quantified and within documented bounds for chosen preprocessing path.
- Selected derivative settings preserve model-relevant dynamics and reduce residual error on held-out data.

## Execution checkpoints

- **Checkpoint A (before identification):** conversion equation and signs for `Kt_joint` locked and documented.
- **Checkpoint B (before regression matrix finalization):** timestamp and filter configuration validated on representative logs.
- **Checkpoint C (before final model export):** ambiguity decisions reflected in reproducible scripts/configs and included in run notes.

## Deliverables produced by resolving ambiguities

- `kt_conversion_notes` (equation, sign, ratio, efficiency policy per joint).
- `timing_quality_report` (jitter statistics and plots).
- `derivative_filter_config` (selected method and parameters with rationale).
- Identification run log referencing all above decisions.
