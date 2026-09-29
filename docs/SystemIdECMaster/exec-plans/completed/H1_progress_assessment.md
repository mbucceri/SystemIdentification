# H1 — Requirements Elicitation Progress Assessment

**Project:** SystemIdECMaster

## H1.1 — System purpose and operational context
**Status: COMPLETE**

Purpose, CLI execution, external trajectory source, EtherCAT role, data acquisition, Luna DB 3.5 scope, and the high-level application lifecycle are defined.

## H1.2 — EtherCAT functional requirements
**Status: SUBSTANTIALLY COMPLETE**

Defined: IgH master, runtime ENI parsing, 1 ms cycle, no Distributed Clocks requirement, INIT/PREOP/SAFEOP/OP progression, OP-loss emergency behavior, continued cyclic communication after emergency when possible.

Residual: WKC/frame/link-loss semantics and exact emergency-output mapping.

## H1.3 — DS402 requirements
**Status: SUBSTANTIALLY COMPLETE**

Defined: Profile Position Mode, Cyclic Synchronous Velocity, arbitrary joint subset, non-excited-joint behavior, Profile Position move-to-start, TARGET_REACHED gating, drive-generated move-to-start profile.

Residual: exact current feedback PDO and detailed controlword sequencing.

## H1.4 — Real-time requirements
**Status: COMPLETE FOR H1**

Defined: nominal 1 ms cycle and configurable ±100 µs target.

Deferred to H2: exact jitter metric semantics, execution-time interpretation, violation-count policy, and platform evidence.

## H1.5 — Configuration requirements
**Status: SUBSTANTIALLY COMPLETE**

Defined: runtime ENI, engineering XML, safety XML, human-readable trajectory definition, start/completion parameters.

Residual: concrete trajectory serialization and XML schema validation.

## H1.6 — Diagnostics and observability
**Status: PARTIALLY COMPLETE**

Defined: MCAP output, cycle index, monotonic timestamp, diagnostic communication retained after emergency.

Still to define in H3: runtime diagnostic/logging interface, timing-statistics structure, EtherCAT diagnostic counters, RT-safe logging policy.

## H1.7 — Safety-related behavior
**Status: SUBSTANTIALLY COMPLETE**

Defined: position/speed/current supervision, global drive disable, emergency digital output, OP-loss behavior, final error states, restart-required recovery.

Residual: threshold semantics, emergency-output PDO/polarity/latching, WKC/link-loss mapping, timing-fault emergency policy.

## H1.8 — External interfaces
**Status: COMPLETE FOR H1**

Interfaces are captured in the updated interface specification.

## H1.9 — Verification strategy
**Status: COMPLETE**

A dedicated verification strategy defines host tests, static analysis, Linux target timing tests, physical EtherCAT HIL tests, and controlled robot tests.

## H1.10 — Open questions
**Status: COMPLETE / ACTIVE REGISTER**

Remaining questions are explicitly tracked and do not block H2.

## H1 Exit Criteria

- intended behavior explicit enough for architecture: YES
- critical unknowns visible: YES
- real-time constraints quantified or explicitly deferred: YES
- EtherCAT/DS402 behavior identified: YES
- interfaces listed: YES
- intended verification methods defined: YES
- Codex can proceed without inventing major product behavior: YES

## Conclusion

H1 can be considered complete once the updated baseline documents are copied into the repository and the residual open-question register remains active for H2/H3.
