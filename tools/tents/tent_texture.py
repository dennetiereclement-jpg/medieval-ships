"""Shared texture atlas of the six tents (tents.png, 256x256): worn beige canvas with seams, patches and
stains, red and dark cloth, torn fringes (transparent holes), post wood, floor planks, rope, pegs, lantern
glass, and the materials of the stand-in furniture (crate, barrel, blanket, linen, straw, sack, parchment).

Every region is (u, v, w, h) in pixels; REGIONS is shared by tools/tents/tentlib.py and every tent generator.
Run any tent generator to (re)write the atlas: it is deterministic, so the six tents share one file.
"""
import math
import os
import random
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from galley_texture import _rgb, _jitter, _mix, _scale, fine_wood, hammered_iron, twisted_rope, end_grain, paint_lamp_glass  # noqa: E402

SIZE = 256
NAME = "tents.png"

REGIONS = {
    # cloth panels, stretched over a whole canvas panel (seams, patches, stains)
    "canvas":      (0, 0, 96, 64),
    "canvas_b":    (96, 0, 96, 64),
    "canvas_red":  (192, 0, 64, 32),
    "canvas_dark": (192, 32, 64, 32),
    # torn edges hanging under the panels (transparent holes, ragged bottom)
    "fringe":      (0, 64, 96, 8),
    "fringe_red":  (96, 64, 64, 8),
    "fringe_dark": (160, 64, 32, 8),
    # wood
    "wood":        (0, 72, 64, 16),    # posts and poles, grain along u
    "wood_dark":   (64, 72, 64, 16),   # weathered, darker (pegs, braces)
    "plank":       (0, 88, 64, 16),    # floor planks along u
    "end_grain":   (128, 72, 16, 16),
    "rope":        (144, 72, 16, 16),
    "peg":         (160, 72, 16, 16),
    "lantern":     (176, 72, 16, 16),
    "iron":        (192, 72, 16, 16),
    "gold":        (208, 72, 16, 16),
    "white":       (224, 72, 16, 16),
    "red_paint":   (240, 72, 16, 16),
    # stand-in furniture and soft things
    "crate":       (0, 104, 32, 32),
    "barrel":      (32, 104, 32, 32),
    "blanket":     (64, 104, 32, 32),
    "linen":       (96, 104, 32, 32),
    "leather":     (128, 104, 32, 32),
    "straw":       (160, 104, 32, 32),
    "stone":       (192, 104, 32, 32),
    "sack":        (224, 104, 32, 32),
    "map":         (0, 136, 32, 32),
    "books":       (32, 136, 32, 32),
    "glass":       (64, 136, 16, 16),
    "fur":         (96, 136, 32, 32),
}

BEIGE = _rgb("c9b48a")
BEIGE_DARK = _rgb("8d7a56")
RED = _rgb("8f2b22")
DARK = _rgb("4a3a2e")


