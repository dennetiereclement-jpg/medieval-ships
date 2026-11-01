"""Shared texture atlas of the eight carts (carts.png, 256x256), Minecraft-like (16 px per block on the planks).

Wood (posts, beams, wheel felloes), dark wood, planks (beds, floors, fence boards), end grain, rope, iron (tyres,
hubs, hoops), gold trim, white and teal canvas (covers, stretched over a whole cover: seams and hoop shadows),
dark-red planks (the merchant wagon), red/white stripes (the market awning), hay (bales), bark + log end rings,
barrel staves with iron hoops + barrel lid, crate, produce (apples, carrots, cabbages), lantern glass and a glow.

Every region is (u, v, w, h) in pixels; REGIONS is shared by tools/carts/cartlib.py and every cart generator.
The names used by tools/tents/tentlib.py helpers (wood, wood_dark, plank, end_grain, rope, iron, gold, lantern,
crate, barrel, glow) exist here too, so those helpers work unchanged on a cart. Deterministic: run any cart
generator to (re)write it, the eight carts share one file.
"""
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "tents"))
from galley_texture import _rgb, _jitter, _mix, _scale, fine_wood, hammered_iron, twisted_rope, end_grain, paint_lamp_glass  # noqa: E402
import tent_texture as tt  # noqa: E402

SIZE = 256
NAME = "carts.png"

REGIONS = {
    # wood
    "wood":        (0, 0, 64, 16),     # beams, posts, shafts: grain along u
    "wood_dark":   (64, 0, 64, 16),    # weathered dark (chassis, axle, felloes, braces)
    "plank":       (0, 16, 64, 16),    # floor / side boards along u (4 px boards)
    "plank_dark":  (64, 16, 64, 16),
    "red_plank":   (128, 0, 64, 16),   # merchant wagon walls (dark red painted boards)
    "red_roof":    (128, 16, 64, 16),  # merchant wagon roof boards
    "end_grain":   (192, 0, 16, 16),
    "rope":        (208, 0, 16, 16),
    "iron":        (224, 0, 16, 16),
    "gold":        (240, 0, 16, 16),
    "lantern":     (192, 16, 16, 16),  # lit glass (lanterns.convert rebuilds lantern bodies with it)
    "glow":        (208, 16, 16, 16),
    "glass":       (224, 16, 16, 16),  # window glass (lit when named glow_*)
    "red_paint":   (240, 16, 16, 16),
    # cloth, stretched over a whole cover / awning
    "canvas":      (0, 32, 96, 48),    # white canvas cover
    "canvas_teal": (96, 32, 96, 48),   # teal canvas cover
    "stripes":     (192, 32, 64, 48),  # red / white awning, stripes along v
    "trim_gold":   (0, 80, 64, 8),     # gold / yellow cover edge
    "trim_white":  (64, 80, 64, 8),
    # cargo
    "hay":         (0, 88, 32, 32),    # hay bale side
    "hay_top":     (32, 88, 32, 32),
    "bark":        (64, 88, 32, 32),   # log bark (along u)
    "log_end":     (96, 88, 32, 32),   # log end rings
    "barrel":      (128, 88, 32, 32),  # barrel staves + iron hoops (vertical staves)
    "barrel_top":  (160, 88, 32, 32),
    "crate":       (192, 88, 32, 32),
    "sack":        (224, 88, 32, 32),
    "apples":      (0, 120, 32, 32),
    "carrots":     (32, 120, 32, 32),
    "cabbage":     (64, 120, 32, 32),
    "flowers":     (96, 120, 32, 32),
    "cloth_red":   (128, 120, 32, 32),
    "leather":     (160, 120, 32, 32),
    "linen":       (192, 120, 32, 32),
}


def _cover(img, region, base, rng):
    """Canvas cover: fine weave, seams across (between hoops), soft shading and stains."""
    tt._weave(img, region, base, rng, seams=12, patches=1, stains=3, tears=0, seam_dir="v")


