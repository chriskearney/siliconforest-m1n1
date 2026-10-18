# SiliconForest m1n1: Neo development profile

Personal downstream m1n1 source for J700 / T8140 (A18 Pro, Neo), based on
public `omacom/m1n1:integration/neo` at
`1b36287e04788f4a028e6180c64d3d96e49f06b1` (see the main source manifest for the exact pin).
The original code, authorship and licenses are retained. AI-assisted maintenance
is authorized here; see AGENTS.md.

This profile retains the Neo-specific inherited display, CPU/WFE, NVMe and
USB handoffs. It is separate from the M3 integration because those branches
have divergent boot paths and firmware handoff implementations. It does not
include the M3 Max integration or the new upstream 2.0 hypervisor work.

Pairing with `siliconforest-mesa:siliconforest/next` requires the kernel's
alternative native UAPI (`CONFIG_SILICONFOREST_M3=y`), including its G17 driver.
The normal legacy UAPI uses different feature bits and payload layouts and is
rejected by native Mesa. Host tests and a cross-build do not qualify that full
combination on hardware. No boot components are installed by building this tree.

The branch has a Linux stage 2 cross-build and 80 passing pytest cases (7
platform/environment skips). Build with LLVM 22.1.8 and Rust 1.89.0:

```sh
RUSTUP_TOOLCHAIN=1.89.0 make -j4 RELEASE=1 CHAINLOADING=0 USE_CLANG=1 ARCH=aarch64-linux-gnu
```

[Main integration, provenance and review](https://github.com/iconidentify/siliconforest-m1n1/tree/siliconforest/next).
Original upstream documentation is in README.upstream.md.
