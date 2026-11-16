"""The Glossy Slate logo tile in the sidebar of the System menu:

    python3 tools/build_system_logo.py

tools/sources/glossyslate_logo.png is the finished tile (480 x 480, RGBA,
hard edges). This script scales it to 88 x 88 px as an area average of the
premultiplied pixels (so the round corners come out smooth), puts it onto
sidebar.bmp at the place where the skin shows it and writes it opaque as
system_logo.bmp: a 24 bit BMP with RGB565 values and the 4 x 4 ordered
dither of build_side_reflections.py, anchored to the screen. The skin engine
loads such values without change. Needs Pillow and NumPy.

Place (DESIGN.md 6.2): x 36, y 51 of the sidebar (screen 196, 51), above
"Glossy Slate" and the version in the viewports TileSys of glossyslate.sbs.
No reflection: the name stands directly below the tile.
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tools import raster as R  # noqa: E402
from build_side_reflections import PKG, SRC, SIDE_X, dither565, write_bmp24  # noqa: E402

SIZE = 88                        # like the USB logo
PLACE = (36, 51)                 # top left corner on the sidebar


def area_weights(n_in, n_out):
    """matrix that averages n_in samples down to n_out (exact pixel overlap)"""
    w = np.zeros((n_out, n_in))
    scale = n_in / n_out
    for o in range(n_out):
        lo, hi = o * scale, (o + 1) * scale
        for i in range(int(np.floor(lo)), int(np.ceil(hi))):
            w[o, i] = (min(hi, i + 1) - max(lo, i)) / scale
    return w


def main():
    src = np.asarray(Image.open(os.path.join(SRC, 'glossyslate_logo.png')).convert('RGBA'), dtype=np.float64)
    alpha = src[..., 3] / 255.0
    pre = src[..., :3] * alpha[..., None]
    wy = area_weights(src.shape[0], SIZE)
    wx = area_weights(src.shape[1], SIZE)
    a = wy @ alpha @ wx.T
    rgb = np.stack([wy @ pre[..., c] @ wx.T for c in range(3)], axis=-1)
    side = R.read_bmp(os.path.join(PKG, 'sidebar.bmp'))
    out = []
    for y in range(SIZE):
        row = []
        for x in range(SIZE):
            sx, sy = PLACE[0] + x, PLACE[1] + y
            ur, ug, ub, _ = side[sy][sx]
            k = a[y, x]
            if k <= 0:
                row.append((ur, ug, ub))          # the sidebar unchanged
                continue
            # premultiplied colour over the sidebar
            mix = tuple(rgb[y, x, c] + u * (1 - k) for c, u in enumerate((ur, ug, ub)))
            row.append(dither565(mix, SIDE_X + sx, sy))
        out.append(row)
    write_bmp24(os.path.join(PKG, 'system_logo.bmp'), out)
    print('system_logo.bmp  %d x %d at %d,%d of the sidebar, opaque' % (SIZE, SIZE, PLACE[0], PLACE[1]))


if __name__ == '__main__':
    main()
