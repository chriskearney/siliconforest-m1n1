# SPDX-License-Identifier: MIT
"""Exercise real raw-artwork rules without building or installing a boot image."""
import os
from pathlib import Path
import subprocess


def test_changed_artwork_directory_and_invalid_pixels(tmp_path):
    root = Path(__file__).resolve().parents[2]
    (tmp_path / "Makefile").write_bytes((root / "Makefile").read_bytes())
    (tmp_path / "data").mkdir()
    for name, byte in (("first", 0x31), ("second", 0x72)):
        folder = tmp_path / name
        folder.mkdir()
        for size in (48, 128, 256):
            image = folder / f"bootlogo_{size}.bin"
            image.write_bytes(bytes([byte]) * (size * size * 4))
            os.utime(image, (1, 1))
    targets = [f"build/bootlogo_{size}.bin" for size in (48, 128, 256)]
    for name, byte in (("first", 0x31), ("second", 0x72)):
        subprocess.run(["make", "USE_CLANG=1", f"BOOTLOGO_DIR={tmp_path / name}",
                        *targets], cwd=tmp_path, check=True)
        for size, target in zip((48, 128, 256), targets):
            assert (tmp_path / target).read_bytes() == bytes([byte]) * (size * size * 4)
    (tmp_path / "second/bootlogo_128.bin").write_bytes(b"truncated")
    result = subprocess.run(["make", "USE_CLANG=1", f"BOOTLOGO_DIR={tmp_path / 'second'}",
                             targets[1]], cwd=tmp_path)
    assert result.returncode != 0
    assert (tmp_path / targets[1]).read_bytes() == bytes([0x72]) * (128 * 128 * 4)
