# SystemIdECMaster Agent Instructions

## Purpose

This project implements a C++ EtherCAT master application targeting
a Linux real-time environment.

Development and host-side verification run inside the repository
Dev Container.

## Authoritative documentation

Consult the relevant documents under:

../../docs/SystemIdECMaster/

including:

- requirements/
- architecture/
- decisions/
- exec-plans/
- experiments/

Do not invent missing requirements.

If required behavior is ambiguous, identify the ambiguity rather than
silently selecting an interpretation.

## Scope discipline

Keep implementation changes focused on SystemIdECMaster unless an
approved execution plan explicitly requires changes elsewhere.

The rest of the monorepo may be inspected and reused where justified.

## Build and verification

For host-side work, run:

    ./tools/verify-host.sh

from this project directory.

A task is not complete if required verification fails.

Do not remove, weaken or bypass a test merely to make verification pass.

## C++

Follow the language version and warning policy configured by CMake.

MISRA C++:2023 is the intended coding standard, but do not claim formal
compliance unless the configured compliance process verifies it.

## Real-time and hardware safety

The final application will communicate with EtherCAT devices and may
control physical actuators.

Do not infer safe physical-device behavior.

Do not perform hardware or motion tests unless an execution plan
explicitly authorizes them.

## Environment boundaries

The Dev Container is a development and host-verification environment.

Do not treat timing results obtained inside the Dev Container as
evidence of target real-time performance.

Do not request privileged container access or host-device access unless
an approved execution plan explicitly requires it.