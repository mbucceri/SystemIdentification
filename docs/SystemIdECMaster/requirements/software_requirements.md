# SystemIdECMaster — Software Requirements

**Status:** Baseline for H2 entry  
**Milestone:** H1 — Requirements Elicitation  
**Revision:** 3

## SW-001 — Command-line application
The software shall provide a command-line entry point for launching an experiment.

## SW-002 — Required inputs
The software shall obtain references to:
1. ENI file;
2. robot engineering XML;
3. safety-limit XML;
4. experiment trajectory file;
5. MCAP output destination.

## SW-ECAT-001 — IgH master integration
The software shall use the IgH/EtherLab EtherCAT Master stack.

## SW-ECAT-002 — Runtime ENI processing
The software shall parse the ENI at runtime and use it to configure the EtherCAT master/application mapping.

## SW-ECAT-003 — Cyclic exchange
The software shall exchange configured EtherCAT process data with a nominal cycle period of 1 ms.

## SW-ECAT-004 — Configurable timing tolerance
The software shall support a configurable cycle-timing tolerance with a default target of ±100 µs.

## SW-ECAT-005 — No DC dependency
The first implementation shall not require EtherCAT Distributed Clocks.

## SW-ECAT-006 — One trajectory sample per cycle
During an active experiment, the software shall consume exactly one trajectory sample per EtherCAT cycle for each excited joint.

## SW-ECAT-007 — Communication after emergency
Following an emergency-trigger condition, the software shall keep cyclic EtherCAT communication active for diagnostics until shutdown/restart unless communication failure makes this impossible.

## SW-ECAT-008 — OP-state supervision
The software shall supervise slave operational state and shall trigger the emergency sequence if any required slave leaves OP.

## SW-DS402-001 — Position mode transport
For position experiments, the software shall transport externally supplied target-position samples using CiA 402 Profile Position Mode.

## SW-DS402-002 — CSV transport
For velocity experiments, the software shall transport externally supplied target-velocity samples using DS402 Cyclic Synchronous Velocity mode.

## SW-DS402-003 — Arbitrary joint subset
The software shall support commanding any configured subset of the 11 Luna DB 3.5 joints.

## SW-DS402-004 — Non-excited joints
The software shall command non-excited joints according to experiment mode:
- velocity experiment: target velocity = 0;
- position experiment: target position = configured trajectory starting position.

## SW-SAFE-001 — Cyclic safety monitoring
The software shall evaluate configured position, speed, and current limits during experiment execution.

## SW-SAFE-002 — Global drive disable
On a configured safety-limit violation or required-slave OP-state loss, the software shall disable all robot drives.

## SW-SAFE-003 — Emergency digital output
On the same emergency conditions, the software shall assert the configured emergency digital output.

## SW-SAFE-004 — Restart-required recovery
After an emergency response, recovery shall require application restart.

## SW-DATA-001 — Selective PDO recording
The software shall support configuration of which received and transmitted process-data fields are persisted.

## SW-DATA-002 — MCAP output
The software shall write experiment data in MCAP format.

## SW-DATA-003 — Timing metadata
Every recorded MCAP sample shall include:
- EtherCAT cycle index;
- monotonic host timestamp.

## SW-CFG-001 — XML engineering configuration
Robot engineering configuration shall be loaded from XML.

## SW-CFG-002 — XML safety configuration
Safety-limit configuration shall be loaded from XML.

## SW-EXP-001 — Human-readable trajectory file
The software shall load a human-readable trajectory representation supporting:
- experiment mode;
- selected joints;
- one setpoint per selected joint per cycle;
- trajectory length;
- completion delay.

The concrete serialization format remains to be selected.

## SW-EXP-002 — Position completion
After the final position-mode sample, the software shall hold the final position for the configured completion delay and then disable the drives.

## SW-EXP-003 — Velocity completion
After the final velocity-mode sample, the software shall command zero velocity for the configured completion delay and then disable the drives.


