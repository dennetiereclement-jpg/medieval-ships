"""Hull profile shared by the model generator.

MUST stay identical to fr.medievalships.core.HullProfile (Java), which uses
the same formulas for deck/wall collisions, seats and terrain probes.

Ship-local coordinates, in blocks:
  x = lateral (+x = port / babord), y = up (0 = waterline), z = forward (+z = bow).
"""

HALF_LENGTH = 10.0
MAIN_DECK_Y = 0.45
RAISED_DECK_Y = 0.95
AFT_DECK_START = -6.6   # z below this: raised stern deck (poupe)
FORE_DECK_START = 7.2   # z above this: raised bow platform (proue)


def half_width(z):
    a = abs(z) / 10.3
    if a >= 1.0:
        return 0.0
    return 2.55 * (1.0 - a ** 2.3) ** 0.75


def deck_y(z):
    if z < AFT_DECK_START or z > FORE_DECK_START:
        return RAISED_DECK_Y
    return MAIN_DECK_Y


def rail_y(z):
    return 1.6 + 1.0 * (abs(z) / 10.0) ** 3


def keel_y(z):
    return -1.2 + 1.0 * (abs(z) / 10.0) ** 4


def inner_half_width(z):
    """Half width of the walkable deck (inside of the planking)."""
    return max(0.0, 0.97 * half_width(z) - 0.12)
