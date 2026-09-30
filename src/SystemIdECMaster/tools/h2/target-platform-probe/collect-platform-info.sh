#!/bin/sh
# H2.1 read-only Linux platform inventory.  Intended to run without the repo.
set +e

out_root=${1:-h2.1-platform-inventory-$(date -u +%Y%m%dT%H%M%SZ)}
mkdir -p "$out_root" || exit 1

run() {
    name=$1
    shift
    file="$out_root/$name.txt"
    {
        printf '$'
        for arg in "$@"; do printf ' %s' "$arg"; done
        printf '\n'
        "$@"
        status=$?
        printf '\n[exit status: %s]\n' "$status"
    } >"$file" 2>&1
}

run shell-environment env
run distribution sh -c 'if [ -r /etc/os-release ]; then cat /etc/os-release; else echo unavailable; fi'
run kernel uname -a
run kernel-command-line sh -c 'cat /proc/cmdline 2>/dev/null || echo unavailable'
run kernel-config sh -c '
    for f in /proc/config.gz /boot/config-$(uname -r); do
        if [ -r "$f" ]; then
            case "$f" in *.gz) zcat "$f";; *) cat "$f";; esac
            exit $?
        fi
    done
    echo unavailable: kernel configuration is not readable
    exit 1
'
run cpu-model-topology sh -c '
    grep -E "^(processor|model name|cpu MHz|physical id|core id|CPU family|CPU\(s\)|Thread|Core|Socket|NUMA)" /proc/cpuinfo 2>/dev/null || true
    command -v lscpu >/dev/null 2>&1 && lscpu || true
'
run cpu-frequency sh -c '
    for d in /sys/devices/system/cpu/cpu[0-9]*; do
        [ -d "$d/cpufreq" ] || continue
        printf "%s: governor=" "$d"
        cat "$d/cpufreq/scaling_governor" 2>/dev/null || printf unavailable
        printf " driver="
        cat "$d/cpufreq/scaling_driver" 2>/dev/null || printf unavailable
        printf " min="
        cat "$d/cpufreq/scaling_min_freq" 2>/dev/null || printf unavailable
        printf " max="
        cat "$d/cpufreq/scaling_max_freq" 2>/dev/null || printf unavailable
        printf "\n"
    done
    [ -d /sys/devices/system/cpu/cpufreq ] && find /sys/devices/system/cpu/cpufreq -maxdepth 2 -type f -name "*governor*" -o -name "*driver*" 2>/dev/null | sort
'
run virtualization sh -c '
    command -v systemd-detect-virt >/dev/null 2>&1 && systemd-detect-virt --all || true
    command -v virt-what >/dev/null 2>&1 && virt-what || true
    [ -r /sys/class/dmi/id/product_name ] && printf "product_name: " && cat /sys/class/dmi/id/product_name
    [ -r /sys/class/dmi/id/sys_vendor ] && printf "sys_vendor: " && cat /sys/class/dmi/id/sys_vendor
    grep -m1 -E "^flags.*(hypervisor|vmx|svm)" /proc/cpuinfo 2>/dev/null || true
'
run network-interfaces sh -c 'ip -details link show 2>/dev/null || cat /proc/net/dev'
run network-addresses sh -c 'ip -brief address show 2>/dev/null || true'
run pci-ethernet lspci -nnk
run nic-details sh -c '
    for n in /sys/class/net/*; do
        name=${n##*/}
        [ "$name" = lo ] && continue
        printf "== %s ==\n" "$name"
        printf "address: "; cat "$n/address" 2>/dev/null || true
        printf "operstate: "; cat "$n/operstate" 2>/dev/null || true
        printf "ifindex: "; cat "$n/ifindex" 2>/dev/null || true
        printf "pci/device: "; readlink -f "$n/device" 2>/dev/null || printf unavailable
        printf "driver: "; readlink -f "$n/device/driver" 2>/dev/null || printf unavailable
        if command -v ethtool >/dev/null 2>&1; then ethtool -i "$name" 2>&1; fi
    done
'
run interrupts-and-affinity sh -c '
    for n in /sys/class/net/*; do
        name=${n##*/}; [ "$name" = lo ] && continue
        printf "== %s ==\n" "$name"
        grep -i "$name" /proc/interrupts 2>/dev/null || true
        find "$n" -maxdepth 2 -type f \( -name "*rps_cpus" -o -name "*xps_cpus" \) -print -exec sh -c "printf \"%s: \" \"\$1\"; cat \"\$1\"" sh {} \; 2>/dev/null
        for irq in $(grep -i "$name" /proc/interrupts 2>/dev/null | sed -n "s/^ *\([0-9][0-9]*\):.*/\1/p"); do
            printf "irq %s affinity: " "$irq"
            cat "/proc/irq/$irq/smp_affinity_list" 2>/dev/null || cat "/proc/irq/$irq/smp_affinity" 2>/dev/null || printf unavailable
            printf "\n"
        done
    done
'
run process-affinity sh -c 'printf "probe pid %s affinity: " "$$"; taskset -pc $$ 2>&1 || true; printf "shell status: "; ps -o pid,psr,cls,rtprio,pri,ni,stat,comm -p $$ 2>&1 || true'
run limits sh -c 'ulimit -a; printf "\n/proc/self/limits:\n"; cat /proc/self/limits'
run realtime-tools sh -c '
    for tool in cyclictest perf trace-cmd ethtool lspci; do
        printf "== %s ==\n" "$tool"
        if command -v "$tool" >/dev/null 2>&1; then
            command -v "$tool"
            "$tool" --version 2>&1 || "$tool" -V 2>&1 || true
        else
            echo unavailable
        fi
    done
    printf "== IgH/EtherLab ==\n"
    for tool in ethercat; do
        if command -v "$tool" >/dev/null 2>&1; then command -v "$tool"; "$tool" version 2>&1 || "$tool" --version 2>&1 || true; else echo "$tool: unavailable"; fi
    done
    for p in /lib/modules/$(uname -r)/updates /lib/modules/$(uname -r)/kernel /usr/include/ecrt.h /usr/local/include/ecrt.h /usr/lib/libethercat.so /usr/local/lib/libethercat.so; do
        [ -e "$p" ] && printf "present: %s\n" "$p"
    done
'
run loaded-modules lsmod
run probe-metadata sh -c 'date -u +%Y-%m-%dT%H:%M:%SZ; id; printf "hostname: "; hostname'

printf 'Wrote H2.1 platform probe results to %s\n' "$out_root"
exit 0
