"""Procedural pixel-art textures of the Royal Lion Ship (royal_lion_ship): a 512x512 atlas of the hull, the
fittings and the rooms (royal_lion_ship.png) and a 512x512 atlas of the sails, the jibs and the pennants
(royal_lion_ship_sails.png), so that the gold lions keep their resolution.

Colours of the references (docs/RoyalLion_PLAN.md): a dark brown wooden hull with royal blue strakes and gold
trims (gilded rails and wales, gold scrollwork), royal blue heater shields bearing a gold rampant lion, royal
blue sails made of blocky cloths with wide gold borders and a big gold rampant lion on the courses, blue and gold
swallow-tailed pennants, a blue slate roof with gold ridges on the stern castle, arched lit windows in gold
frames, a blue and white striped awning with a scalloped edge, lanterns; inside, dark panelling with a gold rail
(the cabins), plank floors and beams, the plain planks of the lower deck.

Every region is (u, v, w, h); REGIONS and SAIL_REGIONS are shared with tools/generate_royal_lion.py.
"""
import math
import random

from PIL import Image, ImageDraw

from galley_texture import _jitter, _rgb, paint_lamp_glass
import corsair_texture as ct
import frigate_texture as ftx

SIZE = 512
SAIL_SIZE = 512

REGIONS = dict(ftx.REGIONS)
REGIONS.update({
    # the hull of the Royal Lion: dark brown planking, royal blue strakes (blocky, the voxel blue of the references)
    "hull_blue":    (0, 0, 64, 32),      # royal blue planks (bulwarks, the forecastle and castle sides)
    "hull_blue2":   (64, 0, 64, 32),
    "hull_brown":   (192, 0, 64, 32),    # below the water
    "strake_lo":    (192, 64, 64, 32),   # the dark brown strakes above the water (a mosaic of blocks)
    "strake_mid":   (448, 112, 64, 32),  # royal blue strake (lower blue band, with the lit ports)
    "strake_hi":    (384, 128, 64, 32),  # royal blue strake (upper blue band, with the shields)
    "shield":       (0, 208, 48, 56),    # the heater shield: royal blue, gold border, gold rampant lion
    "port_lit":     (48, 208, 16, 16),   # a small square lit port in a gold frame
    "arch_window":  (64, 208, 24, 32),   # an arched lit window (round head) in a gold frame, cut out above the arch
    "arch_window_in": (88, 208, 24, 32),
    "awning":       (112, 208, 64, 32),  # the blue and white striped awning (stripes along u)
    "awning_fringe": (176, 208, 64, 16), # its scalloped edge (cut out under the scallops)
    "roof":         (240, 208, 64, 32),  # blue slates of the stern castle roof
    "roof_ridge":   (176, 224, 64, 16),  # gold ridge and hip boards with scrolls
    "lion_relief":  (304, 208, 48, 48),  # a gold rampant lion on a royal blue panel (stern, bow, figurehead plates)
    "mane":         (352, 208, 32, 32),  # the figurehead's gilded mane (gold locks)
    "lion_face":    (384, 208, 32, 32),  # its face: eyes, open mouth, red tongue
    "banner":       (416, 208, 32, 64),  # a hanging banner (blue, gold border, gold lion, pointed foot)
    "scroll":       (448, 208, 64, 16),  # gold scrollwork band (castle cornices)
    "deck_plank":   (448, 224, 64, 32),
})
for _alias, _src in (("hull_mid", "wood_mid"), ("hull_light", "wood_light"), ("hull_dark", "wood_dark"), ("wood_trim", "wood_dark"),
                     ("wood_honey", "wood_mid"), ("blue_paint", "hull_blue"), ("pilaster", "wood_dark"), ("velvet", "red_paint"),
                     ("cushion", "red_paint"), ("brass", "bronze"), ("organ_wood", "wood_dark"), ("steel", "iron"), ("stripe", "white_paint"),
                     ("patch_wood", "wood_light"), ("repair", "wood_mid"), ("plate", "iron"), ("hearth_stone", "wall_stone"), ("soot", "iron"),
                     ("stone_floor", "wall_stone")):
    REGIONS[_alias] = REGIONS[_src]

