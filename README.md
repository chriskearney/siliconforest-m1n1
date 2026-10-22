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
native G17 UAPI. The candidate profile uses `CONFIG_SILICONFOREST_NATIVE_GPU=y`
with `CONFIG_SILICONFOREST_M3` unset: native GPU, normal display drivers.
Validate the resolved config and built UAPI against the locked Mesa source.
This source choice has not qualified a complete Neo stack on hardware.

Build with LLVM 22.1.8 and Rust 1.89.0. The basic development build is:

```sh
RUSTUP_TOOLCHAIN=1.89.0 make -j4 RELEASE=1 CHAINLOADING=0 USE_CLANG=1 ARCH=aarch64-linux-gnu
```

For a **local, unsigned Neo candidate**, use the role-aware recipe instead
of the legacy KIS-pair packager. It requires a Linux build host, Python 3.12+,
GNU Make 4.3+, a clean worktree,
the exact source SHA, cached Cargo dependencies, and a branding export with
`manifest.json` plus `m1n1/bootlogo_{48,128,256}.bin`:

```sh
python3 tools/build_neo.py \
  --expected-commit FULL_REVIEWED_SOURCE_SHA \
  --artwork /path/to/siliconforest-branding-export \
  --output /path/to/new-candidate-directory --jobs 4
```

The output directory must not exist. Each role builds from a fresh source
snapshot with warnings treated as errors. Stage 1 retains the existing KIS
recovery profile and its configuration ABI; ESP stage 2 uses the emitted
`ESP_STAGE2` role and has no stage-1 configuration block. Both enable the
storage chainloader. The recipe verifies the effective defines, raw ELF entry,
ELF-to-binary equality and `STACKBOT` tail, and records source, artwork,
toolchains and artifact hashes in `receipt.json` and `SHA256SUMS`.
Compiler prefix maps remove temporary and home paths from the debug ELFs and
Rust file names. The receipt records the full Make argument list and Rust
flags with those paths normalized; build logs are redacted with the same maps.
Logs retain parallel ordering and timings, so the complete bundle and its
`SHA256SUMS` file are not claimed to be reproducible even when the binary,
ELFs and receipt match across repeated builds.

The artwork is linked raw RGBA. To change it later, regenerate the branding
export and build a new version; inherited source artwork is unchanged. Existing
wire identifiers and stage-1 configuration magic remain for compatibility.

No boot components, Apple boot policy or public catalog are changed by this
recipe. Hardware qualification requires the matched kernel/DTBs/Mesa, the
actual firmware tuple and boot backend, attended recovery and a reboot-tested
rollback. Stage-1 enrollment is a separate owner Recovery operation.

The first attended J700 boot must capture the stage-1-to-stage-2 storage
handoff log. With the ordinary controller-disable handoff, require
`nvme: controller disabled; preserving live RTKit session` and successful
entry into stage 2. `nvme: unsafe post-M4 queue handoff; retaining DMA resources until reboot`
is a failed qualification: keep the recovery path available and do not bypass
the refusal. Delete-SQ/CQ errors and controller shutdown/disable timeouts must
not occur. A separately selected live-Linux-adoption path instead requires
`nvme: leaving controller and RTKit running for Linux adoption`; that message
does not qualify the stage-1-to-stage-2 disable path.

Failure-path limits: joining a pending CPU callback waits up to 300 seconds,
without resending its interrupt, before refusing the boot. This safety rule
also applies if this source is built for an older supported chip. PMGR's
missing-parent tolerance covers the known virtual-device cases; cleanup of
an active non-virtual device with a missing parent still fails strictly.

Run host checks with `USE_CLANG=1 RUSTUP_TOOLCHAIN=1.89.0 python3 -m pytest`.
Platform skips and source/build results are not physical-display or boot claims.

[Main integration, provenance and review](https://github.com/iconidentify/siliconforest-m1n1/tree/siliconforest/next).
Original upstream documentation is in README.upstream.md.
