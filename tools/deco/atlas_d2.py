"""D2's extra regions of the decorations' atlas (decolib's extension mechanism: imported by decolib, allocated after
the base regions): denser and bigger herb bundles of the drying rack (deco_sechoir), the cut stems over a bundle's
tie, and the crown banner (deco_banniere: navy, gold border, a bold golden rampant lion facing left, the lower end cut
into a point with stepped gold dags). Painters take a w x h RGBA image and a seeded random.Random."""
import math

from galley_texture import _jitter, _mix, _rgb, _scale  # noqa: F401


def _P(img, x, y, c, a=255):
    if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
        img.putpixel((int(x), int(y)), tuple(int(k) for k in c[:3]) + (a,))


def _clear(img):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            img.putpixel((x, y), (0, 0, 0, 0))


ROPE_LIGHT, ROPE_DARK = _rgb("d8c08e"), _rgb("8a7048")
GOLD, GOLD_DARK, GOLD_LIGHT, GOLD_DEEP = _rgb("e0a830"), _rgb("9a6414"), _rgb("f6d470"), _rgb("c07a18")
NAVY, NAVY_DARK = _rgb("34327e"), _rgb("1a1840")


# ---------------------------------------------------------------- herb bundles
def _tie(img, rng, tie):
    """The rope tie at the top centre of a bundle texture (rows 0 .. tie)."""
    w = img.size[0]
    for y in range(tie):
        for x in range(w // 2 - 2, w // 2 + 2):
            _P(img, x, y, ROPE_LIGHT if (x + 2 * y) % 4 else ROPE_DARK)
    for y in range(tie - 2, tie):
        for x in range(w // 2 - 3, w // 2 + 3):
            _P(img, x, y, ROPE_DARK if y == tie - 1 else ROPE_LIGHT)


def _sprigs(w, h, rng, n, tie, spread=0.92, minlen=0.7, curve=0.85):
    """Stem polylines from the tie (top centre) spreading down to the bottom: list of point lists."""
    out = []
    for k in range(n):
        f = (k + 0.5) / n * 2 - 1                          # -1 .. 1 across
        x1 = w / 2 + f * (w / 2) * spread + rng.uniform(-1.2, 1.2)
        L = rng.uniform(minlen, 1.0) * (h - tie - 1)
        L *= 1.0 - 0.18 * abs(f) ** 2                         # the outer sprigs a little shorter: a rounded bottom
        pts = []
        steps = int(L)
        for i in range(steps):
            t = i / max(1, steps - 1)
            x = w / 2 + (x1 - w / 2) * (t ** curve) + 0.6 * math.sin(t * 5 + k)
            pts.append((x, tie + i))
        out.append(pts)
    return out


def p_herbs_green(img, rng):
    """A big dense bunch of green herbs (thyme / rosemary sprigs): leaf pairs pointing down and out along stems
    spreading from the tie, lit on the left."""
    _clear(img)
    w, h = img.size
    tie = 6
    cols = [_rgb("6e9c34"), _rgb("8ab846"), _rgb("a6cc5a"), _rgb("587e2a"), _rgb("44641e")]
    stem = _rgb("566a2a")
    for pts in _sprigs(w, h, rng, 14, tie, spread=0.95, minlen=0.78):
        for i, (x, y) in enumerate(pts):
            _P(img, x, y, stem)
            if i > 3 and i % 3 == 0:
                for side in (-1, 1):
                    ln = 3 + (1 if rng.random() < 0.5 else 0)
                    c = cols[rng.choice((0, 1, 2)) if side < 0 else rng.choice((0, 3, 4))]
                    for j in range(1, ln + 1):
                        xx, yy = x + side * j * 0.8, y + j * 0.9
                        _P(img, xx, yy, _jitter(c, rng, 6))
                        if j < ln:
                            _P(img, xx, yy + 1, _jitter(_scale(c, 0.9), rng, 6))
        # the sprig's tip
        x, y = pts[-1]
        _P(img, x, y + 1, cols[2])
    _tie(img, rng, tie)


def p_herbs_lavender(img, rng):
    """Lavender: green stems from the tie, the lower half of each a dense purple spike."""
    _clear(img)
    w, h = img.size
    tie = 6
    cols = [_rgb("7a4ab4"), _rgb("9a68d4"), _rgb("5c3294"), _rgb("b490e4"), _rgb("4a2878")]
    stem = _rgb("5e7040")
    for k, pts in enumerate(_sprigs(w, h, rng, 13, tie, spread=0.9, minlen=0.72)):
        n = len(pts)
        for i, (x, y) in enumerate(pts):
            t = i / max(1, n - 1)
            if t < 0.4:
                _P(img, x, y, stem)
                if t > 0.15 and i % 4 == 0:
                    _P(img, x + rng.choice((-1, 1)), y + 1, _rgb("6e8450"))
            else:
                for dx in (-1, 0, 1):
                    if dx == 0 or rng.random() < 0.8:
                        c = cols[rng.choice((0, 1, 2, 3)) if dx <= 0 else rng.choice((0, 2, 4))]
                        _P(img, x + dx, y, _jitter(c, rng, 10))
    _tie(img, rng, tie)


def p_herbs_sage(img, rng):
    """Sage-green sprigs: a long thin bunch, soft grey-green elongated leaves along the stems."""
    _clear(img)
    w, h = img.size
    tie = 6
    cols = [_rgb("8aa06a"), _rgb("a6ba84"), _rgb("6c8452"), _rgb("bccca0"), _rgb("56703e")]
    stem = _rgb("5a6a42")
    for pts in _sprigs(w, h, rng, 11, tie, spread=0.85, minlen=0.75, curve=1.0):
        for i, (x, y) in enumerate(pts):
            _P(img, x, y, stem)
            if i > 3 and i % 3 == 0:
                side = 1 if (i // 3) % 2 else -1
                for j in range(1, 4):
                    _P(img, x + side * (1 if j < 3 else 2), y + j, _jitter(cols[rng.choice((0, 1, 3)) if side < 0 else rng.choice((0, 2, 4))], rng, 8))
    _tie(img, rng, tie)


def p_herbs_white(img, rng):
    """White flowers (yarrow / chamomile): green stems, round clusters of small white flowers at the bottom."""
    _clear(img)
    w, h = img.size
    tie = 6
    stem = _rgb("5a7a3a")
    whites = [_rgb("f4f0e2"), _rgb("ffffff"), _rgb("dcd6c4"), _rgb("ece6d2")]
    sprigs = _sprigs(w, h - 3, rng, 12, tie, spread=0.8, minlen=0.62)
    for k, pts in enumerate(sprigs):
        n = len(pts)
        for i, (x, y) in enumerate(pts):
            t = i / max(1, n - 1)
            _P(img, x, y, stem)
            if 0.2 < t < 0.6 and i % 5 == 0:
                _P(img, x + rng.choice((-1, 1)), y, _rgb("6e9446"))
    for k, pts in enumerate(sprigs):
        # clusters of florets along the lower part of the stem: a rounded white mass at the bottom of the bunch
        for t in (0.62, 0.8, 1.0):
            x, y = pts[min(len(pts) - 1, int(t * (len(pts) - 1)))]
            r = rng.uniform(2.4, 3.6)
            for yy in range(int(y - r), int(y + r) + 1):
                for xx in range(int(x - r), int(x + r) + 1):
                    d = math.hypot(xx - x, (yy - y) * 1.15) / r
                    if d < 1 and rng.random() < 0.88:
                        c = whites[0] if (xx + 2 * yy) % 4 else whites[2]
                        if xx < x and yy < y:
                            c = whites[1]
                        if d > 0.8:
                            c = whites[2]
                        _P(img, xx, yy, _jitter(c, rng, 5))
            if rng.random() < 0.5:
                _P(img, x, y, _rgb("e8d06a"))
    _tie(img, rng, tie)


def p_herb_stems(img, rng):
    """The cut stem ends sticking up over a bundle's tie (sides of a small box)."""
    w, h = img.size
    for y in range(h):
        for x in range(w):
            c = (_rgb("5e6e34"), _rgb("4a5a26"), _rgb("74843e"))[(x + (y // 5)) % 3]
            _P(img, x, y, _jitter(c, rng, 8))


# ---------------------------------------------------------------- crown banner
def _lion_mask(W, H):
    """A bold rampant lion facing left (heraldic, gold): True where gold. Designed on a 40 x 62 grid (x right, y
    down), drawn as thick strokes and polygons on a supersampled canvas, then reduced to W x H."""
    from PIL import Image, ImageDraw
    S = 8
    sx, sy = W * S / 40.0, H * S / 62.0
    im = Image.new("L", (W * S, H * S), 0)
    d = ImageDraw.Draw(im)

    def P(pts):
        return [(x * sx, y * sy) for x, y in pts]

    def stroke(pts, width):
        r = width * sx / 2
        d.line(P(pts), fill=255, width=max(1, int(width * sx)), joint="curve")
        for (x, y) in pts:
            d.ellipse((x * sx - r, y * sy - r, x * sx + r, y * sy + r), fill=255)
    # the mane (locks pointing back) and the round head, the muzzle and the open jaws to the left, an ear
    d.polygon(P([(12, 4), (18, 2), (21, 5), (26, 5), (25, 9), (29, 11), (26, 14), (29, 18), (25, 20), (26, 24), (20, 24),
                 (14, 22)]), fill=255)
    d.ellipse(P([(7, 5), (20, 19)]), fill=255)
    d.polygon(P([(2, 8), (9, 7), (10, 13), (3, 13)]), fill=255)            # upper jaw / muzzle
    d.polygon(P([(4, 15), (10, 14), (11, 18), (6, 18)]), fill=255)         # lower jaw
    d.polygon(P([(14, 4), (16, 0), (18, 4)]), fill=255)                     # ear
    # the body: a thick diagonal from the chest (upper left) to the haunches (lower right)
    d.polygon(P([(12, 20), (22, 18), (28, 26), (33, 36), (33, 45), (25, 47), (19, 39), (13, 30)]), fill=255)
    # fore legs: the upper one reaching up to the left (below the jaws), the lower one forwards; claws
    stroke([(15, 23), (9, 22), (4, 19)], 5.0)
    stroke([(16, 31), (9, 33), (4, 32)], 5.0)
    for (x, y) in ((1.5, 17), (1.0, 20.5), (1.5, 30.5), (1.0, 34)):
        stroke([(x + 2, y), (x, y - 0.6)], 1.6)
    # hind legs: the front one striding forward and down, the back one standing; feet with claws
    stroke([(25, 42), (19, 49), (14, 54)], 6.0)
    stroke([(14, 54), (8, 56)], 4.0)
    stroke([(30, 44), (31, 52), (28, 58)], 6.0)
    stroke([(28, 58), (22, 60)], 4.0)
    for (x, y) in ((5.5, 57), (19.5, 61)):
        stroke([(x + 2, y), (x, y + 0.5)], 1.6)
    # the tail curling up behind, ending in a flame-shaped tuft
    stroke([(32, 41), (36, 36), (38, 29), (35, 22), (36, 15)], 2.6)
    d.polygon(P([(33, 16), (34, 9), (37, 3), (40, 8), (39, 14), (36, 17)]), fill=255)
    small = im.resize((W, H), Image.BOX)
    return [[small.getpixel((x, y)) > 100 for x in range(W)] for y in range(H)]


def _paint_lion(img, rng, x0, y0, W, H):
    m = _lion_mask(W, H)

    def on(x, y):
        return 0 <= x < W and 0 <= y < H and m[y][x]
    for y in range(H):
        for x in range(W):
            if not m[y][x]:
                continue
            edge = not (on(x + 1, y) and on(x - 1, y) and on(x, y + 1) and on(x, y - 1))
            if edge:
                c = GOLD_DARK if not on(x, y - 1) is False or not on(x + 1, y) else GOLD_DEEP
                c = GOLD_DARK
            elif not on(x - 1, y - 1) or not on(x, y - 2):
                c = GOLD_LIGHT                                     # lit from the upper left
            elif not on(x + 2, y) or not on(x, y + 2):
                c = GOLD_DEEP                                      # shade on the lower right
            else:
                c = GOLD
            _P(img, x0 + x, y0 + y, _jitter(c, rng, 6))
    # mane locks (darker strands), the eye, the open mouth and its tongue, the line of the haunch
    gx, gy = W / 40.0, H / 62.0
    for (fx, fy) in ((20, 8), (22, 12), (21, 17), (17, 21), (24, 16)):
        _P(img, x0 + int(fx * gx), y0 + int(fy * gy), GOLD_DEEP)
        _P(img, x0 + int(fx * gx) + 1, y0 + int(fy * gy) + 1, GOLD_DEEP)
    _P(img, x0 + int(11 * gx), y0 + int(10 * gy), _rgb("3a1a08"))
    _P(img, x0 + int(12 * gx), y0 + int(10 * gy), _rgb("3a1a08"))
    for x in range(int(3 * gx), int(9 * gx)):
        _P(img, x0 + x, y0 + int(13.8 * gy), _rgb("7a1a10") if x > int(5 * gx) else NAVY)
    _P(img, x0 + int(4 * gx), y0 + int(14.6 * gy), _rgb("c03028"))
    for k in range(5):
        _P(img, x0 + int((23 + k) * gx), y0 + int((36 + k * 1.6) * gy), GOLD_DEEP)


def p_banner_crown(img, rng):
    """The crown banner: navy cloth with soft vertical folds, a gold border (lit / dark edges), the lower end cut
    into a point whose gold edge goes down in steps (dags), the bold golden lion in the middle."""
    w, h = img.size
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.07 * math.sin(2 * math.pi * x / 14 + 0.6 + 0.25 * math.sin(y * 0.08)) + (0.025 if (x + y) % 2 else -0.025)
            _P(img, x, y, _jitter(_scale(NAVY, k), rng, 4))
    body = int(h * 0.72)
    step = 5
    B = 3

    def inside(x, y):
        if x < 0 or x >= w or y < 0 or y >= h:
            return False
        if y < body:
            return True
        q = ((y - body) // step + 1) * step                    # the stepped (dagged) point: a staircase each side
        half = (w / 2) * (1 - q / (h - body + 2)) + 1.5
        return abs(x + 0.5 - w / 2) <= half

    for y in range(h):
        for x in range(w):
            if not inside(x, y):
                _P(img, x, y, (0, 0, 0), 0)
                continue
            # distance (in px, square neighbourhood) to the outside: the gold border follows every edge and step
            dist = 99
            for r in range(1, B + 3):
                if any(not inside(x + dx, y + dy) for dx in range(-r, r + 1) for dy in (-r, r)) or \
                        any(not inside(x + dx, y + dy) for dy in range(-r, r + 1) for dx in (-r, r)):
                    dist = r
                    break
            if dist == 1:
                _P(img, x, y, _jitter(GOLD_DARK, rng, 6))
            elif dist <= B:
                lit = not inside(x - dist, y) or not inside(x, y - dist)
                _P(img, x, y, _jitter(GOLD_LIGHT if (lit and dist == 2) else GOLD, rng, 8))
            elif dist == B + 1:
                _P(img, x, y, NAVY_DARK)
    # the sleeve over the rod: a darker fold line under the top border
    for x in range(B + 1, w - B - 1):
        _P(img, x, B + 3, _scale(img.getpixel((x, B + 3)), 0.8))
    lw = int(w * 0.8)
    lh = int(h * 0.55)
    _paint_lion(img, rng, (w - lw) // 2 + 1, int(h * 0.12), lw, lh)


REGIONS = [
    ("herbs_green_big", 48, 80, p_herbs_green),
    ("herbs_lavender_big", 40, 56, p_herbs_lavender),
    ("herbs_sage_big", 32, 64, p_herbs_sage),
    ("herbs_white_big", 32, 48, p_herbs_white),
    ("herb_stems", 16, 16, p_herb_stems),
    ("banner_crown", 48, 112, p_banner_crown),
]
