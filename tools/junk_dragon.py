"""The black dragon painted on the Dragon Junk's great red sail (tools/junk_texture.py), drawn as a stencil with PIL,
after the reference sheet (its perspective view): a Chinese dragon rising up the sail in a tall narrow column, about
twice as high as wide; its head on the left at a quarter of the height, turned forwards (towards the luff), jaws open
with fangs, the whiskers trailing; above it a crest of long mane strands sweeping up and back; the body a thick coil of
black scale bars with thin cuts of red cloth between them and a thin cut along the belly (the stencil look), coiling in
an S down the middle; brush-stroke flames along its back, four legs reaching out with three hooked talons each; the tail
sweeping down and aft into a big fan of flames at the bottom.

draw_dragon(draw, box, ink) paints it in the box (x0, y0, x1, y1) of a PIL ImageDraw (its head on the left, facing
left); the design is scaled to fit the box (one unit = the box's width, or half its height if that is smaller) and
centred in it, so the same design serves any resolution.
"""
import math

# the design's size in its units (x right = towards the leech, y down)
DESIGN_H = 2.0


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


# the spine, from the back of the head to the tail's tip (as on the reference's sail): the neck runs right from the head,
# the body swings down round the right, back left across the middle, down and right again with the hind legs; the tail
# drops, then sweeps aft (right) to its fan of flames at the bottom
SPINE = [(0.31, 0.53), (0.43, 0.46), (0.57, 0.44), (0.7, 0.5), (0.77, 0.62), (0.72, 0.75), (0.58, 0.83), (0.44, 0.9), (0.37, 1.01),
         (0.41, 1.13), (0.54, 1.2), (0.65, 1.27), (0.62, 1.37), (0.51, 1.43), (0.48, 1.52), (0.56, 1.59), (0.69, 1.64), (0.79, 1.7)]


def _width(t):
    """Half thickness of the body along the spine (0 at the neck, 1 at the tail's tip), in units."""
    if t < 0.12:
        return 0.085 + 0.045 * t / 0.12
    if t < 0.55:
        return 0.13 - 0.02 * (t - 0.12) / 0.43
    return max(0.02, 0.11 * (1.0 - (t - 0.55) / 0.45) ** 0.85)


