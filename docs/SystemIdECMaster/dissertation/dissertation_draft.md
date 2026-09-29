# Agentic Development of a Real-Time EtherCAT Master Application

## Dissertation / Project Journal

**Status:** Living document  
**Project phase:** H0 — Harness bootstrap  
**Last updated:** 2026-09-11

---

## 1. Introduction

This project investigates the practical use of an AI-assisted agentic software-development harness to design, implement, verify, and progressively refine a complete C++ real-time EtherCAT master application for robotic systems.

The objective is deliberately broader than using an AI coding assistant to implement isolated functions. The project studies how a coding agent can operate within a structured engineering process encompassing requirements, architecture, implementation, verification, integration, real-time performance characterization, and documentation.

A second objective is methodological: the project records the evolution of the development harness itself, including which forms of repository context, deterministic verification, specialized agent roles, code-intelligence tools, and runtime-observability mechanisms are effective for long-running software-engineering tasks.

This document is maintained as a living technical record. It captures the stable project rationale, important design decisions, milestone progress, experiments, and lessons learned. Detailed authoritative decisions are maintained separately as Architecture Decision Records (ADRs), while this document preserves the higher-level development narrative.

---

## 2. Project Direction

### 2.1 Development host

The primary development environment is:

- Ubuntu 22.04.5 LTS
- C++17
- CMake 3.30
- Ninja
- GCC, subject to compatibility requirements introduced by the EtherCAT stack and target platform
- Conan 2 is planned for application-level dependency management
- JFrog Artifactory may later be introduced if a private package repository becomes useful

### 2.2 Runtime platform

The target runtime is Linux with real-time capabilities appropriate for a firm/soft real-time cyclic EtherCAT application.

The final kernel configuration and real-time tuning strategy will be selected through measurement rather than assumed in advance. PREEMPT_RT and related Linux real-time facilities are part of the expected investigation.

### 2.3 EtherCAT stack

The application will use the open-source IgH / EtherLab EtherCAT Master as the reference EtherCAT implementation.

The project initially considered proprietary runtime and EtherCAT components. During preliminary design, the decision was made to rely on open-source alternatives wherever practical. This removes licensing constraints and simplifies the development, build, deployment, and automated testing infrastructure.

### 2.4 Physical system

The application will operate as an EtherCAT master for a robot containing:

- CiA 402 / DS402 servo drives
- sensors
- additional EtherCAT slave devices as required by the robot architecture

A pre-existing QNX-based Hardware-in-the-Loop simulator is available. It simulates both robot dynamics and the EtherCAT protocol layer and can be connected to the Linux master through a real physical EtherCAT network.

The HIL environment is therefore treated as an independent integration and verification asset rather than part of the production runtime.

### 2.5 Software starting point

The new EtherCAT master application is greenfield.

An existing EtherCAT master application will be available as an architectural reference and source of implementation experience. Existing application libraries may also be available. Reuse will be decided case by case based on:

- architectural suitability
- dependency cost
- complexity
- testability
- real-time behavior
- maintenance implications
- amount of functionality actually required

Existing code will initially be treated as reference material rather than automatically adopted.

### 2.6 Development constraints

MISRA C++:2023 is the intended coding standard because the application has real-time and safety implications.

The project will not claim formal MISRA compliance solely from compiler diagnostics or generic static-analysis tools. The eventual compliance and deviation process will be explicitly defined.

---


### 2.7 Build-output convention

`SystemIdECMaster` uses C++17.

Generated build artifacts are kept outside the source tree at the `SystemIdentification` monorepo root. The canonical build variants are:

- `build/linux-debug`
- `build/linux-release`
- `build/linux_rt-debug`
- `build/linux_rt-release`

This keeps source directories free of generated files and establishes a stable convention for standard Linux and future real-time Linux builds.


## 3. Development Methodology

### 3.1 Core agentic-development principle

The project does not assign the agent the global task of “implementing the application.”

Instead, requirements and architectural decisions are decomposed into bounded execution plans with explicit acceptance criteria.

The development loop is:

