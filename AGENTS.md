# SystemIdentification Repository Agent Instructions

## Repository purpose

This is a multi-project robotics and system-identification monorepo.

The repository contains C++, Python, MATLAB scripts, robot descriptions,
experimental data and supporting utilities.

The canonical development environment is the repository Dev Container.

## Repository visibility

Agents may inspect any part of the repository when it is useful for
understanding a task.

Do not assume that neighboring projects are unrelated merely because
they use another language.

## Change scope

Modify only files required by the active task or execution plan.

For the current project phase, implementation work is focused on:

- src/SystemIdECMaster/
- docs/SystemIdECMaster/

Changes elsewhere require an explicit task reason.

## Engineering behavior

Do not invent missing requirements.

Prefer existing repository knowledge and utilities when appropriate,
but do not create dependencies on neighboring projects without
evaluating their architectural cost.

Do not perform broad refactoring as a side effect of a focused task.

## Verification

Use the verification procedure defined by the project being modified.

A task is not complete if required deterministic verification fails.