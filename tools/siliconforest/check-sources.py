#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check pinned source refs and, optionally, the paired kernel/Mesa contract."""

import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-git", action="store_true", help="verify source tags in a full clone")
    parser.add_argument("--kernel", type=Path)
    parser.add_argument("--mesa", type=Path)
    args = parser.parse_args()
    data = json.loads((ROOT / "SILICONFOREST-SOURCES.json").read_text())
    public = {entry["repository"] for entry in data["visibility_checks"]
              if entry["visibility"] == "public"}
    tags = set()
    for entry in data["source_snapshots"]:
        assert entry["repository"] in public
        assert entry["tag"] not in tags
        tags.add(entry["tag"])
        assert len(entry["commit"]) == 40 and all(c in "0123456789abcdef" for c in entry["commit"])
        if args.check_git:
            assert git("rev-parse", "refs/tags/" + entry["tag"]) == entry["commit"]
    if args.check_git:
        for entry in data["profiles"]:
            assert git("rev-parse", entry["commit"] + "^") == entry["source_commit"]
    subprocess.run(["git", "merge-base", "--is-ancestor",
                    data["upstream_integrated"], "HEAD"], cwd=ROOT, check=True)
    if bool(args.kernel) != bool(args.mesa):
        parser.error("--kernel and --mesa must be supplied together")
    if args.kernel:
        kernel, mesa = args.kernel.resolve(), args.mesa.resolve()
        for name, path in (("kernel", kernel), ("mesa", mesa)):
            actual = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
            assert actual == data[name]["commit"], f"{name}: checkout differs from manifest"
        uuid = "DDF38191-93B3-324A-BC8F-643006F5AC82"
        assert uuid in (ROOT / "src/kboot.c").read_text()
        assert uuid in (kernel / "drivers/gpu/drm/apple-m3/dcp.c").read_text()
        assert 'apple,agx-t8140' in (kernel / "drivers/gpu/drm/asahi-m3/driver.rs").read_text()
        for constraint in data.get("boot_chain_constraints", []):
            subprocess.run(["git", "-C", str(kernel), "merge-base", "--is-ancestor",
                            constraint["minimum_kernel_commit"], "HEAD"], check=True)
        marker = '"apple,t8122-dcpext-firmware-ready"'
        assert marker in (ROOT / "src/kboot.c").read_text()
        assert marker in (kernel / "drivers/soc/apple/t6030-display-gate.c").read_text()
        subprocess.run(["python3", str(mesa / "tools/siliconforest/check-kernel-abi.py"), str(kernel)], check=True)
        print("Pinned kernel/Mesa, J514S firmware identity and native wire ABI matched")
    print(f"{len(tags)} public source records checked; hardware qualification remains separate")


if __name__ == "__main__":
    main()
