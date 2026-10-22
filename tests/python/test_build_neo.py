# SPDX-License-Identifier: MIT
"""Check source/artwork refusals before the Neo recipe executes a build."""

import argparse
import hashlib
import json
from pathlib import Path

import pytest

from tools import build_neo


def test_make_minimum_and_flavour():
    for version in ("GNU Make 4.3\nBuilt for x86_64", "GNU Make 4.4.1", "GNU Make 5.0"):
        build_neo.require_make(version)
    for version in ("GNU Make 4.2.1", "GNU Make 3.82", "BSD Make 20261021", "GNU Make unknown"):
        with pytest.raises(ValueError, match="GNU Make 4.3"):
            build_neo.require_make(version)


def test_log_redaction_keeps_role_and_diagnostics(tmp_path, monkeypatch):
    home = tmp_path / "host-home"
    temp = home / "random-temporary"
    tree = temp / "source-stage1"
    monkeypatch.setattr(Path, "home", lambda: home)
    mappings = build_neo.path_maps(tree, temp, {})
    log = f"error in {tree}/src/main.c; dependency {home}/.cargo/git/source.rs; sysroot {home}/.rustup/lib"
    normalized = build_neo.normalize_paths(log, mappings)
    assert str(home) not in normalized
    assert normalized == (
        "error in /siliconforest/neo/stage1/src/main.c; dependency "
        "/siliconforest/neo/cargo/git/source.rs; sysroot /siliconforest/neo/rustup/lib")


def artwork(tmp_path):
    (tmp_path / "m1n1").mkdir()
    files = {}
    for size in (48, 128, 256):
        name = f"m1n1/bootlogo_{size}.bin"
        pixels = bytes([1, 2, 3, 255]) * (size * size)
        (tmp_path / name).write_bytes(pixels)
        files[name] = hashlib.sha256(pixels).hexdigest()
    (tmp_path / "manifest.json").write_text(json.dumps({"files": files}))


def test_artwork_hash_and_shape(tmp_path):
    artwork(tmp_path)
    manifest, images = build_neo.artwork_inputs(tmp_path)
    assert len(images) == 3
    path = tmp_path / "m1n1/bootlogo_48.bin"
    path.write_bytes(bytes([9, 8, 7, 255]) * (48 * 48))
    with pytest.raises(ValueError, match="hash mismatch"):
        build_neo.artwork_inputs(tmp_path)
    path.write_bytes(bytes([9, 8, 7, 0]) * (48 * 48))
    with pytest.raises(ValueError, match="opaque RGBA"):
        build_neo.artwork_inputs(tmp_path)
    path.write_bytes(b"short")
    with pytest.raises(ValueError, match="opaque RGBA"):
        build_neo.artwork_inputs(tmp_path)


def test_existing_output_untouched(tmp_path):
    output = tmp_path / "result"
    output.mkdir()
    keep = output / "keep"
    keep.write_bytes(b"existing result")
    args = argparse.Namespace(source=tmp_path, output=output, expected_commit="0" * 40)
    with pytest.raises(ValueError, match="output must not exist"):
        build_neo.build(args)
    assert keep.read_bytes() == b"existing result"


def test_wrong_pin_refused_before_archive(tmp_path, monkeypatch):
    args = argparse.Namespace(source=tmp_path, output=tmp_path / "result",
                              expected_commit="0" * 40)
    monkeypatch.setattr(build_neo, "command", lambda *a, **kw: "1" * 40)
    with pytest.raises(ValueError, match="HEAD does not match"):
        build_neo.build(args)
    assert not args.output.exists()


def test_dirty_source_refused_before_archive(tmp_path, monkeypatch):
    args = argparse.Namespace(source=tmp_path, output=tmp_path / "result",
                              expected_commit="0" * 40)
    replies = iter([args.expected_commit, " M src/kboot.c"])
    monkeypatch.setattr(build_neo, "command", lambda *a, **kw: next(replies))
    with pytest.raises(ValueError, match="must be clean"):
        build_neo.build(args)
    assert not args.output.exists()


def test_make_metacharacters_refused(tmp_path):
    parent = tmp_path / "unsafe-$(touch surprise)"
    parent.mkdir()
    args = argparse.Namespace(source=tmp_path, output=parent / "result",
                              expected_commit="0" * 40)
    with pytest.raises(ValueError, match="metacharacters"):
        build_neo.build(args)
    assert not (parent / "surprise").exists()
    assert not args.output.exists()


def test_publication_does_not_replace_a_concurrent_empty_directory(tmp_path):
    source = tmp_path / "staged"
    source.mkdir()
    (source / "receipt.json").write_bytes(b"reviewed result")
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(FileExistsError):
        build_neo.publish_directory(source, output)
    assert not list(output.iterdir())
    assert (source / "receipt.json").read_bytes() == b"reviewed result"
    output.rmdir()
    build_neo.publish_directory(source, output)
    assert (output / "receipt.json").read_bytes() == b"reviewed result"
    assert not source.exists()
