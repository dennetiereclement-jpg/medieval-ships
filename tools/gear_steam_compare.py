#!/usr/bin/env python3
"""Camera-matched comparison of the Gear Steamship model with its reference picture.

    python3 tools/gear_steam_compare.py <reference.png> <out.png> [model.bbmodel]

The camera of the reference (one starboard view, bow to the right) is fitted on points measured on the
picture (POINTS: ship-local point -> pixel), then the model is rendered by tools/preview.py from that camera
and pasted beside the reference (top: reference, bottom: render), both 640 wide; the fitted points are
drawn on both (red: measured, green: where the model's point falls). Also writes <out>_side.png, an
orthographic starboard view, and prints the residuals.
"""
import base64
import io
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import preview as pv  # noqa: E402
import gear_steam_shape as gs  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W0, H0 = 1672, 941

# ship-local point (x port, y up, z bow) -> pixel of the reference (1672 x 941)
POINTS = [
    ((0.0, 0.0, gs.stem_z(0.0)), (1350, 745)),                      # stem at the waterline
    ((-3.25, 6.92, gs.GALLERY_Z - 0.25), (107, 462)),               # stern gallery, top rail's aft corner (starboard)
    ((0.0, gs.FUNNEL_TOP, gs.FUNNEL_Z), (545, 100)),                # funnel top (phase 4: measured again, 545 px, not 527)
    ((0.0, 20.0, gs.MAIN_MAST_Z), (962, 5)),                        # main masthead box top
    ((0.0, 18.1, gs.MIZZEN_Z), (272, 105)),                         # mizzen masthead box top
    ((-5.25, gs.BIG_GEAR[0], gs.BIG_GEAR[1]), (640, 560)),          # big gear centre (starboard)
    ((-(gs.hull_x(gs.BOW_GEAR[1], gs.BOW_GEAR[0]) + 0.2), gs.BOW_GEAR[0], gs.BOW_GEAR[1]), (1320, 545)),   # bow gear
    (gs.BOOM_TIP, (1620, 343)),                                     # bow boom tip
    ((0.0, gs.DOME_TOP, gs.DOME_Z), (687, 225)),                    # dome top
    ((-4.55, gs.WAIST_CAP_Y, gs.FORECASTLE_Z), (1085, 548)),        # waist cap at the forecastle's break
    ((0.0, sum(gs.CRATE_Y) / 2, gs.CRANE_TIP[2]), (96, 416)),       # hanging crate
    ((0.0, gs.STEM_HEAD[1], gs.STEM_HEAD[2]), (1500, 333)),         # stem head
    # phase 4: points along the stern and the middle, so that the fit does not trade the stern's places for perspective
    ((-gs.DECKHOUSE_HALF, gs.BRIDGE_Y, gs.DECKHOUSE_Z[0]), (314, 330)),                     # deckhouse, aft top corner
    ((-gs.hull_x(gs.CREW_WINDOWS_Z[0], 5.65), 5.65, gs.CREW_WINDOWS_Z[0]), (280, 510)),     # crew window, aft
    ((-(gs.hull_x(gs.PIPE_ARCH_Z[1], 8.2) + 0.55), 8.2, gs.PIPE_ARCH_Z[1]), (750, 452)),    # the U pipe's fore elbow
    ((-gs.hull_x(5.0, 3.0), 3.0, 5.0), (825, 610)),                                          # hold window, fore
]


