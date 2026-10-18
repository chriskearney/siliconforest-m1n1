# SiliconForest m1n1

A personally maintained Apple Silicon bootloader and research fork, maintained
by [iconidentify](https://github.com/iconidentify). AI-assisted development is
explicitly authorized here. Original contributor history, attribution and
licenses are preserved. No upstream participation or approval is required to
maintain this downstream fork.

**Development source, not a qualified bootloader release.** Nothing in the build
or check helpers installs a payload or changes a machine's boot policy.

| Profile | Source and intended pairing | Validation here |
| --- | --- | --- |
| `siliconforest/next` (default) | Current Asahi upstream plus M3 Air handoffs, Eryk's J514S display/HDMI/SIO and the M3 Max source handoff | Stage 2 cross-build; Python and focused host checks; see known test failures below |
| [`experimental/neo`](https://github.com/iconidentify/siliconforest-m1n1/tree/experimental/neo) | Separate J700 / T8140 inherited display, CPU/WFE, storage and USB profile | Stage 2 cross-build; 80 Python tests passed, 7 skipped |
| [`experimental/m4`](https://github.com/iconidentify/siliconforest-m1n1/tree/experimental/m4) | Public J616S / T6040 bring-up | Preserved, unbuilt and unqualified |
| [`experimental/m5-t6050`](https://github.com/iconidentify/siliconforest-m1n1/tree/experimental/m5-t6050) | DJ's public T6050 ATC/display and J714S research | Preserved, unbuilt and unqualified |

The default branch incorporates Asahi upstream through
`25b1d89ca50be848b136ce771ce7167244852a91` (2026-10-18), the four Max commits
through `a2b3a4ad018c12b83980f052e51a1560855fa15f`, Eryk's five J514S
handoff commits from public PR34, the public T8122 26.6.2 ISP heap fix, and
Marius Gehrmann's public J613 external-firmware marker patch.
[The source manifest](SILICONFOREST-SOURCES.json) pins 175 public branch/PR
snapshots and records 93 PRs. Snapshot tags preserve research; they do not mean
all those changes are merged or approved.

## Pairing with SiliconForest Linux and Mesa

Use the exact kernel/Mesa commits in the manifest. Native M3 Pro/Max and Neo Mesa
requires **the kernel's alternative native UAPI**, selected with
`CONFIG_SILICONFOREST_M3=y`. Its `asahi-m3` source also includes the G17/Neo driver.
The normal kernel profile exposes incompatible feature bits and command layouts;
current Mesa deliberately rejects it on native AGX3 chips. m1n1 cannot repair a
userspace/kernel ABI mismatch.

For J514S use the kernel's `apple/m3-g15/t6030-j514s.dtb` and its native display
properties. Other M3 device trees retain their existing handoff. M3 Max GPU
power/probing now requires **`chosen.asahi,t6031-gpu=1`**; its leakage/power model
uses stand-ins and remains experimental. The kernel admits only its measured
J516C board profile and still requires source-derived board data. A loader's
J514C recognition does not establish kernel or Mesa support for that board.

M3 Air 14.x and 26.6.2/HAL200 profiles remain distinct, with their own exact board,
firmware and opt-in checks. Use the matching Mesa compatibility profile for the
Air; the default Mesa M3 Pro/Max/Neo integration is not an Air support claim.
M4/M5 research is not a complete matched graphics stack.

Read [the review](SILICONFOREST-REVIEW.md) and
[validation report](SILICONFOREST-VALIDATION.md) before choosing a profile.
Physical boot, firmware takeover, GPU rendering, suspend and recovery are not
qualified by a cross-build or host test. No install one-liner is published yet.

## J613 external-display pairing

The loader now reserves the external processor's firmware after the panel
handoff and sets `apple,t8122-dcpext-firmware-ready = <1>`. The controller,
DARTs, mailbox, crossbars and routes remain disabled for the kernel gate. A
failed reservation or firmware update publishes no marker or partial DT edits.

The paired kernel is `17a9930f20a0895b5980385b0b2d67edda8a24be` or a descendant.
**Never ship the new J613 DTB with an older kernel:** its disabled internal
Type-C route is not accepted by the older panel driver. Build the kernel and
DTBs from one locked source revision. The panel now also waits for atcphy1.
The 25G83 tree includes the same base DT, so both rules apply to it too.

The marker consumer and lid-closed second-display work are in the normal
kernel display profile. Its external firmware gate requires exactly three u32
cells, `14 7 0`. The paired kernel has no J613 external display on 26.6.2;
the camera fix is separate. Both display gates depend on
`!SILICONFOREST_M3`: the alternative M3 copies intentionally have no T8122/J613
support. See the [review](SILICONFOREST-REVIEW.md) for export consumers and rollback.

## Build and check

The maintained default uses LLVM 22.1.8 and Rust 1.99.0 with the
`aarch64-unknown-none-softfloat` target. The separate Neo profile uses Rust
1.89.0. Current upstream's Rust 1.99 LLVM workaround is incompatible with Rust
1.89; do not reuse the older default toolchain pin.

```sh
git clone --recurse-submodules --branch siliconforest/next https://github.com/iconidentify/siliconforest-m1n1.git
cd siliconforest-m1n1
RUSTUP_TOOLCHAIN=1.99.0 make -j4 RELEASE=1 CHAINLOADING=0 USE_CLANG=1 ARCH=aarch64-linux-gnu
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt pytest
USE_CLANG=1 .venv/bin/python -m pytest -q tests/python tests/test_t8122_gpu_reader.py tests/test_t8122_gpu_resources.py
python3 tools/siliconforest/check-sources.py
```

This produces an uninstalled stage 2 `build/m1n1.bin`, not a complete `boot.bin`.
A usable boot chain also needs the exact matching DTBs, U-Boot, firmware and
machine configuration. Stage 1 remains a separate qualification decision.

**Known inherited test failures:** the G15 standalone suite has 65 passing and
10 failing old stand-in scenarios, with the identical failures reproduced at the
original `fec93c15` pin. These fixtures predate stricter Air identity admission.
The report lists each failure; they have not been hidden by weakening the gate.
The complete suite is therefore not green.

## Maintenance and licenses

Use explicit reviewed refs when publishing; do not mirror a research checkout.
Source visibility is checked before publication. Private Mesa research remains
local under the owner's instruction. See AGENTS.md for the downstream policy.

This integration includes upstream's GPL transition. Read LICENSE, LICENSE.MIT,
per-file SPDX notices and 3rdparty_licenses; preserve all applicable notices.
The original upstream documentation is retained in README.upstream.md.
