"""Tente du marchand d'armes et d'armures (tente_armurier): red and beige pavilion (merchantlib shell), crossed swords
on the banners, weapon racks (swords, axes, spears) on the left wall and at the back, two plate-armour stands behind
the L-shaped counter, helmets / shields / ingots on the shelves and the counter, the shield with the golden lion
leaning at the front, barrels and crates of the decoration mods by the front posts, the emblem rug.

Run: python3 tools/merchant/generate_tente_armurier.py (MERCHANT_OUT=<file.bbmodel> for a preview only).
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402

NAME = "tente_armurier"
v3, UP, EYE = ml.v3, ml.UP, ml.EYE


# ---------------------------------------------------------------- this tent's regions
def paint_lion_shield(img):
    """Heater shield: iron rim, red field, a golden lion rampant (cut-out outside the shield)."""
    from PIL import ImageDraw, Image
    w, h = img.size
    S = 4
    big = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    W, H = w * S, h * S
    outline = [(0, 0), (W - 1, 0), (W - 1, H * 0.5)]
    for k in range(1, 12):
        t = k / 12
        outline.append((W / 2 + (W / 2 - 1) * math.cos(t * math.pi / 2), H * 0.5 + H * 0.5 * math.sin(t * math.pi / 2) - 1))
    outline += [(W / 2 - (W / 2 - 1) * math.cos(t * math.pi / 2), H * 0.5 + H * 0.5 * math.sin(t * math.pi / 2) - 1)
                for t in [k / 12 for k in range(11, 0, -1)]]
    outline.append((0, H * 0.5))
    d.polygon(outline, fill=(132, 134, 140))
    inner = [(W / 2 + (x - W / 2) * 0.86, H * 0.06 + y * 0.9) for (x, y) in outline]
    d.polygon(inner, fill=(168, 36, 30))
    gold, dark = (236, 184, 60), (150, 96, 20)

    def P(x, y):
        return (x * W, y * H)
    # lion rampant facing left: body, hind legs, raised fore paws, head with mane, tail
    body = [P(0.42, 0.34), P(0.62, 0.3), P(0.7, 0.5), P(0.64, 0.66), P(0.48, 0.62), P(0.4, 0.48)]
    d.polygon(body, fill=gold, outline=dark)
    d.ellipse([*P(0.26, 0.16), *P(0.48, 0.36)], fill=gold, outline=dark)          # mane
    d.ellipse([*P(0.22, 0.22), *P(0.34, 0.32)], fill=gold, outline=dark)          # muzzle
    d.line([P(0.4, 0.38), P(0.24, 0.42), P(0.2, 0.36)], fill=gold, width=int(W * 0.07))   # fore paw low
    d.line([P(0.46, 0.33), P(0.3, 0.12), P(0.24, 0.1)], fill=gold, width=int(W * 0.07))   # fore paw raised
    d.line([P(0.6, 0.62), P(0.5, 0.8), P(0.4, 0.84)], fill=gold, width=int(W * 0.08))     # hind leg
    d.line([P(0.66, 0.6), P(0.66, 0.8), P(0.58, 0.88)], fill=gold, width=int(W * 0.08))   # other hind leg
    d.line([P(0.68, 0.5), P(0.82, 0.42), P(0.8, 0.22), P(0.86, 0.16)], fill=gold, width=int(W * 0.05))  # tail
    d.ellipse([*P(0.81, 0.11), *P(0.91, 0.2)], fill=gold)
    d.point([P(0.29, 0.24)], fill=(60, 20, 10))
    img.alpha_composite(big.resize((w, h), Image.LANCZOS))


def paint_armour(img):
    """Plate armour: polished steel, darker lames (horizontal plate edges), rivets."""
    rng = random.Random(7)
    w, h = img.size
    for y in range(h):
        for x in range(w):
            k = 0.82 + 0.3 * math.sin((x / w) * math.pi) - 0.08 * ((y % 8) / 8)
            c = ml._mix((96, 98, 106), (226, 230, 236), k - 0.5)
            if y % 8 == 7:
                c = (70, 72, 78)
            img.putpixel((x, y), ml._jitter(c, rng, 4) + (255,))
    for y in range(3, h, 8):
        for x in (2, w - 3):
            img.putpixel((x, y), (220, 190, 110, 255))


def paint_visor(img):
    """Great helm front: steel with a dark eye slit and breathing holes."""
    rng = random.Random(8)
    w, h = img.size
    for y in range(h):
        for x in range(w):
            c = ml._mix((110, 112, 120), (214, 218, 224), 0.5 + 0.4 * math.sin(x / w * math.pi) - 0.3)
            if 5 <= y <= 6 and 1 <= x <= w - 2:
                c = (20, 20, 24)
            if y >= 9 and x % 3 == 1 and y % 3 == 0 and 3 <= x <= w - 4:
                c = (30, 30, 34)
            if x in (w // 2 - 1, w // 2) and y > 6:
                c = (150, 150, 158)
            img.putpixel((x, y), ml._jitter(c, rng, 4) + (255,))


# ---------------------------------------------------------------- props
def helmet(bone, name, foot, yaw=0.0, s=1.0):
    """A great helm standing on foot (visor towards its front, +z turned by yaw)."""
    foot = v3(*foot)
    R = ml.ry(yaw)
    ml.add_cube(bone, name, foot + UP * 0.15 * s, R, (0.24 * s, 0.3 * s, 0.26 * s), {"all": "armour", "+3": "visor", "+2": "armour"}, stretch=True)
    ml.add_cube(bone, name + "_crest", foot + UP * 0.31 * s, R, (0.04 * s, 0.05 * s, 0.22 * s), "gold")


def round_shield(bone, name, center, normal, r=0.26, region="cloth"):
    """A small round shield (octagonal plate, iron rim, gold boss) facing `normal`."""
    c = v3(*center)
    n = ml.norm(v3(*normal))
    for k, a in enumerate((0.0, math.pi / 4)):
        up = ml.rz(a) @ UP if abs(n[2]) > 0.5 else ml.rx(a) @ UP
        ml.plate(bone, "%s_%d" % (name, k), c, 2 * r * 0.83, 2 * r * 0.83, region, normal=n, up=up, th=0.04, edge="iron")
    ml.add_cube(bone, name + "_boss", c + n * 0.03, EYE, (0.09, 0.09, 0.09), "gold")


def armour_stand(bone, det, name, foot, yaw=0.0):
    """A wooden stand wearing a full plate armour (greaves, tassets, cuirass, pauldrons, arms, great helm)."""
    foot = v3(*foot)
    R = ml.ry(yaw)

    def B(nm, c, size, reg="armour", rot=None, b=None):
        ml.add_cube(b or bone, "%s_%s" % (name, nm), foot + R @ v3(*c), R @ (rot if rot is not None else EYE), size, reg, stretch=True)
    B("base", (0, 0.04, 0), (0.56, 0.08, 0.5), "plank_dark")
    B("post", (0, 0.5, -0.12), (0.08, 0.9, 0.08), "wood_dark")
    for s in (-1, 1):
        B("greave_%d" % s, (s * 0.11, 0.48, 0), (0.18, 0.8, 0.2))
        B("sabaton_%d" % s, (s * 0.1, 0.12, 0.05), (0.16, 0.1, 0.27))
        B("knee_%d" % s, (s * 0.1, 0.56, 0.08), (0.12, 0.12, 0.05), "armour", b=det)
        B("pauldron_%d" % s, (s * 0.34, 1.57, 0), (0.28, 0.2, 0.36), "armour", rot=ml.rz(-s * 0.35))
        B("arm_%d" % s, (s * 0.37, 1.24, 0.0), (0.15, 0.52, 0.17))
        B("gauntlet_%d" % s, (s * 0.38, 0.94, 0.02), (0.13, 0.14, 0.15), "steel", b=det)
    B("tassets", (0, 0.95, 0), (0.5, 0.22, 0.32))
    B("cuirass", (0, 1.3, 0), (0.56, 0.54, 0.34))
    B("plastron", (0, 1.32, 0.07), (0.34, 0.48, 0.34), "armour", rot=ml.ry(math.pi / 4))
    B("gorget", (0, 1.6, 0), (0.24, 0.08, 0.22), "steel")
    B("belt", (0, 1.06, 0.0), (0.5, 0.05, 0.3), "leather", b=det)
    helmet(bone, name + "_helm", foot + R @ v3(0, 1.64, 0), yaw=yaw, s=1.15)
    hx, hz = 0.32, 0.27
    ml.collide((foot[0] - hx, 0.0, foot[2] - hz, foot[0] + hx, 1.95, foot[2] + hz))


def ingot_stack(bone, name, foot, n=3, gold=False, yaw=0.0):
    foot = v3(*foot)
    R = ml.ry(yaw)
    k = 0
    for layer in range(2):
        for i in range(n - layer):
            off = v3((i - (n - layer - 1) / 2) * 0.1, 0.04 + layer * 0.06, 0)
            ml.add_cube(bone, "%s_%d" % (name, k), foot + R @ off, R @ ml.ry(math.pi / 2 * layer), (0.08, 0.05, 0.2),
                        "gold_ingot" if gold and (k % 2 == 0) else "ingot", stretch=True)
            k += 1


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="red")
    atlas.add("lion_shield", 32, 40, paint_lion_shield)
    atlas.add("armour", 32, 32, paint_armour)
    atlas.add("visor", 16, 16, paint_visor)
    root = ml.Bone(NAME)
    L = ml.pavilion(root, atlas, emblem="swords", flag_corner="back_left", side_banners=1, rug=True, lanterns=2, front_counter=True,
                    back_shelves=True)
    shell, det = L.shell, L.detail
    hw, hd, ey = L.half_w, L.half_d, L.eave_y
    D = hd + 0.34
    # the third banner: front right, between the big one and the right post
    ml.banner(shell, "banner_front_right", (2.2, ey + 0.1, D + 0.1), 0.85, 1.45, normal=(0, 0, 1))
    # ---- weapon racks: the left wall (facing the inside) and the back (facing the front)
    ml.weapon_rack(shell, "rack_left", (-hw + 0.45, 0, -1.65), (-hw + 0.45, 0, 1.05), h=1.8, normal=(1, 0, 0),
                   items=("sword", "spear", "axe", "sword", "spear", "axe", "sword"), detail=det)
    ml.weapon_rack(shell, "rack_back", (-1.35, 0, -1.72), (0.55, 0, -1.72), h=1.9, normal=(0, 0, 1),
                   items=("sword", "sword", "spear", "sword", "sword", "spear", "sword"), detail=det)
    # ---- two armour stands behind the counter
    armour_stand(shell, det, "armour_0", (0.8, 0, 0.15))
    armour_stand(shell, det, "armour_1", (1.55, 0, 0.0), yaw=-0.25)
    # ---- the back shelves: helmets, round shields, ingots
    for lvl, (x0, x1, y, zf, zb) in enumerate(L.shelf_levels):
        zc = (zf + zb) / 2
        if lvl == 0:
            for i, x in enumerate((-2.2, -1.5, 1.2, 1.9)):
                ingot_stack(det, "shelf_ingots_%d" % i, (x, y, zc), n=3, gold=(i == 2))
        elif lvl in (1, 2):
            for i, x in enumerate((-2.25, -1.65, 1.0, 1.65, 2.25)):
                if (i + lvl) % 2 == 0:
                    helmet(det, "shelf_helm_%d_%d" % (lvl, i), (x, y, zc + 0.02), s=0.85)
                else:
                    round_shield(det, "shelf_shield_%d_%d" % (lvl, i), (x, y + 0.24, zb + 0.08), (0, 0.25, 1), r=0.22,
                                 region="cloth" if i % 2 else "cloth_blue")
        else:
            for i, x in enumerate((-2.0, 1.4)):
                ml.sword(det, "shelf_sword_%d" % i, (x - 0.5, y + 0.03, zc), up=(1, 0, 0), facing=(0, 1, 0), length=0.95)
    # ---- the counter: helmets, gauntlets, a sword, ingots
    (fx0, fy, fz0, fx1, _, fz1) = L.counter_boxes[0]
    helmet(shell, "counter_helm", (fx0 + 0.35, fy, (fz0 + fz1) / 2), yaw=0.3)
    ml.sword(det, "counter_sword", (fx0 + 0.75, fy + 0.03, fz1 - 0.2), up=(1, 0, -0.1), facing=(0, 1, 0), length=0.9)
    ingot_stack(det, "counter_ingots", (fx1 - 0.55, fy, (fz0 + fz1) / 2 - 0.05), n=3, gold=True, yaw=0.2)
    for s in (0, 1):
        ml.add_cube(det, "counter_gauntlet_%d" % s, (fx0 + 1.2 + s * 0.16, fy + 0.06, fz0 + 0.3), ml.ry(0.3 * s), (0.12, 0.12, 0.18), "steel",
                    stretch=True)
    (sx0, sy, sz0, sx1, _, sz1) = L.counter_boxes[1]
    round_shield(shell, "counter_shield_0", ((sx0 + sx1) / 2, sy + 0.27, sz0 + 0.35), (-1, 0.3, 0), r=0.24, region="cloth")
    helmet(det, "counter_helm_1", ((sx0 + sx1) / 2, sy, sz0 + 1.05), yaw=-1.2, s=0.9)
    ingot_stack(det, "counter_ingots_1", ((sx0 + sx1) / 2, sy, sz1 - 0.3), n=2, yaw=1.4)
    # ---- the lion shield leaning on a small crate at the front left
    ml.crate(shell, "shield_crate", (-1.95, 0, 2.95), size=0.5)
    c = v3(-1.95, 0.44, 3.32)
    n = ml.norm(v3(0, 0.22, 1))
    ml.plate(shell, "lion_shield", c, 0.72, 0.9, "lion_shield", normal=n, th=0.05, edge=None)
    ml.add_cube(det, "lion_shield_back", c - n * 0.04, ml.np.column_stack([ml.X, ml.norm(ml.np.cross(n, ml.X)), n]), (0.6, 0.5, 0.03), "wood_dark")
    # ---- crates and barrels inside (own models), left front
    ml.crate(shell, "crate_in_0", (-2.35, 0, 1.75), size=0.72)
    ml.crate(shell, "crate_in_1", (-2.3, 0.72, 1.72), size=0.55, yaw=0.3, solid=False)
    ml.crate(shell, "crate_in_2", (-1.55, 0, 2.05), size=(0.6, 0.5, 0.6), content="ingot")
    ml.barrel(shell, "barrel_in_0", (2.45, 0, -1.72), r=0.3, h=0.85)
    for i in range(3):
        ml.spear(det, "barrel_spear_%d" % i, (2.45 + 0.08 * math.cos(i * 2.1), 0.5, -1.72 + 0.08 * math.sin(i * 2.1)),
                 up=(0.08 * math.cos(i * 2.1), 1, 0.08 * math.sin(i * 2.1)), length=1.6)
    # ---- furniture of the decoration mods (vanilla alt / stand-in when missing)
    decor = ml.Decor()
    decor.block("landsoficaria:cypress_barrel", -3.75, 0.0, 3.4, facing="front", alt="minecraft:barrel", fallback="barrel")
    decor.block("landsoficaria:cypress_barrel", -3.55, 0.0, 4.45, facing="neg_x", alt="minecraft:barrel", fallback="barrel")
    decor.block("furnish:spruce_crate", 3.55, 0.0, 3.45, facing="front", scale=0.85, fallback="crate")
    decor.block("furnish:spruce_crate", 3.55, 0.85, 3.45, facing="pos_x", scale=0.7, fallback="crate")
    decor.block("furnish:dark_oak_crate", 2.75, 0.0, 3.85, facing="front", scale=0.7, fallback="crate")
    decor.block("farmhouse_decorations:kerosene_lantern", fx1 - 0.2, fy, (fz0 + fz1) / 2, facing="front", glow=True, fallback="lantern",
                solid=False)
    decor.block("furnish:spruce_crate", 2.4, 0.0, -0.98, facing="neg_x", scale=0.7, fallback="crate")
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="red", emblem="swords"))


if __name__ == "__main__":
    main()
