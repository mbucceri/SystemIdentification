# SystemIdECMaster — Verification Strategy

**Status:** H1 baseline

## Verification Levels

### V1 — Host unit tests
Pure logic in the Dev Container.

### V2 — Host component tests
Multiple software components using deterministic fakes/mocks.

### V3 — Static analysis / inspection
MISRA process, architecture constraints, dependency/build rules.

### V4 — Linux target timing tests
Executed directly on the Linux target. Measure cycle period, jitter, execution time, and timing violations.

### V5 — Physical EtherCAT HIL tests
SystemIdECMaster communicates through the real EtherCAT network with the QNX HIL simulator.

### V6 — Controlled physical robot tests
Executed only after the HIL acceptance gate has passed.

## Requirement-family mapping

| Requirement family | Primary verification |
|---|---|
| CLI/configuration | V1 / V2 |
| ENI/XML parsing | V1 / V2 / V5 |
| Lifecycle state machine | V1 / V2 / V5 |
| DS402 command behavior | V2 / V5 |
| EtherCAT state progression | V5 |
| 1 ms / ±100 µs timing | V4, then V5 |
| Safety limits | V1 / V2 / V5 |
| Emergency output | V5, then V6 |
| Global drive disable | V5, then V6 |
| MCAP recording | V1 / V2 / V5 |
| MISRA/code constraints | V3 |

## Rules

1. AI review never replaces deterministic verification.
2. Timing claims must come from the target Linux runtime.
3. Hardware-motion tests require explicit authorization.
4. HIL is the primary integration gate before physical robot testing.
5. Safety-related transitions require negative/fault tests.
6. Open requirements remain unverified until their semantics are resolved.
