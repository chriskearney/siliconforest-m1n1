# SPDX-License-Identifier: MIT
"""Compile actual USB entry points with each Makefile-derived role definition."""

from pathlib import Path
import os
import re
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]


def function(source, name):
    start = source.index("void " + name + "(void)")
    pos = source.index("{", start) + 1
    depth = 1
    while depth:
        depth += (source[pos] == "{") - (source[pos] == "}")
        pos += 1
    return source[start:pos]


@pytest.mark.parametrize("options,preserve", [
    ([], False),
    (["ESP_STAGE2=1"], True),
    (["J700_ESP_STAGE2=1"], True),
    (["T8140_KIS_PROXY=1"], True),
    (["J700_CDC_PROXY=1"], True),
])
def test_role_preserves_only_neo_carrier(tmp_path, options, preserve):
    cfg = subprocess.check_output([
        "make", "-s", "--no-print-directory", "--eval",
        "sf-print-cfg:;@printf '%s\\n' '$(CFG)'", "sf-print-cfg",
        "RELEASE=1", "CHAINLOADING=1", *options,
    ], cwd=ROOT, text=True).split()
    assert all(re.fullmatch(r"[A-Z][A-Z0-9_]*", flag) for flag in cfg), cfg
    source = Path(os.environ.get("USB_ROLE_SOURCE", ROOT / "src/usb.c")).read_text()
    bodies = "\n".join(function(source, name) for name in ("usb_init", "usb_iodev_init"))
    harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#define T8140 0x8140
#define FIRST_USB_IODEV 0
#define USB_IODEV_COUNT 4
#define IODEV_USB0 10
#define SPINLOCK_ALIGN 64
#define USAGE_CONSOLE 1
#define USAGE_UARTPROXY 2
typedef int dwc3_dev_t;
struct iodev { void *ops, *opaque; int usage, lock; };
static struct iodev devices[USB_IODEV_COUNT];
static int chip_id, hpm_calls, phy_calls, bringup_calls, registered;
static bool usb_is_initialized;
static void *adt;
static int iodev_usb_ops;
static bool usb_init_match(char *p, void *unused) { return true; }
static int usb_init_one(char *p, void *d, void *unused) { return 0; }
static int adt_path_offset(void *a, const char *p) { return -1; }
static void tps6598x_foreach_hpm(bool (*match)(char *, void *),
                               int (*action)(char *, void *, void *), void *data)
{ hpm_calls++; }
static void usb_phy_bringup(int i) { phy_calls++; }
static dwc3_dev_t *usb_iodev_bringup(int i) { bringup_calls++; return &iodev_usb_ops; }
static void *memalign(size_t align, size_t size)
{ assert(size == sizeof(struct iodev)); return &devices[registered]; }
static void spin_init(int *lock) { *lock = 0; }
static void iodev_register_device(int id, struct iodev *dev)
{ assert(id == IODEV_USB0 + registered); registered++; }
''' + bodies + r'''
static void run(int chip, bool skip)
{
    chip_id = chip;
    usb_is_initialized = false;
    hpm_calls = phy_calls = bringup_calls = registered = 0;
    usb_init();
    usb_iodev_init();
    assert(hpm_calls == !skip);
    assert(phy_calls == (skip ? 0 : USB_IODEV_COUNT));
    assert(bringup_calls == (skip ? 0 : USB_IODEV_COUNT));
    assert(registered == (skip ? 0 : USB_IODEV_COUNT));
    assert(usb_is_initialized == !skip);
    usb_init();
    assert(hpm_calls == !skip);
}
int main(void)
{
    run(T8140, EXPECT_PRESERVE);
    run(0x8103, false);
    run(0x8112, false);
    run(0x8122, false);
    run(0x6030, false);
    return 0;
}
'''
    binary = tmp_path / "neo-usb-role"
    subprocess.run([
        "cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter",
        *["-D" + flag for flag in cfg], "-DEXPECT_PRESERVE=" + str(int(preserve)),
        "-x", "c", "-", "-o", str(binary),
    ], input=harness, text=True, check=True)
    subprocess.run([str(binary)], check=True)
