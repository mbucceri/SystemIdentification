# H2.1 target-platform-probe

This is a portable, read-only Linux inventory probe for H2.1. It does not
install packages or change kernel, scheduler, CPU, NIC, IRQ, networking, or
power-management settings. It does not require Codex or this repository on the
target host. Optional commands are recorded as unavailable when absent.

## Run on a target host

Copy this directory (or just `collect-platform-info.sh`) to the target Linux
machine, make the script executable if necessary, and run:

```sh
chmod +x collect-platform-info.sh
./collect-platform-info.sh /tmp/h2.1-platform-inventory-$(date -u +%Y%m%dT%H%M%SZ)
```

The argument is an output directory. Every collected item is saved in a
separate text file containing the command, output, and exit status. The script
continues when optional files or commands are unavailable.

Run as an ordinary user first. A read-only `sudo` execution may expose more
detail for `/proc/interrupts`, `/proc/irq/*`, kernel configuration, PCI data,
and loaded modules, depending on the target's policy. Do not use `sudo` to
change settings; no such operation is required by this probe.

Copy the complete timestamped output directory back into the repository under
`docs/SystemIdECMaster/experiments/H2.1/target-host/`, preserving files and
contents unchanged. Record the target hostname, date, invocation, and whether
sudo was used in the accompanying evidence note.

The probe is an inventory only. Its output cannot establish 1 ms timing
compliance, PREEMPT_RT suitability, or EtherCAT/NIC suitability.