def _trim(img, region, base, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 1.08 if y < 2 else (0.78 if y >= h - 2 else 1.0)
            if x % 8 == 0:
                k *= 0.85
            px[u + x, v + y] = _jitter(_scale(base, k), rng, 5) + (255,)


def _hay(img, region, rng, top=False):
    u, v, w, h = region
    px = img.load()
    base = _rgb("c8a748")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter(_scale(base, 0.82 + 0.12 * ((x * 5 + y * 3) % 7) / 6), rng, 10) + (255,)
    for _ in range(70):
        x0, y0, L = rng.randint(0, w - 1), rng.randint(0, h - 1), rng.randint(3, 10)
        c = _scale(base, rng.choice((0.66, 1.18, 1.1)))
        for i in range(L):
            x, y = ((x0 + i) % w, y0) if not top else ((x0 + i // 2) % w, (y0 + i) % h)
            px[u + x, v + y] = c + (255,)
    if not top:  # two binding strings
        for xs in (w // 4, 3 * w // 4):
            for y in range(h):
                px[u + xs, v + y] = _rgb("7a5a2a") + (255,)


def _bark(img, region, rng):
    u, v, w, h = region
    px = img.load()
    base = _rgb("5a4026")
    for y in range(h):
        ridge = 0.85 + 0.25 * abs(math.sin(y * 0.9 + rng.random() * 0.3))
        for x in range(w):
            k = ridge * (0.9 + 0.2 * math.sin(x * 0.35 + y))
            px[u + x, v + y] = _jitter(_scale(base, k), rng, 7) + (255,)
    for _ in range(6):
        x0, y0 = rng.randint(0, w - 3), rng.randint(0, h - 3)
        for dx in range(3):
            px[u + x0 + dx, v + y0] = _rgb("6e7a3a") + (255,)   # a little moss


def _rings(img, region, rng):
    u, v, w, h = region
    px = img.load()
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        for x in range(w):
            r = math.hypot(x - cx, y - cy)
            if r > w / 2 - 2.5:
                c = _rgb("4e3820")                       # bark rim
            else:
                light = _rgb("cfa66a")
                k = 0.85 if int(r) % 3 == 0 else 1.0
                c = _scale(light, k * (0.95 + 0.05 * (r / (w / 2))))
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)


def _barrel(img, region, rng):
    u, v, w, h = region
    fine_wood(img, region, _rgb("94643a"), _rgb("4a3018"), 4, rng, joints=False, knots=0.08, grain=0.1, shade=0.08, vertical=True)
    px = img.load()
    for y in (3, 4, 13, 14, 17, 18, 27, 28):
        for x in range(w):
            px[u + x, v + y] = _jitter(_rgb("3c3c40") if y % 2 else _rgb("56565a"), rng, 5) + (255,)


def _barrel_top(img, region, rng):
    u, v, w, h = region
    fine_wood(img, region, _rgb("9a6a3e"), _rgb("4a3018"), 6, rng, joints=False, knots=0.0, grain=0.1, shade=0.05)
    px = img.load()
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        for x in range(w):
            r = math.hypot(x - cx, y - cy)
            if r > w / 2 - 2:
                px[u + x, v + y] = _jitter(_rgb("3c3c40"), rng, 5) + (255,)
            elif r > w / 2 - 4:
                px[u + x, v + y] = _jitter(_rgb("6a4628"), rng, 5) + (255,)


def _produce(img, region, rng, colors, leaf=None, r=(2.5, 4.0)):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter(_rgb("3a2a1a"), rng, 6) + (255,)
    for _ in range(60):
        cx, cy, rr = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(*r)
        c = rng.choice(colors)
        for y in range(int(cy - rr), int(cy + rr) + 1):
            for x in range(int(cx - rr), int(cx + rr) + 1):
                d = math.hypot(x - cx, y - cy) / rr
                if d < 1 and 0 <= x < w and 0 <= y < h:
                    k = 1.15 - 0.4 * d + (0.15 if (x - cx) < -rr * 0.3 and (y - cy) < -rr * 0.3 else 0)
                    px[u + x, v + y] = _jitter(_scale(c, k), rng, 4) + (255,)
        if leaf and rng.random() < 0.5:
            px[u + int(cx) % w, v + max(0, int(cy - rr)) % h] = leaf + (255,)


def make_texture(path):
    rng = random.Random(2027)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    R = REGIONS
    fine_wood(img, R["wood"], _rgb("a07546"), _rgb("5a3c1e"), 8, rng, joints=False, knots=0.25, grain=0.1, shade=0.07)
    fine_wood(img, R["wood_dark"], _rgb("6e4c2c"), _rgb("36220e"), 8, rng, joints=False, knots=0.2, grain=0.1, shade=0.07)
    fine_wood(img, R["plank"], _rgb("9a7044"), _rgb("4e341a"), 4, rng, joints=True, knots=0.2, grain=0.1, shade=0.08)
    fine_wood(img, R["plank_dark"], _rgb("74502e"), _rgb("3a2410"), 4, rng, joints=True, knots=0.15, grain=0.1, shade=0.08)
    fine_wood(img, R["red_plank"], _rgb("7e2a22"), _rgb("3e100c"), 4, rng, joints=True, knots=0.05, grain=0.08, shade=0.08)
    fine_wood(img, R["red_roof"], _rgb("8e2e24"), _rgb("44140e"), 4, rng, joints=False, knots=0.0, grain=0.07, shade=0.1)
    end_grain(img, R["end_grain"], _rgb("b08656"), _rgb("5e4022"), rng)
    twisted_rope(img, R["rope"], _rgb("c9ad7a"), _rgb("6e5634"), rng)
    hammered_iron(img, R["iron"], _rgb("3c3c40"), rng)
    tt._fill(img, R["gold"], _rgb("d4a83a"), rng, noise=10)
    u, v, w, h = R["lantern"]
    paint_lamp_glass(img.load(), u, v, w, h)
    tt._fill(img, R["glow"], _rgb("ffd27a"), rng, noise=6)
    tt._fill(img, R["glass"], _rgb("f0c870"), rng, noise=8)
    tt._fill(img, R["red_paint"], _rgb("8f2b22"), rng, noise=6)
    _cover(img, R["canvas"], _rgb("e8e0cc"), rng)
    _cover(img, R["canvas_teal"], _rgb("2f8f8a"), rng)
    tt._stripes(img, R["stripes"], [_rgb("b0261e"), _rgb("ece4d4")] * 4, rng, horizontal=False)
    _trim(img, R["trim_gold"], _rgb("d8aa38"), rng)
    _trim(img, R["trim_white"], _rgb("e8e0cc"), rng)
    _hay(img, R["hay"], rng)
    _hay(img, R["hay_top"], rng, top=True)
    _bark(img, R["bark"], rng)
    _rings(img, R["log_end"], rng)
    _barrel(img, R["barrel"], rng)
    _barrel_top(img, R["barrel_top"], rng)
    tt._crate(img, R["crate"], rng)
    tt._weave(img, R["sack"], _rgb("a89060"), rng, seams=0, patches=0, stains=3, tears=1)
    _produce(img, R["apples"], rng, [_rgb("b8261c"), _rgb("c8321e"), _rgb("9a1c14"), _rgb("8aa030")], leaf=_rgb("4a7a20"))
    _produce(img, R["carrots"], rng, [_rgb("e07a1c"), _rgb("d06a14")], leaf=_rgb("4a8a20"), r=(1.5, 3.0))
    _produce(img, R["cabbage"], rng, [_rgb("7aa848"), _rgb("5a8a30"), _rgb("9ac060")], r=(4.0, 6.0))
    _produce(img, R["flowers"], rng, [_rgb("d83a3a"), _rgb("e8c83a"), _rgb("c85ac8"), _rgb("4a8a30"), _rgb("4a8a30")], r=(1.2, 2.2))
    tt._weave(img, R["cloth_red"], _rgb("8f2b22"), rng, seams=0, patches=0, stains=2, tears=0)
    tt._fill(img, R["leather"], _rgb("6e4a2a"), rng, noise=9)
    tt._weave(img, R["linen"], _rgb("e0d6c0"), rng, seams=0, patches=0, stains=2, tears=0)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return img


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/agent_carts/carts.png"
    make_texture(out)
    print("wrote", out)
