# SiliconForest m1n1 validation — 2026-10-18

The exact source/tree identities, stage 2 hashes and commands are recorded in
SILICONFOREST-VALIDATION.json. Later policy/provenance/documentation commits do not
change the compiled src/rust/Makefile trees.

| Check | Result |
| --- | --- |
| Default stage 2, LLVM 22.1.8 / Rust 1.99.0 | Built and linked both ELF forms, raw binary and Mach-O |
| Main Python suite, resource/firmware readers and new failure-injection controls | 54 passed, 7 platform/environment skips, 10 subtests passed |
| Boot-logo, relocation gate, payload profile, T6030 display facts, Air PMP/display/full-start/GPU diagnostics, stage 1 config and 25G83 board helpers | 10 standalone runners passed, including ASan/UBSan host controls |
| Entire standalone G15 scenario inventory | 65 pass, 10 fail; identical failures at original fec93c15 baseline |
| Neo profile stage 2, LLVM 22.1.8 / Rust 1.89.0 | Built and linked |
| Neo Python suite | 80 passed, 7 platform/environment skips |
| Native Mesa/kernel wire ABI | 18 selected ioctl/layout/feature facts match |
| J514S firmware UUID and G17 native kernel entry | Static contract checked |
| Public source provenance | 175 exact tags and 3 profile source parents checked |
| Physical Mac boot / GPU / display / recovery / suspend / stage 1 replacement | Not performed |

The source manifest pins the kernel and Mesa commits used for contract checking.
A binary hash identifies this local development build; it is not a signed or
hardware-qualified release artifact. No binary was installed or flashed.

Reproduce the maintained checks using the commands in README.md, plus:

```sh
python3 tools/siliconforest/check-sources.py --check-git --kernel PATH_TO_KERNEL --mesa PATH_TO_MESA
sh tests/run-bootlogo.sh
sh tests/run-m3-move-gate.sh
sh tests/run-payload-profile.sh
sh tests/run-t6030-display.sh
sh tests/run-t8122-air-pmp.sh
sh tests/run-t8122-display-handoff.sh
sh tests/run-t8122-full-start.sh
sh tests/run-t8122-gpu-diagnostics.sh
python3 tests/run-stage1-config.py
python3 tests/run-t8122-25g83-board.py
```

The focused GitHub workflow runs provenance, the Python suite and four host
runners. It does not claim a complete cross-build or a green complete G15 suite.
The standalone runners require a host C compiler, LLVM tools, dtc and a QEMU
AArch64 userspace interpreter. The first CI run passed Python but exposed the
missing QEMU package; that runner dependency is now explicit.

## Inherited G15 failures

The existing run-kboot-gpu-g15.sh stops at its first failure. For review, every
scenario was run individually, and all 75 were also run against the original
source pin. Both gave exactly 65 passes and these 10 failures:

- `t8122-j613-standin-10`
- `t8122-j613-standin-8`
- `t8122-j613-standin-idleoff`
- `t8122-j613-standin-sram-below`
- `t8122-j613-standin-no-room`
- `t8122-j613-standin-wrong-id`
- `t8122-j613-standin-fuse-off`
- `t8122-j613-standin-fuse-on`
- `t8122-j613-standin-fuse-on-fault`
- `t8122-j613-standin-fuse-not-j613`

These old fixtures expect stand-in startup without the current full-start board
identity requirements, or an error reached only after that earlier admission.
Current named J613/J615 full-start, per-machine calibration and refusal controls
pass. Production admission checks have not been relaxed to satisfy old fixtures.
This is a known test-debt item and prevents claiming the entire host suite passes.

The ADT-driven T6031 full-machine suite was preserved, with fixtures updated to
opt in explicitly; no personal ADT capture was collected or used to run it here.
The Max opt-in is covered separately by production-function fault injection.
M4/M5 profile snapshots were not built or tested in this run. Host validation
cannot establish that an inherited firmware session can safely be taken over.


## J613 firmware-ready follow-up validation

The updated stage 2 cross-build passes with LLVM 22.1.8 and Rust 1.99.0.
Python has 54 passes, 7 skips and 10 passing subtests. The new production-code
regression covers complete reservations, first/second reservation failures,
firmware-copy and marker failures, missing/short/malformed ADT values, invalid
physical/remap spans, stale markers and wrong-chip/tree controls. It confirms
that controller and supplier status stays disabled. The older enable=true
path still enables its controller without a T8122 marker.

The normal J613 DTB was built directly from kernel
17a9930f20a0895b5980385b0b2d67edda8a24be. All internal-display host scenarios
and contract self-checks pass against that DTB and the bundled fixture. This
checks the FDT handoff; it does not exercise the physical atcphy1 probe or the
new lid-closed display session. The paired native kernel/Mesa ABI check still
matches 18 selected facts. Ten inherited G15 fixture failures remain unchanged.
