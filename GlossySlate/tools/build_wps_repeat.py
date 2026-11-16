"""Repeat "One" on the now playing screen (DESIGN.md 5.8) of Glossy Slate,
without a browser:

    python3 tools/build_wps_repeat.py

rewrites frame 3 (repeat one) of .rockbox/wps/glossyslate/wps_repeat.bmp
from frame 2 (repeat all): the same loop with a small accent dot at its top
left corner and a gap of about 1 px between dot and loop, like the badge of
the quick menu but without the "1" (14 x 10 px are too small for it; the
quick menu shows the "1"). The other frames and the header stay as they
are. Run it after build_assets.py; on an unchanged tree it reproduces the
file byte for byte. Pure Python.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tools import raster as R  # noqa: E402

PATH = os.path.join(os.path.dirname(HERE), '.rockbox', 'wps', 'glossyslate', 'wps_repeat.bmp')
FRAME_H = 10
ALL, ONE = 1, 2              # frame indices from 0: off, all, one, (4), A-B
ACCENT = R.hexc('2160CB')    # design.ACCENT['solid'], the active symbols
DOT = (2.0, 2.2, 1.8)        # centre x, y and radius of the dot in px
GAP = 0.9                    # free ring around the dot


def main():
    d = bytearray(open(PATH, 'rb').read())
    off = struct.unpack_from('<I', d, 10)[0]
    w, h = struct.unpack_from('<ii', d, 18)
    assert struct.unpack_from('<H', d, 28)[0] == 32 and h > 0 and h == 5 * FRAME_H, (w, h)

    def at(frame, y):
        """offset of row y of a frame; the rows are stored bottom-up"""
        return off + (h - 1 - (frame * FRAME_H + y)) * w * 4

    cx, cy, r = DOT
    dot = R.coverage(w, FRAME_H, R.circle(cx, cy, r), 8)
    gap = R.coverage(w, FRAME_H, R.circle(cx, cy, r + GAP), 8)
    for y in range(FRAME_H):
        src, dst = at(ALL, y), at(ONE, y)
        for x in range(w):
            px = d[src + x * 4:src + x * 4 + 4]
            if dot[y][x] or gap[y][x]:
                loop = px[3] / 255.0 * (1 - gap[y][x])
                q = int(round(max(loop, dot[y][x]) * 15))
                if not q:
                    px = bytes(4)
                elif dot[y][x] >= loop:
                    px = bytes((ACCENT[2], ACCENT[1], ACCENT[0], 17 * q))
                else:
                    px = bytes(px[:3]) + bytes((17 * q,))
            d[dst + x * 4:dst + x * 4 + 4] = px
    open(PATH, 'wb').write(d)


if __name__ == '__main__':
    main()
