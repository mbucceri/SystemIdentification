# SystemIdECMaster — System Requirements

**Status:** Baseline for H2 entry  
**Milestone:** H1 — Requirements Elicitation  
**Revision:** 3

## 1. Purpose

`SystemIdECMaster` is a command-line EtherCAT master application supporting system-identification experiments on the Luna DB 3.5 Arm.

Its primary responsibilities are:
1. configure and operate the EtherCAT network as master;
2. transport externally generated excitation trajectories to DS402 drives;
3. acquire and record EtherCAT process data;
4. supervise joint safety limits;
5. trigger an emergency digital output when required.

## 2. Initial Target System

The first supported robot is the **Luna DB 3.5 Arm**:
- 11 DS402 motor drives;
- 1 force/torque sensor;
- 2 Microchip I/O boards;
- 1 IDS custom EtherCAT node.

ENI/ESI information describing the topology is available.

## 3. Requirements

### SYS-001 — EtherCAT master role
The system shall configure and operate the EtherCAT communication network as master.

### SYS-002 — External excitation transport
The system shall transport externally generated joint trajectories or motor commands to selected DS402 drives.

### SYS-003 — Position experiments
The system shall support DS402 Profile Position Mode experiments, with one target-position sample per EtherCAT cycle for each selected joint.

### SYS-004 — Velocity experiments
The system shall support DS402 Cyclic Synchronous Velocity mode experiments, with one target-velocity sample per EtherCAT cycle for each selected joint.

### SYS-005 — Multi-joint excitation
An experiment shall support simultaneous excitation of any subset of the 11 joints.

### SYS-006 — Non-excited joints
Joints not selected for excitation shall remain stationary according to experiment mode:
- velocity time-series: command zero target velocity;
- position time-series: command the configured trajectory starting position as target position.

### SYS-007 — Process-data acquisition
The system shall acquire the real-time process data exchanged through EtherCAT cyclic datagrams.

### SYS-008 — Selective recording
The experiment configuration shall allow selecting a subset of EtherCAT process-data fields for persistent recording.

### SYS-009 — MCAP output
The system shall record experiment output in MCAP format.

### SYS-010 — Sample timing metadata
Every recorded sample shall include:
- EtherCAT cycle index;
- monotonic host timestamp.

### SYS-011 — Safety supervision
The system shall monitor configured position, speed, and drive-current safety limits during an experiment.

### SYS-012 — Emergency reaction
On a configured safety-limit violation the system shall:
1. assert the configured emergency digital output;
2. disable all robot drives;
3. keep cyclic EtherCAT communication active for diagnostics until application termination/restart.

Recovery from such an emergency shall require restarting the application.

### SYS-013 — Communication-fault emergency behavior
If any EtherCAT slave leaves OP state, the system shall trigger the same emergency response defined for a safety-limit violation.

### SYS-014 — Command-line execution
The system shall operate as a manually launched command-line application.

### SYS-015 — Configuration inputs
The system shall accept:
- EtherCAT robot/network configuration from an ENI file;
- robot motor/joint/sensor engineering configuration;
- joint/motor safety-limit configuration;
- excitation trajectory data.

### SYS-016 — Runtime ENI parsing
`SystemIdECMaster` shall parse the ENI directly at runtime.

### SYS-017 — Engineering/safety configuration format
Robot engineering configuration and safety configuration shall be represented as XML files.

### SYS-018 — Human-readable trajectory format
The trajectory input format shall be human-readable.

The final selection among CSV, JSON, YAML, or another human-readable representation remains a design decision.

### SYS-019 — Nominal EtherCAT cycle
The nominal EtherCAT cycle period shall be 1 ms.

### SYS-020 — Timing tolerance
The target cycle timing tolerance shall be ±100 µs relative to the nominal 1 ms period.

The timing tolerance shall be configurable.

### SYS-021 — No Distributed Clocks requirement
The first Luna DB 3.5 implementation is not required to use EtherCAT Distributed Clocks.

### SYS-022 — Position-mode normal completion
At the end of a position-mode experiment, the controlled joint or joints shall hold the final commanded position for a configurable completion delay and shall then be disabled.