# the sails (second texture): one region each, 16 px a block of canvas
SAIL_REGIONS = {
    "main_course":    (0, 0, 272, 192),
    "fore_course":    (272, 0, 240, 176),
    "main_topsail":   (0, 192, 208, 96),
    "fore_topsail":   (208, 192, 192, 88),
    "mizzen_course":  (0, 288, 176, 112),
    "jib":            (176, 288, 128, 160),
    "pennant":        (304, 288, 208, 24),
    "pennant_small":  (304, 312, 160, 20),
    "flag_lion":      (304, 336, 96, 64),   # the royal standard at the stern: blue, gold border, gold lion
}
SAIL_CELLS = {  # (columns, rows) of cloth blocks drawn in each sail region
    "main_course": (17, 12), "fore_course": (15, 11), "main_topsail": (13, 6), "fore_topsail": (12, 5.5),
    "mizzen_course": (11, 7), "jib": (8, 10),
}
LION_SAILS = {"main_course": 0.72, "fore_course": 0.64}   # sail -> height of the lion (fraction of the sail)

_mix, _scale, _planks, _blocks, _fill = ct._mix, ct._scale, ct._planks, ct._blocks, ct._fill
GOLD, GOLD_HI, GOLD_LO, GOLD_DARK = _rgb("e0ae32"), _rgb("f6d466"), _rgb("b8841e"), _rgb("6e4c0e")
ROYAL = ("1f3c9c", "22409f", "1b3690", "2747aa", "1d3a96")


# ---------------------------------------------------------------- the rampant lion
def lion_mask(w, h, facing=-1):
    """Mask (an 'L' image, 0/255) of a heraldic rampant lion facing left (facing -1) or right (+1): rearing on its
    left hind leg, the other raised, both forepaws clawing, a big shaggy mane round the head and down the chest,
    open jaws, the tail curling up behind with a tuft. Drawn from shapes on a 100 x 120 canvas, scaled to w x h."""
    big = Image.new("L", (100, 120), 0)
    d = ImageDraw.Draw(big)

    def blob(cx, cy, r):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)

    def limb(pts, wd):
        d.line(pts, fill=255, width=wd)
        for p in pts:
            blob(p[0], p[1], wd / 2 - 0.5)
    # the body, rising from the hips to the chest
    d.polygon([(30, 44), (56, 36), (66, 58), (72, 80), (54, 92), (44, 72), (34, 58)], fill=255)
    # the mane: a lumpy mass of locks round the head and down the neck
    blob(40, 30, 16)
    for k in range(14):
        a = math.radians(-150 + k * 22)
        blob(40 + 16 * math.cos(a), 30 + 17 * math.sin(a), 6.5)
    blob(44, 48, 12)
    # the muzzle and the open jaws (forward, to the left)
    d.polygon([(30, 17), (14, 21), (8, 27), (12, 30), (28, 31)], fill=255)          # upper jaw and nose
    d.polygon([(28, 36), (14, 35), (11, 40), (18, 43), (30, 42)], fill=255)        # lower jaw
    d.polygon([(10, 30), (22, 32), (12, 35)], fill=0)                               # the open mouth
    blob(25, 23, 2.2)
    d.ellipse((23, 21, 27, 25), fill=0)                                             # the eye
    d.polygon([(42, 8), (47, 0), (51, 9)], fill=255)                                # an ear
    # the forelegs, raised and clawing (paws with three claws each)
    limb([(42, 50), (28, 50), (16, 46)], 9)
    limb([(48, 60), (34, 68), (20, 66)], 9)
    for (px, py) in ((12, 46), (16, 66)):
        for k in range(3):
            d.line([(px + 2, py - 3 + 3 * k), (px - 5, py - 6 + 4 * k)], fill=255, width=3)
    # the hind legs: the left one standing, the right one raised forward
    limb([(62, 84), (56, 98), (60, 108)], 11)
    d.ellipse((42, 108, 64, 119), fill=255)
    limb([(58, 84), (42, 92), (28, 88)], 10)
    for k in range(3):
        d.line([(26, 85 + 3 * k), (19, 82 + 4 * k)], fill=255, width=3)
    # the tail, curling up behind, its tuft
    pts = [(70, 80), (82, 72), (86, 58), (80, 44), (84, 30), (88, 22)]
    limb(pts, 5)
    d.polygon([(82, 26), (84, 12), (92, 4), (96, 14), (94, 26)], fill=255)
    if facing > 0:
        big = big.transpose(Image.FLIP_LEFT_RIGHT)
    return big.resize((w, h), Image.BILINEAR).point(lambda v: 255 if v > 110 else 0)