## SW-EXP-004 — Pre-experiment enable
Before consuming trajectory samples, the software shall enable the drives required by the experiment.

## SW-EXP-005 — Pre-experiment stationary command
After drive enable, the software shall command selected joints to a stationary state appropriate to the active mode before initiating the move-to-start sequence.

## SW-EXP-006 — Move-to-start in position mode
Before trajectory execution, the software shall command selected joints to their configured starting positions using CiA 402 Profile Position Mode.

## SW-EXP-007 — Move-to-start velocity limit
The software shall enforce the configured maximum velocity during the move to the starting position.

## SW-EXP-008 — Move-to-start acceleration limit
The software shall enforce the configured maximum acceleration during the move to the starting position.

## SW-EXP-009 — Start-position hold delay
After reaching the configured starting position, the software shall hold that position for the configured start delay.

## SW-EXP-010 — Start gate
The software shall begin consuming experiment trajectory samples only after:
1. required drives are enabled;
2. selected joints have reached their configured starting positions;
3. the configured start-position hold delay has elapsed;
4. no emergency or startup fault condition is active.

## SW-EXP-011 — Pre-experiment configuration parameters
The experiment definition shall provide:
- starting position;
- move-to-start maximum velocity;
- move-to-start maximum acceleration;
- start-position hold delay.

The exact per-joint/shared representation shall be defined by the selected trajectory serialization format.


## SW-EXP-012 — TARGET_REACHED criterion
The software shall use the CiA 402 `TARGET_REACHED` status condition as the criterion that an individual selected joint has reached its configured starting position.

## SW-EXP-013 — All-joints synchronization before start delay
The software shall start the configured starting-position hold delay only after every selected joint reports `TARGET_REACHED`.

## SW-EXP-014 — Independent move-to-start
The software shall allow each selected joint to reach its configured starting position independently.

## SW-EXP-015 — Drive-generated start-position profile
The software shall rely on the DS402 drive's Profile Position Mode trajectory generation for the move to the starting position.

The software shall configure target position and applicable velocity/acceleration limits rather than generate the complete interpolation profile itself.

## SW-SM-001 — Explicit lifecycle state machine
The software shall implement an explicit application state machine coordinating the complete experiment lifecycle.

The nominal state flow shall contain at least:
- Application Boot;
- Application Configuration;
- EtherCAT Initialization;
- EtherCAT INIT/PREOP/SAFEOP/OP transition;
- Experiment Start Sequence;
- Experiment Execution;
- Experiment Completion;
- Error state(s).

## SW-SM-002 — Application Boot state
The Application Boot state shall validate command-line arguments and startup preconditions.

## SW-SM-003 — Application Configuration state
The Application Configuration state shall validate required files for existence and semantic correctness.

## SW-SM-004 — EtherCAT Initialization state
The EtherCAT Initialization state shall initialize the EtherCAT stack, establish cyclic communication infrastructure, and validate network topology against the runtime ENI.

## SW-SM-005 — EtherCAT state progression
The software shall supervise and coordinate EtherCAT progression through INIT, PREOP, SAFEOP, and OP before the Experiment Start Sequence.

## SW-SM-006 — Experiment Start Sequence state
The Experiment Start Sequence state shall enable the required drives, command starting positions using Profile Position Mode, monitor per-joint `TARGET_REACHED`, wait until all selected joints report `TARGET_REACHED`, hold the starting positions for the configured delay, and then transition to Experiment Execution.

## SW-SM-007 — Experiment Execution state
The Experiment Execution state shall consume one excitation sample per EtherCAT cycle and perform configured acquisition and safety supervision.

## SW-SM-008 — Experiment Completion state
The Experiment Completion state shall perform the configured mode-specific completion sequence and disable the drives after the configured completion delay.

## SW-SM-009 — Final error states
The software shall provide explicit final error state(s) for unrecoverable faults.

Once entered, these states shall not autonomously transition back to an operational experiment state. Recovery requiring user intervention is outside the application domain.