### SYS-023 — Velocity-mode normal completion
At the end of a velocity-mode experiment, the controlled joint or joints shall be commanded to zero velocity for a configurable completion delay and shall then be disabled.

### SYS-024 — Completion delay configuration
The post-trajectory completion delay shall be part of the experiment trajectory configuration.

### SYS-025 — Luna DB 3.5 initial support
The first implementation shall support the Luna DB 3.5 Arm topology described above.

## 4. Verification Categories

Requirements will be verified using one or more of:
- host unit/component test;
- static analysis;
- Linux target integration test;
- physical EtherCAT HIL test;
- timing/performance measurement;
- controlled robot test.


### SYS-026 — Pre-experiment drive enable
Before trajectory execution begins, the system shall enable the drives required by the experiment.

**Verification:** HIL integration test.

### SYS-027 — Initial stationary state
After drive enable and before moving to the experiment start position, the selected joints shall be commanded to a stationary state appropriate to the active mode, using hold position or zero velocity as applicable.

**Verification:** HIL integration test.

### SYS-028 — Move to experiment starting position
Before trajectory execution begins, the system shall move each selected joint to its configured experiment starting position using position mode.

**Verification:** HIL integration test.

### SYS-029 — Start-position motion limits
The move to the configured starting position shall respect experiment-configured maximum velocity and acceleration limits.

**Verification:** HIL integration test and recorded-data inspection.

### SYS-030 — Starting-position hold
After reaching the configured starting position, the system shall hold that position for a configurable start delay before beginning trajectory execution.

**Verification:** HIL integration test.

### SYS-031 — Start parameters in experiment specification
The experiment specification shall contain:
- starting position;
- maximum velocity for the move to start;
- maximum acceleration for the move to start;
- starting-position hold delay.

**Verification:** Host parser/component test.

### SYS-032 — Experiment execution start
The first trajectory sample shall not be consumed until the pre-experiment initialization sequence has completed successfully.

**Verification:** Host component test and HIL integration test.


### SYS-033 — Move-to-start DS402 mode
The move to the configured experiment starting position shall use CiA 402 Profile Position Mode.

### SYS-034 — Start-position reached criterion
A selected joint shall be considered to have reached its configured starting position when the drive reports the CiA 402 `TARGET_REACHED` status condition.

### SYS-035 — Independent move-to-start coordination
Each selected joint shall move independently toward its configured starting position.

The configured starting-position hold delay shall begin only when all selected joints report `TARGET_REACHED`.

### SYS-036 — Application execution state machine
The application shall coordinate its lifecycle through an explicit state machine.

The nominal lifecycle shall contain at least:
1. Application Boot;
2. Application Configuration;
3. EtherCAT Initialization;
4. EtherCAT INIT → PREOP → SAFEOP → OP transition;
5. Experiment Start Sequence;
6. Experiment Execution;
7. Experiment Completion;
8. Error state(s).

### SYS-037 — Application Boot
During Application Boot, the application shall perform startup and command-line sanity checks.

### SYS-038 — Application Configuration
During Application Configuration, the application shall verify required configuration-file existence and semantic correctness.

### SYS-039 — EtherCAT Initialization
During EtherCAT Initialization, the application shall initialize the EtherCAT stack, establish cyclic communication, and verify the observed network topology against the runtime ENI configuration.

### SYS-040 — EtherCAT state progression
The application shall coordinate EtherCAT transition through INIT, PREOP, SAFEOP, and OP before the Experiment Start Sequence begins.

### SYS-041 — Experiment Start Sequence
The Experiment Start Sequence shall:
1. enable the required drives;
2. command configured starting positions using Profile Position Mode;
3. independently monitor each selected joint for `TARGET_REACHED`;
4. start the configured start delay only after all selected joints report `TARGET_REACHED`;
5. hold the starting positions for the configured delay;
6. transition to Experiment Execution only if no error condition is active.

### SYS-042 — Final application error states
The application state machine shall include explicit error states for unrecoverable application or experiment faults.

These states shall be final from the application perspective. Recovery requiring user intervention is outside the application domain.
