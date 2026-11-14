"""Item icons of the door keys (1.32.0): 16 x 16 pixel art, drawn here pixel by pixel.

  textures/item/cle.png              the key: an iron shaft and bit, a brass bow
  textures/item/cle_universelle.png  the administrators' master key: all gold, a trefoil bow with a ruby, a collar,
                                     a three-toothed bit

Each map below is the key's silhouette, one letter per pixel (the material); the shading (light towards the top left,
dark towards the bottom right, as the vanilla items) and the dark outline are added by the script.

usage: python3 tools/keys/generate_key_icons.py [--preview DIR]   (writes the two PNGs; --preview: 16x enlargements)
"""
import os
import sys

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src', 'main', 'resources', 'assets', 'medievalships',
                    'textures', 'item')

# materials: (light, mid, dark)
IRON = ((0xE6, 0xEA, 0xEE), (0xA4, 0xAB, 0xB2), (0x63, 0x6A, 0x72))
BRASS = ((0xF4, 0xD9, 0x86), (0xCC, 0x99, 0x34), (0x8C, 0x60, 0x1C))
GOLD = ((0xFF, 0xF4, 0xB0), (0xF2, 0xBE, 0x2C), (0xA6, 0x6E, 0x0C))
RUBY = ((0xFF, 0x9A, 0x8A), (0xD4, 0x2A, 0x26), (0x7E, 0x10, 0x14))
OUTLINE = {'iron': (0x24, 0x26, 0x2A), 'brass': (0x3A, 0x26, 0x0C), 'gold': (0x4A, 0x2E, 0x06), 'ruby': (0x3C, 0x08, 0x0A)}
MATERIALS = {'i': ('iron', IRON), 'b': ('brass', BRASS), 'g': ('gold', GOLD), 'r': ('ruby', RUBY)}

# the key: bow (brass ring) bottom left, shaft (iron) up to the top right, the bit's two teeth below its end
KEY = [
    "................",
    "............ii..",
    "...........iii..",
    "..........iiiii.",
    ".........iii.ii.",
    "........iii..i..",
    ".......iii......",
    "...bbb.ii.......",
    "..bbbbbi........",
    ".bbb.bbb........",
    ".bb...bb........",
    ".bb...bb........",
    ".bbb.bbb........",
    "..bbbbb.........",
    "...bbb..........",
    "................",
]

# the master key: the same build, all gold, a ruby set in the bow, a collar on the shaft, an ornate bit
MASTER = [
    "................",
    "............gg..",
    "...........ggg..",
    "..........ggggg.",
    ".........ggg.g..",
    "........ggg.ggg.",
    "......gggg...g..",
    "...ggg.ggg......",
    "..gggggg........",
    ".ggggggg........",
    ".ggrrrgg........",
    ".ggrrrgg........",
    ".ggggggg........",
    "..ggggg.........",
    "...ggg..........",
    "................",
]


def draw(rows, sparkle=False):
    h, w = len(rows), len(rows[0])
    assert h == 16 and all(len(r) == 16 for r in rows), "16 x 16"
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()

    def filled(x, y):
        return 0 <= x < w and 0 <= y < h and rows[y][x] != '.'

    def same(x, y, c):
        return 0 <= x < w and 0 <= y < h and rows[y][x] == c

    for y in range(h):
        for x in range(w):
            c = rows[y][x]
            if c == '.':
                continue
            name, (light, mid, dark) = MATERIALS[c]
            # the light comes from the top left: an edge facing it is light, one facing away dark (a gem: its own edges)
            inside = (lambda xx, yy: same(xx, yy, c)) if c == 'r' else filled
            lit = not inside(x - 1, y) or not inside(x, y - 1)
            shade = not inside(x + 1, y) or not inside(x, y + 1)
            col = light if lit and not shade else dark if shade and not lit else mid
            px[x, y] = col + (255,)
    # the outline: every empty pixel next to the key (four neighbours) takes the dark colour of its material
    out = img.copy()
    opx = out.load()
    for y in range(h):
        for x in range(w):
            if filled(x, y):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if filled(x + dx, y + dy):
                    opx[x, y] = OUTLINE[MATERIALS[rows[y + dy][x + dx]][0]] + (255,)
                    break
    if sparkle:
        # a glint on the bow and the shaft of the master key
        for (x, y) in ((2, 9), (9, 5), (3, 10)):
            if filled(x, y):
                opx[x, y] = (0xFF, 0xFF, 0xF0, 255)
    return out


def main():
    preview = None
    if '--preview' in sys.argv:
        preview = sys.argv[sys.argv.index('--preview') + 1]
    for name, rows, sparkle in (('cle', KEY, False), ('cle_universelle', MASTER, True)):
        img = draw(rows, sparkle)
        path = os.path.normpath(os.path.join(ROOT, name + '.png'))
        img.save(path)
        print('wrote', path)
        if preview:
            big = Image.new('RGBA', (16 * 16, 16 * 16), (90, 90, 96, 255))
            big.alpha_composite(img.resize((256, 256), Image.NEAREST))
            big.save(os.path.join(preview, name + '_x16.png'))


if __name__ == '__main__':
    main()
