"""Second texture pass of the Royal Lion Ship (1.27.1, the visual upgrade): the two atlases are saved at twice their
UV resolution (32 texels a block; the models keep their 512 x 512 UV space through the textures' uv_width, so no UV
changes), and every region seen from outside is repainted at that resolution with its shading baked in, because the
game lights an entity model almost flat: darker joints and seams, lit top edges and shadowed lower edges on every
block and plank (the voxel relief of the references), ambient darkening under the wales and the rail, per-block
colour variation, grain and a little wear; gold and brass in highlight and shadow bands rather than flat yellow;
warm glowing windows; sails of blocky royal blue cloth with stronger vertical panel seams, a reinforcement band with
reef points, a bolt rope, soft folds and a top-to-bottom gradient; the lions with an outline, a lit and a shadowed
edge and carved lines.

The painters work on numpy arrays (rows = v, columns = u) at K texels a UV pixel and are deterministic (one seeded
generator per region). Regions not repainted here keep the first pass (tools/royal_lion_texture.py) scaled up.
"""
import math
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

K = 2   # texels per UV pixel


# ---------------------------------------------------------------- helpers
def hx(c):
    if isinstance(c, str):
        return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], float)
    return np.array(c, float)


def gen(name, seed=0):
    return np.random.default_rng(zlib.crc32(name.encode()) + seed)


def vnoise(rng, W, H, cx, cy=None):
    """Smooth value noise in [-1, 1], cells cx x cy texels (anisotropic: long streaks with cx >> cy)."""
    cy = cy or cx
    gw, gh = int(math.ceil(W / cx)) + 3, int(math.ceil(H / cy)) + 3
    g = rng.uniform(0, 255, (gh, gw)).astype(np.uint8)
    im = Image.fromarray(g, "L").resize((gw * cx, gh * cy), Image.BILINEAR)
    return np.asarray(im, float)[cy:cy + H, cx:cx + W] / 127.5 - 1.0


def stops(t, pts):
    """Colours (..., 3) of the gradient pts [(t, hex), ...] at t (array)."""
    ts = [p[0] for p in pts]
    cs = np.array([hx(p[1]) for p in pts])
    t = np.asarray(t, float)
    return np.stack([np.interp(t, ts, cs[:, k]) for k in range(3)], axis=-1)


def shifted(m, dy, dx):
    """m moved by (dy, dx), False brought in at the borders."""
    out = np.zeros_like(m)
    H, W = m.shape
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    out[yd, xd] = m[ys, xs]
    return out


def edges(m, d=1):
    """Lit (upper-left) and shadowed (lower-right) rims of a boolean mask, d texels wide."""
    lit = np.zeros_like(m)
    dark = np.zeros_like(m)
    for k in range(1, d + 1):
        lit |= m & (~shifted(m, k, 0) | ~shifted(m, 0, k))
        dark |= m & (~shifted(m, -k, 0) | ~shifted(m, 0, -k))
    return lit & ~dark, dark