def lion_detail(w, h, facing=-1):
    """Mask of the carved lines inside the lion (drawn darker on the gold): the locks of the mane, the eye, the line
    of the jaws, the far foreleg and hind leg set apart from the body, the tuft's strands."""
    big = Image.new("L", (100, 120), 0)
    d = ImageDraw.Draw(big)
    for k in range(9):
        a = math.radians(-140 + k * 30)
        d.line([(40 + 7 * math.cos(a), 30 + 7 * math.sin(a)), (40 + 17 * math.cos(a), 30 + 18 * math.sin(a))], fill=255, width=3)
    d.arc((30, 36, 58, 62), 200, 340, fill=255, width=3)               # the mane's lower edge on the chest
    d.ellipse((22, 20, 28, 26), fill=255)                               # the eye
    d.line([(12, 31), (28, 33)], fill=255, width=3)                     # the jaws
    d.line([(44, 56), (34, 64)], fill=255, width=3)                     # the far foreleg
    d.line([(56, 86), (46, 92)], fill=255, width=3)                     # the far hind leg
    d.line([(60, 66), (64, 80)], fill=255, width=3)                     # the haunch
    d.line([(86, 20), (92, 8)], fill=255, width=2)
    if facing > 0:
        big = big.transpose(Image.FLIP_LEFT_RIGHT)
    return big.resize((w, h), Image.BILINEAR).point(lambda v: 255 if v > 90 else 0)


def _outline(mask):
    """Pixels just outside the mask (a dark contour that makes the gold emblem read on the blue)."""
    w, h = mask.size
    src = mask.load()
    out = Image.new("L", (w, h), 0)
    px = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < w and 0 <= Y < h and src[X, Y]:
                    px[x, y] = 255
                    break
    return out


def _gold_at(x, y, cell=1):
    """Gold of a voxel emblem: a light and a shadow tone by block, a few highlights."""
    bx, by = x // cell, y // cell
    k = (bx * 7 + by * 13) % 5
    c = (GOLD, GOLD_HI, GOLD, GOLD_LO, GOLD)[k]
    return c


