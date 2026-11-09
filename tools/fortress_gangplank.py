"""The boarding gangplank of the Fortress Ship (fortress_ship), with the gangplank system of tools/gangplank/ships_g2.py
(docs/PASSERELLES.md): its spec, its plank model, the flush fit of its compact stowed pack. ships_g2.py is not edited:
this helper adds the ship's spec to its SPECS table at run time and calls its writers for this ship only.

    python3 tools/fortress_gangplank.py            # gangplanks/fortress_ship.json + models/entity/gangplank_fortress_ship.bbmodel
    python3 tools/fortress_gangplank.py compact    # model surface under the stowed pack (after generate_fortress.py)

Placement (rules of ships_g2.py): starboard, amidships on the waist between the main shrouds (z < -0.6) and the
starboard stair to the forecastle (z > 3.5), clear of the stone ribs' heads; the hinge at the top of the waist's
bulwark (6.0, the collision top of the stone gunwale and its rail) on the hull's outer face; the stairs fill from
the main deck (4.5) to the hinge against the bulwark; the lever stands on the deck aft of them. No stone merlon nor
rail is drawn over the plank's width (tools/generate_fortress.py GANGPLANK_Z). The stowed pack hangs flat on the
stone belt; its outer skin wears the hull's colours (gangplanklib.CAMO "fortress_ship": grey stone, iron trim).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "gangplank"))
import ships_g2 as g2  # noqa: E402
import fortress_shape as fs  # noqa: E402

SHIP = "fortress_ship"
Z = 1.6                     # centre of the plank along the hull
WIDTH = 3.0
HINGE_Y = 6.0               # FortressLayout.WAIST_WALL
HINGE_X = round(fs.hull_x(Z, fs.WAIST_TOP), 2)             # the hull's outer face (the bulwark rises straight from the sheer)
INNER_X = round(HINGE_X - 0.6, 2)                           # the bulwark's inner face (interior grid)
# compact stowed pack (1.23.2): segments, stow_drop, stow_offset, stow_tilt (from `compact`, rounded up to 0.01)
COMPACT = (None, 0.6, 0.39, 4)

g2.place(SHIP, "starboard", Z, WIDTH, HINGE_Y, HINGE_X, fs.MAIN_DECK_Y, INNER_X, 9.0, "dark_wood", (-15, 42), rail_gap=False, lever_end=-1)
_n, _drop, _off, _tilt = COMPACT
if _n:
    g2.SPECS[SHIP]["segments"] = _n
if _drop is not None:
    g2.SPECS[SHIP]["stow_drop"] = _drop
g2.SPECS[SHIP]["stow_offset"] = _off
if _tilt:
    g2.SPECS[SHIP]["stow_tilt"] = _tilt


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "compact":
        worst, rows = g2.compact_probe(SHIP)
        sp = g2.SPECS[SHIP]
        off, tilt, gap = g2.fit_stow(rows, sp.get("stow_drop", g2.STOW_DROP))
        print("%s: model surface up to %.3f outboard of the hinge over the compact pack (spec stow_offset %s); flush fit: stow_offset %.3f "
              "stow_tilt %d (largest gap %.3f)" % (SHIP, worst, sp.get("stow_offset"), off, tilt, gap))
        print("   ", " ".join("%.2f:%.2f" % r for r in rows))
        return
    g2.write_specs([SHIP])
    g2.make_models([SHIP])


if __name__ == "__main__":
    main()
