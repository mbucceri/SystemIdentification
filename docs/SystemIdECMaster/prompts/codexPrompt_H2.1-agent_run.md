Read:

- AGENTS.md
- src/SystemIdECMaster/AGENTS.md
- docs/SystemIdECMaster/requirements/
- docs/SystemIdECMaster/exec-plans/active/H2_platform_investigation_plan.md

We are starting H2 — Platform Investigation.

This task is H2.1: establish a reproducible inventory of the current Linux
development machine as a candidate EtherCAT/real-time test platform.

Do not install packages.
Do not modify host configuration.
Do not change kernel, scheduler, CPU, NIC, IRQ, or networking settings.
Do not implement EtherCAT functionality.

Create:

docs/SystemIdECMaster/experiments/H2.1-platform-inventory.md

and, if useful,

src/SystemIdECMaster/tools/platform-inventory.sh

Collect and document, where available:

- Linux distribution and version
- kernel version and kernel command line
- PREEMPT / PREEMPT_RT related kernel configuration
- CPU model, topology, logical/physical core count
- current CPU frequency governor information
- virtualization/hypervisor status
- available network interfaces
- Ethernet NIC vendor/model
- kernel driver used by each relevant Ethernet NIC
- PCI address for relevant NICs
- IRQ information associated with relevant NICs
- current CPU affinity information where observable
- current realtime scheduling limits
- memory-locking limits
- availability/version of cyclictest
- availability/version of perf
- availability/version of trace-cmd
- availability/version of ethtool
- availability/version of lspci
- availability of IgH/EtherLab components

Clearly distinguish:

1. facts observed from the actual Linux host;
2. information visible only inside the Dev Container;
3. information that cannot be established from the container.

Do not claim that timing or PREEMPT_RT suitability has been verified.

The output must be reproducible: record the commands used to collect every
important fact.

If container isolation prevents obtaining a fact about the host, record that
limitation instead of guessing.

At the end, provide:

- files created/modified;
- commands executed;
- important observations;
- unresolved platform questions.

Do not make architecture decisions in this task.