def _weave(img, region, base, rng, seams=16, patches=3, stains=4, tears=2, seam_dir="h", noise=5):
    """Worn cloth: a fine weave, horizontal (or vertical) seams, a few patches of another beige, stains,
    a few dark tears (the holes themselves are on the fringes)."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 1.0 + (0.035 if (x + y) % 2 == 0 else -0.035) * (0.6 if x % 3 else 1.0)
            k += 0.06 * math.sin(x * 0.21 + y * 0.07) * math.sin(y * 0.33)   # soft dirt variation
            px[u + x, v + y] = _jitter(_scale(base, k), rng, noise) + (255,)
    # seams: a double stitched line every `seams` pixels
    if seams:
        n = (h if seam_dir == "h" else w) // seams
        for i in range(1, n + 1):
            s = i * seams - 1
            for a in range(w if seam_dir == "h" else h):
                for off, k in ((0, 0.78), (1, 1.08)):
                    b = s + off
                    if b >= (h if seam_dir == "h" else w):
                        continue
                    x, y = (a, b) if seam_dir == "h" else (b, a)
                    c = px[u + x, v + y][:3]
                    c = _scale(c, k if (a % 3) else k * 0.92)
                    px[u + x, v + y] = c + (255,)
    # patches: rectangles of a slightly different beige, stitched round
    for _ in range(patches):
        pw, ph = rng.randint(8, 18), rng.randint(6, 14)
        x0, y0 = rng.randint(2, w - pw - 2), rng.randint(2, h - ph - 2)
        tone = _scale(base, rng.uniform(0.84, 1.1))
        for y in range(ph):
            for x in range(pw):
                edge = x in (0, pw - 1) or y in (0, ph - 1)
                c = _scale(tone, 0.72) if edge and (x + y) % 2 else _jitter(tone, rng, 4)
                px[u + x0 + x, v + y0 + y] = c + (255,)
    # stains and shadows of old dirt
    for _ in range(stains):
        cx, cy, r = rng.uniform(4, w - 4), rng.uniform(4, h - 4), rng.uniform(3, 7)
        for y in range(max(0, int(cy - r)), min(h, int(cy + r) + 1)):
            for x in range(max(0, int(cx - r)), min(w, int(cx + r) + 1)):
                d = math.hypot(x - cx, (y - cy) * 1.4) / r
                if d < 1:
                    c = px[u + x, v + y][:3]
                    px[u + x, v + y] = _scale(c, 1 - 0.14 * (1 - d)) + (255,)
    # tears: short dark slits
    for _ in range(tears):
        x0, y0, L = rng.randint(4, w - 10), rng.randint(4, h - 4), rng.randint(4, 9)
        for i in range(L):
            x = x0 + i
            y = y0 + int(round(0.6 * math.sin(i)))
            px[u + x, v + y] = _scale(base, 0.45) + (255,)
            if 0 <= y + 1 < h:
                px[u + x, v + y + 1] = _scale(base, 0.62) + (255,)


def _fringe(img, region, base, rng):
    """Torn edge: the upper rows are cloth, then ragged strips hang down with holes between them; the bottom
    row is almost all transparent (the edge is never straight)."""
    u, v, w, h = region
    px = img.load()
    cuts = sorted(rng.sample(range(1, w - 1), max(2, w // 5)))
    depth = {x: rng.randint(2, h - 1) for x in cuts}
    for x in range(w):
        # the depth of the tear closest to this column decides how far the cloth reaches
        reach = h
        for cx, d in depth.items():
            if abs(x - cx) <= 1:
                reach = min(reach, h - d)
        if rng.random() < 0.18:
            reach = min(reach, rng.randint(h // 2, h))
        for y in range(h):
            if y < reach:
                k = 1.0 - 0.05 * (y / h) + (0.03 if (x + y) % 2 == 0 else -0.03)
                c = _jitter(_scale(base, k), rng, 5)
                px[u + x, v + y] = c + (255,)
            else:
                px[u + x, v + y] = (0, 0, 0, 0)
    for x in range(w):
        if rng.random() < 0.3:
            px[u + x, v + h - 1] = (0, 0, 0, 0)


def _fill(img, region, color, rng, noise=8):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter(color, rng, noise) + (255,)


def _crate(img, region, rng):
    u, v, w, h = region
    fine_wood(img, region, _rgb("a37a46"), _rgb("5a3c1e"), 8, rng, joints=False, knots=0.2, grain=0.1, shade=0.06)
    px = img.load()
    dark = _rgb("6a4a28")
    for y in range(h):
        for x in range(w):
            if x < 4 or x >= w - 4 or y < 4 or y >= h - 4:
                px[u + x, v + y] = _jitter(_mix(dark, _rgb("8a6236"), 0.4), rng, 5) + (255,)
            if (x in (1, w - 2) and y in (1, h - 2)):
                px[u + x, v + y] = _rgb("2a2a2a") + (255,)


def _barrel(img, region, rng):
    u, v, w, h = region
    fine_wood(img, region, _rgb("8a5e34"), _rgb("4a3018"), 5, rng, joints=False, knots=0.1, grain=0.1, shade=0.08, vertical=True)
    px = img.load()
    for y in (4, 5, 26, 27):
        for x in range(w):
            px[u + x, v + y] = _jitter(_rgb("3a3a3c"), rng, 6) + (255,)


def _stripes(img, region, stripes, rng, horizontal=True):
    u, v, w, h = region
    px = img.load()
    n = len(stripes)
    for y in range(h):
        for x in range(w):
            i = (y if horizontal else x) * n // (h if horizontal else w)
            k = 1.0 + (0.04 if (x + y) % 2 == 0 else -0.04)
            px[u + x, v + y] = _jitter(_scale(stripes[i], k), rng, 5) + (255,)


def _straw(img, region, rng):
    u, v, w, h = region
    px = img.load()
    base = _rgb("c9a85a")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter(_scale(base, 0.85 + 0.1 * ((x * 7 + y * 3) % 5) / 4), rng, 10) + (255,)
    for _ in range(40):
        x0, y0, L, s = rng.randint(0, w - 1), rng.randint(0, h - 1), rng.randint(3, 9), rng.choice((-1, 0, 1))
        c = _scale(base, rng.choice((0.7, 1.15)))
        for i in range(L):
            x, y = (x0 + i) % w, (y0 + i * s // 3) % h
            px[u + x, v + y] = c + (255,)


def _stone(img, region, rng):
    u, v, w, h = region
    px = img.load()
    base = _rgb("8b8a84")
    for y in range(h):
        for x in range(w):
            k = 0.9 + 0.15 * math.sin(x * 0.5) * math.sin(y * 0.4)
            px[u + x, v + y] = _jitter(_scale(base, k), rng, 7) + (255,)
    for y in range(0, h, 8):
        for x in range(w):
            px[u + x, v + y] = _scale(base, 0.6) + (255,)
    for x in range(0, w, 11):
        for y in range(h):
            if (y // 8) % 2 == 0 and x < w:
                px[u + (x + 5) % w, v + y] = _scale(base, 0.6) + (255,)
            else:
                px[u + x, v + y] = _scale(base, 0.6) + (255,)


def _map(img, region, rng):
    u, v, w, h = region
    px = img.load()
    base = _rgb("d9c89a")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter(_scale(base, 0.92 + 0.08 * math.sin(x * 0.3 + y * 0.2)), rng, 5) + (255,)
    ink = _rgb("5a3a28")
    pts = [(4, 20), (9, 14), (14, 16), (19, 9), (25, 12), (28, 6)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for i in range(12):
            t = i / 11
            px[u + int(x0 + (x1 - x0) * t), v + int(y0 + (y1 - y0) * t)] = ink + (255,)
    for x, y in ((8, 24), (22, 22), (16, 6)):
        for dx in range(3):
            px[u + x + dx, v + y] = _rgb("8f2b22") + (255,)


def _books(img, region, rng):
    u, v, w, h = region
    px = img.load()
    cols = [_rgb(c) for c in ("6b2f22", "2f4a6b", "4a5a2a", "6b5a2a", "3a2a22")]
    x = 0
    while x < w:
        bw = rng.randint(3, 6)
        c = rng.choice(cols)
        for xx in range(x, min(w, x + bw)):
            for y in range(h):
                k = 0.75 if xx == x else 1.0
                if y % 9 == 4:
                    k *= 1.3
                px[u + xx, v + y] = _jitter(_scale(c, k), rng, 6) + (255,)
        x += bw


def make_texture(path):
    rng = random.Random(2026)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    R = REGIONS
    _weave(img, R["canvas"], BEIGE, rng, seams=16, patches=3, stains=5, tears=2)
    _weave(img, R["canvas_b"], _rgb("c4ad82"), rng, seams=16, patches=4, stains=4, tears=3, seam_dir="v")
    _weave(img, R["canvas_red"], RED, rng, seams=8, patches=1, stains=3, tears=1)
    _weave(img, R["canvas_dark"], DARK, rng, seams=8, patches=1, stains=2, tears=1)
    _fringe(img, R["fringe"], BEIGE, rng)
    _fringe(img, R["fringe_red"], RED, rng)
    _fringe(img, R["fringe_dark"], DARK, rng)
    fine_wood(img, R["wood"], _rgb("a87b4a"), _rgb("5e4022"), 8, rng, joints=False, knots=0.25, grain=0.1, shade=0.07)
    fine_wood(img, R["wood_dark"], _rgb("7a5632"), _rgb("3e2814"), 8, rng, joints=False, knots=0.2, grain=0.1, shade=0.07)
    fine_wood(img, R["plank"], _rgb("8e6a40"), _rgb("4a3218"), 4, rng, joints=True, knots=0.2, grain=0.1, shade=0.06)
    end_grain(img, R["end_grain"], _rgb("b08656"), _rgb("5e4022"), rng)
    twisted_rope(img, R["rope"], _rgb("c9ad7a"), _rgb("6e5634"), rng)
    fine_wood(img, R["peg"], _rgb("5a3e22"), _rgb("2e1c0c"), 16, rng, joints=False, knots=0.0, grain=0.08, shade=0.05, vertical=True)
    u, v, w, h = R["lantern"]
    paint_lamp_glass(img.load(), u, v, w, h)
    hammered_iron(img, R["iron"], _rgb("3c3c40"), rng)
    _fill(img, R["gold"], _rgb("c9a24a"), rng, noise=10)
    _fill(img, R["white"], _rgb("ece6d8"), rng, noise=3)
    _fill(img, R["red_paint"], _rgb("8f2b22"), rng, noise=6)
    _crate(img, R["crate"], rng)
    _barrel(img, R["barrel"], rng)
    _stripes(img, R["blanket"], [_rgb("8f2b22"), _rgb("6b4a2e"), _rgb("8f2b22"), _rgb("c9b48a"), _rgb("6b4a2e"), _rgb("8f2b22")], rng)
    _weave(img, R["linen"], _rgb("e0d6c0"), rng, seams=0, patches=0, stains=2, tears=0)
    _fill(img, R["leather"], _rgb("6e4a2a"), rng, noise=9)
    _straw(img, R["straw"], rng)
    _stone(img, R["stone"], rng)
    _weave(img, R["sack"], _rgb("a89060"), rng, seams=0, patches=0, stains=3, tears=1)
    _map(img, R["map"], rng)
    _books(img, R["books"], rng)
    _fill(img, R["glass"], _rgb("b9d4dc"), rng, noise=5)
    _fill(img, R["fur"], _rgb("8a7a66"), rng, noise=14)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return img


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/agent_tents/tents.png"
    make_texture(out)
    print("wrote", out)
