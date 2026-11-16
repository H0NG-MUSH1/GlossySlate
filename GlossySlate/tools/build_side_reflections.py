"""Smooth reflections for the pictures on the blue sidebar, without a browser:

    python3 tools/build_side_reflections.py

The default cover of the mini player (cover100_fx.bmp) and the preview of
"Album Art Corners" (artprev.bmp) came as 32 bit BMPs with 16 alpha steps (the
skin engine keeps only 4 bits anyway). Their reflection, 60 % -> 0 over
35/36 px, showed as broad bands. This script takes the alpha versions in
tools/sources/, computes the reflection again with full precision (the
mirrored cover rows, opacity 0.6 * (1 - (k + 0.5) / height) times the
coverage of the mirrored pixel), puts both pictures onto sidebar.bmp at the
place where the skin shows them and writes them opaque, as 24 bit BMPs with
RGB565 values and a 4 x 4 ordered dither (anchored to the screen, so it
fits the dither of the firmware cover effect). The skin engine loads such
values without change.

Places (DESIGN.md 5.4): artprev.bmp at x 41, y 79 of the sidebar (viewports
SideArtR/SideArtS), cover100_fx.bmp at x 30, y 36 (viewport Cover at 189,35
plus the image offset 1,1). Both lie on the plain sidebar.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tools import raster as R  # noqa: E402

PKG = os.path.join(os.path.dirname(HERE), '.rockbox', 'wps', 'glossyslate')
SRC = os.path.join(HERE, 'sources')
SIDE_X = 160                     # the sidebar starts at x 160 on the screen

# name, cover height, reflection height, opacity, place on the sidebar
PICTURES = [
    ('artprev.bmp', 78, 35, 0.60, (41, 79)),
]
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def quant(v, bits, t):
    m = (1 << bits) - 1
    q = int(v * m / 255.0 + t)
    q = max(0, min(m, q))
    return (q << (8 - bits)) | (q >> (2 * bits - 8))


def dither565(rgb, ax, ay):
    t = (BAYER[ay & 3][ax & 3] + 0.5) / 16.0
    return (quant(rgb[0], 5, t), quant(rgb[1], 6, t), quant(rgb[2], 5, t))


def write_bmp24(path, rows):
    h, w = len(rows), len(rows[0])
    stride = (w * 3 + 3) & ~3
    data = bytearray()
    for row in reversed(rows):
        line = bytearray()
        for r, g, b in row:
            line += bytes((b, g, r))
        line += b'\0' * (stride - len(line))
        data += line
    hdr = struct.pack('<2sIHHI', b'BM', 54 + len(data), 0, 0, 54)
    info = struct.pack('<IiiHHIIiiII', 40, w, h, 1, 24, 0, len(data), 2835, 2835, 0, 0)
    open(path, 'wb').write(hdr + info + data)


def build(name, cover_h, refl_h, opacity, place):
    src = R.read_bmp(os.path.join(SRC, name))
    side = R.read_bmp(os.path.join(PKG, 'sidebar.bmp'))
    w = len(src[0])
    fh = cover_h + refl_h
    frames = len(src) // fh
    out = []
    for f in range(frames):
        fr = src[f * fh:(f + 1) * fh]
        for y in range(fh):
            row = []
            for x in range(w):
                if y < cover_h:
                    r, g, b, a = fr[y][x]
                else:
                    k = y - cover_h
                    r, g, b, ma = fr[cover_h - 1 - k][x]
                    a = opacity * (1 - (k + 0.5) / refl_h) * ma
                sx, sy = place[0] + x, place[1] + y
                ur, ug, ub, _ = side[sy][sx]
                if a <= 0:
                    row.append((ur, ug, ub))          # the sidebar unchanged
                    continue
                mix = (ur + (r - ur) * a, ug + (g - ug) * a, ub + (b - ub) * a)
                row.append(dither565(mix, SIDE_X + sx, sy))
            out.append(row)
    write_bmp24(os.path.join(PKG, name), out)
    print('%-16s %d x %d, %d frames, opaque' % (name, w, fh, frames))


if __name__ == '__main__':
    for p in PICTURES:
        build(*p)
