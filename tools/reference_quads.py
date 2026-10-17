#!/usr/bin/env python3
"""Writes the reference quads of a model, computed by tools/preview.py, for the Java
loader test (BbModel must produce exactly the same geometry and UVs).

Usage: python3 tools/reference_quads.py model.bbmodel out.json anim=time,...
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import preview as pv  # noqa: E402


def main():
    model = json.load(open(sys.argv[1]))
    anim = {k: float(v) for k, v in (a.split("=") for a in sys.argv[3].split(","))}
    sizes = [(t.get("uv_width", model["resolution"]["width"]), t.get("uv_height", model["resolution"]["height"]))
             for t in model["textures"]]
    quads = []
    for corners, uvs, glow, tex in pv.build_mesh(model, anim):
        tw, th = sizes[tex]
        quads.append([[round(float(c), 4) for p in corners for c in p],
                      [round(x, 5) for u, v in uvs for x in (u / tw, v / th)], glow, tex])
    with open(sys.argv[2], "w") as f:
        json.dump({"anim": anim, "quads": quads}, f, separators=(",", ":"))
    print(len(quads), "quads")


if __name__ == "__main__":
    main()