1. identify an approved, dependency-ready task;
2. allow the implementation agent to inspect the relevant requirements and architecture;
3. implement only the declared scope;
4. execute deterministic verification;
5. perform an independent semantic review;
6. accept the task only if both verification layers pass;
7. create a Git checkpoint;
8. continue with the next task.

AI judgment supplements deterministic verification; it does not replace it.

### 3.2 Repository as persistent engineering memory

Long-lived context will be stored in the repository rather than repeatedly supplied through large prompts.

The expected knowledge structure includes:

- `AGENTS.md` — compact engineering instructions and navigation
- `requirements/` — system and software requirements
- `docs/architecture/` — approved software and real-time architecture
- `docs/decisions/` — ADRs
- `docs/exec-plans/` — active and completed bounded work packages
- `tests/` — executable verification
- `docs/dissertation/` — this research/project journal
- experiment and milestone records

`AGENTS.md` should remain relatively short and point the agent toward authoritative project documents rather than duplicate them.

### 3.3 Verification strategy

Three major verification levels are planned.

#### Level 1 — Host software verification

Executed frequently on the Ubuntu development environment:

- compilation
- unit tests
- component tests
- deterministic simulation/fakes
- static analysis
- sanitizers
- architecture checks where practical

#### Level 2 — Linux real-time / EtherCAT integration

Executed using the actual Linux EtherCAT stack and networking environment:

- IgH master integration
- NIC and driver configuration
- scheduler configuration
- timer behavior
- CPU/IRQ affinity where required
- cyclic timing measurements
- EtherCAT communication behavior

#### Level 3 — Physical EtherCAT HIL and robot verification

The Linux master communicates through a physical EtherCAT network first with the existing QNX HIL simulator and eventually with the real robot.

The HIL environment provides a valuable intermediate verification step because it exercises actual EtherCAT communication and realistic robot behavior without immediately introducing physical robot motion risk.

---

## 4. Harness Architecture

The initial harness is intentionally kept small.

### 4.1 Core roles

The first operational version will contain:

- one Codex implementation agent
- one deterministic verifier
- one independent read-only reviewer

Additional specialized agents will be introduced only when they demonstrate measurable value.

### 4.2 Optional extensions

Three agent-support technologies have been identified for later evaluation.

#### CodeGraph

Planned early adoption for structural code exploration, including symbol relationships, call graphs, dependencies, and change-impact analysis. It is expected to be particularly useful when analysing the existing EtherCAT application and later when evaluating changes to the new codebase.

#### Graphify

Candidate for a later project phase when requirements, architecture, source code, experiments, and documentation provide enough heterogeneous material to justify a broader semantic knowledge graph.

#### Caveman

Candidate optimization layer for compact agent-to-agent communication and context reduction. It is not considered part of the correctness-critical harness and must remain removable without altering the engineering process.

### 4.3 Runtime observability

Real-time observability is expected to become more important than sophisticated multi-agent coordination.

The harness should eventually expose structured evidence including:

- cycle period
- cycle execution time
- wake-up latency and jitter
- deadline misses
- CPU migrations
- page faults after initialization
- scheduler behavior
- EtherCAT working-counter errors
- network faults and recovery behavior
- NIC/IRQ configuration

Agents should reason from measured evidence rather than subjective assessment.

---

## 5. Milestones

### H0 — Agentic harness bootstrap

Establish the local repository, Codex environment, CMake/Ninja build, basic deterministic verification, safe agent permissions, and Git workflow.

### H1 — Requirements elicitation

Convert the current informal product knowledge into structured system/software/interface/verification requirements with stable identifiers.

### H2 — Platform investigation

Establish the Linux real-time and IgH baseline, evaluate relevant kernel/NIC options, and obtain initial timing measurements.

CodeGraph is expected to be introduced during this phase when the existing application is investigated.

### H3 — Architecture

Define application decomposition, cyclic execution model, EtherCAT abstraction, DS402 architecture, lifecycle, diagnostics, error-handling strategy, and testability architecture.

Graphify may be evaluated during or after this phase.

