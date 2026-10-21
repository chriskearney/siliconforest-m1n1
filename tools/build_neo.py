#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build an uninstalled Neo stage-1 / ESP-stage-2 pair from exact source and art."""

import argparse
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[1]
RUST = "1.89.0"
LLVM = "22.1.8"
MAGIC = b"AURORA-S1-CFG01\0"
ROLES = {
    "stage1": ["CHAINLOADING=1", "T8140_KIS_PROXY=1", "T8140_PROXY_WINDOW_MS=15000"],
    "esp-stage2": ["CHAINLOADING=1", "ESP_STAGE2=1"],
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def command(args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs).strip()


def publish_directory(source, output):
    """Atomically publish on Linux, refusing even a concurrently created empty dir."""
    library = ctypes.CDLL(None, use_errno=True)
    rename = getattr(library, "renameat2", None)
    if rename is None:
        raise ValueError("atomic candidate publication requires Linux renameat2")
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                       ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    # AT_FDCWD, RENAME_NOREPLACE; all writes remain inside the requested parent.
    if rename(-100, os.fsencode(source), -100, os.fsencode(output), 1):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(output))


def artwork_inputs(folder):
    manifest_bytes = (folder / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
        raise ValueError("artwork manifest must contain a files hash map")
    images = {}
    for size in (48, 128, 256):
        name = f"m1n1/bootlogo_{size}.bin"
        pixels = (folder / name).read_bytes()
        if len(pixels) != size * size * 4 or any(alpha != 255 for alpha in pixels[3::4]):
            raise ValueError(f"{name}: expected opaque RGBA8888 pixels")
        if manifest["files"].get(name) != digest(pixels):
            raise ValueError(f"{name}: artwork manifest hash mismatch")
        images[Path(name).name] = pixels
    return manifest_bytes, images


def check_image(folder, role, artwork):
    cfg = (folder / "build_cfg.h").read_text().splitlines()
    defines = {line[len("#define "):] for line in cfg if line.startswith("#define ")}
    expected = {"RELEASE", "CHAINLOADING", "BUILTIN_LOGO bootlogo"}
    if role == "stage1":
        expected |= {"T8140_KIS_PROXY", "USE_DEBUG_USB", "T8140_PROXY_WINDOW_MS 15000"}
    else:
        expected.add("ESP_STAGE2")
    if defines != expected:
        raise ValueError(f"{role}: unexpected effective build defines: {defines ^ expected}")
    image = (folder / "m1n1.bin").read_bytes()
    if not image.endswith(b"STACKBOT") or image.count(MAGIC) != (role == "stage1"):
        raise ValueError(f"{role}: wrong bare-image/configuration layout")
    for name, pixels in artwork.items():
        if image.count(pixels) != 1:
            raise ValueError(f"{role}: pinned artwork {name} is not linked exactly once")
    elf = (folder / "m1n1-raw.elf").read_bytes()
    if elf[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<H", elf, 18)[0] != 183:
        raise ValueError(f"{role}: expected AArch64 ELF64")
    if struct.unpack_from("<Q", elf, 24)[0] != 2048:
        raise ValueError(f"{role}: raw entry point changed")
    reproduced = folder / "reproduced.bin"
    subprocess.run(["llvm-objcopy", "-O", "binary", "--strip-debug",
                    str(folder / "m1n1-raw.elf"), str(reproduced)], check=True)
    if reproduced.read_bytes() != image:
        raise ValueError(f"{role}: raw ELF does not reproduce the shipped binary")
    reproduced.unlink()
    return {"image_sha256": digest(image), "image_bytes": len(image),
            "raw_elf_sha256": digest(elf), "effective_defines": sorted(defines)}


def build(args):
    source = args.source.resolve()
    output = args.output.absolute()
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError("output must not exist and its parent must exist")
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", str(output.parent)):
        raise ValueError("output parent must not contain whitespace or Make/shell metacharacters")
    if not re.fullmatch(r"[0-9a-f]{40}", args.expected_commit):
        raise ValueError("expected commit must be a full lowercase SHA-1")
    if command(["git", "rev-parse", "HEAD"], cwd=source) != args.expected_commit:
        raise ValueError("source HEAD does not match expected commit")
    if command(["git", "status", "--porcelain", "--untracked-files=all"], cwd=source):
        raise ValueError("source worktree must be clean")
    subprocess.run(["git", "merge-base", "--is-ancestor",
                    "c57f27f473de3d75266cf4d3f17e02866acd0edb", args.expected_commit],
                   cwd=source, check=True)
    manifest, images = artwork_inputs(args.artwork.resolve())
    env = dict(os.environ, RUSTUP_TOOLCHAIN=RUST, RUSTFLAGS="-D warnings",
               CARGO_NET_OFFLINE="true", SOURCE_DATE_EPOCH=command(
                   ["git", "show", "-s", "--format=%ct", args.expected_commit], cwd=source))
    # These would override the recorded command-line flags or compiler choice.
    for key in ("MAKEFLAGS", "MFLAGS", "MAKEOVERRIDES", "CARGO_ENCODED_RUSTFLAGS",
                "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "RUSTC", "RUSTDOC",
                "CARGO_BUILD_TARGET", "CARGO_TARGET_DIR"):
        env.pop(key, None)
    versions = {tool: command([tool, "--version"], env=env)
                for tool in ("clang", "ld.lld", "llvm-objcopy", "rustc", "cargo")}
    if not versions["rustc"].startswith(f"rustc {RUST} "):
        raise ValueError("unexpected Rust version")
    if not versions["cargo"].startswith(f"cargo {RUST} "):
        raise ValueError("unexpected Cargo version")
    for tool in ("clang", "ld.lld", "llvm-objcopy"):
        if not re.search(r"(?<![\d.])" + re.escape(LLVM) + r"(?![\d.])", versions[tool]):
            raise ValueError(f"unexpected {tool} version")
    archive = subprocess.check_output(["git", "archive", "--format=tar", args.expected_commit], cwd=source)
    with tempfile.TemporaryDirectory(prefix=".neo-build-", dir=output.parent) as temporary:
        temp = Path(temporary)
        result = temp / "result"
        result.mkdir()
        art = temp / "artwork"
        art.mkdir()
        for name, pixels in images.items():
            (art / name).write_bytes(pixels)
        (result / "artwork-manifest.json").write_bytes(manifest)
        roles = {}
        tag = "v2.0.0-siliconforest.neo.dev.g" + args.expected_commit[:12]
        for role, options in ROLES.items():
            tree = temp / ("source-" + role)
            tree.mkdir()
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                tar.extractall(tree, filter="data")
            folder = result / role
            folder.mkdir()
            make = ["make", "-j" + str(args.jobs), "RELEASE=1", *options,
                    "USE_CLANG=1", "ARCH=aarch64-linux-gnu", "EXTRA_CFLAGS=-Werror",
                    "TOOLCHAIN=", "LLDDIR=", "RUSTARCH=aarch64-unknown-none-softfloat",
                    "BUILTIN_LOGO=bootlogo", "BOOTLOGO_DIR=" + str(art), "M1N1_VERSION_TAG=" + tag]
            with (folder / "build.log").open("w") as log:
                subprocess.run(make, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            for name in ("m1n1.bin", "m1n1-raw.elf", "m1n1.elf", "build_cfg.h", "build_tag.h"):
                shutil.copy2(tree / "build" / name, folder / name)
            roles[role] = check_image(folder, role, images)
            roles[role]["linked_artwork_verified"] = True
            roles[role]["make_options"] = ["RELEASE=1", *options, "USE_CLANG=1",
                                           "ARCH=aarch64-linux-gnu", "EXTRA_CFLAGS=-Werror",
                                           "BUILTIN_LOGO=bootlogo"]
            if role == "stage1":
                shutil.copy2(tree / "LICENSE", result / "LICENSE")
                shutil.copytree(tree / "3rdparty_licenses", result / "3rdparty_licenses")
                shutil.copy2(tree / "rust/Cargo.lock", result / "Cargo.lock")
        receipt = {
            "schema": 1, "profile": "neo-first-candidate", "board": "apple,j700",
            "source_commit": args.expected_commit, "source_archive_sha256": digest(archive),
            "artwork_manifest_sha256": digest(manifest),
            "artwork_files": {name: digest(data) for name, data in images.items()},
            "toolchains": versions, "rustflags": "-D warnings", "cargo_offline": True,
            "build_tag": tag, "roles": roles, "hardware_qualified": False,
            "installed": False, "signed": False,
            "limits": ["No installation or boot-policy change is performed.",
                       "Stage 1 is generic until filled for an authorized target in Recovery.",
                       "Paired kernel/DTB/Mesa and the boot backend require separate qualification."]}
        (result / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        paths = [p for p in sorted(result.rglob("*")) if p.is_file()]
        (result / "SHA256SUMS").write_text("".join(
            digest(p.read_bytes()) + "  " + p.relative_to(result).as_posix() + "\n" for p in paths))
        if output.exists() or output.is_symlink():
            raise ValueError("output appeared during the build; refusing replacement")
        publish_directory(result, output)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--artwork", type=Path, required=True,
                        help="branding export containing manifest.json and m1n1/*.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jobs", type=int, choices=range(1, 17), default=4)
    args = parser.parse_args()
    try:
        receipt = build(args)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        parser.exit(1, f"build-neo: {error}\n")
    print(json.dumps({"output": str(args.output), "source_commit": receipt["source_commit"],
                      "hardware_qualified": False}))


if __name__ == "__main__":
    main()