def basis(yaw, pitch):
    fwd = np.array([math.cos(pitch) * math.sin(yaw), math.sin(pitch), math.cos(pitch) * math.cos(yaw)])
    right = np.cross(fwd, [0, 1, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return fwd, right, up


def project(params, pts, W=W0, H=H0):
    ex, ey, ez, yaw, pitch, fov = params
    fwd, right, up = basis(yaw, pitch)
    f = (H / 2) / math.tan(math.radians(fov) / 2)
    out = []
    for p in pts:
        d = np.array(p, float) - [ex, ey, ez]
        z = d @ fwd
        out.append((W / 2 + (d @ right) * f / z, H / 2 - (d @ up) * f / z))
    return np.array(out)


def fit():
    pts = [p for p, _ in POINTS]
    px = np.array([q for _, q in POINTS], float)
    best = None
    for yaw0 in (math.radians(70), math.radians(80), math.radians(95), math.radians(105)):
        x = np.array([-55.0 * math.sin(yaw0), 8.0, -55.0 * math.cos(yaw0) + 2.0, yaw0, -0.05, 32.0])
        lam = 1e-2
        for _ in range(400):
            r = (project(x, pts) - px).ravel()
            J = np.zeros((len(r), 6))
            for k in range(6):
                dx = np.zeros(6)
                dx[k] = 1e-4 * (1 if k >= 3 else 100)
                J[:, k] = ((project(x + dx, pts) - px).ravel() - r) / dx[k]
            A = J.T @ J + lam * np.diag(np.diag(J.T @ J) + 1e-9)
            step = np.linalg.solve(A, -J.T @ r)
            xn = x + step
            rn = (project(xn, pts) - px).ravel()
            if rn @ rn < r @ r:
                x, lam = xn, lam * 0.5
            else:
                lam *= 4
        err = float(np.sqrt(np.mean(((project(x, pts) - px) ** 2).sum(1))))
        if best is None or err < best[1]:
            best = (x, err)
    return best


def camera(params):
    ex, ey, ez, yaw, pitch, fov = params
    fwd, _, _ = basis(yaw, pitch)
    eye = np.array([ex, ey, ez])
    return eye, eye + fwd * 40.0, fov


def load(path):
    model = json.load(open(path))
    tex = [np.array(Image.open(io.BytesIO(base64.b64decode(t["source"].split(",", 1)[1]))).convert("RGBA")).astype(float)
           for t in model["textures"]]
    return model, tex


def with_water(quads, tex, y=0.0, size=48.0):
    """The sea: an opaque plane at the waterline (the reference shows nothing under the water)."""
    water = np.zeros((4, 4, 4))
    water[..., :3] = (38, 62, 96)
    water[..., 3] = 255
    k = len(tex)
    tiles = []
    step = 6.0
    for x0 in np.arange(-size, size, step):
        for z0 in np.arange(-size, size, step):
            corners = [np.array(c, float) for c in ((x0, y, z0), (x0 + step, y, z0), (x0 + step, y, z0 + step), (x0, y, z0 + step))]
            tiles.append((corners, [(0, 0), (4, 0), (4, 4), (0, 4)], False, k))
    return quads + tiles, tex + [water]


def main():
    ref_path, out = sys.argv[1], sys.argv[2]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mpath = args[2] if len(args) > 2 else os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/gear_steamship.bbmodel")
    params, err = fit()
    print("camera: eye (%.1f, %.1f, %.1f) yaw %.1f pitch %.1f fov %.1f, rms %.1f px" % (
        params[0], params[1], params[2], math.degrees(params[3]), math.degrees(params[4]), params[5], err))
    pts = [p for p, _ in POINTS]
    proj = project(params, pts)
    for (p, q), r in zip(POINTS, proj):
        print("   %-28s measured %s model %s" % (tuple(round(c, 1) for c in p), q, tuple(int(round(c)) for c in r)))
    model, tex = load(mpath)
    quads = pv.build_mesh(model, {"sail_furl": 0.0, "steer": 1.0, "flag_wave": 0.2})
    quads, tex = with_water(quads, tex)
    eye, tgt, fov = camera(params)
    W, H = 640, 360
    im = pv.render(quads, tex, W=W, H=H, eye=tuple(eye), target=tuple(tgt), fov=fov, bg=(150, 170, 200))
    ref = Image.open(ref_path).convert("RGB").resize((W, H))
    s = W / W0
    for img, col, pp in ((ref, (255, 40, 40), [q for _, q in POINTS]), (im, (40, 255, 40), proj)):
        d = ImageDraw.Draw(img)
        for x, y in pp:
            d.rectangle((x * s - 2, y * s - 2, x * s + 2, y * s + 2), outline=col)
    sheet = Image.new("RGB", (W, 2 * H))
    sheet.paste(ref, (0, 0))
    sheet.paste(im, (0, H))
    sheet.save(out)
    side = pv.render([q for q in quads if q[3] < len(tex) - 1], tex, W=640, H=320, eye=(-80, 9, 1.5), target=(0, 9, 1.5), ortho=52, bg=(150, 170, 200))
    side.save(os.path.splitext(out)[0] + "_side.png")
    if "--zoom" in sys.argv:
        # close-ups: stern, middle, bow (reference crop | render crop, same camera, 1280 x 720)
        Wz, Hz = 1280, 720
        big = pv.render(quads, tex, W=Wz, H=Hz, eye=tuple(eye), target=tuple(tgt), fov=fov, bg=(150, 170, 200))
        refz = Image.open(ref_path).convert("RGB").resize((Wz, Hz))
        boxes = [(0, 60, 460, 600), (380, 120, 840, 660), (820, 160, 1280, 700)]
        sheet = Image.new("RGB", (920, 540 * 3))
        for k, b in enumerate(boxes):
            sheet.paste(refz.crop(b), (0, 540 * k))
            sheet.paste(big.crop(b), (460, 540 * k))
        sheet.save(os.path.splitext(out)[0] + "_zoom.png")
    print("wrote", out)


if __name__ == "__main__":
    main()
