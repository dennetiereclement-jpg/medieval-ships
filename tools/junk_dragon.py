"""The black dragon painted on the Dragon Junk's great red sail (tools/junk_texture.py), drawn as a vector design
with PIL: a long Chinese dragon rising up the sail, the head at the top turned forwards (towards the luff) with
open jaws, fangs, a red eye, two long swept-back horns, a spiky mane and trailing whiskers; a ribbed serpent body in
an S, a crest of flame-like spines along its back, four legs with spread talons, the tail coiling at the bottom
into a flame-like tuft. Ink black, a little worn, as if painted on the cloth.

draw_dragon(draw, box, ink) paints it in the box (x0, y0, x1, y1) of a PIL ImageDraw (its head at the top left,
facing left); the units follow the box, so the same design serves any resolution.
"""
import math


def _catmull(pts, n=12):
    """Points of a Catmull-Rom spline through pts (n per segment)."""
    out = []
    p = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3)
                             for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(pts[-1])
    return out


def _resample(pts, n):
    """n + 1 points evenly spaced along a polyline, with their tangent."""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg)
    out = []
    i, acc = 0, 0.0
    for k in range(n + 1):
        target = total * k / n
        while i < len(seg) - 1 and acc + seg[i] < target:
            acc += seg[i]
            i += 1
        f = 0.0 if seg[i] == 0 else (target - acc) / seg[i]
        f = max(0.0, min(1.0, f))
        a, b = pts[i], pts[i + 1]
        p = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        out.append((p, (dx / ln, dy / ln)))
    return out, total


# the spine of the dragon in a unit box (x right = towards the leech, y down), from the back of the head to the tail
# tip: the neck comes down from the head, the body swings left, coils up to the right and round, the tail sweeps
# left then right into its tuft (as on the reference sheet's sail)
SPINE = [(0.36, 0.215), (0.44, 0.25), (0.49, 0.32), (0.48, 0.41), (0.42, 0.48), (0.4, 0.55), (0.47, 0.6), (0.58, 0.59),
         (0.68, 0.6), (0.73, 0.67), (0.69, 0.74), (0.59, 0.765), (0.5, 0.775), (0.45, 0.81), (0.48, 0.86), (0.58, 0.885),
         (0.68, 0.895), (0.75, 0.92)]


def _width(t):
    """Half thickness of the body along the spine (0 at the head, 1 at the tail tip)."""
    if t < 0.1:
        return 0.04 + 0.12 * t
    if t < 0.55:
        return 0.052 + 0.01 * math.sin(math.pi * (t - 0.1) / 0.45)
    return max(0.008, 0.052 * (1.0 - (t - 0.55) / 0.45) ** 0.85)


def _band(poly, a, b, wa, wb, ink):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    ox, oy = -dy / ln, dx / ln
    poly([(a[0] + ox * wa, a[1] + oy * wa), (b[0] + ox * wb, b[1] + oy * wb), (b[0] - ox * wb, b[1] - oy * wb),
          (a[0] - ox * wa, a[1] - oy * wa)], ink)


def _flame(poly, base, d, length, width, curl, ink):
    """A flame-like spike from base along d, curling to the side by curl."""
    dx, dy = d
    ox, oy = -dy, dx
    mid = (base[0] + dx * length * 0.55 + ox * curl * 0.5, base[1] + dy * length * 0.55 + oy * curl * 0.5)
    tip = (base[0] + dx * length + ox * curl, base[1] + dy * length + oy * curl)
    poly([(base[0] - ox * width, base[1] - oy * width), (mid[0] - ox * width * 0.45, mid[1] - oy * width * 0.45), tip,
          (mid[0] + ox * width * 0.3, mid[1] + oy * width * 0.3), (base[0] + ox * width, base[1] + oy * width)], ink)