### H4 — Minimal EtherCAT vertical slice

Implement the smallest end-to-end application path using Linux and IgH with a controlled EtherCAT endpoint.

### H5 — HIL integration

Connect the Linux master to the QNX HIL simulator using a physical EtherCAT network.

### H6 — DS402 functional layer

Implement and verify required DS402 behavior and sensor handling using simulation/HIL.

### H7 — Cyclic real-time implementation

Implement and characterize the production cyclic execution architecture, timer/scheduler policy, and latency behavior.

### H8 — Fault and recovery architecture

Verify startup, shutdown, bus faults, slave faults, communication loss, timing violations, and recovery behavior.

### H9 — Full HIL robot integration

Exercise the complete robot application against the dynamic QNX HIL simulator.

### H10 — Physical robot integration

Progress from the HIL environment to controlled testing on the physical robot.

### H11 — Final evidence and traceability

Consolidate requirements traceability, timing evidence, static-analysis results, test evidence, design records, and lessons learned.

---

## 6. Current Project State

The preliminary direction and milestone structure are considered stable enough to begin implementation of H0.

No production EtherCAT architecture has yet been selected beyond the choice of Linux and IgH as the reference platform.

The following topics remain deliberately open for later evidence-based decisions:

- exact Linux distribution/runtime image
- PREEMPT_RT/kernel configuration
- target hardware
- network interface controller
- native versus generic IgH network driver
- cyclic period and timing limits
- scheduler policy and CPU isolation strategy
- Conan dependency set
- JFrog usage
- logging architecture
- static-analysis/MISRA tooling
- final testing framework
- existing-library reuse

These are not missing decisions to be guessed by the agent; they are explicit future engineering decisions.

---

## 7. Immediate Next Step

Proceed with H0.

H0 should prove that:

1. Codex can safely operate inside the project repository.
2. the project builds reproducibly with CMake and Ninja;
3. a deterministic verification command exists;
4. Codex can make a controlled change;
5. the agent can run the verifier and correctly react to failure;
6. Git provides a clean checkpoint before and after an agent task.

EtherCAT, Conan, PREEMPT_RT, HIL integration, and multi-agent extensions are intentionally excluded from H0 unless they become necessary to prove the harness itself.


---

## 8. Monorepo Development Environment Decision

`SystemIdECMaster` is developed as a subproject of the existing `SystemIdentification` Git monorepo rather than as an independent repository.

A single VS Code Dev Container located at the monorepo root is used as the canonical development environment. This reflects the intended software-stack organization and promotes one compatible toolchain across present and future projects.

The initial container provides the common C++ and Python development baseline. MATLAB remains outside the container because it is not currently required by the agentic workflow.

Agents are intentionally allowed to inspect the complete monorepo because future tasks may require information or reusable components from neighboring projects, robot descriptions, utilities, or datasets. During the initial `SystemIdECMaster` work, changes are temporarily scoped to that project and its documentation unless an execution plan explicitly requires modifications elsewhere.

The Dev Container remains a development and host-verification environment only. Real-time Linux behavior, IgH integration, NIC/IRQ behavior, EtherCAT timing, HIL testing, and physical robot verification will be performed on the relevant runtime environment rather than inferred from container execution.


### 8.1 Codex sandbox inside the Dev Container

The Codex development agent uses a Bubblewrap-based `workspace-write` sandbox inside the repository Dev Container.

During H0, Docker's default seccomp and AppArmor confinement prevented Bubblewrap from creating the nested user namespace and mount-propagation environment required by Codex. The Dev Container was therefore configured with `seccomp=unconfined` and `apparmor=unconfined`.

This is a deliberate compatibility setting for the outer development container, not a removal of Codex sandboxing. The container remains non-privileged and does not expose the Docker socket, host devices, or the host home directory. With this configuration, Codex's inner workspace sandbox operates normally and routine repository reads, edits, builds, and tests no longer require escalation solely because of sandbox initialization failures.


## 9. Milestone H0 Completion

H0 was completed successfully.