def draw_dragon(d, box, ink=(16, 12, 12, 255), gap=None, eye=(190, 40, 26, 255)):
    """Paints the dragon in the box. gap: the colour of the cloth showing through the stencil's cuts (the eye, the lines
    in the head and along the belly, between the scale bars), None for transparent (the caller composites the ink over
    the cloth)."""
    bx0, by0, bx1, by1 = box
    S = min(bx1 - bx0, (by1 - by0) / DESIGN_H)          # the unit
    x0 = (bx0 + bx1) / 2 - S / 2
    y0 = (by0 + by1) / 2 - S * DESIGN_H / 2
    hole = gap if gap is not None else (0, 0, 0, 0)

    def P(u, v):
        return (x0 + u * S, y0 + v * S)

    def poly(pts, fill=ink):
        d.polygon([P(u, v) for u, v in pts], fill=fill)

    def flame(base, direction, length, width, curl, fill=ink, n=10):
        """A brush-stroke flame / strand / claw: thick near its root, tapering to a point, its middle line curling
        sideways (by curl, in units) towards the tip."""
        dx, dy = direction
        ln = math.hypot(dx, dy) or 1.0
        dx, dy = dx / ln, dy / ln
        ox, oy = -dy, dx
        left, right = [], []
        for i in range(n + 1):
            t = i / n
            bend = curl * t * t
            c = (base[0] + dx * length * t + ox * bend, base[1] + dy * length * t + oy * bend)
            w = width * math.sin(math.pi * (0.18 + 0.82 * t)) ** 0.75     # a leaf: broadest a third of the way out
            left.append((c[0] + ox * w, c[1] + oy * w))
            right.append((c[0] - ox * w, c[1] - oy * w))
        poly(left + right[::-1], fill)

    def band(a, b, wa, wb, fill=ink):
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        ox, oy = -dy / ln, dx / ln
        poly([(a[0] + ox * wa, a[1] + oy * wa), (b[0] + ox * wb, b[1] + oy * wb), (b[0] - ox * wb, b[1] - oy * wb),
              (a[0] - ox * wa, a[1] - oy * wa)], fill)

    def dot(c, r, fill=ink):
        d.ellipse([*P(c[0] - r, c[1] - r), *P(c[0] + r, c[1] + r)], fill=fill)

    spine = _catmull(SPINE, 16)
    N = 320
    samples, total = _resample(spine, N)
    pts = []
    for k, ((u, v), (tx, ty)) in enumerate(samples):
        t = k / N
        pts.append(((u, v), (ty, -tx), (tx, ty), _width(t), t))     # point, dorsal normal, tangent, half width, t

    def at(t):
        return pts[max(0, min(N, int(round(t * N))))]

    # ---- the crest: long mane strands rising from the back of the head and the neck, sweeping up and back (right)
    for k in range(9):
        f = k / 8
        (u, v), (nx, ny), (tx, ty), w, t = at(0.01 + 0.2 * f)
        base = (u + nx * w * 0.4, v + ny * w * 0.4)
        up = (0.2 + 0.6 * f, -1.0)
        flame(base, up, 0.2 + 0.1 * math.sin(math.pi * (0.25 + 0.6 * f)) + 0.025 * math.sin(k * 2.3), 0.03, 0.1 + 0.03 * f)
    # ---- flames along the back: broad curved tongues swept towards the tail; smaller ones under the belly
    for k in range(int(0.22 * N), int(0.84 * N), 20):
        (u, v), (nx, ny), (tx, ty), w, t = pts[k]
        big = 1.0 if t < 0.6 else max(0.45, 1.0 - (t - 0.6) / 0.35)
        base = (u + nx * w * 0.55, v + ny * w * 0.55)
        flame(base, (nx * 0.8 + tx * 0.6, ny * 0.8 + ty * 0.6), (0.1 + 0.025 * math.sin(k * 1.3)) * big + w * 0.4, 0.04 * big,
              0.06 * big)
    for k in range(int(0.3 * N), int(0.7 * N), 30):
        (u, v), (nx, ny), (tx, ty), w, t = pts[k]
        base = (u - nx * w * 0.6, v - ny * w * 0.6)
        flame(base, (-nx * 0.7 + tx * 0.7, -ny * 0.7 + ty * 0.7), 0.06 + w * 0.3, 0.03, -0.035)
    # ---- the legs: (t along the body, the side (+1 dorsal, -1 ventral), the upper leg's and the forearm's directions,
    # their lengths)
    legs = ((0.13, -1, (-0.95, 0.2), (-0.7, 0.75), 0.17, 0.12), (0.2, 1, (0.85, -0.35), (0.85, 0.3), 0.13, 0.1),
            (0.5, -1, (-0.8, 0.45), (-0.45, 0.9), 0.17, 0.13), (0.56, 1, (0.9, 0.05), (0.55, 0.8), 0.13, 0.1))
    for t, side, d1, d2, l1, l2 in legs:
        (u, v), (nx, ny), (tx, ty), w, _ = at(t)
        a = (u - nx * w * 0.1 * side, v - ny * w * 0.1 * side)
        n1, n2 = math.hypot(*d1), math.hypot(*d2)
        knee = (a[0] + d1[0] / n1 * l1, a[1] + d1[1] / n1 * l1)
        foot = (knee[0] + d2[0] / n2 * l2, knee[1] + d2[1] / n2 * l2)
        band(a, knee, w * 0.6, 0.05)
        band(knee, foot, 0.045, 0.034)
        dot(knee, 0.05)
        # flame tufts at the elbow, streaming back
        bx, by = -d1[0] / n1, -d1[1] / n1
        for j in range(2):
            flame(knee, (bx * 0.5 + d2[1] / n2 * side * (1.0 + 0.4 * j), by * 0.5 - d2[0] / n2 * side * (1.0 + 0.4 * j)), 0.11 - 0.02 * j,
                  0.032, 0.045 * side)
        # three hooked talons spread from the foot, a spur behind
        base_a = math.atan2(d2[1], d2[0])
        dot(foot, 0.038)
        for c in range(3):
            ang = base_a + (c - 1) * 0.62
            flame((foot[0] + math.cos(ang) * 0.025, foot[1] + math.sin(ang) * 0.025), (math.cos(ang), math.sin(ang)), 0.09, 0.024,
                  -0.04 * side)
        flame(foot, (-math.cos(base_a + 0.6 * side), -math.sin(base_a + 0.6 * side)), 0.05, 0.018, 0.012)
    # ---- the body: a chain of black scale bars (crescents bowed towards the head), thin cuts of cloth between them
    pitch, bar = 8, 5
    for k in range(0, N - 2, pitch):
        (u, v), (nx, ny), (tx, ty), w, t = pts[k]
        k2 = min(N, k + bar)
        (u2, v2), (nx2, ny2), (tx2, ty2), w2, _ = pts[k2]
        lead = w * 0.5                          # the crescent's middle leads its tips by this much
        front = [(u + nx * w, v + ny * w), (u + nx * w * 0.5 - tx * lead * 0.75, v + ny * w * 0.5 - ty * lead * 0.75),
                 (u - tx * lead, v - ty * lead), (u - nx * w * 0.5 - tx * lead * 0.75, v - ny * w * 0.5 - ty * lead * 0.75),
                 (u - nx * w, v - ny * w)]
        back = [(u2 - nx2 * w2, v2 - ny2 * w2), (u2 - nx2 * w2 * 0.5 - tx2 * lead * 0.7, v2 - ny2 * w2 * 0.5 - ty2 * lead * 0.7),
                (u2 - tx2 * lead * 0.95, v2 - ty2 * lead * 0.95),
                (u2 + nx2 * w2 * 0.5 - tx2 * lead * 0.7, v2 + ny2 * w2 * 0.5 - ty2 * lead * 0.7), (u2 + nx2 * w2, v2 + ny2 * w2)]
        poly(front + back)
    # the dorsal ridge joining the scale bars, so the body reads as one
    rim = pts[:-6]
    poly([(u + nx * w * 1.04, v + ny * w * 1.04) for (u, v), (nx, ny), _, w, t in rim]
         + [(u + nx * w * 0.84, v + ny * w * 0.84) for (u, v), (nx, ny), _, w, t in rim][::-1])
    # the belly's cut: a thin line of cloth along the body, a third of the way from the belly
    cut = [p for p in pts[4:int(0.8 * N)]]
    for i in range(len(cut) - 1):
        (u, v), (nx, ny), _, w, _ = cut[i]
        (u2, v2), (nx2, ny2), _, w2, _ = cut[i + 1]
        band((u - nx * w * 0.42, v - ny * w * 0.42), (u2 - nx2 * w2 * 0.42, v2 - ny2 * w2 * 0.42), 0.006, 0.006, hole)
    # ---- the tail's fan: long curved flames hanging down and spreading at the end
    for c in range(6):
        (u, v), (nx, ny), (tx, ty), w, t = pts[N - 14 + 2 * c]
        base_a = math.atan2(ty, tx)
        ang = base_a + 0.85 + (c - 2.5) * 0.42
        flame((u, v), (math.cos(ang), math.sin(ang)), 0.23 * (1.1 - 0.1 * abs(c - 2.5)), 0.036, 0.08 * (1 if c < 3 else -1))
    # ---- the head (facing left): a heavy skull and snout, open jaws with fangs, a beard, whiskers, small antlers
    (hu, hv), (nx, ny), _, w, _ = pts[0]
    hx, hy = hu - 0.04, hv + 0.01
    sc = 0.85                                   # the head's size

    def H(a, b):
        return (hx + a * sc, hy + b * sc)
    for k, (dx, dy) in enumerate(((0.45, -1.0), (0.9, -0.8))):
        root = H(-0.04 + 0.04 * k, -0.08)
        flame(root, (dx, dy), 0.17 * sc + 0.02, 0.022, 0.05, n=10)
        ln = math.hypot(dx, dy)
        mid = (root[0] + dx / ln * 0.07, root[1] + dy / ln * 0.07)
        flame(mid, (dx - 0.9, dy - 0.1), 0.06, 0.013, -0.02)
    upper = [(0.08, -0.06), (0.02, -0.1), (-0.06, -0.105), (-0.13, -0.085), (-0.2, -0.08), (-0.23, -0.1), (-0.265, -0.08),
             (-0.26, -0.035), (-0.19, -0.015), (-0.1, -0.005), (-0.03, 0.02), (0.05, 0.06), (0.11, 0.01)]
    poly([H(a, b) for a, b in upper])
    lower = [(0.0, 0.04), (-0.08, 0.06), (-0.17, 0.09), (-0.21, 0.125), (-0.17, 0.14), (-0.08, 0.12), (0.02, 0.105), (0.07, 0.07)]
    poly([H(a, b) for a, b in lower])
    for k in range(4):
        flame(H(-0.1 + 0.045 * k, 0.11), (0.25, 1.0), 0.08 + 0.012 * k, 0.018, 0.035)
    for fx, fy, dn in ((-0.24, -0.04, 1), (-0.185, -0.017, 1), (-0.115, -0.008, 1), (-0.175, 0.105, -1), (-0.115, 0.09, -1)):
        poly([H(fx - 0.013, fy), H(fx + 0.002, fy + dn * 0.04), H(fx + 0.014, fy)])
    # the stencil's cuts in the head: the eye, the brow, the cheek's line, the nostril
    d.ellipse([*P(*H(-0.085, -0.075)), *P(*H(-0.04, -0.045))], fill=hole)
    if eye is not None:
        d.ellipse([*P(*H(-0.07, -0.067)), *P(*H(-0.052, -0.051))], fill=eye if gap is not None else ink)
    band(H(-0.13, -0.09), H(-0.01, -0.082), 0.006, 0.004, hole)
    band(H(-0.02, -0.02), H(0.06, 0.025), 0.006, 0.005, hole)
    band(H(-0.17, -0.03), H(-0.06, -0.025), 0.005, 0.004, hole)
    d.ellipse([*P(*H(-0.25, -0.075)), *P(*H(-0.225, -0.055))], fill=hole)
    # whiskers: two curling lines trailing from the snout
    lw = max(1, int(round(S * 0.01)))
    for pts_w in (((-0.255, -0.05), (-0.3, -0.03), (-0.31, 0.02), (-0.29, 0.06)),
                  ((-0.22, -0.02), (-0.25, 0.04), (-0.24, 0.1), (-0.21, 0.13))):
        wp = _catmull([H(a, b) for a, b in pts_w], 6)
        d.line([P(*p) for p in wp], fill=ink, width=lw)


if __name__ == "__main__":
    import sys
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (600, 1150), (178, 72, 56, 255))
    draw_dragon(ImageDraw.Draw(im), (30, 30, 570, 1120), gap=(178, 72, 56, 255))
    im.save(sys.argv[1] if len(sys.argv) > 1 else "/tmp/dragon.png")