def draw_dragon(d, box, ink=(16, 12, 12, 255), gap=None, eye=(190, 40, 26, 255)):
    """Paints the dragon in the box. gap: the colour of the thin lines between the ribs (the cloth seen through
    the paint), None to leave them black."""
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    S = min(W, H)

    def P(u, v):
        return (x0 + u * W, y0 + v * H)

    def poly(pts, fill):
        d.polygon([P(u, v) for u, v in pts], fill=fill)

    spine = _catmull(SPINE, 16)
    N = 200
    samples, total = _resample(spine, N)
    pts = []
    for k, ((u, v), (tx, ty)) in enumerate(samples):
        t = k / N
        w = _width(t)
        nx, ny = ty, -tx                      # the back of the dragon (its crest) on this side
        pts.append(((u, v), (nx, ny), w, t))
    # ---- crest: flame-like spines along the back, longest along the body, a few on the belly
    for k in range(6, N - 6, 6):
        (u, v), (nx, ny), w, t = pts[k]
        tx, ty = -ny, nx
        big = 0.075 if t < 0.6 else 0.075 * (1.0 - (t - 0.6) / 0.4) + 0.015
        length = big * (1.0 + 0.35 * math.sin(k * 0.9))
        dirx, diry = nx * 0.8 + tx * 0.6, ny * 0.8 + ty * 0.6
        ln = math.hypot(dirx, diry)
        _flame(poly, (u + nx * w * 0.7, v + ny * w * 0.7), (dirx / ln, diry / ln), length + w * 0.3, 0.016, 0.02, ink)
        if k % 18 == 0 and 0.15 < t < 0.85:
            dirx, diry = -nx * 0.8 + tx * 0.6, -ny * 0.8 + ty * 0.6
            ln = math.hypot(dirx, diry)
            _flame(poly, (u - nx * w * 0.7, v - ny * w * 0.7), (dirx / ln, diry / ln), length * 0.55 + w * 0.3, 0.008, -0.008, ink)
    # ---- legs with talons: (t along the body, direction of the upper leg, of the lower leg, length)
    legs = ((0.14, (-0.75, 0.75), (-0.95, 0.25), 1.15), (0.1, (0.9, -0.15), (0.6, -0.8), 0.95),
            (0.45, (-0.7, 0.75), (-0.8, 0.45), 1.15), (0.48, (0.8, 0.5), (0.95, 0.05), 0.9))
    for t, d1, d2, sc in legs:
        k = int(t * N)
        (u, v), (nx, ny), w, _ = pts[k]
        n1 = math.hypot(*d1)
        n2 = math.hypot(*d2)
        a = (u - nx * w * 0.2, v - ny * w * 0.2)
        knee = (a[0] + d1[0] / n1 * 0.11 * sc, a[1] + d1[1] / n1 * 0.11 * sc)
        foot = (knee[0] + d2[0] / n2 * 0.09 * sc, knee[1] + d2[1] / n2 * 0.09 * sc)
        _band(poly, a, knee, 0.034, 0.022, ink)
        _band(poly, knee, foot, 0.022, 0.014, ink)
        # flame-like tufts at the elbow, pointing back
        ex, ey = -d1[0] / n1, -d1[1] / n1
        _flame(poly, knee, (ex * 0.4 - d1[1] / n1 * 0.9, ey * 0.4 + d1[0] / n1 * 0.9), 0.07, 0.014, 0.015, ink)
        _flame(poly, knee, (ex * 0.6 + d1[1] / n1 * 0.8, ey * 0.6 - d1[0] / n1 * 0.8), 0.055, 0.011, -0.015, ink)
        # four talons spread like a hand, hooked
        base_a = math.atan2(d2[1], d2[0])
        for c in range(4):
            ang = base_a + (c - 1.5) * 0.5
            cx, cy = math.cos(ang), math.sin(ang)
            _flame(poly, foot, (cx, cy), 0.055, 0.009, 0.014 * (1 if c > 1 else -1), ink)
    # ---- body
    left = [(u + nx * w, v + ny * w) for (u, v), (nx, ny), w, t in pts]
    right = [(u - nx * w, v - ny * w) for (u, v), (nx, ny), w, t in pts]
    poly(left + right[::-1], ink)
    # ribs: thin curved lines across the body (the cloth showing through), a seam along the belly
    if gap is not None:
        lw = max(1, int(round(S * 0.0075)))
        for k in range(10, N - 8, 6):
            (u, v), (nx, ny), w, t = pts[k]
            tx, ty = -ny, nx
            a = (u - nx * w * 0.78, v - ny * w * 0.78)
            m = (u + tx * w * 0.25, v + ty * w * 0.25)
            b = (u + nx * w * 0.6, v + ny * w * 0.6)
            d.line([P(*a), P(*m), P(*b)], fill=gap, width=lw)
    # ---- tail tuft: a fan of long flames sweeping down at the end
    (u, v), (nx, ny), w, t = pts[-1]
    tx, ty = -ny, nx
    base_a = math.atan2(ty, tx)
    for c in range(6):
        ang = base_a + 0.25 + (c - 2.5) * 0.36
        _flame(poly, (u, v), (math.cos(ang), math.sin(ang)), 0.12 * (1.1 - 0.1 * abs(c - 2.5)), 0.017, 0.03, ink)
    # ---- head (facing left, at the start of the spine), larger than life
    (hu, hv), (nx, ny), w, _ = pts[0]
    hx, hy = hu + 0.005, hv + 0.01
    # mane: a crown of long curved locks fanning up and back from the back of the head
    for k in range(12):
        ang = math.radians(-150 + k * 13)
        length = 0.16 + 0.07 * math.sin(k * 1.3 + 0.4)
        _flame(poly, (hx + 0.01, hy - 0.005), (math.cos(ang), math.sin(ang)), length, 0.018, 0.04, ink)
    # skull and upper jaw, the snout pointing forwards (left) and a little down
    upper = [(hx + 0.04, hy - 0.05), (hx - 0.03, hy - 0.065), (hx - 0.09, hy - 0.05), (hx - 0.15, hy - 0.035), (hx - 0.175, hy - 0.015),
             (hx - 0.16, hy - 0.002), (hx - 0.1, hy + 0.0), (hx - 0.04, hy + 0.012), (hx + 0.04, hy + 0.04)]
    poly(upper, ink)
    # lower jaw, wide open
    lower = [(hx - 0.02, hy + 0.016), (hx - 0.09, hy + 0.04), (hx - 0.15, hy + 0.07), (hx - 0.135, hy + 0.085), (hx - 0.05, hy + 0.07),
             (hx + 0.03, hy + 0.055)]
    poly(lower, ink)
    # fangs
    for fx, fy, dn in ((-0.15, -0.003, 1), (-0.115, 0.001, 1), (-0.13, 0.067, -1), (-0.095, 0.058, -1)):
        poly([(hx + fx - 0.007, hy + fy), (hx + fx + 0.003, hy + fy + dn * 0.022), (hx + fx + 0.009, hy + fy)], ink)
    # the curled nostril on the snout, the brow ridge, the cheek spikes
    _flame(poly, (hx - 0.16, hy - 0.03), (-0.3, -1.0), 0.04, 0.009, 0.015, ink)
    _flame(poly, (hx - 0.06, hy - 0.055), (0.2, -1.0), 0.045, 0.011, 0.015, ink)
    for k in range(3):
        _flame(poly, (hx - 0.01 + 0.015 * k, hy + 0.03 + 0.01 * k), (0.55, 0.85), 0.06 + 0.01 * k, 0.01, 0.012, ink)
    # horns: two long tapered curves swept back and up
    for k, (cx, cy, ex, ey) in enumerate(((0.06, -0.12, 0.15, -0.16), (0.09, -0.09, 0.19, -0.1))):
        hp = _catmull([(hx - 0.01 + 0.02 * k, hy - 0.055), (hx + cx, hy + cy), (hx + ex, hy + ey)], 8)
        n = len(hp)
        L = [(p[0], p[1] - 0.013 * (1 - i / n)) for i, p in enumerate(hp)]
        R = [(p[0], p[1] + 0.013 * (1 - i / n)) for i, p in enumerate(hp)]
        poly(L + R[::-1], ink)
    # whiskers: two curls trailing down from the snout
    for k, pts_w in enumerate((((-0.17, -0.01), (-0.21, 0.03), (-0.2, 0.08), (-0.17, 0.1)),
                               ((-0.15, 0.0), (-0.18, 0.05), (-0.165, 0.11), (-0.13, 0.13)))):
        wp = _catmull([(hx + a, hy + b) for a, b in pts_w], 6)
        d.line([P(*p) for p in wp], fill=ink, width=max(1, int(S * 0.009)))
    # the eye
    if eye is not None:
        r = 0.011
        ex, ey = hx - 0.06, hy - 0.035
        if gap is not None:
            d.ellipse([P(ex - r * 1.5, ey - r)[0], P(ex - r * 1.5, ey - r)[1], P(ex + r * 1.5, ey + r)[0], P(ex + r * 1.5, ey + r)[1]], fill=gap)
        d.ellipse([P(ex - r, ey - r * 0.6)[0], P(ex - r, ey - r * 0.6)[1], P(ex + r, ey + r * 0.6)[0], P(ex + r, ey + r * 0.6)[1]], fill=eye)


if __name__ == "__main__":
    import sys
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (800, 1000), (160, 58, 44, 255))
    draw_dragon(ImageDraw.Draw(im), (60, 40, 760, 960), gap=(160, 58, 44, 255))
    im.save(sys.argv[1] if len(sys.argv) > 1 else "/tmp/dragon.png")