def dilate(m, r):
    im = Image.fromarray((m * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(2 * r + 1))
    return np.asarray(im) > 127


def rgba(rgb, alpha=None):
    H, W = rgb.shape[:2]
    a = np.full((H, W, 1), 255.0) if alpha is None else alpha[..., None].astype(float) * 255
    return np.concatenate([np.clip(rgb, 0, 255), a], axis=-1).astype(np.uint8)


def put(atlas, region, arr):
    u, v, w, h = region
    atlas[v * K:(v + h) * K, u * K:(u + w) * K] = arr


# ---------------------------------------------------------------- colours
GOLD_STOPS = [(0.0, "fff4c0"), (0.06, "ffe07e"), (0.2, "ffc848"), (0.5, "f4ac30"), (0.76, "d88c20"), (0.9, "a86618"),
              (1.0, "683c0a")]
GOLD_FLAT = [(0.0, "6a400e"), (0.2, "b07a22"), (0.45, "dca23a"), (0.7, "eebc54"), (0.88, "fad472"), (1.0, "fff0b0")]
NAVY = ("26407e", "223b76", "2a4686", "1f376e", "2d4a8c")       # the deep royal blue of the hull (texel values)
NAVY_JOINT = "0c1634"
SAIL_BLUE = ("233e8a", "264394", "213a84", "2a4898", "203b82", "22408c")
SAIL_JOINT = "0d1a44"
WOOD_LO = ("64401f", "5a381b", "6e4724", "4c2f16", "7a522c", "5e3c1c", "835a33")
WOOD_MID = ("70482a", "653f24", "7b5230", "56371e", "86603a", "6a4426")
WOOD_DARK = ("3a2414", "33200f", "422918", "2c1a0c", "4a2e1a")
JOINT_BROWN = "1a0e06"


def gold_px(shape, rng, base=1.0):
    """Gold of an emblem (H, W, 3): a warm mid gold with a slow sheen."""
    H, W = shape
    sheen = vnoise(rng, W, H, 10, 10)
    return stops(0.42 - 0.16 * sheen, GOLD_STOPS) * base


# ---------------------------------------------------------------- planking, blocks
def p_blocks(w, h, palette, joint, rng, rows=4, blen=32, grain=0.08, ao=(0.0, 0.0), nails=0.25, wear=0.0, jw=2,
             lens=(1, 1, 1, 0.5, 1.5), bevel=1.0, stagger=True):
    """The voxel planking of the references: rows of blocks (blen texels long), one tone each with grain along u, a lit
    top edge, a shadowed foot and right end, dark joints; ao = darkening of the top and the foot of the whole region
    (a band v-stretched on its strake: the shadow under the wale above, the corner over the wale below)."""
    W, H = w * K, h * K
    pal = [hx(c) for c in palette]
    jcol = hx(joint)
    out = np.zeros((H, W, 3))
    gr = vnoise(rng, W, H, 24, 2)
    gr2 = vnoise(rng, W, H, 7, 1)
    fine = rng.uniform(-1, 1, (H, W))
    rh = H / rows
    for r in range(rows):
        y0, y1 = int(round(r * rh)), int(round((r + 1) * rh))
        bh = y1 - y0
        x = -((r % 2) * blen // 2 if stagger else 0) - int(rng.integers(0, max(1, blen // 4)))
        while x < W:
            L = max(6, int(blen * lens[int(rng.integers(len(lens)))]))
            x0, x1 = max(0, x), min(W, x + L)
            if x1 > x0:
                base = pal[int(rng.integers(len(pal)))] * rng.uniform(0.9, 1.08)
                g = 1 + grain * gr[y0:y1, x0:x1] + 0.5 * grain * gr2[y0:y1, x0:x1] + 0.03 * fine[y0:y1, x0:x1]
                ly = np.arange(bh)[:, None]
                lx = np.arange(x0, x1)[None, :] - x
                k = np.ones((bh, x1 - x0))
                k = k + bevel * (0.24 * (ly < 1) + 0.11 * ((ly >= 1) & (ly < 3)) + 0.05 * (lx < 2))
                k = k - bevel * (0.10 * (ly >= bh - jw - 4) + 0.12 * (ly >= bh - jw - 2) + 0.10 * (lx >= L - jw - 2))
                blk = base[None, None, :] * (g * k)[..., None]
                jm = (ly >= bh - jw) | (lx >= L - jw)
                jm = np.broadcast_to(jm, (bh, x1 - x0))
                blk[jm] = jcol * rng.uniform(0.8, 1.15)
                if wear and rng.random() < wear:
                    cx_, cy_ = rng.uniform(0, L), rng.uniform(2, bh - 3)
                    d = ((lx - cx_) / max(3.0, L * 0.25)) ** 2 + ((ly - cy_) / max(1.5, bh * 0.22)) ** 2
                    sc = (d < 1) & ~jm
                    blk[sc] = blk[sc] * 1.14 + 6
                if nails and rng.random() < nails:
                    for nx in (3, L - jw - 5):
                        X = x + nx
                        Y = y0 + bh // 2 - 1
                        if x0 <= X < x1 - 1 and bh > 6:
                            blk[Y - y0:Y - y0 + 2, X - x0:X - x0 + 2] = jcol * 1.3
                            blk[Y - y0, X - x0] = base * 1.25
                out[y0:y1, x0:x1] = blk
            x += L
    if ao[0] or ao[1]:
        v = (np.arange(H) + 0.5) / H
        prof = 1 - ao[0] * np.clip(1 - v / 0.16, 0, 1) ** 1.6 - ao[1] * np.clip((v - 0.86) / 0.14, 0, 1) ** 1.6
        out *= prof[:, None, None]
    return np.clip(out, 0, 255)


def p_planks(w, h, palette, seam, rng, plank=8, grain=0.1, butt=(40, 140), nails=True, worn=0.0, worn_col=None, bevel=1.0):
    """Planks along u (plank texels wide): a tone each, grain streaks, a lit upper edge, a dark caulked seam, butt
    joints with two nail heads, a little wear."""
    W, H = w * K, h * K
    pal = [hx(c) for c in palette]
    sc = hx(seam)
    out = np.zeros((H, W, 3))
    gr = vnoise(rng, W, H, 18, 2)
    knots = vnoise(rng, W, H, 5, 5)
    fine = rng.uniform(-1, 1, (H, W))
    for y0 in range(0, H, plank):
        y1 = min(H, y0 + plank)
        ph = y1 - y0
        x = -int(rng.integers(0, butt[1]))
        while x < W:
            L = int(rng.integers(butt[0], butt[1]))
            x0, x1 = max(0, x), min(W, x + L)
            if x1 > x0:
                base = pal[int(rng.integers(len(pal)))] * rng.uniform(0.92, 1.07)
                ly = np.arange(ph)[:, None]
                lx = np.arange(x0, x1)[None, :] - x
                g = 1 + grain * gr[y0:y1, x0:x1] + 0.03 * fine[y0:y1, x0:x1] - 0.12 * np.clip(knots[y0:y1, x0:x1] - 0.8, 0, 1) * 5
                k = 1 + bevel * (0.16 * (ly < 1) + 0.05 * (ly == 1) - 0.12 * (ly >= ph - 2) - 0.08 * (lx >= L - 2))
                blk = base[None, None, :] * (g * k)[..., None]
                seam_m = np.broadcast_to((ly >= ph - 1) | (lx >= L - 1), blk.shape[:2])
                blk[seam_m] = sc
                if nails and ph >= 6:
                    for nx in (2, L - 4):
                        if 0 <= x + nx - x0 < x1 - x0 - 1:
                            blk[ph // 2 - 1:ph // 2 + 1, x + nx - x0:x + nx - x0 + 1] = sc * 1.2
                if worn and rng.random() < worn:
                    blk[:ph - 1] = blk[:ph - 1] * 0.7 + hx(worn_col) * 0.3
                out[y0:y1, x0:x1] = blk
            x += L
    return np.clip(out, 0, 255)


# ---------------------------------------------------------------- gold
def p_gold_v(w, h, rng, pts=GOLD_STOPS, seam=32, specks=0.004):
    """Gold mapped across the full height of each face (the faces' v range covers the region): a bright lit edge at the
    top, warm gold, a deep ochre shadow at the foot; a slow sheen and the joints of the gilded pieces along u."""
    W, H = w * K, h * K
    v = (np.arange(H) + 0.5) / H
    sheen = vnoise(rng, W, H, 14, 6)
    t = np.clip(v[:, None] - 0.06 * sheen, 0, 1)
    out = stops(t, pts)
    out *= (1 + 0.035 * rng.uniform(-1, 1, (H, W)))[..., None]
    if seam:
        xs = np.arange(W)
        out[:, xs % seam == seam - 1] *= 0.72
        out[:, xs % seam == 0] *= 1.08
    m = rng.random((H, W))
    out[m < specks] *= 0.7
    out[m > 1 - specks] = out[m > 1 - specks] * 0.6 + hx("fff4c8") * 0.4
    return np.clip(out, 0, 255)


def p_iron(w, h, rng):
    """Blackened iron across the full height of each face: a lit upper edge, a dark foot, round rivet heads along the
    middle (lit on their upper left)."""
    W, H = w * K, h * K
    v = (np.arange(H) + 0.5) / H
    out = stops(np.broadcast_to(v[:, None], (H, W)), [(0, "8a8e94"), (0.1, "5a5d62"), (0.5, "3c3e42"), (0.85, "26282b"),
                                                       (1, "141516")])
    out *= (1 + 0.06 * vnoise(rng, W, H, 6, 6))[..., None]
    cy = H // 2
    for x in range(6, W - 3, 16):
        out[cy - 2:cy + 2, x - 2:x + 2] = hx("4a4c50")
        out[cy - 2, x - 2:x + 1] = hx("a4a8ae")
        out[cy - 1, x - 2] = hx("a4a8ae")
        out[cy + 1, x - 1:x + 2] = hx("161718")
    return np.clip(out, 0, 255)


def p_rope(w, h, rng, light, dark):
    """Laid hemp across the full height of each face: diagonal strands (lit crowns, dark lays) over a round profile
    (lit top, shadowed foot), so that the ratlines and stays read as round ropes."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W]
    v = (yy + 0.5) / H
    lay = ((xx + yy * 3 // max(1, H // 6)) % 6)
    base = stops(np.clip(0.15 + 0.55 * v, 0, 1), [(0, light), (0.5, light), (1, dark)])
    out = base * np.choose(lay, [1.12, 1.05, 0.98, 0.9, 0.82, 0.95])[..., None]
    out *= (1.08 - 0.3 * np.clip((v - 0.6) / 0.4, 0, 1))[..., None]
    out *= (1 + 0.04 * rng.uniform(-1, 1, (H, W)))[..., None]
    return np.clip(out, 0, 255)


def p_gold_band(w, h, rng):
    """A flush gold moulding between two strakes (stretched): dark edge lines, a lit upper roll, a shadowed lower roll,
    small bead studs along the middle."""
    W, H = w * K, h * K
    v = (np.arange(H) + 0.5) / H
    pts = [(0.0, "4a2c08"), (0.08, "4a2c08"), (0.1, "fff0b0"), (0.22, "f2c45c"), (0.5, "dca23a"), (0.75, "b47822"),
           (0.9, "7a4c12"), (0.92, "3a2206"), (1.0, "3a2206")]
    out = stops(np.broadcast_to(v[:, None], (H, W)), pts)
    out *= (1 + 0.05 * vnoise(rng, W, H, 12, 4))[..., None]
    for x in range(8, W, 16):
        cy = H // 2
        out[cy - 1:cy + 2, x:x + 3] = hx("8e5a16")
        out[cy - 1, x:x + 2] = hx("fff0b0")
    return np.clip(out, 0, 255)


def p_scroll(w, h, rng, period=32, kind="c"):
    """Carved gold scrollwork in relief (castle cornices, the gallery fascias, the bow): C (or S) scrolls between two
    gold rolls, lit on their upper-left rims and shadowed on their lower-right rims over a dark ground."""
    W, H = w * K, h * K
    big = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(big)
    m0 = max(2, H // 8)
    d.rectangle((0, 0, W, m0), fill=255)
    d.rectangle((0, H - m0 - 1, W, H), fill=255)
    r = (H - 2 * m0) * 0.36
    cy = H / 2
    lw = max(2, int(H * 0.11))
    for x0 in range(-period, W + period, period):
        cx = x0 + period / 2
        if kind == "s":
            d.arc((cx - r - period / 4, cy - r, cx + r - period / 4, cy + r), 180, 360, fill=255, width=lw)
            d.arc((cx - r + period / 4, cy - r, cx + r + period / 4, cy + r), 0, 180, fill=255, width=lw)
        else:
            d.arc((cx - r, cy - r, cx + r, cy + r), 40, 320, fill=255, width=lw)
            d.ellipse((cx + r * 0.25 - lw * 0.7, cy - r * 0.55 - lw * 0.7, cx + r * 0.25 + lw * 0.7, cy - r * 0.55 + lw * 0.7), fill=255)
            d.ellipse((cx + r * 0.25 - lw * 0.7, cy + r * 0.55 - lw * 0.7, cx + r * 0.25 + lw * 0.7, cy + r * 0.55 + lw * 0.7), fill=255)
            d.line((cx + r * 0.9, cy, cx + period / 2, cy), fill=255, width=max(1, lw // 2))
    m = np.asarray(big) > 127
    v = (np.arange(H) + 0.5) / H
    out = np.zeros((H, W, 3))
    out[:] = stops(np.clip(0.5 - 0.15 * vnoise(rng, W, H, 9, 9), 0, 1), GOLD_STOPS)
    ground = stops(np.broadcast_to(v[:, None], (H, W)), [(0, "5a3610"), (0.5, "6e4414"), (1, "3e2408")])
    lit, dark = edges(m, 1)
    out[~m] = ground[~m]
    out[lit] = hx("fbe08c")
    out[dark] = hx("8a5614")
    # the rolls: lit top line, shadowed foot
    out[0] = hx("fff0b0")
    out[-1] = hx("3a2206")
    return np.clip(out, 0, 255)


# ---------------------------------------------------------------- the lion emblems
def lion_layers(lw, lh, cell, facing=-1, bold=0.0, rt=None):
    """Masks (bool, lh x lw texels) of the voxel lion (cells of `cell` texels), its carved lines and its outline."""
    rt = rt or __import__("royal_lion_texture")
    small = rt.lion_mask(max(4, lw // cell), max(4, lh // cell), facing=facing, bold=bold)
    det = rt.lion_detail(max(4, lw // cell), max(4, lh // cell), facing=facing)
    m = np.asarray(small.resize((lw, lh), Image.NEAREST)) > 0
    dl = np.asarray(det.resize((lw, lh), Image.NEAREST)) > 0
    return m, dl


def paint_lion(out, x0, y0, m, dl, rng, cell, outline=2, outline_col="0b1430", shadow=True):
    """Gold voxel lion into out (H, W, 3) at (x0, y0): a dark outline round it, a drop shadow to the lower right, per
    voxel lit and shadowed rims, the silhouette's lit upper-left and dark lower-right edges, carved lines."""
    H, W = out.shape[:2]
    lh, lw = m.shape
    pad = outline + 3
    M = np.zeros((lh + 2 * pad, lw + 2 * pad), bool)
    M[pad:pad + lh, pad:pad + lw] = m
    D = np.zeros_like(M)
    D[pad:pad + lh, pad:pad + lw] = dl & m
    ring = dilate(M, outline) & ~M
    drop = shifted(M, 2, 2) & ~M & ~ring
    Y0, X0 = y0 - pad, x0 - pad
    ys, xs = slice(max(0, Y0), min(H, Y0 + M.shape[0])), slice(max(0, X0), min(W, X0 + M.shape[1]))
    sy, sx = slice(ys.start - Y0, ys.stop - Y0), slice(xs.start - X0, xs.stop - X0)
    sub = out[ys, xs]
    Ms, Ds, Rs, Dr = M[sy, sx], D[sy, sx], ring[sy, sx], drop[sy, sx]
    if shadow:
        sub[Dr] *= 0.55
    sub[Rs] = hx(outline_col)
    yy, xx = np.mgrid[0:Ms.shape[0], 0:Ms.shape[1]]
    yy = yy + sy.start - pad
    xx = xx + sx.start - pad
    # the volume: lit towards the upper left of the emblem, deeper gold towards its foot, a slow sheen
    t = 0.26 + 0.3 * np.clip(yy / max(1, lh), 0, 1) + 0.08 * np.clip(xx / max(1, lw), 0, 1)
    t = t - 0.08 * vnoise(rng, Ms.shape[1], Ms.shape[0], 9, 9)
    g = stops(np.clip(t, 0, 1), GOLD_STOPS)
    # the voxels: a tone each and a faint joint (the blocky emblems of the references, without a grid)
    ly, lx = yy % cell, xx % cell
    k = 1 + 0.06 * (ly == 0) - 0.08 * (ly == cell - 1) - 0.04 * (lx == cell - 1)
    tone = (((yy // cell) * 73856093) ^ ((xx // cell) * 19349663)) % 5
    k = k * np.choose(tone, [1.0, 1.04, 0.97, 1.06, 0.95])
    gl = g * k[..., None]
    lit, dark = edges(Ms, 2)
    lit4, dark4 = edges(Ms, 5)
    gl[dark4 & ~dark] *= 0.86
    gl[lit4 & ~lit] = gl[lit4 & ~lit] * 0.8 + hx("ffe07e") * 0.2
    gl[lit] = gl[lit] * 0.45 + hx("fff4c0") * 0.55
    gl[dark] = gl[dark] * 0.5 + hx("683c0a") * 0.5
    gl[Ds] = hx("7a4a10")
    sub[Ms] = gl[Ms]
    out[ys, xs] = sub
    return out


def heater(w, h, inset):
    """Mask of the heater shield's outline (flat top, curved sides to a point), inset texels in."""
    yy, xx = np.mgrid[0:h, 0:w]
    fy = (yy + 0.5) / h
    half = np.where(fy < 0.45, w / 2 - inset, (w / 2 - inset) * np.clip(np.cos((fy - 0.45) / 0.55 * math.pi / 2), 0, 1) ** 0.7)
    return (np.abs(xx + 0.5 - w / 2) <= half) & (yy >= inset) & (yy <= h - 1 - inset * 0.7)


def p_shield(w, h, rng, rt):
    """The heater shield: a bevelled gold border with four rivets, a royal blue field lit at the top and darker at the
    foot, the embossed gold lion."""
    W, H = w * K, h * K
    m0, m1, m2, m3 = heater(W, H, 0), heater(W, H, 2), heater(W, H, 9), heater(W, H, 11)
    yy, xx = np.mgrid[0:H, 0:W]
    out = np.zeros((H, W, 3))
    # the field: vertical boards of blue, lit upper left, shadow at the foot and under the border
    fld = np.array([hx(c) for c in NAVY])[((xx // 10) + (yy // 40)) % len(NAVY)]
    shade = 1.18 - 0.38 * (yy / H) - 0.1 * (xx / W)
    out[:] = fld * shade[..., None] * (1 + 0.05 * vnoise(rng, W, H, 6, 20))[..., None]
    out[(xx % 10) == 9] *= 0.78
    inner_sh = m3 & ~shifted(m3, 3, 0)
    out[inner_sh] *= 0.6
    # the border: gold, lit on the upper-left half, shadowed on the lower-right, a dark line inside and out
    bord = m1 & ~m2
    g = stops(np.clip(0.3 + 0.45 * (yy / H) + 0.15 * (xx / W - 0.5) - 0.1 * vnoise(rng, W, H, 8, 8), 0, 1), GOLD_STOPS)
    out[bord] = g[bord]
    lit, dark = edges(bord, 1)
    out[lit] = out[lit] * 0.4 + hx("fff0b0") * 0.6
    out[dark] = out[dark] * 0.5 + hx("5e380c") * 0.5
    out[m0 & ~m1] = hx("3e2408")
    out[m2 & ~m3] = hx("2a1a08")
    for fx, fy in ((0.12, 0.08), (0.88, 0.08), (0.2, 0.5), (0.8, 0.5)):
        cx, cy = int(fx * W), int(fy * H)
        for dy in range(-2, 2):
            for dx in range(-2, 2):
                if dx * dx + dy * dy <= 4 and bord[min(H - 1, cy + dy), min(W - 1, cx + dx)]:
                    out[cy + dy, cx + dx] = hx("fff0b0") if dx + dy < -1 else hx("8a5614")
    lw = int(W * 0.64)
    lh = int(lw * 1.2)
    cell = 3
    m, dl = lion_layers(lw, lh, cell, bold=0.6, rt=rt)
    paint_lion(out, (W - lw) // 2, int(H * 0.14), m, dl, rng, cell, outline=2)
    out[~m3 & ~bord & m2] = hx("2a1a08")
    return rgba(out, m0)


def p_banner(w, h, rng, rt):
    """A hanging banner: royal blue cloth with soft vertical folds, darker at the foot, a bevelled gold border, the
    gold lion, its foot cut to a point."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W]
    fy, fx = (yy + 0.5) / H, (xx + 0.5) / W
    pt = 0.78
    half_pt = np.where(fy > pt, (1 - (fy - pt) / (1 - pt)) * W / 2, W / 2)
    inside = np.abs(xx + 0.5 - W / 2) <= half_pt
    edge = np.minimum(np.minimum(xx, W - 1 - xx), yy)
    edge = np.where(fy > pt, np.minimum(edge, half_pt - np.abs(xx + 0.5 - W / 2)), edge)
    fold = 0.1 * np.sin(fx * 2 * math.pi * 2.0 + 0.6) + 0.05 * np.sin(fx * 2 * math.pi * 4.3)
    base = hx("27448a")
    out = base * (1.06 + fold - 0.28 * fy)[..., None] * (1 + 0.04 * vnoise(rng, W, H, 3, 12))[..., None]
    bord = edge < 5
    g = stops(np.clip(0.35 + 0.3 * fy - 0.25 * fold - 0.1 * vnoise(rng, W, H, 6, 6), 0, 1), GOLD_STOPS)
    out[bord] = g[bord]
    out[(edge >= 5) & (edge < 6)] = hx("10183a")
    out[edge < 1] = hx("5e380c")
    lw = int(W * 0.72)
    lh = int(lw * 1.2)
    m, dl = lion_layers(lw, lh, 2, rt=rt)
    paint_lion(out, (W - lw) // 2, int(H * 0.2), m, dl, rng, 2, outline=1)
    out = out * (1 + 0.9 * fold * (1 - bord))[..., None] ** 0.5
    return rgba(out, inside)


def p_lion_panel(w, h, rng, rt, field="27448a", frame=3, fringe=0):
    """A gold rampant lion on a royal blue panel in a bevelled gold frame (the stern and bow plates, the tapestry)."""
    W, H = w * K, h * K
    Hf = H - fringe * K
    yy, xx = np.mgrid[0:H, 0:W]
    out = hx(field) * (1.12 - 0.3 * yy / Hf - 0.08 * xx / W)[..., None] * (1 + 0.04 * vnoise(rng, W, H, 4, 4))[..., None]
    e = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, Hf - 1 - yy))
    bord = e < frame * K
    g = stops(np.clip(0.3 + 0.4 * yy / H - 0.1 * vnoise(rng, W, H, 6, 6), 0, 1), GOLD_STOPS)
    out[bord] = g[bord]
    lit, dark = edges(bord & (yy < Hf), 1)
    out[lit] = out[lit] * 0.4 + hx("fff0b0") * 0.6
    out[dark] = out[dark] * 0.5 + hx("5e380c") * 0.5
    inner = (e >= frame * K) & (e < frame * K + 2)
    out[inner & (yy < Hf)] *= 0.45
    lh = Hf - 2 * frame * K - 8
    lw = int(lh * 100 / 120)
    m, dl = lion_layers(lw, lh, 2, rt=rt)
    paint_lion(out, (W - lw) // 2, frame * K + 4, m, dl, rng, 2, outline=2)
    alpha = np.ones((H, W), bool)
    if fringe:
        fr = yy >= Hf
        out[fr] = stops(np.clip((yy[fr] - Hf) / (H - Hf), 0, 1), [(0, "eebc54"), (1, "8e5a16")])
        alpha[fr & ((xx // 2) % 2 == 1)] = False
    return rgba(out, alpha)


# ---------------------------------------------------------------- the castle
def p_panel(w, h, rng, field, field_joint, frame_kind="gold", boards=10, recess=True):
    """A wall panel stretched on one bay of the castle: a frame (gold, or dark wood with a gold bead), the field of
    vertical boards sunk behind it (shadowed under the upper and inside the left rail, lit along the lower and right
    rails), a small gold rosette at each corner."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W]
    pal = [hx(c) for c in field]
    bi = (xx // boards)
    tone = np.array(pal)[(bi * 7 + 3) % len(pal)] * (0.94 + 0.12 * ((bi * 37) % 5) / 4)[..., None]
    gr = vnoise(rng, W, H, 3, 26)
    out = tone * (1 + 0.07 * gr)[..., None]
    out[(xx % boards) == boards - 1] = hx(field_joint)
    out[(xx % boards) == 0] *= 1.08
    fw = 6 if frame_kind == "gold" else 9
    e_x = np.minimum(xx, W - 1 - xx)
    e_y = np.minimum(yy, H - 1 - yy)
    frame = (e_x < fw) | (e_y < fw - 1)
    # the sunk field: a shadow under the upper rail and inside the left stile, a light line along the lower/right rails
    out[(yy >= fw - 1) & (yy < fw + 4) & ~frame] *= 0.62
    out[(xx >= fw) & (xx < fw + 3) & ~frame] *= 0.74
    out[(yy >= H - fw - 1) & (yy < H - fw + 1) & ~frame] *= 1.2
    out[(xx >= W - fw - 2) & (xx < W - fw) & ~frame] *= 1.12
    # a soft overall light: brighter top, darker foot (the overhang of the cornice, the deck below)
    out *= (1.06 - 0.16 * (yy / H))[..., None]
    if frame_kind == "gold":
        t = np.where(e_y < fw - 1, np.where(yy < H / 2, 0.15 + 0.06 * e_y, 0.85 - 0.06 * e_y), 0.35 + 0.08 * (xx > W / 2) + 0.2 * yy / H)
        g = stops(np.clip(t - 0.06 * vnoise(rng, W, H, 8, 8), 0, 1), GOLD_STOPS)
        out[frame] = g[frame]
        out[(e_x == fw - 1) | (e_y == fw - 2)] = hx("4a2c08")
        out[(e_x == 0) | (e_y == 0)] = hx("5e380c")
    else:
        wood = np.array([hx(c) for c in WOOD_DARK])[(xx // 40 + yy // 40) % len(WOOD_DARK)]
        wood = wood * (1 + 0.08 * vnoise(rng, W, H, 30, 2))[..., None]
        out[frame] = wood[frame] * np.where(yy < H / 2, 1.12, 0.86)[frame][..., None]
        bead = ((e_x == fw - 3) | (e_y == fw - 4)) & ~((e_x < fw - 3) | (e_y < fw - 4))
        bead_t = np.where((yy < H / 2) & (xx < W / 2), 0.15, 0.6)
        out[bead] = stops(bead_t, GOLD_STOPS)[bead]
        out[(e_x == fw - 1) | (e_y == fw - 2)] = hx("1a0e06")
        out[(e_x == 0) | (e_y == 0)] = hx("1a0e06")
    for cx in (fw // 2, W - 1 - fw // 2):
        for cy in (fw // 2, H - 1 - fw // 2):
            out[cy - 2:cy + 2, cx - 2:cx + 2] = hx("dca23a")
            out[cy - 2, cx - 2:cx + 1] = hx("fff0b0")
            out[cy + 1, cx - 1:cx + 2] = hx("8a5614")
    return np.clip(out, 0, 255)


def p_window(w, h, rng, arch=True, lit=True, frame=3):
    """A lit window: a warm glow (a pale core low in the middle, amber, deep orange at the edges) behind dark leading,
    a bevelled gold frame; the round head cut out above the arch."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W]
    r = W / 2
    cx, cy = xx + 0.5 - r, yy + 0.5 - r
    inside = np.ones((H, W), bool)
    if arch:
        inside = ~((yy < r) & (cx * cx + cy * cy > r * r))
        dist = np.where(yy < r, r - np.hypot(cx, cy), np.minimum(xx + 0.5, W - xx - 0.5))
    else:
        dist = np.minimum(np.minimum(xx + 0.5, W - xx - 0.5), yy + 0.5)
    dist = np.minimum(dist, H - yy - 0.5)
    fk = frame * K
    if lit:
        gx = np.abs(cx) / r
        gy = (yy - H * 0.62) / H
        t = np.clip(np.sqrt(gx * gx * 0.8 + gy * gy * 2.2), 0, 1)
        out = stops(t, [(0.0, "fff6cc"), (0.25, "ffd67a"), (0.55, "f4a83e"), (0.85, "c86a1e"), (1.0, "8a3e10")])
        lead = hx("3a220c")
    else:
        out = stops(np.clip(yy / H, 0, 1), [(0, "a8c0c8"), (0.5, "7d939c"), (1, "56666e")])
        lead = hx("2a1e12")
    pane = W / 3
    mull = (np.abs((xx + 0.5) - W / 2) < 1.0) | ((yy > r) & ((yy % int(pane * 1.2)) < 1)) | ((np.abs(cx) > pane * 0.5) & (np.abs(np.abs(cx) - pane * 0.5) < 0.8))
    out[mull] = lead
    hl = shifted(mull, 0, 1) & ~mull
    out[hl] = out[hl] * 1.1 + 10
    g = stops(np.clip(0.2 + 0.5 * yy / H + 0.15 * (xx > W / 2), 0, 1), GOLD_STOPS)
    fr = dist < fk
    out[fr] = g[fr]
    out[(dist >= fk - 1) & (dist < fk)] = hx("4a2c08")
    out[dist < 1] = hx("5e380c")
    out[(dist >= 1) & (dist < 2) & (yy < H * 0.5)] = hx("fff0b0")
    return rgba(out, inside)


def p_port(w, h, rng):
    """A small lit square port: four warm panes behind a dark cross, a gold frame lit at the top-left."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
    t = np.clip(np.hypot((xx - W / 2) / W, (yy - H * 0.6) / H) * 2.2, 0, 1)
    out = stops(t, [(0, "fff6cc"), (0.4, "ffc860"), (0.8, "e08a2a"), (1, "a04e14")])
    cross = (np.abs(xx + 0.5 - W / 2) < 1.1) | (np.abs(yy + 0.5 - H / 2) < 1.1)
    out[cross] = hx("3a220c")
    fr = d < 6
    g = stops(np.clip(0.15 + 0.6 * ((xx + yy) / (W + H)), 0, 1), GOLD_STOPS)
    out[fr] = g[fr]
    out[d == 0] = hx("4a2c08")
    out[d == 5] = hx("3a2206")
    return rgba(out)


def p_lid(w, h, rng):
    """A closed port lid (stretched): dark vertical planks lit at the top, a dark rim, two iron hinge straps with
    nail heads, a ring."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W]
    pal = [hx(c) for c in WOOD_DARK]
    out = np.array(pal)[(xx // 8) % len(pal)] * (1.18 - 0.4 * yy / H)[..., None] * (1 + 0.08 * vnoise(rng, W, H, 2, 12))[..., None]
    out[(xx % 8) == 7] = hx(JOINT_BROWN)
    e = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
    out[e < 2] = hx("140a04")
    out[(e == 2) & (yy < H / 2)] *= 1.3
    for y0 in (int(H * 0.25), int(H * 0.68)):
        strap = (yy >= y0) & (yy < y0 + 3) & (e >= 2)
        out[strap] = hx("3a3c40")
        out[strap & (yy == y0)] = hx("6a6e74")
        for x0 in range(5, W - 4, 9):
            out[y0 + 1, x0] = hx("9a9ea4")
    cx, cy = W // 2, int(H * 0.5)
    ring = (np.abs(np.hypot(xx - cx, yy - cy) - 2.5) < 0.8)
    out[ring] = hx("4a4c50")
    return np.clip(out, 0, 255)


# ---------------------------------------------------------------- roof, awning, figurehead
def p_roof(w, h, rng):
    """Blue slates in staggered rows: each slate shadowed at its top (under the row above), a lit lower lip, dark gaps,
    a tone each, a slow darkening up the roof."""
    W, H = w * K, h * K
    out = np.zeros((H, W, 3))
    sh, sw = 12, 16
    pal = [hx(c) for c in ("2c4a8e", "28437f", "32528f", "243d78", "2f4f96")]
    for r, y0 in enumerate(range(0, H, sh)):
        off = (sw // 2) * (r % 2)
        for x0 in range(-off, W, sw):
            c = pal[int(rng.integers(len(pal)))] * rng.uniform(0.9, 1.1)
            ys, xs = slice(y0, min(H, y0 + sh)), slice(max(0, x0), min(W, x0 + sw))
            ly = np.arange(ys.stop - ys.start)[:, None]
            k = 0.68 + 0.42 * (ly / sh) + 0.2 * (ly >= sh - 3) - 0.1 * (ly >= sh - 1)
            out[ys, xs] = c * k[..., None] * (1 + 0.05 * rng.uniform(-1, 1, (ys.stop - ys.start, xs.stop - xs.start)))[..., None]
            out[ys, max(0, x0):max(0, x0) + 1] = hx("0e1a3c")
        out[min(H - 1, y0 + sh - 1)] = hx("0e1a3c")
    return np.clip(out, 0, 255)


def p_awning(w, h, rng, fringe=False):
    """Royal blue and white stripes (along u) with soft folds (each stripe pair a sag), a gold hem; the fringe cut in
    scallops under it."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W]
    k = (xx // 16) % 2
    blue, white = hx("27448a"), hx("ece4d0")
    out = np.where(k[..., None] == 0, blue, white).astype(float)
    t = (xx % 32) / 32.0
    fold = 0.12 * np.cos(2 * math.pi * t) + 0.04 * np.sin(4 * math.pi * t)
    out *= (1.0 + fold - 0.12 * (yy / H))[..., None]
    out *= (1 + 0.03 * rng.uniform(-1, 1, (H, W)))[..., None]
    seam = (xx % 16) == 0
    out[seam] *= 0.8
    alpha = np.ones((H, W), bool)
    if fringe:
        tt = (xx % 16 + 0.5) / 16
        depth = (0.35 + 0.65 * np.sin(math.pi * tt) ** 0.6) * H
        alpha = yy <= depth
        hem = (yy > depth - 4) & alpha
        out[hem] = stops(np.clip((yy[hem] - depth[hem] + 4) / 4, 0, 1), [(0, "fad472"), (1, "8e5a16")])
    else:
        out[yy >= H - 3] = stops(np.clip((yy[yy >= H - 3] - H + 3) / 3.0, 0, 1), [(0, "fad472"), (1, "8e5a16")])
    return rgba(out, alpha)


def p_mane(w, h, rng):
    """Gilded locks of the figurehead's mane: wavy strands, deep grooves, lit crests."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    s = np.sin(xx * 0.38 + np.sin(yy * 0.18) * 2.2 + 0.6 * vnoise(rng, W, H, 8, 8))
    t = 0.5 - 0.42 * s
    out = stops(np.clip(t, 0, 1), GOLD_STOPS)
    out[s < -0.82] = hx("5e380c")
    return np.clip(out, 0, 255)


def p_lion_face(w, h, rng):
    """The figurehead's face: gold modelled in light (brow, cheeks, muzzle) and shadow (the eye sockets, under the
    brow, round the muzzle), dark eyes with a glint, the open jaws with a red tongue and white fangs."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W]
    fx, fy = (xx + 0.5) / W, (yy + 0.5) / H
    t = 0.32 + 0.35 * np.abs(fx - 0.5) * 2 + 0.25 * fy
    out = stops(np.clip(t, 0, 1), GOLD_STOPS)
    sock = ((fx - 0.28) ** 2 / 0.02 + (fy - 0.27) ** 2 / 0.012 < 1) | ((fx - 0.72) ** 2 / 0.02 + (fy - 0.27) ** 2 / 0.012 < 1)
    out[sock] *= 0.55
    eye = ((fx - 0.28) ** 2 / 0.006 + (fy - 0.27) ** 2 / 0.004 < 1) | ((fx - 0.72) ** 2 / 0.006 + (fy - 0.27) ** 2 / 0.004 < 1)
    out[eye] = hx("2a1408")
    out[eye & (np.abs(fx - 0.25) < 0.03) & (np.abs(fy - 0.25) < 0.03)] = hx("fff0b0")
    out[eye & (np.abs(fx - 0.69) < 0.03) & (np.abs(fy - 0.25) < 0.03)] = hx("fff0b0")
    brow = (fy > 0.13) & (fy < 0.19) & (fx > 0.1) & (fx < 0.9)
    out[brow] = stops(np.full(brow.sum(), 0.08), GOLD_STOPS)
    out[(fy >= 0.19) & (fy < 0.22) & (fx > 0.1) & (fx < 0.9)] *= 0.6
    nose = (fy > 0.34) & (fy < 0.55) & (np.abs(fx - 0.5) < 0.12)
    out[nose] = stops(np.clip(0.15 + 0.6 * (fy[nose] - 0.34) / 0.21, 0, 1), GOLD_STOPS)
    mouth = (fy > 0.6) & (fy < 0.9) & (np.abs(fx - 0.5) < 0.28 - 0.1 * np.abs(fy - 0.75) / 0.15)
    out[mouth] = hx("3a0a08")
    tongue = mouth & (fy > 0.72) & (np.abs(fx - 0.5) < 0.14)
    out[tongue] = stops(np.clip((fy[tongue] - 0.72) / 0.18, 0, 1), [(0, "d84048"), (1, "8a1e24")])
    fang = mouth & ((fy < 0.68) | (fy > 0.84)) & ((np.abs(fx - 0.33) < 0.035) | (np.abs(fx - 0.67) < 0.035))
    out[fang] = hx("f4eedc")
    return np.clip(out, 0, 255)


def p_canvas(w, h, rng, base="e6dfcc", seam_every=22):
    """Canvas over bales and the furled sails: an off-white weave, seams, soft fold shading."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W]
    fold = 0.08 * np.sin(xx * 0.21 + 0.8 * vnoise(rng, W, H, 10, 10)) + 0.05 * vnoise(rng, W, H, 16, 6)
    out = hx(base) * (1 + fold - 0.04 * ((xx + yy) % 2))[..., None]
    out[(yy % seam_every) == 0] *= 0.78
    return np.clip(out, 0, 255)


# ---------------------------------------------------------------- the sails
def rope_line(out, mask_edge, rng):
    """A twisted bolt rope on the texels of mask_edge (diagonal strands, light and dark)."""
    H, W = out.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    tw = ((xx + yy) // 2) % 3
    c0, c1, c2 = hx("ecd090"), hx("c8a464"), hx("8a6a3a")
    out[mask_edge & (tw == 0)] = c0
    out[mask_edge & (tw == 1)] = c1
    out[mask_edge & (tw == 2)] = c2


def p_sail(w, h, cols, rows, rng, rt, lion=0.0, tri=None, leech_stripe=True, widen=1.45):
    """A royal blue sail of blocky cloths: a tone per block, a voxel bevel on each block, a strong seam between the
    vertical cloths and a light one between the rows, a reinforcement band with a row of reef points, soft folds (the
    belly, the tension lines from the clews), a top-to-bottom gradient (the shadow under the yard, the lit belly, a
    darker foot), the wide gold border in bevelled blocks, a twisted bolt rope round the edge, the gold lion."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W]
    fx, fy = (xx + 0.5) / W, (yy + 0.5) / H
    cw, ch = W / cols, H / rows
    nr = int(math.ceil(rows))
    ci = np.minimum(cols - 1, (xx / cw).astype(int))
    ri = np.minimum(nr - 1, (yy / ch).astype(int))
    pal = np.array([hx(c) for c in SAIL_BLUE])
    tones = pal[rng.integers(0, len(pal), (nr, cols))] * rng.uniform(0.95, 1.05, (nr, cols, 1))
    col = tones[ri, ci]
    lx, ly = xx - ci * cw, yy - ri * ch
    k = 1 + 0.13 * (ly < 2) + 0.05 * (lx < 2) - 0.13 * (ly > ch - 3) - 0.07 * (lx > cw - 3)
    # folds: the belly (lit middle, darker towards the leeches), soft vertical folds, tension lines from the clews
    dx = np.abs(fx - 0.5) * 2
    belly = 0.1 * (1 - dx * dx) - 0.14 * dx ** 3
    soft = 0.075 * np.sin(fx * 2 * math.pi * 3.0 + 1.1) * (0.4 + 0.6 * fy) + 0.04 * np.sin(fx * 2 * math.pi * 7.0 + 0.3)
    cl = np.zeros_like(fx)
    for sx in (0.0, 1.0):
        d = np.hypot((fx - sx) * W / H, fy - 1.0)
        ang = np.arctan2(1.0 - fy, np.abs(fx - sx) * W / H + 1e-6)
        cl += 0.06 * np.sin(ang * 14) * np.clip(1 - d / 0.55, 0, 1)
    grad = np.where(fy < 0.05, 0.82 + 3.6 * fy, 1.0) * (1.03 - 0.12 * np.clip((fy - 0.55) / 0.45, 0, 1))
    k = k * (1 + belly + soft + cl) * grad
    out = col * k[..., None] * (1 + 0.03 * rng.uniform(-1, 1, (H, W)))[..., None]
    # seams: strong between the vertical cloths (a dark double stitch and a lit overlap), light between the rows
    vs = (lx < 1.5) & (ci > 0)
    out[vs] = hx(SAIL_JOINT)
    out[(lx >= 1.5) & (lx < 2.5) & (ci > 0)] *= 1.18
    out[(ly < 1) & (ri > 0)] *= 0.72
    # the reinforcement band (a doubled strip across the sail at a third of its height) and its reef points
    if tri is None:
        b0, b1 = 0.30, 0.345
        band = (fy >= b0) & (fy < b1)
        out[band] *= 1.08
        out[(np.abs(fy - b0) * H < 0.8) | (np.abs(fy - b1) * H < 0.8)] *= 0.8
        ry = int(b1 * H) + 1
        for c in range(cols):
            x0 = int(c * cw + cw / 2)
            out[ry - 3:ry - 1, x0:x0 + 2] = hx("0a1430")
            out[ry - 1:ry + 4, x0:x0 + 1] = hx("c8b080")
            out[ry - 1:ry + 4, x0 + 1:x0 + 2] = hx("8a7050")
    # the gold border in blocks, the leech stripes, the bolt rope
    if tri is None:
        d = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
        inside = np.ones((H, W), bool)
    else:
        P = [(a * W, b * H) for a, b in tri]
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).polygon(P, fill=255)
        inside = np.asarray(im) > 127
        d = np.full((H, W), 99.0)
        for (ax, ay), (bx, by) in zip(P, P[1:] + P[:1]):
            ex, ey = bx - ax, by - ay
            L2 = ex * ex + ey * ey
            t = np.clip(((xx + 0.5 - ax) * ex + (yy + 0.5 - ay) * ey) / L2, 0, 1)
            d = np.minimum(d, np.hypot(xx + 0.5 - ax - t * ex, yy + 0.5 - ay - t * ey))
    border = max(12, int(round(min(W, H) * 0.06)))
    gb = (d >= 3) & (d < border)
    gcell = 8
    gt = (((yy // gcell) * 31 + (xx // gcell) * 17) % 5)
    gk = np.choose(gt, [1.0, 1.06, 0.95, 1.1, 0.92])
    glx, gly = xx % gcell, yy % gcell
    gk = gk * (1 + 0.12 * (gly == 0) + 0.05 * (glx == 0) - 0.12 * (gly == gcell - 1) - 0.07 * (glx == gcell - 1))
    gtone = stops(np.clip(0.38 + 0.1 * fy - 0.4 * belly, 0, 1), GOLD_STOPS) * gk[..., None]
    out[gb] = gtone[gb]
    out[(d >= border - 2) & (d < border)] = hx("6a400e")
    out[(d >= border) & (d < border + 1)] = hx("0a1430")
    if leech_stripe and tri is None:
        ls = (np.minimum(xx, W - 1 - xx) >= border + 10) & (np.minimum(xx, W - 1 - xx) < border + 15) & (d >= border)
        out[ls] = gtone[ls] * 0.95
        out[ls & ((np.minimum(xx, W - 1 - xx) == border + 14))] = hx("6a400e")
    rope_line(out, (d < 3) & inside, rng)
    # the lion
    if lion:
        lh = int(H * lion)
        lw = int(lh * 100 / 120 * widen * (cw / ch))
        cell = max(4, int(round(min(cw, ch) / 4)))
        lh, lw = lh // cell * cell, lw // cell * cell
        m, dl = lion_layers(lw, lh, cell, bold=1.6, rt=rt)
        paint_lion(out, (W - lw) // 2, int(H * 0.49 - lh / 2), m, dl, rng, cell, outline=4, outline_col="0a1430")
    return rgba(out, inside)


def p_pennant(w, h, rng, rt, lion=True):
    """A swallow-tailed pennant: royal blue with soft waves, a bevelled gold edge, a small lion at the hoist."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W]
    fx = xx / W
    half = (H / 2) * (1.0 - 0.45 * fx)
    ay = np.abs(yy - H / 2 + 0.5)
    inside = (ay <= half) & ~((fx > 0.7) & (ay < (fx - 0.7) / 0.3 * half))
    wave = 0.12 * np.sin(xx * 0.09 + 0.5) + 0.05 * np.sin(xx * 0.23)
    out = hx("27459a") * (1.02 + wave - 0.1 * (yy / H))[..., None]
    edge = half - ay
    g = stops(np.clip(0.35 - 0.8 * wave + 0.25 * (yy / H), 0, 1), GOLD_STOPS)
    gm = (edge < 4.4) | (xx < 4)
    out[gm] = g[gm]
    if lion:
        lh = H - 12
        lw = int(lh * 100 / 120)
        m, dl = lion_layers(lw, lh, 1, rt=rt)
        paint_lion(out, 10, 6, m, dl, rng, 2, outline=1, shadow=False)
    return rgba(out, inside)


def p_standard(w, h, rng, rt):
    """The royal standard: royal blue with soft waves, a gold border, a gold lion, swallow-tailed at the fly."""
    W, H = w * K, h * K
    yy, xx = np.mgrid[0:H, 0:W]
    fx = xx / W
    inside = ~((fx > 0.76) & (np.abs(yy - H / 2 + 0.5) < (fx - 0.76) / 0.24 * (H / 2 - 1)))
    wave = 0.1 * np.sin(xx * 0.1 + yy * 0.03)
    out = hx("27459a") * (1.02 + wave - 0.12 * (yy / H))[..., None]
    gm = (np.minimum(yy, H - 1 - yy) < 6) | (xx < 6)
    out[gm] = stops(np.clip(0.35 - 0.8 * wave + 0.25 * yy / H, 0, 1), GOLD_STOPS)[gm]
    lh = int(H * 0.76)
    lw = int(lh * 100 / 120)
    m, dl = lion_layers(lw, lh, 2, rt=rt)
    paint_lion(out, int(W * 0.34 - lw / 2), (H - lh) // 2, m, dl, rng, 2, outline=2)
    return rgba(out, inside)


# ---------------------------------------------------------------- the passes
def hull_pass(base, R, rt):
    """The hull atlas: base (the first pass, 512 x 512 RGBA image) scaled to K times, then the outside regions
    repainted (R: the texture regions)."""
    atlas = np.asarray(base.resize((base.width * K, base.height * K), Image.NEAREST)).copy()

    def P(name, arr, alpha=None):
        a = arr if arr.shape[-1] == 4 else rgba(arr, alpha)
        put(atlas, R[name], a)

    def g(name):
        return gen(name, 1661)

    def wh(name):
        return R[name][2], R[name][3]

    # hull strakes (stretched over the band's height: the ambient shadow under the wale above and over the one below)
    vox = dict(lens=(1,), stagger=False, bevel=0.7)
    P("strake_lo", p_blocks(*wh("strake_lo"), WOOD_LO, JOINT_BROWN, g("strake_lo"), rows=2, ao=(0.42, 0.2), wear=0.15, **vox))
    P("strake_mid", p_blocks(*wh("strake_mid"), WOOD_MID, JOINT_BROWN, g("strake_mid"), rows=1, ao=(0.45, 0.22), wear=0.12, **vox))
    P("strake_hi", p_blocks(*wh("strake_hi"), NAVY, NAVY_JOINT, g("strake_hi"), rows=2, ao=(0.48, 0.24), wear=0.08, nails=0.15, **vox))
    P("hull_brown", p_blocks(*wh("hull_brown"), ("4a2e16", "402812", "54341a", "38220f", "5e3c20"), "160c04", g("hull_brown"), rows=2,
                             wear=0.1, **vox))
    P("strake_brown2", p_blocks(*wh("strake_brown2"), ("3e2616", "36210f", "46291a"), "140a04", g("strake_brown2"), rows=1, blen=32,
                                ao=(0.0, 0.3)))
    P("strake_brown", p_blocks(*wh("strake_brown"), WOOD_DARK, JOINT_BROWN, g("strake_brown"), rows=1, ao=(0.25, 0.1)))
    P("hull_blue", p_blocks(*wh("hull_blue"), NAVY, NAVY_JOINT, g("hull_blue"), rows=2, ao=(0.4, 0.2), wear=0.06, nails=0.15, **vox))
    P("hull_blue2", p_blocks(*wh("hull_blue2"), NAVY, NAVY_JOINT, g("hull_blue2"), rows=2, wear=0.15, nails=0.15, **vox))
    # gold, the cap rail, the gold mouldings
    P("gold", p_gold_v(*wh("gold"), g("gold")))
    P("rail", p_gold_v(*wh("rail"), g("rail"), pts=[(0.0, "fff0b0"), (0.12, "fad472"), (0.35, "eebc54"), (0.62, "d49a34"),
                                                     (0.86, "a06c1c"), (1.0, "5e380c")], seam=48))
    P("gold_band", p_gold_band(*wh("gold_band"), g("gold_band")))
    P("scroll", p_scroll(*wh("scroll"), g("scroll")))
    P("roof_ridge", p_scroll(*wh("roof_ridge"), g("roof_ridge"), period=24))
    P("carving", p_scroll(*wh("carving"), g("carving"), period=16, kind="s"))
    P("taffrail", p_scroll(*wh("taffrail"), g("taffrail"), period=24, kind="s"))
    P("bronze", p_gold_v(*wh("bronze"), g("bronze"), seam=0))
    P("iron", p_iron(*wh("iron"), g("iron")))
    P("rope", p_rope(*wh("rope"), g("rope"), "c8aa72", "6e5634"))
    P("rope_light", p_rope(*wh("rope_light"), g("rope_light"), "d8bc84", "7a6040"))
    P("rope_dark", p_rope(*wh("rope_dark"), g("rope_dark"), "d4b67c", "76603c"))
    # wood
    P("wood_dark", p_planks(*wh("wood_dark"), ("5a3a20", "4e321c", "634126", "553620"), "24170c", g("wood_dark")))
    P("dark_wood", p_planks(*wh("dark_wood"), ("4a2f1a", "40281a", "533420"), "1e140a", g("dark_wood")))
    P("wood_mid", p_planks(*wh("wood_mid"), ("7a5130", "6e482a", "855a36", "73502e"), "33210f", g("wood_mid")))
    P("wood_light", p_planks(*wh("wood_light"), ("9a6a3e", "a87644", "8e6038", "b07e4a"), "4a2f17", g("wood_light")))
    P("deck", p_planks(*wh("deck"), ("8a6340", "7d5838", "936a44", "80603e", "6f5234"), "2e1e10", g("deck"), worn=0.15,
                       worn_col="a08060"))
    P("deck_plank", p_planks(*wh("deck_plank"), ("8a6340", "7d5838", "936a44"), "2e1e10", g("deck_plank")))
    P("mast", p_planks(*wh("mast"), ("6a4626", "5e3e20", "74502c"), "2e1d0c", g("mast"), plank=16, grain=0.16, butt=(200, 300), nails=False))
    # the castle: blue panels in gold frames (the state room), dark wood panelling with a gold bead (the cabin storey)
    P("castle_panel", p_panel(*wh("castle_panel"), g("castle_panel"), NAVY, NAVY_JOINT, "gold"))
    P("castle_wood", p_panel(*wh("castle_wood"), g("castle_wood"), WOOD_MID, JOINT_BROWN, "wood"))
    P("roof", p_roof(*wh("roof"), g("roof")))
    P("port_lid", p_lid(*wh("port_lid"), g("port_lid")))
    # emblems, windows, cloth
    P("shield", p_shield(*wh("shield"), g("shield"), rt))
    P("banner", p_banner(*wh("banner"), g("banner"), rt))
    P("lion_relief", p_lion_panel(*wh("lion_relief"), g("lion_relief"), rt))
    P("tapestry", p_lion_panel(*wh("tapestry"), g("tapestry"), rt, frame=4, fringe=6))
    P("arch_window", p_window(*wh("arch_window"), g("arch_window")))
    P("arch_window_in", p_window(*wh("arch_window_in"), g("arch_window_in"), lit=False))
    P("glow_window", p_window(*wh("glow_window"), g("glow_window"), arch=False, frame=2))
    P("port_lit", p_port(*wh("port_lit"), g("port_lit")))
    P("awning", p_awning(*wh("awning"), g("awning")))
    P("awning_fringe", p_awning(*wh("awning_fringe"), g("awning_fringe"), fringe=True))
    P("mane", p_mane(*wh("mane"), g("mane")))
    P("lion_face", p_lion_face(*wh("lion_face"), g("lion_face")))
    P("bale_white", p_canvas(*wh("bale_white"), g("bale_white")))
    P("cloth_roll", p_canvas(*wh("cloth_roll"), g("cloth_roll"), base="2c4890", seam_every=16))
    return Image.fromarray(atlas, "RGBA")


def sail_pass(base, SR, cells, lions, tris, rt, widen):
    atlas = np.asarray(base.resize((base.width * K, base.height * K), Image.NEAREST)).copy()
    for name, (cols, rows) in cells.items():
        tri = tris.get(name)
        u, v, w, h = SR[name]
        put(atlas, SR[name], p_sail(w, h, cols, rows, gen(name, 1715), rt, lion=lions.get(name, 0.0), tri=tri, widen=widen))
    for name in ("pennant", "pennant_small"):
        u, v, w, h = SR[name]
        put(atlas, SR[name], p_pennant(w, h, gen(name, 1715), rt))
    u, v, w, h = SR["flag_lion"]
    put(atlas, SR["flag_lion"], p_standard(w, h, gen("flag_lion", 1715), rt))
    return Image.fromarray(atlas, "RGBA")
