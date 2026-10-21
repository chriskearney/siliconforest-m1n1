# SPDX-License-Identifier: MIT
"""Check source/artwork refusals before the Neo recipe executes a build."""

import argparse
import hashlib
import json
from pathlib import Path

import pytest

from tools import build_neo


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
