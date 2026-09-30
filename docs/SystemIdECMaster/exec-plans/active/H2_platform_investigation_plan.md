# H2 — Platform Investigation

**Project:** SystemIdECMaster  
**Status:** Active  
**Predecessor:** H1 — Requirements Elicitation (completed)

## Objective

Establish an evidence-based Linux real-time + IgH EtherCAT platform baseline before finalizing application architecture.

H2 is an investigation milestone, not a production-implementation milestone.

A key constraint is that Codex is available on the development machine but may not be available on the target Linux machine. Therefore H2 shall distinguish clearly between:

- the **development host**, where Codex can inspect the repository, generate scripts, analyze results, and update documentation;
- the **target host**, where deterministic, portable, read-only inspection and timing tools are executed manually without requiring Codex.

The agent shall not assume that the target host contains the repository, Codex, development tooling, or package-management privileges.

## Main questions

1. Which Linux kernel/runtime configuration is appropriate for the 1 ms cycle and ±100 µs timing target?
2. Is PREEMPT_RT required?
3. Which IgH/EtherLab release/branch should be baselined?
4. Which NIC and IgH driver strategy should be used?
5. Can the selected platform maintain the required timing under representative load?
6. What Linux scheduling, affinity, memory-locking, and IRQ settings materially affect the result?
7. Which relevant facts can be established directly on the development host, and which require target-host evidence?

## H2 evidence model

H2 shall distinguish three evidence classes:

1. **Development-host facts**  
   Facts observed directly on the Codex-enabled development machine.

2. **Target-host facts**  
   Facts collected by portable scripts executed manually on the actual target Linux host.

3. **Derived conclusions**  
   Conclusions drawn only after reviewing the collected evidence.

No conclusion about real-time suitability, PREEMPT_RT need, NIC suitability, or target timing shall be inferred from the Dev Container alone.

## H2 work packages

### H2.1 — Platform inventory and portable target probe

H2.1 is split into four substeps.

#### H2.1a — Development-host inventory

Collect and document, where observable:

- Linux distribution and version;
- kernel version and command line;
- PREEMPT / PREEMPT_RT related kernel configuration;
- CPU model and topology;
- CPU governor/frequency information;
- virtualization/hypervisor status;
- network interfaces;
- Ethernet NIC vendor/model;
- NIC kernel driver;
- PCI address;
- IRQ information;
- CPU affinity information;
- realtime scheduling limits;
- memory-locking limits;
- availability/version of:
  - cyclictest;
  - perf;
  - trace-cmd;
  - ethtool;
  - lspci;
  - IgH/EtherLab components.

Clearly distinguish information coming from the actual development host from information visible only inside the Dev Container.

#### H2.1b — Portable target-platform probe

Create a portable, read-only inspection package under:

```text
src/SystemIdECMaster/tools/h2/target-platform-probe/
├── collect-platform-info.sh
└── README.md
```

The probe shall:

- run without Codex;
- require only standard Linux shell tooling where practical;
- make no persistent system configuration changes;
- not install packages;
- not modify kernel, scheduler, NIC, IRQ, CPU, or power-management settings;
- not assume the project repository is installed on the target;
- continue when optional commands are unavailable;
- clearly record unavailable information;
- record the command, exit status, and output for each important observation;
- write results into a timestamped output directory;
- avoid collecting unrelated personal or sensitive information.

The probe shall collect, where observable:

- distribution/version;
- kernel version and command line;
- PREEMPT / PREEMPT_RT configuration;
- CPU model/topology;
- CPU frequency/governor state;
- virtualization status;
- network interfaces;
- NIC vendor/model;
- kernel NIC driver;
- PCI address;
- IRQ assignment and affinity;
- realtime scheduling limits;
- memory-locking limits;
- availability/versions of cyclictest, perf, trace-cmd, ethtool, lspci, and IgH/EtherLab components.

The README shall describe:

1. how to copy the probe to the target host;
2. how to execute it;
3. which observations may benefit from `sudo`;
4. how to copy the resulting evidence back into the development repository.

#### H2.1c — Target-host evidence collection

The probe is executed manually on the target Linux host.

Codex is not required on the target.

The resulting evidence directory is copied back to the development repository, under a structure such as:

```text
docs/SystemIdECMaster/experiments/H2.1/
├── development-host/
└── target-host/
```

The raw evidence should be preserved unchanged where practical.

#### H2.1d — Evidence analysis

Codex and ChatGPT analyze the development-host and target-host evidence.

The analysis shall identify:

- confirmed platform facts;
- differences between development and target machines;
- missing information;
- platform risks;
- follow-up measurements required;
- whether the target is suitable for the next H2 experiments.

No architecture decision shall be made solely from incomplete inventory evidence.

### H2.2 — IgH baseline

Select and document:

- source repository;
- release/branch;
- build prerequisites;
- kernel-module build procedure;
- userspace library/API build procedure;
- generic vs native NIC driver options;
- any target-host constraints discovered in H2.1.

### H2.3 — Linux real-time baseline

Measure the stock target kernel first.

Then, if evidence requires it, evaluate:

- PREEMPT_RT;
- scheduler policy/priority;
- CPU affinity;
- IRQ affinity;
- memory locking;
- power/frequency management.

Changes to the target host shall be introduced only through explicit, bounded experiments with rollback instructions.

### H2.4 — Timing experiment

Create a minimal 1 ms periodic loop independent of EtherCAT.

The test package shall be deployable to the target host without requiring Codex.

Measure:

- actual cycle period;
- wake-up/start jitter;
- execution time;
- timing-limit violations;
- relevant scheduler/CPU information.

### H2.5 — Minimal IgH cyclic experiment

Run the smallest cyclic IgH userspace loop against a safe EtherCAT endpoint/HIL configuration.

The experiment shall be packaged so it can be built/deployed reproducibly to the target host.

Measure:

- cycle timing;
- EtherCAT state;
- Working Counter behavior;
- NIC/driver behavior;
- timing violations;
- relevant runtime diagnostics.

### H2.6 — Platform decision record

Produce ADRs for:

- Linux kernel strategy;
- IgH version;
- NIC/driver strategy;
- scheduler/tuning baseline.

Decisions shall cite measured evidence from H2 experiments.

## Agentic workflow for H2

H2 deliberately separates reasoning from target execution.

### ChatGPT / reasoning role

Used for:

- experiment design;
- evidence requirements;
- interpretation of results;
- trade-off analysis;
- review of Codex outputs;
- dissertation-level documentation.

### Codex / repository-agent role

Used for:

- inspecting repository content;
- generating portable scripts/tools;
- modifying project files;
- running development-host commands;
- building deterministic experiments;
- analyzing imported target evidence;
- updating repository documentation.

### Target-host execution role

Performed manually or through deterministic scripts.

The target host is not required to run Codex.

This separation is intentional and forms part of the agentic-development learning workflow.

## H2 Exit Criteria

H2 is complete when:

- development-host and target-host platform facts are documented separately;
- the portable target-inspection workflow is reproducible;
- the candidate Linux/IgH platform is reproducibly buildable;
- the 1 ms timing requirement has been measured on the target;
- the need for PREEMPT_RT is supported by evidence;
- the NIC/driver strategy is selected or narrowed;
- the principal platform constraints are documented;
- enough evidence exists to begin H3 architecture with realistic runtime assumptions.
