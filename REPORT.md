# Report

- [System Info](#system-info)
- [Methodology](#methodology)
- [Thread Management](#how-threads-were-created-and-joined)
- [Batching](#whether-batching-was-used)
- [Analysis](#analysis)
- [Table](#table)

## System Info:

### Operating System
```text
PRETTY_NAME="Debian GNU/Linux 13 (trixie)"
NAME="Debian GNU/Linux"
VERSION_ID="13"
VERSION="13 (trixie)"
VERSION_CODENAME=trixie
DEBIAN_VERSION_FULL=13.3
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```

### CPU
```text
Architecture:                            x86_64
CPU op-mode(s):                          32-bit, 64-bit
Address sizes:                           39 bits physical, 48 bits virtual
Byte Order:                              Little Endian
CPU(s):                                  32
On-line CPU(s) list:                     0-31
Vendor ID:                               GenuineIntel
Model name:                              Intel(R) Core(TM) i9-14900HX
CPU family:                              6
Model:                                   183
Thread(s) per core:                      2
Core(s) per socket:                      24
Socket(s):                               1
Stepping:                                1
CPU(s) scaling MHz:                      51%
CPU max MHz:                             5800.0000
CPU min MHz:                             800.0000
BogoMIPS:                                4838.40
Flags:                                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb ssbd ibrs ibpb stibp ibrs_enhanced tpr_shadow flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid rdseed adx smap clflushopt clwb intel_pt sha_ni xsaveopt xsavec xgetbv1 xsaves split_lock_detect user_shstk avx_vnni dtherm ida arat pln pts hwp hwp_notify hwp_act_window hwp_epp hwp_pkg_req hfi vnmi umip pku ospke waitpkg gfni vaes vpclmulqdq rdpid movdiri movdir64b fsrm md_clear serialize arch_lbr ibt flush_l1d arch_capabilities
Virtualization:                          VT-x
L1d cache:                               896 KiB (24 instances)
L1i cache:                               1.3 MiB (24 instances)
L2 cache:                                32 MiB (12 instances)
L3 cache:                                36 MiB (1 instance)
NUMA node(s):                            1
NUMA node0 CPU(s):                       0-31
Vulnerability Gather data sampling:      Not affected
Vulnerability Ghostwrite:                Not affected
Vulnerability Indirect target selection: Not affected
Vulnerability Itlb multihit:             Not affected
Vulnerability L1tf:                      Not affected
Vulnerability Mds:                       Not affected
Vulnerability Meltdown:                  Not affected
Vulnerability Mmio stale data:           Not affected
Vulnerability Old microcode:             Not affected
Vulnerability Reg file data sampling:    Mitigation; Clear Register File
Vulnerability Retbleed:                  Not affected
Vulnerability Spec rstack overflow:      Not affected
Vulnerability Spec store bypass:         Mitigation; Speculative Store Bypass disabled via prctl
Vulnerability Spectre v1:                Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:                Mitigation; Enhanced / Automatic IBRS; IBPB conditional; PBRSB-eIBRS SW sequence; BHI BHI_DIS_S
Vulnerability Srbds:                     Not affected
Vulnerability Tsa:                       Not affected
Vulnerability Tsx async abort:           Not affected
Vulnerability Vmscape:                   Mitigation; IBPB before exit to userspace
```

### RAM
```text
               total        used        free      shared  buff/cache   available
Mem:            62Gi        21Gi        39Gi       1.4Gi       6.9Gi        40Gi
Swap:           19Gi          0B        19Gi
```

### Language versions

#### C:
```text
gcc (Debian 14.2.0-19) 14.2.0
Copyright (C) 2024 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
```
#### Python:
```text
Python 3.13.5
```

## Methodology

We implemented a threading performance testing application in both C and Python. Performance wass measured using the wall-clock time using high-resolution monotonic clocks. We implemented three trials of all three tests and computed an average. We used atomic counters to verify exactly 5000 threads were created and destroyed in each test.

## How threads were created and joined

- **Model 2.a (Flat):** The main thread creates 5000 worker threads that are all parents and then joins the threads.
- **Model 2.b (Two-Level):** The main thread creates 50 "parent" threads that each create 99 "child" threads and then children are joined before parents.
- **Model 2.c (Three-Level):** The main thread creates 20 "parent" threads that each create 3 "child" threads and then 82 "grand child" threads. Grandchildren are joined by childre, children by parents, and parents by the main thread.

## Whether batching was used
No batching was not used or required.

## Analysis
- Discuss why times differ despite identical thread counts
- Discuss scheduling and non-determinism
- Comment on the effect of hierarchy

Even though the overall threads for each expirmient was the same (5,000), the overhead of creating or deleting threads caused measurable slowdown. As the ratio of management thread increase, context switching latency increases.

Threading is inherently non-deterministic. Although threads are created in a specific loop, the OS scheduler decides when they actually execute. This is observable in the "sparse" print outputs, where thread completion messages often appear out of numerical order. Variations between trials (e.g., Trial 1 being faster than Trial 2) are expected as the scheduler balances the 5,000-thread burst against other system processes.

The primary effect of hierarchy is the introduction of synchronization bottlenecks. In a hierarchical model, a parent thread is effectively "blocked" on a join call, waiting for its children to finish. This creates a chain of dependencies. In the 2.c model, the main thread is at the end of a long chain: it waits for initials, which wait for children, which wait for grandchildren. This "nested waiting" increases the total time the system spends in a partially idle or blocked state compared to the flat model where the main thread can start joining any finished thread immediately.

## Table
| Language | Average 2.a (ms) | Average 2.b (ms) | Average 2.c (ms) |
|----------|------------------|------------------|-------------------|
| C        | 187.449          | 209.407          | 233.077           |
| Python    | 412.427          | 470.403          | 471.087           |

