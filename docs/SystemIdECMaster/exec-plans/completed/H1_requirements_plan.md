# H1 — Requirements Elicitation

**Project:** SystemIdECMaster  
**Status:** Active  
**Predecessor:** H0 — Agentic Harness Bootstrap (completed)

## Objective

Convert the current informal understanding of `SystemIdECMaster` into a compact, structured, testable requirements baseline before architecture or production implementation begins.

The objective is not to create a heavyweight certification specification. It is to establish enough precision that:

- Codex does not invent behavior;
- architectural decisions can be traced to explicit needs;
- each significant requirement can later be verified;
- unresolved questions remain visible instead of being silently assumed.

## H1 Deliverables

H1 will produce:

```text
docs/SystemIdECMaster/requirements/
├── system-requirements.md
├── software-requirements.md
├── interfaces.md
├── non-functional-requirements.md
├── verification-strategy.md
└── open-questions.md
```

A lightweight traceability convention will be established from the beginning.

## Requirement identifiers

Use stable identifiers:

```text
SYS-xxx       System-level requirements
SW-xxx        General software requirements
SW-ECAT-xxx   EtherCAT requirements
SW-DS402-xxx  DS402 requirements
SW-RT-xxx     Real-time requirements
SW-CFG-xxx    Configuration requirements
SW-DIAG-xxx   Diagnostics requirements
SW-SAFE-xxx   Safety-related requirements
SW-IF-xxx     Interface requirements
```

Identifiers are never recycled once assigned.

## Requirement format

Each requirement should contain:

```text
ID:
Title:
Statement:
Rationale:
Verification:
Status:
Notes:
```

Example:

```text
ID: SW-ECAT-001

Title:
EtherCAT master role

Statement:
The software shall operate as the EtherCAT master for the configured robot bus.

Rationale:
The application is responsible for cyclic process-data exchange and bus supervision.

Verification:
Integration test using the HIL EtherCAT network.

Status:
Draft
```

Requirements should describe observable behavior and constraints rather than implementation choices unless the implementation choice itself is a project constraint.

## H1 Workflow

### H1.1 — System purpose and operational context

Define:

- what SystemIdECMaster exists to accomplish;
- who or what invokes it;
- what external systems it interacts with;
- normal startup and shutdown;
- expected high-level operating modes;
- what data it produces and consumes.

### H1.2 — EtherCAT functional requirements

Define:

- master startup/configuration;
- slave discovery/configuration assumptions;
- PDO process-data exchange;
- expected EtherCAT states;
- bus supervision;
- Working Counter monitoring;
- fault detection/recovery;
- Distributed Clocks requirements, if any;
- expected network topology constraints.

### H1.3 — DS402 requirements

Define only behavior actually required by this application:

- supported drive states;
- controlword/statusword handling;
- operation modes;
- setpoints;
- feedback;
- drive enable/disable behavior;
- fault handling/reset;
- homing, if applicable.

### H1.4 — Real-time requirements

Define measurable constraints:

- nominal EtherCAT cycle period;
- allowed jitter;
- deadline policy;
- tolerated missed cycles;
- scheduler expectations;
- memory-allocation constraints in cyclic execution;
- logging restrictions;
- timing diagnostics required.

No timing value is to be invented.

### H1.5 — Configuration requirements

Define how the application receives:

- slave configuration;
- PDO mappings;
- drive/sensor definitions;
- cycle time;
- network interface;
- robot-specific parameters.

Decide later whether configuration is compiled, file-based, generated, or hybrid.

### H1.6 — Diagnostics and observability

Define:

- startup diagnostics;
- bus-state reporting;
- timing statistics;
- drive/sensor health;
- error/event reporting;
- runtime metrics;
- log persistence or external consumption.

### H1.7 — Safety-related behavior

Identify software reactions for:

- communication loss;
- stale process data;
- missed deadlines;
- invalid sensor data;
- drive faults;
- incomplete startup;
- unexpected slave states;
- shutdown.

This section records required behavior without claiming a formal functional-safety standard unless one is explicitly adopted.

### H1.8 — External interfaces

Document:

- physical EtherCAT interface;
- HIL environment;
- operator or supervisory interfaces;
- file/configuration interfaces;
- IPC/network interfaces, if any;
- data export needed for system-identification workflows.

### H1.9 — Verification strategy

For each requirement, classify verification as one or more of:

```text
Inspection
Host unit test
Host component test
Static analysis
Linux target integration test
Physical EtherCAT HIL test
Real robot test
Timing/performance measurement
```

### H1.10 — Open questions

Any requirement that cannot yet be made precise is recorded explicitly in `open-questions.md`.

Unknowns are not implementation freedom unless deliberately classified that way.

## H1 Exit Criteria

H1 is complete when:

- the intended system behavior is sufficiently explicit to begin architecture;
- all critical unknowns are visible;
- real-time constraints are quantified or explicitly marked unresolved;
- required EtherCAT and DS402 behavior is identified;
- interfaces are listed;
- every requirement has an intended verification method;
- Codex can read the requirements without needing to infer major product behavior.

## First elicitation session

The first session should establish only the system boundary and primary use cases.

Do not begin detailed EtherCAT or DS402 behavior until the application purpose and operating context are clear.