# ---------------------------------------------------------------- painters
def _royal_sail(px, region, cols, rows, rng, lion=0.0, tri=None, pennant=False):
    """Royal blue blocky sail: one tone per cloth block (shaded by column: lighter at the belly, darker at the
    leeches), a wide gold border all round with a dark inner line, a thin gold stripe inside the leeches; a big
    gold rampant lion (blocky, the voxel emblem of the references) of `lion` x the sail's height; tri = triangle
    mask (region fractions) for the jibs."""
    u, v, w, h = region
    cw, ch = w / cols, h / rows
    tone = []
    for r in range(int(math.ceil(rows))):
        row = []
        for c in range(cols):
            base = _rgb(rng.choice(ROYAL))
            dx = abs((c + 0.5) / cols - 0.5) * 2
            dy = (r + 0.5) / rows
            k = 1.0 + 0.1 * (1 - dx * dx) - 0.16 * dx * dx - 0.05 * dy
            row.append(_scale(base, k * rng.uniform(0.96, 1.04)))
        tone.append(row)
    mask = None
    if lion:
        lh = int(h * lion)
        lw = int(lh * 100 / 120)
        cell = max(2, int(round(min(cw, ch) / 4)))   # the emblem's blocks: a quarter of a cloth block
        lh, lw = lh // cell * cell, lw // cell * cell
        mask = lion_mask(lw // cell, lh // cell).resize((lw, lh), Image.NEAREST)
        edge = _outline(lion_mask(lw // cell, lh // cell)).resize((lw, lh), Image.NEAREST)
        lines = lion_detail(lw // cell, lh // cell).resize((lw, lh), Image.NEAREST)
        mx, my = (w - lw) // 2, int(h * 0.47 - lh / 2)
    border = max(6, int(round(min(w, h) * 0.06)))
    for y in range(h):
        for x in range(w):
            fx, fy = (x + 0.5) / w, (y + 0.5) / h
            if tri is not None and not ct._tri_inside(tri, fx, fy):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c_, r_ = min(cols - 1, int(x / cw)), min(len(tone) - 1, int(y / ch))
            lx, ly = x - c_ * cw, y - r_ * ch
            c = tone[r_][c_]
            if lx < 1 or ly < 1:
                c = _scale(c, 0.86)
            d = min(x, w - 1 - x, y, h - 1 - y)
            if tri is not None:
                d = min(d, min(int(ct._tri_dist(tri, fx, fy) * w) if hasattr(ct, "_tri_dist") else 99, 99))
            if d < border:
                c = _gold_at(x, y, 4)
                if d in (0, border - 1):
                    c = GOLD_DARK if d == 0 else _scale(GOLD_LO, 0.8)
            elif not pennant and tri is None and border + 5 <= min(x, w - 1 - x) <= border + 7:
                c = _gold_at(x, y, 4)    # the thin gold stripe inside each leech
            if mask is not None and mx <= x < mx + mask.width and my <= y < my + mask.height:
                if mask.getpixel((x - mx, y - my)):
                    c = _gold_at(x - mx, y - my, max(2, cell))
                    if lines.getpixel((x - mx, y - my)):
                        c = _scale(GOLD_LO, 0.72)
                elif edge.getpixel((x - mx, y - my)):
                    c = _rgb("10204e")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    if tri is not None:
        # the gold bolt rope along the jib's three edges
        for y in range(h):
            for x in range(w):
                fx, fy = (x + 0.5) / w, (y + 0.5) / h
                if not ct._tri_inside(tri, fx, fy):
                    continue
                for k, dd in enumerate((1.5, 3.5, 6.0)):
                    if not all(ct._tri_inside(tri, fx + dx * dd / w, fy + dy * dd / h) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        px[u + x, v + y] = _jitter((GOLD_DARK, GOLD, GOLD_HI)[k] if k < 2 else GOLD, rng, 3) + (255,)
                        break


def _pennant(px, region, rng, lion=False):
    """A long swallow-tailed pennant: royal blue, gold border, the fly split in two tails (transparent notch);
    a small gold lion near the hoist."""
    u, v, w, h = region
    m = None
    if lion:
        lh = h - 6
        m = lion_mask(int(lh * 100 / 120), lh, facing=-1)
    for y in range(h):
        for x in range(w):
            fx = x / w
            half = (h / 2) * (1.0 - 0.45 * fx)          # tapering toward the fly
            if abs(y - h / 2 + 0.5) > half:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            if fx > 0.7 and abs(y - h / 2 + 0.5) < (fx - 0.7) / 0.3 * half:
                px[u + x, v + y] = (0, 0, 0, 0)          # the swallow tail
                continue
            c = _scale(_rgb("2142a6"), 1.0 + 0.05 * math.sin(x * 0.4))
            edge = half - abs(y - h / 2 + 0.5)
            if edge < 2.2 or x < 2:
                c = _gold_at(x, y, 2)
            if m is not None and 3 <= x - 4 < m.width + 3 and 0 <= y - 3 < m.height and m.getpixel((min(m.width - 1, max(0, x - 7)), y - 3)):
                c = _gold_at(x, y, 1)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _royal_standard(px, region, rng):
    """The royal standard: royal blue, a gold border, a gold rampant lion, swallow-tailed at the fly."""
    u, v, w, h = region
    lh = int(h * 0.76)
    m = lion_mask(int(lh * 100 / 120), lh, facing=-1)
    mx, my = int(w * 0.34 - m.width / 2), (h - lh) // 2
    for y in range(h):
        for x in range(w):
            fx = x / w
            if fx > 0.76 and abs(y - h / 2 + 0.5) < (fx - 0.76) / 0.24 * (h / 2 - 1):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c = _scale(_rgb("1f3fa0"), 1.0 + 0.05 * math.sin(x * 0.5 + y * 0.3))
            if min(y, h - 1 - y) < 3 or x < 3:
                c = _gold_at(x, y, 2)
            if mx <= x < mx + m.width and my <= y < my + m.height and m.getpixel((x - mx, y - my)):
                c = _gold_at(x, y, 2)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _shield(px, region, rng):
    """The heater shield: a royal blue field with a wide gold border, the gold rampant lion; transparent outside
    the shield's outline (flat top, curved sides meeting in a point)."""
    u, v, w, h = region
    lw = int(w * 0.62)
    lh = int(lw * 120 / 100)
    m = lion_mask(lw, lh, facing=-1)
    e = _outline(m)
    dl = lion_detail(lw, lh, facing=-1)
    mx, my = (w - lw) // 2, int(h * 0.15)

    def inside(x, y, inset):
        fy = (y + 0.5) / h
        half = (w / 2 - inset) if fy < 0.45 else (w / 2 - inset) * math.cos((fy - 0.45) / 0.55 * math.pi / 2) ** 0.7
        return abs(x + 0.5 - w / 2) <= half and inset <= y <= h - 1 - inset * 0.7
    for y in range(h):
        for x in range(w):
            if not inside(x, y, 0):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            if not inside(x, y, 1):
                c = GOLD_DARK
            elif not inside(x, y, 5):
                c = _gold_at(x, y, 3)
            elif not inside(x, y, 6):
                c = _scale(GOLD_LO, 0.7)
            else:
                c = _scale(_rgb(("2045a8", "1d3f9c", "2349ae")[(x // 4 + y // 4) % 3]), 1.0 - 0.15 * (y / h))
                if mx <= x < mx + lw and my <= y < my + lh:
                    if m.getpixel((x - mx, y - my)):
                        c = _scale(GOLD_LO, 0.75) if dl.getpixel((x - mx, y - my)) else _gold_at(x, y, 2)
                    elif e.getpixel((x - mx, y - my)):
                        c = _rgb("0f1f50")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _banner(px, region, rng):
    """A hanging banner: royal blue, gold border, the gold lion, its foot cut to a point."""
    u, v, w, h = region
    lw = int(w * 0.7)
    lh = int(lw * 1.2)
    m = lion_mask(lw, lh, facing=-1)
    mx, my = (w - lw) // 2, int(h * 0.2)
    for y in range(h):
        for x in range(w):
            fy = y / h
            if fy > 0.78 and abs(x + 0.5 - w / 2) > (1 - (fy - 0.78) / 0.22) * w / 2:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c = _scale(_rgb("2044a6"), 1.0 + 0.05 * math.sin(y * 0.5))
            edge = min(x, w - 1 - x, y)
            if fy > 0.78:
                edge = min(edge, (1 - (fy - 0.78) / 0.22) * w / 2 - abs(x + 0.5 - w / 2))
            if edge < 3:
                c = _gold_at(x, y, 2)
            elif mx <= x < mx + lw and my <= y < my + lh and m.getpixel((x - mx, y - my)):
                c = _gold_at(x, y, 2)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _lion_relief(px, region, rng):
    """A gold rampant lion on a royal blue panel framed in gold (the stern emblem, the bow plates)."""
    u, v, w, h = region
    lh = h - 12
    lw = int(lh * 100 / 120)
    m = lion_mask(lw, lh, facing=-1)
    e = _outline(m)
    dl = lion_detail(lw, lh, facing=-1)
    mx, my = (w - lw) // 2, 6
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("1f40a2"), 1.0 + 0.04 * math.sin(x * 0.8 + y * 0.6))
            if min(x, y, w - 1 - x, h - 1 - y) < 3:
                c = _gold_at(x, y, 2)
            elif mx <= x < mx + lw and my <= y < my + lh:
                if m.getpixel((x - mx, y - my)):
                    c = _scale(GOLD_LO, 0.75) if dl.getpixel((x - mx, y - my)) else _gold_at(x, y, 2)
                elif e.getpixel((x - mx, y - my)):
                    c = _rgb("0f1f50")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _port_lit(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            d = min(x, y, w - 1 - x, h - 1 - y)
            if d < 3:
                c = GOLD if d else GOLD_DARK
            else:
                c = _mix(_rgb("ffd27a"), _rgb("f0a23a"), abs(x - w / 2) / w + abs(y - h / 2) / h)
                if x == w // 2 or y == h // 2:
                    c = _rgb("5a3a14")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _arch_window(px, region, rng, lit=True):
    """An arched window: lit amber panes with dark leading under a round head, a gold frame; transparent above
    the arch (the wall shows round it)."""
    u, v, w, h = region
    r = w / 2
    for y in range(h):
        for x in range(w):
            cx, cy = x + 0.5 - r, y + 0.5 - r
            if y < r and cx * cx + cy * cy > r * r:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            dist = (r - math.hypot(cx, cy)) if y < r else min(x + 0.5, w - x - 0.5)
            dist = min(dist, h - y - 0.5)
            if dist < 3:
                c = GOLD if dist >= 1 else GOLD_DARK
            elif lit:
                c = _mix(_rgb("ffd47a"), _rgb("e8902e"), min(1.0, abs(cx) / r * 0.6 + y / h * 0.5))
                if x % 6 == 0 or (y > r and y % 7 == 0) or x == w // 2:
                    c = _rgb("5a3a14")
            else:
                c = _mix(_rgb("8aa4b0"), _rgb("5d6f78"), y / h)
                if x % 6 == 0 or x == w // 2:
                    c = _rgb("3a2a18")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _awning(px, region, rng):
    """Royal blue and white stripes (along u), a thin gold edge line."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            k = (x // 8) % 2
            c = _rgb("2346a8") if k == 0 else _rgb("ece6d6")
            c = _scale(c, 1.0 + 0.05 * math.sin(y * 0.7) - 0.05 * (y > h - 3))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _awning_fringe(px, region, rng):
    """The scalloped edge of the awning: blue and white stripes, rounded tongues with a gold hem (cut out
    between them)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            k = (x // 8) % 2
            t = (x % 8 + 0.5) / 8
            depth = 0.35 + 0.65 * math.sin(math.pi * t) ** 0.6
            if y > depth * h:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c = _rgb("2346a8") if k == 0 else _rgb("ece6d6")
            if y > depth * h - 2:
                c = GOLD
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _roof(px, region, rng):
    """Royal blue slates in staggered rows, lighter edges, dark gaps."""
    u, v, w, h = region
    for y in range(h):
        row = y // 6
        for x in range(w):
            off = 4 if row % 2 else 0
            col = (x + off) // 8
            base = _rgb(("27489f", "2a4fae", "213f92", "2d55b6")[(row * 3 + col * 7) % 4])
            c = _scale(base, 1.0 + 0.06 * (y % 6 == 0) - 0.12 * ((x + off) % 8 == 0) - 0.08 * (y % 6 == 5))
            if (x + off) % 8 == 0 or y % 6 == 5:
                c = _rgb("12234e")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _scroll(px, region, rng):
    """Gold scrollwork band: C scrolls between gold edge lines (castle cornices, the bow, the taffrail)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _mix(GOLD, GOLD_LO, abs(y - h / 2) / (h / 2))
            fx, fy = (x % 16) / 16.0, (y - 2) / max(1, h - 4)
            cx, cy = fx - 0.5, fy - 0.5
            rr = math.hypot(cx, cy * 0.9)
            if 2 <= y <= h - 3 and abs(rr - 0.3) < 0.07 and not (cx > 0.05 and cy < 0):
                c = GOLD_DARK
            if y in (1, h - 2):
                c = GOLD_HI
            if y in (0, h - 1):
                c = GOLD_DARK
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _mane(px, region, rng):
    """Gilded locks of the lion's mane: wavy gold strands with dark grooves."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            s = math.sin(x * 0.7 + math.sin(y * 0.35) * 2.0)
            c = _mix(GOLD_HI, GOLD_LO, 0.5 + 0.5 * s)
            if s < -0.75:
                c = _scale(GOLD_DARK, 1.2)
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)


def _lion_face(px, region, rng):
    """The figurehead's face (front): gold, dark eyes under a heavy brow, a broad nose, the open jaws with a red
    tongue and white fangs."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _mix(GOLD, GOLD_LO, abs(x - w / 2) / w + 0.2 * (y / h))
            fx, fy = x / w, y / h
            if 0.2 < fy < 0.32 and (0.18 < fx < 0.38 or 0.62 < fx < 0.82):
                c = _rgb("2a1a08")                       # the eyes
            elif 0.14 < fy < 0.2 and 0.12 < fx < 0.88:
                c = GOLD_DARK                            # the brow
            elif 0.36 < fy < 0.55 and 0.38 < fx < 0.62:
                c = _scale(GOLD_LO, 0.85)               # the nose
            elif 0.6 < fy < 0.9 and 0.22 < fx < 0.78:
                c = _rgb("4a0e0a")                       # the open mouth
                if fy > 0.72 and 0.35 < fx < 0.65:
                    c = _rgb("c2303a")                   # the tongue
                if (fy < 0.66 or fy > 0.85) and (abs(fx - 0.3) < 0.04 or abs(fx - 0.7) < 0.04):
                    c = _rgb("f0ead8")                   # fangs
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def make_texture(path):
    rng = random.Random(1661)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    R = REGIONS
    # start from the frigate's painters for the shared pieces (fittings, rooms), then repaint the hull
    _planks(px, R["hull_blue"], ROYAL, "0e1d4c", rng, plank_h=4, joints=2, grain=0.05)
    _planks(px, R["hull_blue2"], ("1d3990", "203f9a", "1a348a", "2443a2"), "0e1d4c", rng, plank_h=4, joints=3, grain=0.06,
            worn=0.04, worn_col="4a5a8a")
    ftx._gold(px, R["gold"], rng)
    ftx._gold_band(px, R["gold_band"], rng)
    _planks(px, R["hull_brown"], ("3a2416", "321e10", "42291a", "362214"), "160c04", rng, plank_h=4, joints=2, grain=0.05)
    _planks(px, R["wood_dark"], ("5a3a20", "4e321c", "634126", "553620"), "24170c", rng)
    _planks(px, R["wood_mid"], ("7a5130", "6e482a", "855a36", "73502e"), "33210f", rng)
    _planks(px, R["wood_light"], ("9a6a3e", "a87644", "8e6038", "b07e4a"), "4a2f17", rng)
    _planks(px, R["rail"], ("dcaa36", "c4922a"), "7a5a12", rng, plank_h=8, joints=1)
    _planks(px, R["mast"], ("6a4626", "5e3e20", "74502c"), "2e1d0c", rng, plank_h=4, joints=0, grain=0.1)
    _planks(px, R["deck"], ("8a6340", "7d5838", "936a44", "80603e", "6f5234"), "3a2716", rng, plank_h=4, joints=2)
    _planks(px, R["dark_wood"], ("4a2f1a", "40281a"), "1e140a", rng, plank_h=4, joints=1)
    _planks(px, R["cloth_roll"], ("2a49a8", "22409c", "3051b0"), "14286a", rng, plank_h=4, joints=0)
    ftx._carving(px, R["carving"], rng)
    # the strakes: dark brown blocks above the water, two royal blue bands (blocks a block long)
    brown = ("4a2c18",) * 6 + ("3e2414",) * 5 + ("553420",) * 3 + ("2e1a0e",)
    blue = ("1f3c9c",) * 9 + ("2a4bb0",) * 4 + ("3558c0",) * 2 + ("172f80",)
    blue_hi = ("2241a4",) * 9 + ("2e50b6",) * 4 + ("3a60c8",) * 2 + ("1a3488",)
    ftx._strake(px, R["strake_lo"], brown, "1a0e06", rng, grain=0.04, block=16)
    ftx._strake(px, R["strake_mid"], blue, "0b1a48", rng, grain=0.03, block=16)
    ftx._strake(px, R["strake_hi"], blue_hi, "0d1d50", rng, grain=0.03, block=16)
    ftx._strake(px, R["strake_brown"], ("3e2616", "3a2414"), "160c04", rng, grain=0.07)
    ftx._strake(px, R["strake_brown2"], ("46291a", "402617"), "160c04", rng, grain=0.07)
    ftx._castle_panel(px, R["castle_panel"], rng)
    ftx._taffrail(px, R["taffrail"], rng)
    ct._rope(px, R["rope"], "b89a62", "7a6038", rng)
    ct._rope(px, R["rope_light"], "c8aa72", "8a7048", rng)
    ct._rope(px, R["rope_dark"], "a88a56", "6e5634", rng)     # the light hemp ratlines of the references
    _fill(px, R["iron"], "3a3b3e", rng, 6)
    _fill(px, R["bronze"], "b08a2e", rng, 8)
    _fill(px, R["glow"], "ffd27a", rng, 4)
    _fill(px, R["glass"], "b8d4dc", rng, 4)
    _fill(px, R["red_paint"], "a8262a", rng, 6)
    _fill(px, R["white_paint"], "ece8dc", rng, 5)
    _fill(px, R["navy"], "17244c", rng, 4)
    _fill(px, R["end_grain"], "8a6a42", rng, 10)
    _fill(px, R["bore"], "141210", rng, 3)
    ftx._cannon_tex(px, R["cannon"], rng)
    u, v, w, h = R["lantern"]
    paint_lamp_glass(px, u, v, w, h)
    ct._window(px, R["glow_window"], rng, lit=True)
    ct._window(px, R["window_in"], rng, lit=False)
    ct._door(px, R["door"], rng)
    ct._grating(px, R["grating"], rng)
    ftx._gunport(px, R["gunport"], rng)
    ftx._gunport_open(px, R["gunport_open"], rng)
    ftx._gunport_lid(px, R["gunport_lid"], rng)
    ftx._tricolour(px, R["flag"], rng)
    ftx._tricolour(px, R["flag_red"], rng, red_cross=True)
    ct._compass(px, R["compass"], rng)
    ct._chart(px, R["chart"], rng)
    ct._books(px, R["books"], rng)
    ct._painting(px, R["painting"], rng)
    ftx._stern_lily(px, R["stern_lily"], rng)
    ftx._cabin_wall(px, R["wall_wood"], rng)
    _planks(px, R["floor"], ("6e4a2a", "634226", "7a5230", "5a3c22"), "2b1b0e", rng, plank_h=8, joints=2)
    ct._ceil(px, R["ceil"], rng)
    _planks(px, R["hold_floor"], ("5e4228", "553b24", "684a2e"), "241810", rng, plank_h=8, joints=3, worn=0.04, worn_col="3a3a30")
    _planks(px, R["hold_wall"], ("4e3420", "5a3c24", "46301c"), "1e140a", rng, plank_h=8, joints=2)
    _blocks(px, R["wall_stone"], ("7f7a72", "8a857c", "736e66"), "3e3b36", rng, bw=16, bh=8)
    ct._carpet(px, R["carpet"], rng, border="c9981f", field="1f3f9e", centre="162c6e")
    ct._rug(px, R["rug"], rng)
    ct._boat(px, R["boat"], rng)
    ct._weave(px, R["sack"], rng, "a98b5e", "8e7349")
    ct._weave(px, R["canvas"], rng, "ab9a76", "9c8a66", period=1)
    _fill(px, R["linen"], "e6dfcc", rng, 4)
    _blocks(px, R["ham"], ("9a4632", "8a3c2a"), "5a2418", rng, bw=8, bh=4)
    _fill(px, R["bedding"], "1f3f9e", rng, 8)
    # the Royal Lion's own pieces
    _shield(px, R["shield"], rng)
    _port_lit(px, R["port_lit"], rng)
    _arch_window(px, R["arch_window"], rng, lit=True)
    _arch_window(px, R["arch_window_in"], rng, lit=False)
    _awning(px, R["awning"], rng)
    _awning_fringe(px, R["awning_fringe"], rng)
    _roof(px, R["roof"], rng)
    _scroll(px, R["roof_ridge"], rng)
    _lion_relief(px, R["lion_relief"], rng)
    _mane(px, R["mane"], rng)
    _lion_face(px, R["lion_face"], rng)
    _banner(px, R["banner"], rng)
    _scroll(px, R["scroll"], rng)
    _planks(px, R["deck_plank"], ("8a6340", "7d5838", "936a44"), "3a2716", rng, plank_h=4, joints=2)
    img.save(path)
    return img


def make_sail_texture(path, tris=None):
    rng = random.Random(1715)
    img = Image.new("RGBA", (SAIL_SIZE, SAIL_SIZE), (0, 0, 0, 0))
    px = img.load()
    for name, (cols, rows) in SAIL_CELLS.items():
        tri = None
        if name == "jib":
            tri = (tris or {}).get(name) or [(0.0, 0.0), (1.0, 0.0), (0.62, 1.0)]
        _royal_sail(px, SAIL_REGIONS[name], cols, rows, rng, lion=LION_SAILS.get(name, 0.0), tri=tri)
    _pennant(px, SAIL_REGIONS["pennant"], rng, lion=True)
    _pennant(px, SAIL_REGIONS["pennant_small"], rng, lion=True)
    _royal_standard(px, SAIL_REGIONS["flag_lion"], rng)
    img.save(path)
    return img


def make_item_icon(path):
    """16x16 icon: the dark hull with its blue band and gold trims, three masts with royal blue square sails
    bordered in gold (a gold mark of the lion on the main course), blue pennants."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    blue, gold, brown = _rgb("2142a6"), _rgb("e0ae32"), _rgb("3e2616")
    sail, mast = _rgb("1f3c9c"), _rgb("5e3e20")
    for x in range(1, 15):
        for y in range(10, 15):
            if y == 14 and (x < 3 or x > 13):
                continue
            c = gold if y in (10, 12) else (brown if y >= 13 else blue)
            px[x, y] = c + (255,)
    for y in range(7, 10):
        for x in range(12, 15):
            px[x, y] = (gold if y == 7 else blue) + (255,)   # the stern castle
    for x in range(0, 3):
        px[x, 9 - x] = mast + (255,)  # bowsprit
    for mx, top in ((4, 2), (8, 0), (12, 3)):
        for y in range(top, 10):
            px[mx, y] = mast + (255,)
    for (x0, x1, y0, y1) in ((2, 6, 3, 8), (6, 10, 2, 8), (10, 14, 4, 7)):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                edge = x in (x0, x1) or y in (y0, y1)
                px[x, y] = (gold if edge else sail) + (255,)
    px[8, 5] = gold + (255,)
    px[7, 4] = gold + (255,)
    px[9, 0] = blue + (255,)
    px[10, 0] = gold + (255,)
    img.save(path)


if __name__ == "__main__":
    import os
    out = os.environ.get("OUT", "/tmp/claude-0/agent_royal_lion")
    os.makedirs(out, exist_ok=True)
    make_texture(os.path.join(out, "royal_lion_ship.png"))
    make_sail_texture(os.path.join(out, "royal_lion_ship_sails.png"))
    make_item_icon(os.path.join(out, "icon.png"))
    lion_mask(100, 120).resize((300, 360), Image.NEAREST).save(os.path.join(out, "lion.png"))
    print("ok")
