# SystemIdECMaster — External Interfaces

**Status:** H1 baseline

## IF-001 — Command line
The application is manually launched and receives references to ENI, engineering XML, safety XML, trajectory input, and MCAP output destination.

## IF-002 — EtherCAT network
IgH/EtherLab master; Luna DB 3.5 initial target. Runtime ENI parsing is required. Distributed Clocks are not required initially.

## IF-003 — DS402 drives
Required behaviors:
- Profile Position Mode for position experiments;
- Cyclic Synchronous Velocity for velocity experiments;
- Profile Position Mode for move-to-start;
- TARGET_REACHED used for start-position completion.

## IF-004 — Trajectory input
Human-readable representation including experiment mode, selected joints, one sample per EtherCAT cycle, start position, move-to-start velocity/acceleration limits, start hold delay, samples, and completion delay.

## IF-005 — Engineering configuration
XML-based motor/joint/sensor engineering configuration.

## IF-006 — Safety configuration
XML-based safety-limit configuration.

## IF-007 — MCAP output
Each recorded sample includes at least cycle index, monotonic host timestamp, and configured signals.

## IF-008 — Emergency hardware output
A digital EtherCAT output is connected to the robot drive emergency line. Emergency behavior disables all drives and keeps EtherCAT alive where possible until restart.

## IF-009 — QNX HIL simulator
Physical EtherCAT integration environment representing protocol, DS402 behavior, and robot dynamics before physical robot testing.
