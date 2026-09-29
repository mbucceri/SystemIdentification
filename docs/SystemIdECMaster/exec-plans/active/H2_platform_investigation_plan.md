# H2 — Platform Investigation

**Project:** SystemIdECMaster  
**Status:** Next milestone  
**Predecessor:** H1 — Requirements Elicitation

## Objective

Establish an evidence-based Linux real-time + IgH EtherCAT platform baseline before finalizing application architecture.

H2 is an investigation milestone, not a production-implementation milestone.

## Main questions

1. Which Linux kernel/runtime configuration is appropriate for the 1 ms cycle and ±100 µs timing target?
2. Is PREEMPT_RT required?
3. Which IgH/EtherLab release/branch should be baselined?
4. Which NIC and IgH driver strategy should be used?
5. Can the selected platform maintain the required timing under representative load?
6. What Linux scheduling, affinity, memory-locking, and IRQ settings materially affect the result?

## H2 work packages

### H2.1 — Target topology
Define whether the first measurements run:
- on the development workstation;
- on a dedicated Linux target;
- or both.

Record CPU, NIC, kernel, and distribution details.

### H2.2 — IgH baseline
Select and document:
- source repository;
- release/branch;
- build prerequisites;
- kernel-module build procedure;
- userspace library/API build procedure;
- generic vs native NIC driver options.

### H2.3 — Linux real-time baseline
Measure the stock kernel first.

Then, if needed, evaluate:
- PREEMPT_RT;
- scheduler policy/priority;
- CPU affinity;
- IRQ affinity;
- memory locking;
- power/frequency management.

### H2.4 — Timing experiment
Create a minimal 1 ms periodic loop independent of EtherCAT.

Measure:
- actual cycle period;
- wake-up/start jitter;
- execution time;
- deadline/limit violations.

### H2.5 — Minimal IgH cyclic experiment
Run the smallest cyclic IgH userspace loop against a safe EtherCAT endpoint/HIL configuration.

Measure the same timing quantities plus EtherCAT state/WKC behavior.

### H2.6 — Platform decision record
Produce ADRs for:
- Linux kernel strategy;
- IgH version;
- NIC/driver strategy;
- scheduler/tuning baseline.

## H2 Exit Criteria

H2 is complete when:
- the candidate Linux/IgH platform is reproducibly buildable;
- the 1 ms timing requirement has been measured;
- the need for PREEMPT_RT is supported by evidence;
- the NIC/driver strategy is selected or narrowed;
- the principal platform constraints are documented;
- enough evidence exists to begin H3 architecture with realistic runtime assumptions.
