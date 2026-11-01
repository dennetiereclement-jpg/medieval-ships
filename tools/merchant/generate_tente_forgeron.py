#!/usr/bin/env python3
"""tente_forgeron — Tente du forgeron / Blacksmith Merchant Tent (reference: scratchpad/ref/tente_forgeron_ref.png).

The shared merchant pavilion (merchantlib.pavilion) in navy blue and beige with the anvil banner, dressed as a
smith's stall: a stone forge with a glowing hearth at the back left, a big black anvil on a stone block at the front,
a sword rack along the left wall and another behind the anvil, helmets, shields, tools and ingots on the shelves and
the counters, barrels and iron-banded crates by the front posts.

Usage:  python3 tools/merchant/generate_tente_forgeron.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merchantlib as ml  # noqa: E402
import props_m2 as pm  # noqa: E402

NAME = "tente_forgeron"
v3 = pm.v3


def build():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="blue")
    pm.add_regions(atlas, "forge")
    root = ml.Bone(NAME)
    L = ml.pavilion(root, atlas, emblem="anvil", flag_corner="back_left", side_banners=0, rug=True, lanterns=2,
                    front_counter=True, back_shelves=True)
    detail = L.detail
    props = ml.Bone("smithy", parent=root)
    decor = ml.Decor()
    hw, hd = L.half_w, L.half_d
    return root, atlas, L, detail, props, decor, hw, hd


def main():
    root, atlas, L, detail, props, decor, hw, hd = build()
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="blue", emblem="anvil"))


if __name__ == "__main__":
    main()
