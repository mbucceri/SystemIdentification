# SystemIdECMaster — Open Requirements Questions

**Status:** Residual open items after H1  
**Revision:** 4

The functional baseline is sufficient to enter H2. The following items remain intentionally open for platform/design investigation.

## OQ-003 — Timing semantics
The target timing tolerance is ±100 µs around the nominal 1 ms cycle. During H2/H3 define:
- whether this limit applies to wake-up jitter, cycle-start jitter, cycle execution time, or total period error;
- how violations are counted;
- how many violations are tolerated before an emergency response;
- whether timing faults trigger the same global emergency sequence.

## OQ-004 — Emergency-output details
Define:
- slave/PDO carrying the emergency digital output;
- active polarity;
- latching behavior;
- reset behavior;
- maximum detection-to-output latency.

## OQ-005 — Current signal definition
Define the exact PDO quantity used as drive-current feedback for recording and safety supervision.

## OQ-006 — Trajectory serialization
Select the concrete human-readable format (CSV, JSON, YAML, or other) based on validation, multi-joint representation, metadata, and C++ parsing needs.

## OQ-007 — MCAP schema
Define channels/messages, schemas, metadata, compression policy, and signal mapping.

## OQ-008 — XML schemas
Define validation rules/schema strategy for the engineering and safety XML files.

## OQ-009 — WKC/link-fault behavior
Only loss of slave OP state is currently specified as an emergency trigger. Define whether invalid WKC, frame loss, or physical-link loss map directly to the same emergency sequence or are handled through the OP-state mechanism.

## OQ-010 — HIL acceptance gate
Define the mandatory test set against the QNX HIL simulator before physical robot testing.

## OQ-SM-001 — Error-state taxonomy
Define the specific error states required by the application state machine and map fault classes to them.

## OQ-SM-002 — State entry/exit actions
Define precise entry and exit actions for each lifecycle state, especially drive disable, emergency-output handling, MCAP finalization, and EtherCAT shutdown.

## OQ-SM-003 — State-transition timeouts
Define timeout requirements for EtherCAT state transitions, drive enable, move-to-start, `TARGET_REACHED` wait, and completion/shutdown transitions.

## OQ-SM-004 — Configuration semantic validation
Define the semantic consistency checks required across ENI, engineering XML, safety XML, and trajectory specification before EtherCAT initialization.
