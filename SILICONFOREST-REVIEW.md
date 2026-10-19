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


## J613 firmware-ready follow-up

Public patch: [Marius Gehrmann's source](https://github.com/GehrmannSolutions/omarchy-m3-air/blob/5f0d61514cf2bf2ec598850bcca4e007c0c1f083/boot/m1n1-aurora-t8122-dcpext.patch),
blob and SHA256 recorded in the manifest. The import credits Marius as author
and preserves his MIT notice. The patch supplied no Signed-off-by, and none
was invented. Its weak wcslen fallback was omitted because current upstream's
Rust 1.99 workaround already links without it.

The original marker change relies on a common helper that could return success
when reservation allocation failed, and could leave partial firmware properties.
The downstream fix propagates that failure and validates segment-list shape.
T8122 publication additionally checks bounded, aligned physical spans against
exact DRAM metadata and runs each controller update on a scratch FDT. An old
marker is withdrawn before retry. The marker is written last, after complete
reservation and firmware publication; supplier, controller and route status is
never enabled by this path. Missing metadata, allocation failure, a partial
second reservation, firmware-copy failure and marker failure are exercised
against production functions with real FDTs. The existing enable=true path has
a positive control, and foreign chip/tree controls refuse T8122 publication.

The paired J613 DTB now includes the disabled internal DCP Type-C route.
Minimum kernel commit is 17a9930f20a0895b5980385b0b2d67edda8a24be; use a
matching kernel and DTB from one pin. The internal panel additionally depends
on atcphy1 probing. The 25G83 DT includes the same base tree, so this PHY
dependency and pairing floor apply to it too. The new kernel carry is in normal
drm/apple and the normal display gate. Both gate Kconfigs depend on
!SILICONFOREST_M3; the alternative M3 copies intentionally have no T8122/J613
support. Do not port this carry to them. The external gate requires exactly
three u32 firmware-compat cells: 14 7 0. The 26.6.2 native-panel profile bypasses
this gate and leaves dcpext disabled; camera support there does not supply
external display.

The contributor's hardware evidence is in omacom/linux-aurora issue 103 and
PR114. Our validation adds host failure injection and internal-display checks
against the exact new DTB; it is not a new physical display or suspend test.
The existing M3 relocation algorithm and T6030 PMP chosen export are unchanged.


## Kernel consumer confirmation at 17a9930f

The kernel maintainer confirmed the handoff contract against
17a9930f20a0895b5980385b0b2d67edda8a24be. The gate requires a disabled dcpext,
a u32 readiness marker equal to 1, exactly 14 7 0 firmware compatibility, and a
memory-region; m1n1 also publishes iommu-addresses. Its disabled DARTs, mailbox
and route crossbars are enabled together in one kernel changeset. Existing
nomodeset, DRM configuration, PMP request and command-line admission checks
still apply. No driver or default changes are needed for this confirmation.

| Export | Consumer at the paired kernel revision |
| --- | --- |
| apple,j514s-native-piodma; apple,j514s-inherited-mappings; aurora,j514s-display-handoff; apple,tunable-dp-calibration | Alternative M3 display/PHY profile and m3-g15 DTs only. |
| asahi,t6031-pmp; asahi,t6031-fw-uuids | Normal display gate with apple_t6031_display.enable=1. |
| asahi,t6031-gpu; asahi,t6031-gpu-powered-identity | Normal t6031_knobs path with asahi.t6031_start=1. |
| asahi,t6031-facts; asahi,t6031-gpu-image | No kernel reader at this revision; diagnostic records, not kernel activation inputs. |

Old m1n1 with the new kernel leaves external display unarmed. New m1n1 with an
old kernel also leaves dcpext disabled, but only a DTB matching that old kernel
is a valid fallback: a new J613 DTB with an old kernel breaks the internal
panel. Roll back the kernel and its DTBs as a matched set.


## T600x route handoff follow-up

[PR33](https://github.com/aurora-silicon/m1n1/pull/33),
`9b4dcc65874e3aa64898a375d1e3f453f03b6aee`, is adapted by Chris Kearney in
`24a133ff` with Andreas Fernandez credited for the original public design;
`99817310` preserves the legacy enable path. The larger downstream transaction,
exact-status checks, reservation fix and tests are attributed to their downstream
author. `a28c2231` adds a later-controller regression and wording corrections.
For T6000/T6001/T6002, explicitly disabled routes and their reserved owning DCP
are published together through a scratch-FDT transaction. Failed allocation,
property edits, malformed tree traversal or reservation abort publication.
Missing, already-enabled, reserved, failed and malformed route statuses are
preserved. An existing reservation allocation error now returns failure instead
of a stale zero. Other chips keep their original allocation-free controller
enablement; optional external enable failures keep log-and-continue behavior.

Our kernel already skips unavailable route ancestors (`5ca53abe30ab`) and its
T600x routes intentionally carry no status. They retain today's dual USB-C
behavior with older loaders; this helper does not claim to newly unlock that
feature. It also supports upstream-style DTBs with explicitly disabled routes.
The paired kernel locks the fixed-HDMI/all-disabled compatibility policy while
retaining strict T6030/T8122 external admission. The T8122 marker transaction,
disabled suppliers/routes, and the separate T6030 handoff remain unchanged.

Validation: 26 Python cases passed with 7 skipped using USE_CLANG=1, including
real-libfdt relocation and failure controls and the production reservation
caller. A T8112-style injected first enable failure still reserves/enables the
second controller; restoring an early bail fails this regression. Focused T6030 and T8122 display host tests passed. Stage 2 builds with
LLVM 22.1.8 and Rust 1.99.0; no boot policy or installed payload was changed.
These checks do not qualify physical multi-monitor or suspend/resume operation.
The previously documented full G15 fixture debt remains outside this change.