A repository-root VS Code Dev Container was established as the canonical development environment. Codex was authenticated and configured with a functioning Bubblewrap-based `workspace-write` sandbox. A deterministic CMake/Ninja host build and test gate was created for `SystemIdECMaster`, and a controlled dummy implementation task demonstrated that the agent can inspect the repository, make scoped changes, execute verification, and complete a simple task successfully.

The project therefore proceeds to H1: Requirements Elicitation.


## 10. Milestone H1 Completion

H1 established the initial functional requirements baseline for `SystemIdECMaster`.

The application is defined as a command-line IgH/EtherCAT master for Luna DB 3.5 system-identification experiments. It supports externally generated position and velocity trajectories, arbitrary multi-joint excitation, a 1 ms cyclic period, selective MCAP recording, runtime position/speed/current supervision, and a global emergency response that disables all drives while keeping EtherCAT communication alive for diagnostics until application restart.

The first timing target is a configurable ±100 µs tolerance around the nominal 1 ms cycle. EtherCAT Distributed Clocks are not required for the initial implementation. Engineering and safety configuration are XML-based, ENI is parsed at runtime, and each recorded sample contains a cycle index and monotonic host timestamp.

The remaining timing semantics and low-level EtherCAT/platform choices are intentionally deferred to H2, where they will be resolved through measurement rather than assumption.



## 11. H1 Closure and Transition to H2

H1 — Requirements Elicitation is considered complete.

The project now has a sufficiently explicit requirements baseline covering the system purpose, EtherCAT role, DS402 operation modes, experiment lifecycle, configuration inputs, safety behavior, timing targets, MCAP recording, external interfaces, non-functional constraints, and verification strategy.

Residual questions remain active by design, but they no longer prevent platform investigation. These include detailed WKC/link-loss behavior, exact emergency-output mapping, current-feedback PDO selection, trajectory serialization, XML schemas, detailed state-machine timeout policy, and other low-level design choices.

The next milestone is H2 — Platform Investigation.

### 11.1 H2 objective

H2 establishes an evidence-based Linux real-time and IgH/EtherLab platform baseline before application architecture is finalized.

The principal questions are:

1. Which Linux kernel/runtime configuration is appropriate for the 1 ms cycle and configurable ±100 µs timing target?
2. Is PREEMPT_RT required?
3. Which IgH/EtherLab release and build strategy should be baselined?
4. Which NIC and EtherCAT driver strategy should be adopted?
5. Which scheduler, CPU-affinity, IRQ-affinity, memory-locking, and power-management settings materially affect timing?
6. What timing performance is demonstrated on the actual target platform?

### 11.2 Agentic workflow introduced in H2

H2 is also the first milestone in which the project deliberately separates two AI roles.

**ChatGPT discussion/reasoning role**

Used for:
- requirements interpretation;
- experiment design;
- trade-off analysis;
- deciding what evidence is required;
- reviewing results and identifying the next bounded task;
- maintaining the dissertation-level narrative.

**Codex repository agent role**

Used for:
- inspecting the local repository and target-related files;
- creating bounded investigation scripts and utilities;
- modifying project documentation in the repository;
- executing builds and deterministic checks;
- collecting reproducible command output;
- implementing approved H2 experiments.

The transition between the two is task-based rather than milestone-based. A task should move to Codex when successful completion requires direct repository inspection, file modification, command execution, build/test execution, or reproducible local evidence. Conceptual decisions and interpretation can remain in ChatGPT until they have been converted into a bounded execution task.

### 11.3 H2 harness evolution

No separate autonomous multi-agent framework is required at the start of H2.

The existing harness already contains the minimum useful agentic loop:

1. human + ChatGPT define a bounded investigation;
2. Codex executes it inside the controlled workspace;
3. deterministic commands produce evidence;
4. ChatGPT and/or an independent Codex review pass interpret the evidence;
5. accepted results are documented and committed.

H2 will use this loop deliberately and progressively. Additional agent roles, graph tools, or automation should be introduced only when a concrete limitation of the baseline workflow is observed and can be measured.
