"""Props of the jeweller's tent (1.21.0): tente_joaillier.

The tent is the gabled market stall of merchantlib.stall (posts with iron bands and gold caps, the purple and beige
roof striped down the slopes, the dagged valance edged in gold) with what this module adds:

  - the roof variants: peak() raises a small pointed pavilion (purple and beige gores, a wooden and gold finial) in
    the middle of the ridge; hip_left() makes the left end of the roof slope down further over the left wall (a
    rounded hip with its own dagged valance, replacing the stall's left end valance);
  - the walls: draped curtains in big harlequin quarters (purple top / beige bottom and the reverse, gold trims) on the
    two sides and the back (purple drapes inside at the back), side curtains tied back near the front posts;
  - the jeweller's goods: black velvet busts with gold necklaces set with rubies, sapphires and emeralds, ring trays,
    a tray of cut gems, jewellery coffers (one open with a necklace), gem crystals, the glass vitrine with the golden
    crown set with rubies, the hanging gold balance, an iron-banded treasure chest, a crate of crystal clusters,
    banners with the gold diamond (merchantlib emblem "diamond") and dagged edges.

    import props_m10 as p10
    p10.add_regions(atlas)                    # before export: the "m10_..." regions + the few borrowed ones
    p10.peak(L), p10.hip_left(L), p10.walls(L)
    p10.bust(bone, name, foot, gem="ruby"), p10.vitrine_crown(...), p10.balance(...), ...

Coordinates: tent-local blocks (y up, +z = the open front). Cubes named "glow..." are drawn full bright (the gems).
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m1 as p1  # noqa: E402
import props_m4 as p4  # noqa: E402
import props_m7 as p7  # noqa: E402

wb = p1.wb
v3, norm, add_cube, beam, loft = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry = ml.ry
_rgb, _mix, _jitter, _scale = ml._rgb, ml._mix, ml._jitter, ml._scale
PURPLE, PURPLE_D, PURPLE_L = ml.COLOURS["purple"]
BEIGE, GOLD, GOLD_D = ml.BEIGE, ml.GOLD, ml.GOLD_DARK
CLEAR = (0, 0, 0, 0)
GEMS = {"ruby": "c41e34", "sapphire": "2448d8", "emerald": "1ea456", "amethyst": "9a3ee0"}


# ================================================================ painters (img = the region, w x h RGBA)
def _harlequin(seed):
    """The curtain walls: two big panels side by side, the left purple above / beige below, the right the reverse
    (harlequin quarters), gold trims between them, a gold hem at the bottom, a dark heading at the top, soft folds."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        split = int(h * 0.46)
        for y in range(h):
            for x in range(w):
                left = x < w // 2
                top = y < split
                c = PURPLE if left == top else BEIGE
                c = _scale(c, 1.0 + 0.12 * math.sin(2 * math.pi * x / 10.0) + 0.03 * ((x + y) % 2))
                if y < 3:
                    c = _scale(c, 0.7)
                if abs(y - split) <= 1 or y >= h - 3 or abs(x - w // 2) <= 0 or x == 0:
                    c = GOLD
                px[x, y] = _jitter(c, rng, 5) + (255,)
    return p


def _drape_purple(seed):
    """The purple drapes inside at the back: deep folds, a gold band low down and a gold fringe at the bottom."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _scale(PURPLE, 0.95 + 0.18 * math.sin(2 * math.pi * x / 8.0))
                if int(h * 0.84) <= y <= int(h * 0.86) or y < 2:
                    c = GOLD
                if y >= h - 3:
                    c = GOLD if x % 2 == 0 else GOLD_D
                px[x, y] = _jitter(c, rng, 5) + (255,)
    return p


def _banner_dagged(seed):
    """The jeweller's banner: purple, a gold border, the gold diamond, the bottom cut in three pointed dags edged in
    gold (cut-out)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        body = int(h * 0.8)
        for y in range(h):
            for x in range(w):
                c = _scale(PURPLE, 1.0 + 0.04 * ((x + y) % 2))
                e = min(x, w - 1 - x, y)
                if e < 3:
                    c = GOLD
                elif e < 5:
                    c = PURPLE_D
                if y >= body:
                    lx = (x + 0.5) / w * 3.0
                    tri = 1.0 - abs(2.0 * (lx % 1.0) - 1.0)
                    bottom = body + (h - 2 - body) * tri
                    if y > bottom:
                        px[x, y] = CLEAR
                        continue
                    if y > bottom - 3 or x < 3 or x >= w - 3:
                        c = GOLD
                px[x, y] = _jitter(c, rng, 6) + (255,)
        # a gold band above the dags
        for x in range(3, w - 3):
            for y in (body - 4, body - 3):
                px[x, y] = _jitter(GOLD, rng, 6) + (255,)
        ml._emblem(img, (5, int(h * 0.16), w - 10, w - 10), "diamond", "purple", scale=0.98)
    return p


def _peak(seed):
    """A gore pair of the raised pointed centre: purple left half, beige right half, a dark seam, lighter low down."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = PURPLE if x < w // 2 else BEIGE
                c = _scale(c, 0.88 + 0.16 * y / h)
                if x in (0, w // 2 - 1, w // 2, w - 1):
                    c = _scale(c, 0.72)
                px[x, y] = _jitter(c, rng, 5) + (255,)
    return p


def _noise(base, seed, n=6, sheen=0.0):
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _scale(base, 1.0 + sheen * (1.0 - x / max(1, w - 1)))
                px[x, y] = _jitter(c, rng, n) + (255,)
    return p


def _gem(colour, seed):
    """A cut gem's face: a bright table in the middle, darker facets at the edges, a white sparkle."""
    base = _rgb(colour)

    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                k = 0.7 + 0.22 * min(e, 3) + (0.12 if (x + y) % 3 == 0 else 0.0)
                px[x, y] = _jitter(_scale(base, k), rng, 4) + (255,)
        px[w // 3, h // 3] = (255, 255, 255, 255)
    return p


def _rings(seed):
    """A ring tray seen from above: black velvet, two rows of gold rings set with coloured gems."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                c = _rgb("7a4e28") if e < 2 else _rgb("1c1820")
                px[x, y] = _jitter(c, rng, 4) + (255,)
        cols = [_rgb(c) for c in GEMS.values()] + [_rgb("f0f0f0")]
        k = 0
        for cy in (h // 3, 2 * h // 3 + 1):
            for cx in range(5, w - 3, 6):
                for dy in (-2, -1, 0, 1, 2):
                    for dx in (-2, -1, 0, 1, 2):
                        if 3 <= dx * dx + dy * dy <= 5 and 0 <= cx + dx < w and 0 <= cy + dy < h:
                            px[cx + dx, cy + dy] = GOLD + (255,)
                px[cx, cy - 2] = cols[k % len(cols)] + (255,)
                k += 1
    return p


def _gemtray(seed):
    """A wooden tray of cut gems seen from above: red, green, blue, purple and gold stones on black velvet."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                c = _rgb("8a5a2e") if e < 2 else _rgb("201a24")
                px[x, y] = _jitter(c, rng, 4) + (255,)
        cols = [_rgb(c) for c in GEMS.values()] + [GOLD]
        k = 0
        for cy in range(4, h - 2, 4):
            for cx in range(4, w - 2, 4):
                c = cols[(k * 3 + cy) % len(cols)]
                for dx, dy in ((0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)):
                    px[cx + dx, cy + dy] = _scale(c, 1.15 if (dx, dy) == (0, 0) else 0.9) + (255,)
                px[cx - 1, cy - 1] = (255, 255, 255, 255) if k % 2 == 0 else _scale(c, 1.3) + (255,)
                k += 1
    return p


def _glass(seed):
    """A vitrine pane: clear (cut-out), a thin pale frame and two bright diagonal glints."""
    def p(img):
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = CLEAR
                if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                    px[x, y] = (196, 214, 222, 255)
                elif (x + y) in (w // 2, w // 2 + 1) or (x + y) == w // 2 + 5:
                    px[x, y] = (232, 244, 250, 255)
    return p


def _crown(seed):
    """The golden crown's band (unrolled): a band with red rubies and white pearls, five points with a pearl at
    each tip (cut-out above)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        band = int(h * 0.45)
        n = 5
        for y in range(h):
            for x in range(w):
                lx = (x + 0.5) / w * n
                tri = 1.0 - abs(2.0 * (lx % 1.0) - 1.0)
                top = (h - band) * (1.0 - tri)
                if y < top:
                    px[x, y] = CLEAR
                    continue
                c = _scale(GOLD, 1.12 - 0.3 * (y / h))
                if y == h - 1 or y == h - band:
                    c = GOLD_D
                px[x, y] = _jitter(c, rng, 6) + (255,)
        for k in range(n):
            cx = int((k + 0.5) * w / n)
            px[cx, 0] = (250, 246, 236, 255)
            for dx in (0, 1):
                px[min(w - 1, cx + dx), h - band // 2 - 1] = _rgb("d81c30") + (255,)
                px[min(w - 1, cx + dx), h - band // 2] = _rgb("a01020") + (255,)
            px[int(k * w / n), h - band // 2] = (250, 246, 236, 255)
    return p


def _coffer(seed, top=False, inside=False):
    """A small jewellery coffer: red-brown wood, gold corners and lock (top: the lid); inside: purple velvet with a
    gold necklace and a ruby."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                if inside:
                    c = _scale(PURPLE, 1.0 + 0.06 * ((x + y) % 2))
                else:
                    c = _scale(_rgb("6a2a1a"), 0.9 + 0.1 * ((y // 3) % 2))
                    if min(x, w - 1 - x) < 2 and min(y, h - 1 - y) < 2 or min(x, y, w - 1 - x, h - 1 - y) == 0:
                        c = GOLD
                px[x, y] = _jitter(c, rng, 5) + (255,)
        if inside:
            for k in range(28):
                a = math.pi * k / 27
                x = int(w / 2 + math.cos(a) * w * 0.32)
                y = int(h * 0.25 + math.sin(a) * h * 0.45)
                px[x, y] = GOLD + (255,)
            px[w // 2, int(h * 0.72)] = _rgb("e02038") + (255,)
            px[w // 2, int(h * 0.72) + 1] = _rgb("a01020") + (255,)
        elif not top:
            for y in range(int(h * 0.2), int(h * 0.5)):
                for x in range(w // 2 - 1, w // 2 + 1):
                    px[x, y] = GOLD + (255,)
    return p


def _drawers(seed):
    """A counter's lower front: two dark drawers with iron latches and ring pulls on a plank frame."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _scale(_rgb("5a3a1e"), 0.9 + 0.08 * ((x // 4) % 2))
                if x < 1 or x >= w - 1 or y < 1 or y >= h - 1 or w // 2 - 1 <= x <= w // 2:
                    c = _rgb("2e1c0c")
                px[x, y] = _jitter(c, rng, 5) + (255,)
        for cx in (w // 4, 3 * w // 4):
            for y in range(h // 2 - 2, h // 2 + 2):
                for x in range(cx - 2, cx + 2):
                    px[x, y] = (96, 98, 104, 255)
            px[cx - 1, h // 2 + 2] = (150, 152, 158, 255)
            px[cx, h // 2 + 2] = (150, 152, 158, 255)
    return p


def _p4(name):
    return {n: f for n, w, h, f in p4.REGIONS["barde"]}[name]


def regions():
    """(name, w, h, painter) of every region this tent adds to its atlas."""
    out = [
        ("m10_curtain", 64, 64, _harlequin(1001)),
        ("m10_drape", 32, 64, _drape_purple(1002)),
        ("m10_banner", 48, 112, _banner_dagged(1003)),
        ("m10_peak", 32, 48, _peak(1004)),
        ("m10_velvet", 16, 16, _noise(_rgb("1a161e"), 1005, n=3, sheen=0.35)),
        ("m10_rings", 32, 16, _rings(1006)),
        ("m10_gemtray", 32, 16, _gemtray(1007)),
        ("m10_glass", 16, 16, _glass(1008)),
        ("m10_crown", 32, 8, _crown(1009)),
        ("m10_coffer", 16, 16, _coffer(1010)),
        ("m10_coffer_top", 16, 16, _coffer(1011, top=True)),
        ("m10_coffer_in", 16, 16, _coffer(1012, inside=True)),
        ("m10_drawers", 32, 16, _drawers(1013)),
        ("m10_cushion", 8, 8, _noise(_rgb("6a2a9a"), 1014, n=4)),
        ("m10_valance_short", 64, 32, ml._stall_valance_painter("purple", 2, 1015)),
        ("m4_chest", 32, 16, _p4("m4_chest")),
        ("m4_chest_top", 32, 16, _p4("m4_chest_top")),
        ("iron_dark",) + tuple(p1.PAINTERS["iron_dark"]),
        ("m7_runner", 32, 48, p7.PAINTERS["m7_runner"][2]),
        ("m7_runner_top", 32, 32, p7.PAINTERS["m7_runner_top"][2]),
    ]
    for k, (g, c) in enumerate(GEMS.items()):
        out.append(("m10_" + g, 8, 8, _gem(c, 1020 + k)))
    for k, (g, c) in enumerate((("purple", "9a4ae0"), ("green", "2ac860"), ("red", "e0303e"), ("blue", "3a6ef0"))):
        out.append(("crystal_" + g, 8, 16, p1._ws(p1.wt._crystal, _rgb(c), seed=1030 + k)))
    return out


def add_regions(atlas):
    for name, w, h, painter in regions():
        atlas.add(name, w, h, painter)


# ================================================================ roof and walls
def _roof_y(L, x, z):
    """Height of the stall's roof cloth over (x, z) (merchantlib.stall's roof_pt, without the cloth thickness)."""
    W, D = L.half_w + 0.3, L.half_d + 0.42
    ey = L.eave_y + 0.02
    t = min(1.0, abs(z) / D)
    s = (x + W) / (2 * W)
    return L.ridge_y - (L.ridge_y - ey) * ml._stall_drop(t) - 0.07 * math.sin(math.pi * s) * math.sin(math.pi * t)


def _tri_painter(pts, n, seed, colours=None, dark=0.72):
    """Paints a triangle (pts: apex, base_a, base_b in the region's unit square, y down) cut out of its rectangle,
    in n gores radiating from the apex (alternating colours), a dark seam between them and along the edges."""
    colours = colours or (PURPLE, BEIGE)
    (cx, cy), (ax, ay), (bx, by) = pts

    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                X_, Y_ = (x + 0.5) / w, (y + 0.5) / h
                # barycentric coordinates of the pixel in the triangle
                det = (ay - by) * (cx - bx) + (bx - ax) * (cy - by)
                l1 = ((ay - by) * (X_ - bx) + (bx - ax) * (Y_ - by)) / det
                l2 = ((by - cy) * (X_ - bx) + (cx - bx) * (Y_ - by)) / det
                l3 = 1.0 - l1 - l2
                e = min(l1, l2, l3)
                if e < -0.004:
                    px[x, y] = CLEAR
                    continue
                # where the ray from the apex through the pixel meets the base (0 at base_a, 1 at base_b)
                base = l2 + l3      # l1 = the apex's weight, l2 / l3 = base_a's / base_b's
                sb = l3 / base if base > 1e-6 else 0.5
                k = min(n - 1e-6, max(0.0, sb * n))
                c = colours[int(k) % len(colours)]
                f = 0.88 + 0.16 * base
                if (n > 1 and min(k % 1.0, 1.0 - k % 1.0) < 0.025 / max(base, 0.05)) or e < 0.012:
                    f *= dark
                px[x, y] = _jitter(_scale(c, f), rng, 5) + (255,)
    return p


def tri_plate(bone, atlas, name, apex, a, b, n=2, size=64, seed=0, colours=None, th=0.03):
    """A flat triangle apex-a-b as ONE plate cut out by its own texture (clean straight edges, no stepped strips),
    painted in n gores from the apex; both faces textured. Adds its region "m10_tri_<name>" to the atlas."""
    A, B, C = v3(*a), v3(*b), v3(*apex)
    u = norm(B - A)
    nrm = norm(np.cross(B - A, C - A))
    vv = np.cross(nrm, u)
    pts3 = (C, A, B)
    uv = [(float(np.dot(q - A, u)), float(np.dot(q - A, vv))) for q in pts3]
    u0, u1 = min(q[0] for q in uv), max(q[0] for q in uv)
    v0, v1 = min(q[1] for q in uv), max(q[1] for q in uv)
    W, H = u1 - u0, v1 - v0
    unit = [((q[0] - u0) / W, (v1 - q[1]) / H) for q in uv]
    region = "m10_tri_" + name
    atlas.add(region, size, max(16, int(size * H / W)), _tri_painter(unit, n, seed, colours=colours))
    centre = A + u * ((u0 + u1) / 2) + vv * ((v0 + v1) / 2)
    add_cube(bone, name, centre, np.column_stack([u, vv, nrm]), (W, H, th), {"all": None, "+3": region, "-3": region}, stretch=True,
             u_dir=u, v_dir=-vv)


def peak(L, a=1.2, rise=1.5, cx=0.0):
    """The raised, slightly pointed centre of the roof: a square pavilion peak over the middle of the ridge (four
    triangular faces of two gores each, purple and beige, cut-out plates with clean edges), its front and back feet on
    the slopes, a gold collar, a wooden finial with gold knob and spire. Returns the apex."""
    shell, det = L.shell, L.detail
    apex = v3(cx, L.ridge_y + rise, 0.0)
    yb = _roof_y(L, cx, a) + 0.03
    c = [v3(cx - a, yb, a), v3(cx + a, yb, a), v3(cx + a, yb, -a), v3(cx - a, yb, -a)]
    for k in range(4):
        tri_plate(shell, L.atlas, "peak_%d" % k, apex, c[k], c[(k + 1) % 4], n=2, seed=1040 + k)
    add_cube(shell, "peak_collar", apex - UP * 0.05, ry(math.pi / 4), (0.2, 0.12, 0.2), "gold")
    beam(shell, "peak_finial", apex, apex + UP * 0.38, 0.09, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    add_cube(shell, "peak_knob", apex + UP * 0.45, ry(math.pi / 4), (0.15, 0.15, 0.15), "gold")
    beam(det, "peak_spire", apex + UP * 0.5, apex + UP * 0.86, 0.045, "gold")
    return apex


def hip_left(L, out=0.75, drop=0.32):
    """The left end of the roof sloping down further over the left wall: a hip triangle from the ridge's left end down
    to `out` blocks beyond the gable and `drop` lower than the eaves, two triangles joining it to the slopes' left
    corners (cut-out plates in the roof's stripes), its own dagged valance (the stall's left end valance is taken
    off)."""
    shell = L.shell
    W, D = L.half_w + 0.3, L.half_d + 0.42
    ey = L.eave_y + 0.02
    shell.cubes = [c for c in shell.cubes if not c.name.startswith("valance_2_")]
    top = v3(-W, L.ridge_y + 0.02, 0.0)
    lo_f, lo_b = v3(-W - out, ey - drop, D), v3(-W - out, ey - drop, -D)
    sl_f, sl_b = v3(-W, ey + 0.01, D), v3(-W, ey + 0.01, -D)
    tri_plate(shell, L.atlas, "hip_left", top, lo_f, lo_b, n=5, size=96, seed=1050)
    tri_plate(shell, L.atlas, "hip_front", top, sl_f, lo_f, n=1, size=48, seed=1051, colours=(BEIGE, PURPLE))
    tri_plate(shell, L.atlas, "hip_back", top, lo_b, sl_b, n=1, size=48, seed=1052, colours=(BEIGE, PURPLE))
    vh = 0.55
    for k, (p0, p1, o) in enumerate(((lo_f, lo_b, -X), (sl_f, lo_f, Z), (lo_b, sl_b, -Z))):
        def V(s, t, p0=p0, p1=p1, o=o):
            return p0 + (p1 - p0) * s - UP * (vh * t) + o * (0.02 + 0.05 * t)
        loft(shell, "hip_valance_%d" % k, V, 1, 1, "stall_valance_end" if k == 0 else "m10_valance_short", th=0.025)


def _draped(bone, name, a, b, y0, y1, depth, n_folds, region, nx, both=True, out=None):
    """A draped curtain hanging from a-b (ground points, the top at y1, the bottom at y0) with n_folds soft vertical
    folds of `depth`; out = the side the folds bulge to (default: the normal)."""
    a, b = v3(*a), v3(*b)
    d = b - a
    n = norm(np.cross(d, UP)) if out is None else norm(v3(*out))

    def P(s, t):
        q = a + d * s
        f = depth * math.sin(2 * math.pi * n_folds * s) * (0.55 + 0.45 * t)
        return v3(q[0], y1 + (y0 - y1) * t, q[2]) + n * f
    loft(bone, name, P, nx, 1, region, th=0.025, both=both)


def walls(L, tie_z=None):
    """The closed sides and back: draped harlequin curtains (the back's inside in purple drapes), each side closed
    from the back post to tie_z and its front part a curtain tied back near the front post; thin collision walls on
    the closed parts only (the front stays free)."""
    shell, det = L.shell, L.detail
    hw, hd = L.half_w, L.half_d
    top = L.eave_y - 0.35
    tie_z = hd - 1.15 if tie_z is None else tie_z
    # the back: harlequin outside (faces -z), purple drapes inside (faces +z)
    _draped(shell, "wall_back_out", (-hw, 0, -hd - 0.05), (hw, 0, -hd - 0.05), 0.02, top, 0.05, 4, "m10_curtain", 8, both=False,
            out=(0, 0, -1))
    _draped(shell, "wall_back_in", (hw, 0, -hd + 0.02), (-hw, 0, -hd + 0.02), 0.02, top, 0.06, 6, "m10_drape", 8, both=False,
            out=(0, 0, 1))
    ml.collide((-hw, 0.0, -hd - 0.12, hw, top, -hd + 0.06))
    for k, sx in enumerate((-1, 1)):
        x = sx * hw
        _draped(shell, "wall_side_%d" % k, (x, 0, -hd), (x, 0, tie_z), 0.02, top, 0.06, 3, "m10_curtain", 5, out=(sx, 0, 0))
        ml.collide((x - 0.06, 0.0, -hd, x + 0.06, top, tie_z))
        # the front part tied back near the front post
        p4.curtain(shell, "curtain_tied_%d" % k, (x, top, tie_z), (x, top, hd - 0.28), (x - sx * 0.04, 1.25, hd - 0.42), bottom_y=0.04,
                   region="m10_curtain", nx=3, flare=0.3)
        box(det, "curtain_rod_%d" % k, (x - 0.035, top - 0.02, -hd), (x + 0.035, top + 0.05, hd - 0.2), "wood_dark")


def box(bone, name, lo, hi, region, solid=False, stretch=True):
    return ml.box(bone, name, lo, hi, region, solid=solid, stretch=stretch)


# ================================================================ jewellery
def bust(bone, det, name, foot, gem="ruby", yaw=0.0, s=1.0, side_gems=("sapphire", "emerald")):
    """A black velvet neck bust on a dark wooden foot (facing +z turned by yaw) wearing a gold necklace: a collar
    round the neck, a gold V down the chest, a big pendant gem and two side stones (lit)."""
    f = v3(*foot)
    R = ry(yaw)

    def P(x, y, z):
        return f + R @ (v3(x, y, z) * s)
    vel = {"all": "m10_velvet"}
    add_cube(bone, name + "_foot", P(0, 0.02, 0), R, v3(0.18, 0.04, 0.14) * s, {"all": "wood_dark", "+2": "plank_dark"})
    add_cube(bone, name + "_stem", P(0, 0.09, 0), R, v3(0.045, 0.1, 0.045) * s, vel)
    add_cube(bone, name + "_waist", P(0, 0.2, 0), R, v3(0.16, 0.12, 0.085) * s, vel, stretch=True)
    add_cube(bone, name + "_chest", P(0, 0.31, 0), R, v3(0.24, 0.12, 0.1) * s, vel, stretch=True)
    add_cube(bone, name + "_shoulders", P(0, 0.385, 0), R, v3(0.2, 0.04, 0.085) * s, vel, stretch=True)
    add_cube(bone, name + "_neck", P(0, 0.47, 0), R, v3(0.075, 0.14, 0.07) * s, vel, stretch=True)
    add_cube(det, name + "_neck_top", P(0, 0.545, 0), R, v3(0.085, 0.015, 0.08) * s, "black_iron")
    # the necklace
    zf = 0.052
    add_cube(bone, name + "_collar", P(0, 0.41, 0.0), R, v3(0.095, 0.022, 0.09) * s, "gold")
    for k, sx in enumerate((-1, 1)):
        beam(det, "%s_chain_%d" % (name, k), P(sx * 0.045, 0.405, zf), P(0, 0.315, zf), 0.018 * s, "gold", width=0.012 * s)
    add_cube(bone, "glow_%s_pendant" % name, P(0, 0.29, zf + 0.008), R @ ml.rz(math.pi / 4)[:3, :3], v3(0.045, 0.045, 0.02) * s,
             {"all": "m10_" + gem}, stretch=True)
    for k, (sx, g) in enumerate(zip((-1, 1), side_gems)):
        add_cube(det, "glow_%s_stone_%d" % (name, k), P(sx * 0.03, 0.36, zf + 0.004), R, v3(0.024, 0.024, 0.014) * s, {"all": "m10_" + g},
                 stretch=True)


def ring_tray(bone, name, foot, w=0.28, d=0.17, yaw=0.0):
    """A small wooden tray of gem rings (the rings painted on its black velvet top)."""
    f = v3(*foot)
    add_cube(bone, name, f + UP * 0.02, ry(yaw), (w, 0.04, d), {"all": "wood", "+2": "m10_rings"}, stretch=True, u_dir=ry(yaw) @ X,
             v_dir=ry(yaw) @ Z)


def gem_tray(bone, det, name, foot, w=0.46, d=0.3, yaw=0.0, rng=None):
    """A wooden tray of colourful cut gems: painted stones on its velvet bottom and a few big lit gems lying on it."""
    f = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name, f + UP * 0.025, R, (w, 0.05, d), {"all": "wood", "+2": "m10_gemtray"}, stretch=True, u_dir=R @ X, v_dir=R @ Z)
    rng = rng or random.Random(7)
    for k, g in enumerate(("ruby", "emerald", "sapphire", "amethyst", "ruby")):
        x = (k - 2) * w * 0.18
        z = (0.08 if k % 2 else -0.06) * d / 0.3
        add_cube(det, "glow_%s_gem_%d" % (name, k), f + R @ v3(x, 0.07, z), R @ ry(0.6 * k), (0.05, 0.035, 0.05), {"all": "m10_" + g},
                 stretch=True)


def coffer(bone, det, name, foot, w=0.24, h=0.15, d=0.17, yaw=0.0, open_=False):
    """A small jewellery coffer (gold corners and lock); open_: the lid tilted back and a necklace on purple velvet
    inside."""
    f = v3(*foot)
    R = ry(yaw)
    top = "m10_coffer_in" if open_ else "m10_coffer_top"
    add_cube(bone, name, f + UP * h / 2, R, (w, h, d), {"all": "m10_coffer", "+2": top}, stretch=True, u_dir=R @ X, v_dir=R @ Z)
    if open_:
        lid_n = R @ norm(v3(0, 0.45, 1))
        hinge = f + UP * h + R @ v3(0, 0, -d / 2)
        up = R @ norm(v3(0, 1, -0.45))
        ml.plate(det, name + "_lid", hinge + up * (d / 2), w, d, "m10_coffer_top", normal=lid_n, up=up, th=0.03)
        add_cube(det, "glow_%s_gem" % name, f + UP * (h + 0.01) + R @ v3(0, 0, d * 0.2), R, (0.03, 0.02, 0.03), {"all": "m10_ruby"},
                 stretch=True)


def vitrine_crown(bone, det, name, foot, w=0.6, d=0.48, h=0.5):
    """The glass display case: a wooden base, four corner posts, glass panes on the four sides and the top (cut-out
    glass); inside on a purple cushion the golden crown with five points, pearls and rubies, a purple cap inside.
    Collides (the base and the case)."""
    f = v3(*foot)
    bh = 0.1
    box(bone, name + "_base", f + v3(-w / 2, 0, -d / 2), f + v3(w / 2, bh, d / 2), {"all": "wood_dark", "+2": "plank"})
    box(det, name + "_lid", f + v3(-w / 2 - 0.01, bh + h, -d / 2 - 0.01), f + v3(w / 2 + 0.01, bh + h + 0.035, d / 2 + 0.01),
        {"all": "wood_dark", "+2": "m10_glass", "-2": "m10_glass"})
    for k, (sx, sz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        box(bone, "%s_post_%d" % (name, k), f + v3(sx * w / 2 - 0.02, bh, sz * d / 2 - 0.02), f + v3(sx * w / 2 + 0.02, bh + h, sz * d / 2 + 0.02),
            "gold")
    c = f + UP * (bh + h / 2)
    for k, (n, ww) in enumerate(((Z, w), (-Z, w), (X, d), (-X, d))):
        off = d / 2 if abs(n[2]) > 0.5 else w / 2
        ml.plate(bone, "%s_pane_%d" % (name, k), c + n * off, ww - 0.03, h - 0.01, "m10_glass", normal=n, th=0.008)
    # the cushion, the crown, its cap
    cy = f[1] + bh
    box(bone, name + "_cushion", f + v3(-0.17, bh, -0.15), f + v3(0.17, bh + 0.07, 0.15), "m10_cushion")
    cb = f + UP * (bh + 0.07)
    r = 0.115
    add_cube(bone, name + "_cap", cb + UP * 0.06, EYE, (r * 1.5, 0.11, r * 1.5), "m10_cushion")
    add_cube(det, name + "_cap_cross", cb + UP * 0.135, EYE, (0.03, 0.05, 0.03), "gold")
    for k, a in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "glow_%s_crown_%d" % (name, k), cb + UP * 0.075, ry(a), (2 * r * 0.83, 0.15, 2 * r * 0.83),
                 {"all": "m10_crown", "+2": None, "-2": "gold"}, stretch=True)
    add_cube(det, "glow_%s_ruby" % name, cb + v3(0, 0.05, r * 0.86), EYE, (0.04, 0.04, 0.02), {"all": "m10_ruby"}, stretch=True)
    ml.collide((f[0] - w / 2, f[1], f[2] - d / 2, f[0] + w / 2, cy + h + 0.04, f[2] + d / 2))


def balance(bone, det, name, hook, span=0.62, drop=0.55, pan_drop=0.32, gems=("amethyst", "emerald")):
    """The jeweller's hanging gold balance: a chain from the beam, the pillar with its pointer, the beam with knobs,
    two pans on three-strand chains (a gem on each pan)."""
    h = v3(*hook)
    wb.chain(det, name + "_chain", h, h - UP * (drop - 0.12), link=0.08)
    piv = h - UP * drop
    add_cube(bone, name + "_ring", piv + UP * 0.07, EYE, (0.06, 0.08, 0.03), "gold")
    beam(bone, name + "_beam", piv - X * span / 2, piv + X * span / 2, 0.035, "gold")
    beam(det, name + "_pointer", piv, piv + UP * 0.16, 0.025, "gold")
    for k, sx in enumerate((-1, 1)):
        end = piv + X * sx * span / 2
        add_cube(det, "%s_knob_%d" % (name, k), end, EYE, (0.05, 0.05, 0.05), "gold")
        pan = end - UP * pan_drop
        for j, a in enumerate((0.0, 2.1, 4.2)):
            q = pan + v3(math.cos(a) * 0.1, 0.02, math.sin(a) * 0.1)
            beam(det, "%s_cord_%d_%d" % (name, k, j), end, q, 0.012, "gold")
        ml.octo(bone, "%s_pan_%d" % (name, k), pan - UP * 0.02, 0.12, 0.035, {"all": "gold"})
        add_cube(bone, "glow_%s_gem_%d" % (name, k), pan + UP * 0.04, ry(0.5), (0.06, 0.05, 0.06), {"all": "m10_" + gems[k]}, stretch=True)


def crystals(bone, name, foot, colour, rng, n=4, h=0.3, w=0.07, spread=0.06):
    """A small cluster of lit gem crystals (workshops' crystal_cluster with this tent's crystal_<colour>)."""
    wb.crystal_cluster(bone, name, foot, colour, rng, n=n, h=h, w=w, spread=spread)


def treasure_chest(bone, det, name, foot, size=(1.0, 0.74, 0.64), yaw=0.0):
    """The big iron-banded treasure chest (props_m4.chest) with two more iron bands over the body and the lid; collides."""
    f = v3(*foot)
    p4.chest(bone, det, name, f, size=size, yaw=yaw, solid=True)
    w, hh, d = size
    R = ry(yaw)
    for k, sx in enumerate((-0.32, 0.32)):
        add_cube(det, "%s_band_%d" % (name, k), f + R @ v3(sx * w, hh * 0.5, 0), R, (0.05, hh + 0.02, d + 0.04), "black_iron", stretch=True)
    add_cube(det, name + "_hasp", f + R @ v3(0, hh * 0.66, d / 2 + 0.03), R, (0.12, 0.16, 0.03), "black_iron")


def jeweller_banner(bone, det, name, top, w, h, arm_from=None):
    """A purple banner with dagged gold edges and the gold diamond hanging from a rod (gold knobs) facing +z; arm_from:
    the post point an iron bracket runs from to the rod."""
    t = v3(*top)
    ml.banner(bone, name, t, w, h, normal=(0, 0, 1), region="m10_banner", rod=True, wave=0.03)
    if arm_from is not None:
        a = v3(*arm_from)
        beam(det, name + "_arm", a, t + UP * 0.03 + Z * 0.02, 0.05, "iron")
        beam(det, name + "_strut", a - UP * 0.35, (a + t) / 2 + UP * 0.03, 0.035, "iron")
