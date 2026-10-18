# SiliconForest m1n1 review — 2026-10-18

This is an independent downstream integration. Its owner authorizes AI-assisted
maintenance; the inherited prohibition is replaced by AGENTS.md. Original
contributor identities, history and licenses are retained. No upstream issues,
comments or PRs were submitted by this work.

## Source decisions

| Public source | Decision |
| --- | --- |
| AsahiLinux main `25b1d89ca50be848b136ce771ce7167244852a91` | Merged completely, including current hypervisor fixes, Rust workaround and upstream GPL transition. Existing bounded secondary-status API retained. LICENSE.MIT and component notices preserved. |
| Omacom integration baseline `d05ba17dfb771871d608225be42968bbb1e75a18` | Existing M3 Air/Pro board, firmware, power, stage 1 and 26.6.2 profiles retained. |
| Omacom Max branch `a2b3a4ad018c12b83980f052e51a1560855fa15f` | Four original commits merged with history: display/PMP facts, G15C identity/power closure, firmware observations and tests. |
| Eryk's public Aurora PR34 | Five commits cherry-picked with source SHA trailers: locked DART walk, panel, external display, HDMI calibration and SIO protocol-10 records. |
| Public Omacom PR4 `bd5a2348806923e4139bc300f05b8df887bc06d3` | T8122 26.6.2 ISP heap case imported, then segment arithmetic hardened. The contributor reports a camera stream on their machine; that is not our hardware qualification. |
| Omacom Neo `1b36287e04788f4a028e6180c64d3d96e49f06b1` | Separate experimental/neo profile, built and host-tested. Its broad storage/USB/display/CPU changes are not silently substituted for the M3 paths. |
| Public J616S M4 and DJ T6050 branches | Separate experimental snapshots. Not built, not a matched graphics support claim. |
| Other public branch/PR heads | Pinned source evidence only. Unmerged work such as general Type-C route enablement, tracing and alternate stage 1 branches is not automatically enabled. |

175 exact public source snapshots and 93 PR records are in the manifest. Five
public repositories supply the snapshots; additional Jannau, Hoolock and owner
fork metadata was compared during discovery. This finite snapshot is not a claim
to include every possible branch or every subsequently published change.

## Findings fixed downstream

1. **Max GPU probing was automatic despite stand-in calibration.** The imported
   branch armed the powered probe unless explicitly switched off. The maintained
   profile requires the exact string `chosen.asahi,t6031-gpu=1`, including its NUL.
   Absent, malformed and false intent causes no firmware read or powered probe.
   The passive OS-log reservation path remains available. The kernel's J516C-only
   admission and required board-data blob are not widened to J514C.
2. **J514S device-tree publication could stop after enabling a consumer.** Native
   panel publication and each external controller now run on a scratch FDT. A
   failure discards all edits in that transaction. A failed panel transaction
   prevents external publication. Mandatory live-log reservations and legacy
   handoff remain outside the optional native transaction. The native path is
   selected only by the matched DT's `apple,j514s-native-piodma` property.
3. **J514S metadata accepted partial values or overflowing spans.** DRAM fields
   must be exact u64 values; physical ranges are checked by subtraction; DART
   storage must be aligned, nonempty and inside DRAM. Firmware UUID property
   lengths are checked before indexing. The frontend DART window must cover the
   accessed registers in both trees. The locked walker rejects SID >= 16 before
   any register read.
4. **The imported camera fix did not validate its segment list before indexing.**
   Missing, truncated, single-entry, empty and wrapping segment lists are rejected
   before powering the ISP. Heap start is the maximum validated end, so an
   unordered list cannot overlap a later segment. An image reaching the heap top
   is refused, with the new failure path dropping the ISP power vote.
5. **New upstream hypervisor failure return conflicted with the downstream API.**
   CPU protection-hook failure returns -1 through the existing status API.
   Secondary cleanup/timeout state is retained. A regression control injects hook
   failure. The TLBI VMALLS12E1OS instruction is emitted using its verified
   `0xd50c81df` encoding to retain the Armv8.2 assembler baseline; no global CPU
   instruction-set requirement was added.
6. **The old m1n1 Rust pin no longer builds current upstream.** Its Rust 1.99 LLVM
   workaround flag is rejected by Rust 1.89. Default integration builds with
   1.99.0 and LLVM 22.1.8; the separate older Neo profile retains 1.89.0.

## Pairing and remaining limits

The source check compares 18 native Mesa/kernel wire facts and the J514S DCP UUID.
This establishes selected static contracts, not a physical boot or GPU session.
Native G15S/G15C/G17P Mesa requires CONFIG_SILICONFOREST_M3=y, including its G17
implementation; normal kernel feature assignments/layouts are incompatible.

M3 Air firmware profiles and their Mesa compatibility branches remain separate.
The original Max firmware-family admission is broader than an exact per-image
UUID; it is protected by opt-in here and by the kernel's stricter board/firmware
checks, and is not qualified for a binary release. No Apple firmware or machine
capture is copied into this repository. The full ADT-driven Max host suite still
needs an external appropriately handled input; it was not run with a user's
machine capture. Source-derived J516C board data remains a release prerequisite.

The old G15 synthetic stand-in test suite is not green: the same ten failures
occur on both the original pin and this integration. They were neither treated
as passes nor addressed by weakening production identity admission. Details and
all validation limits are in SILICONFOREST-VALIDATION.md.
