# SystemIdECMaster — Non-Functional Requirements

**Status:** H1 baseline

## NFR-001 — Language baseline
Production code shall use C++17.

## NFR-002 — Coding standard
Production C++ shall follow the project MISRA C++:2023 process.

## NFR-003 — Nominal real-time cycle
The nominal cyclic execution period shall be 1 ms.

## NFR-004 — Configurable timing tolerance
The timing tolerance shall be configurable, with an initial target of ±100 µs around the nominal cycle.

## NFR-005 — Target-based timing evidence
Timing compliance shall be demonstrated on the actual Linux target environment, not inferred from Dev Container execution.

## NFR-006 — Deterministic cyclic-path design
The cyclic path shall avoid or explicitly justify operations capable of unbounded or poorly bounded latency.

## NFR-007 — Runtime observability
The software shall expose sufficient diagnostics to evaluate cycle timing, EtherCAT state, and experiment execution.

## NFR-008 — Configuration validation
Configuration inputs shall be validated before use for physical-device control.

## NFR-009 — Failure containment
Unrecoverable application or experiment faults shall enter explicit final error states.

## NFR-010 — Restart-based recovery
Recovery from an emergency final state shall require application restart.

## NFR-011 — Recorded-data integrity
MCAP output shall preserve sample ordering and timing association sufficiently to reconstruct the EtherCAT acquisition sequence.

## NFR-012 — Open-source runtime stack
The runtime stack shall use open-source components wherever practical, including Linux and IgH/EtherLab.
