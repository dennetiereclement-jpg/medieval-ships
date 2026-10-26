"""The black dragon painted on the Dragon Junk's great red sail (tools/junk_texture.py), drawn as a stencil with PIL,
after the reference sheet: a Chinese dragon rising up the sail, its big head at the top turned forwards (towards the
luff) with open jaws and fangs, two antlers swept back, a mane of long strands flowing back along the neck and long
curling whiskers; its body a chain of black scale bars with thin gaps of red cloth between them (the stencil look),
coiling in an S down the sail; short curved flame tufts along its back, four legs with three hooked talons each, the
tail coiling at the bottom into a tuft of flames.

draw_dragon(draw, box, ink) paints it in the box (x0, y0, x1, y1) of a PIL ImageDraw (its head at the top left, facing
left); the lengths follow the box's width, so the same design serves any resolution.
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
    """n + 1 points evenly spaced along a polyline, with their unit tangent."""
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


# the spine in the box's width units (x right = towards the leech, y down; the box is about 1.4 widths high), from the
# back of the head to the tail's tip: the neck arches up and right, the body swings back left, then right again with
# the hind legs, the tail sweeps left then curls right into its tuft (as on the reference sheet's sail)
SPINE = [(0.4, 0.28), (0.51, 0.3), (0.62, 0.36), (0.68, 0.46), (0.63, 0.56), (0.5, 0.62), (0.43, 0.71), (0.5, 0.79), (0.64, 0.82),
         (0.72, 0.9), (0.66, 0.98), (0.53, 1.02), (0.46, 1.1), (0.52, 1.18), (0.64, 1.23), (0.76, 1.27)]


def _width(t):
    """Half thickness of the body along the spine (0 at the neck, 1 at the tail's tip), in box widths."""
    if t < 0.1:
        return 0.06 + 0.035 * t / 0.1
    if t < 0.5:
        return 0.095 - 0.01 * (t - 0.1) / 0.4
    return max(0.014, 0.085 * (1.0 - (t - 0.5) / 0.5) ** 0.85)


def draw_dragon(d, box, ink=(16, 12, 12, 255), gap=None, eye=(190, 40, 26, 255)):
    """Paints the dragon in the box. gap: the colour of the cloth showing through the stencil's cuts (the eye's white,
    the lines inside the head), None for transparent (the caller composites the ink over the cloth)."""
    x0, y0, x1, y1 = box
    S = x1 - x0                                   # the unit: the box's width
    hole = gap if gap is not None else (0, 0, 0, 0)

    def P(u, v):
        return (x0 + u * S, y0 + v * S)

    def poly(pts, fill=ink):
        d.polygon([P(u, v) for u, v in pts], fill=fill)

    def flame(base, direction, length, width, curl, fill=ink, n=10):
        """A brush-stroke flame / claw: a tongue thick near its root, tapering to a point, its middle line curling
        sideways (by curl, in box widths) like an S at the tip."""
        dx, dy = direction
        ln = math.hypot(dx, dy) or 1.0
        dx, dy = dx / ln, dy / ln
        ox, oy = -dy, dx
        left, right = [], []
        for i in range(n + 1):
            t = i / n
            bend = curl * (t ** 1.8) - 0.25 * curl * math.sin(math.pi * t) * t
            c = (base[0] + dx * length * t + ox * bend, base[1] + dy * length * t + oy * bend)
            w = width * (0.55 + 0.9 * math.sin(math.pi * min(1.0, 0.25 + t))) * (1.0 - t) ** 1.1
            left.append((c[0] + ox * w, c[1] + oy * w))
            right.append((c[0] - ox * w, c[1] - oy * w))
        poly(left + right[::-1], fill)

    def band(a, b, wa, wb, fill=ink):
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        ox, oy = -dy / ln, dx / ln
        poly([(a[0] + ox * wa, a[1] + oy * wa), (b[0] + ox * wb, b[1] + oy * wb), (b[0] - ox * wb, b[1] - oy * wb),
              (a[0] - ox * wa, a[1] - oy * wa)], fill)

    spine = _catmull(SPINE, 16)
    N = 240
    samples, total = _resample(spine, N)
    pts = []
    for k, ((u, v), (tx, ty)) in enumerate(samples):
        t = k / N
        pts.append(((u, v), (ty, -tx), (tx, ty), _width(t), t))     # point, dorsal normal, tangent, half width, t

    def at(t):
        return pts[max(0, min(N, int(round(t * N))))]

    # ---- flame tufts along the back (curved, swept towards the tail), smaller ones along the belly
    for k in range(8, N - 16, 11):
        (u, v), (nx, ny), (tx, ty), w, t = pts[k]
        big = 1.0 if t < 0.55 else max(0.4, 1.0 - (t - 0.55) / 0.45)
        base = (u + nx * w * 0.6, v + ny * w * 0.6)
        flame(base, (nx * 0.85 + tx * 0.6, ny * 0.85 + ty * 0.6), (0.1 + 0.025 * math.sin(k * 1.7)) * big + w * 0.4, 0.024 * big, 0.07 * big)
        if 0.12 < t < 0.8 and k % 22 == 8:
            base = (u - nx * w * 0.6, v - ny * w * 0.6)
            flame(base, (-nx * 0.7 + tx * 0.8, -ny * 0.7 + ty * 0.8), 0.06 * big + w * 0.3, 0.022 * big, -0.03 * big)
    # ---- the legs: (t along the body, the side (+1 dorsal, -1 ventral), the upper leg's and the forearm's directions)
    legs = ((0.1, -1, (-0.9, 0.35), (-0.8, 0.55)), (0.16, 1, (0.8, -0.5), (0.9, 0.25)),
            (0.47, -1, (-0.85, 0.4), (-0.55, 0.85)), (0.52, 1, (0.9, 0.15), (0.55, 0.8)))
    for t, side, d1, d2 in legs:
        (u, v), (nx, ny), (tx, ty), w, _ = at(t)
        a = (u - nx * w * 0.1 * side, v - ny * w * 0.1 * side)
        n1, n2 = math.hypot(*d1), math.hypot(*d2)
        knee = (a[0] + d1[0] / n1 * 0.15, a[1] + d1[1] / n1 * 0.15)
        foot = (knee[0] + d2[0] / n2 * 0.12, knee[1] + d2[1] / n2 * 0.12)
        band(a, knee, w * 0.55, 0.034)
        band(knee, foot, 0.032, 0.024)
        d.ellipse([*P(knee[0] - 0.034, knee[1] - 0.034), *P(knee[0] + 0.034, knee[1] + 0.034)], fill=ink)
        # flame tufts at the elbow, streaming back
        bx, by = -d1[0] / n1, -d1[1] / n1
        flame(knee, (bx * 0.6 + d2[1] / n2 * side, by * 0.6 - d2[0] / n2 * side), 0.11, 0.022, 0.05 * side)
        # three hooked talons spread from the foot, a spur behind
        base_a = math.atan2(d2[1], d2[0])
        d.ellipse([*P(foot[0] - 0.026, foot[1] - 0.026), *P(foot[0] + 0.026, foot[1] + 0.026)], fill=ink)
        for c in range(3):
            ang = base_a + (c - 1) * 0.62
            flame((foot[0] + math.cos(ang) * 0.015, foot[1] + math.sin(ang) * 0.015), (math.cos(ang), math.sin(ang)), 0.085, 0.016,
                  0.05 * (-side if c != 1 else -side * 0.5))
        flame(foot, (-math.cos(base_a + 0.5 * side), -math.sin(base_a + 0.5 * side)), 0.04, 0.012, 0.015)
    # ---- the body: a chain of black scale bars (crescents bowed towards the head), thin gaps of cloth between them
    pitch = 6
    for k in range(0, N - 2, pitch):
        (u, v), (nx, ny), (tx, ty), w, t = pts[k]
        k2 = min(N, k + pitch - 2)
        (u2, v2), (nx2, ny2), (tx2, ty2), w2, _ = pts[k2]
        lead = w * 0.55                         # the crescent's middle leads its tips by this much
        front = [(u + nx * w, v + ny * w), (u + nx * w * 0.5 - tx * lead * 0.75, v + ny * w * 0.5 - ty * lead * 0.75),
                 (u - tx * lead, v - ty * lead), (u - nx * w * 0.5 - tx * lead * 0.75, v - ny * w * 0.5 - ty * lead * 0.75),
                 (u - nx * w, v - ny * w)]
        back = [(u2 - nx2 * w2, v2 - ny2 * w2), (u2 - nx2 * w2 * 0.5 - tx2 * lead * 0.7, v2 - ny2 * w2 * 0.5 - ty2 * lead * 0.7),
                (u2 - tx2 * lead * 0.95, v2 - ty2 * lead * 0.95),
                (u2 + nx2 * w2 * 0.5 - tx2 * lead * 0.7, v2 + ny2 * w2 * 0.5 - ty2 * lead * 0.7), (u2 + nx2 * w2, v2 + ny2 * w2)]
        poly(front + back)
    # the dorsal ridge joining the scale bars, so the body reads as one
    left = [(u + nx * w * 1.02, v + ny * w * 1.02) for (u, v), (nx, ny), _, w, t in pts[:-4]]
    inner = [(u + nx * w * 0.74, v + ny * w * 0.74) for (u, v), (nx, ny), _, w, t in pts[:-4]]
    poly(left + inner[::-1])
    # ---- the tail's tuft: a fan of long curved flames sweeping down and out at the end
    (u, v), (nx, ny), (tx, ty), w, t = pts[-1]
    base_a = math.atan2(ty, tx)
    for c in range(6):
        ang = base_a + 0.45 + (c - 2.5) * 0.33
        flame((u, v), (math.cos(ang), math.sin(ang)), 0.17 * (1.15 - 0.1 * abs(c - 2.5)), 0.026, 0.08 * (1 if c < 3 else -1))
    # ---- the head (facing left): the mane's crown, antlers, a heavy skull and snout, open jaws with fangs, whiskers
    (hu, hv), (nx, ny), _, w, _ = pts[0]
    hx, hy = hu - 0.06, hv + 0.01
    # mane: a crown of long strands from the back of the head, flowing up and back
    for k in range(9):
        ang = math.radians(-120 + k * 13)
        base = (hx + 0.02 + 0.012 * k, hy - 0.05 + 0.006 * k)
        flame(base, (math.cos(ang) + 0.45, math.sin(ang) - 0.35), 0.17 + 0.05 * math.sin(k * 1.9 + 0.5), 0.026, 0.07)
    # antlers: two swept back and up, each with a branch
    for k, (dx, dy) in enumerate(((0.55, -1.0), (0.95, -0.75))):
        root = (hx - 0.04 + 0.03 * k, hy - 0.08)
        flame(root, (dx, dy), 0.19, 0.022, 0.06, n=10)
        ln = math.hypot(dx, dy)
        mid = (root[0] + dx / ln * 0.09, root[1] + dy / ln * 0.09)
        flame(mid, (dx - 0.9, dy - 0.1), 0.07, 0.014, -0.02)
    # skull and upper jaw: a heavy head, the snout pointing forwards (left), the nose turned up
    upper = [(hx + 0.08, hy - 0.06), (hx + 0.02, hy - 0.1), (hx - 0.06, hy - 0.1), (hx - 0.13, hy - 0.08), (hx - 0.2, hy - 0.075),
             (hx - 0.23, hy - 0.095), (hx - 0.26, hy - 0.075), (hx - 0.255, hy - 0.035), (hx - 0.19, hy - 0.015), (hx - 0.1, hy - 0.005),
             (hx - 0.03, hy + 0.02), (hx + 0.05, hy + 0.06), (hx + 0.11, hy + 0.01)]
    poly(upper)
    # lower jaw, wide open, a beard of flames under it
    lower = [(hx - 0.0, hy + 0.04), (hx - 0.08, hy + 0.06), (hx - 0.17, hy + 0.09), (hx - 0.205, hy + 0.12), (hx - 0.17, hy + 0.135),
             (hx - 0.08, hy + 0.115), (hx + 0.02, hy + 0.1), (hx + 0.07, hy + 0.07)]
    poly(lower)
    for k in range(4):
        flame((hx - 0.1 + 0.04 * k, hy + 0.11), (0.3, 1.0), 0.09 + 0.015 * k, 0.02, 0.04)
    # fangs, up and down
    for fx, fy, dn in ((-0.235, -0.04, 1), (-0.18, -0.017, 1), (-0.11, -0.008, 1), (-0.17, 0.1, -1), (-0.11, 0.085, -1)):
        poly([(hx + fx - 0.013, hy + fy), (hx + fx + 0.002, hy + fy + dn * 0.038), (hx + fx + 0.014, hy + fy)])
    # the stencil's cuts in the head: the eye, the brow, the cheek's line, the nostril
    d.ellipse([*P(hx - 0.09, hy - 0.075), *P(hx - 0.035, hy - 0.04)], fill=hole)
    if eye is not None:
        d.ellipse([*P(hx - 0.074, hy - 0.068), *P(hx - 0.05, hy - 0.047)], fill=eye if gap is not None else ink)
    band((hx - 0.12, hy - 0.088), (hx - 0.01, hy - 0.08), 0.006, 0.004, hole)
    band((hx - 0.02, hy - 0.02), (hx + 0.06, hy + 0.025), 0.006, 0.005, hole)
    band((hx - 0.16, hy - 0.03), (hx - 0.06, hy - 0.025), 0.004, 0.004, hole)
    d.ellipse([*P(hx - 0.245, hy - 0.075), *P(hx - 0.22, hy - 0.055)], fill=hole)
    # whiskers: two long curling lines trailing from the snout
    lw = max(1, int(round(S * 0.012)))
    for pts_w in (((-0.25, -0.05), (-0.31, -0.03), (-0.34, 0.04), (-0.31, 0.11), (-0.25, 0.12)),
                  ((-0.22, -0.02), (-0.27, 0.05), (-0.27, 0.14), (-0.22, 0.2), (-0.16, 0.19))):
        wp = _catmull([(hx + a, hy + b) for a, b in pts_w], 6)
        d.line([P(*p) for p in wp], fill=ink, width=lw)


if __name__ == "__main__":
    import sys
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (800, 1150), (178, 72, 56, 255))
    draw_dragon(ImageDraw.Draw(im), (40, 40, 760, 1110), gap=(178, 72, 56, 255))
    im.save(sys.argv[1] if len(sys.argv) > 1 else "/tmp/dragon.png")
