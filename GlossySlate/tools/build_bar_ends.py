"""Progress and volume bar of the now playing screen with a fixed left end:

    python3 tools/build_bar_ends.py

The skin engine draws the fill of %pb/%pv up to the position and puts the
slider (wps_cap.bmp, straight on the left, round on the right) there. Near
the start the fill's round left end was not drawn and the cap's straight
edge stood out of the track's rounding. The skin therefore shows the left
5 px of the fill as a fixed image in its own viewport (like the adwaitapod
volume slider), and the bar with the cap starts behind it.

Cuts tools/sources/wps_fill.bmp and wps_vfill.bmp (32 bit BMPs from
build_assets.py) into <name>_l.bmp (columns 0-4) and <name>_r.bmp (the rest)
in .rockbox/wps/glossyslate/.
"""
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'sources')
PKG = os.path.join(os.path.dirname(HERE), '.rockbox', 'wps', 'glossyslate')
LEFT = 5


def read32(path):
    d = open(path, 'rb').read()
    off = struct.unpack_from('<I', d, 10)[0]
    w, h = struct.unpack_from('<ii', d, 18)
    assert struct.unpack_from('<H', d, 28)[0] == 32
    rows = [d[off + y * w * 4:off + (y + 1) * w * 4] for y in range(abs(h))]
    if h > 0:
        rows.reverse()                  # top row first
    return w, rows


def write32(path, rows, w):
    data = b''.join(reversed(rows))
    hdr = struct.pack('<2sIHHI', b'BM', 54 + len(data), 0, 0, 54)
    info = struct.pack('<IiiHHIIiiII', 40, w, len(rows), 1, 32, 0, len(data), 2835, 2835, 0, 0)
    open(path, 'wb').write(hdr + info + data)


for name in ('wps_fill', 'wps_vfill'):
    w, rows = read32(os.path.join(SRC, name + '.bmp'))
    write32(os.path.join(PKG, name + '_l.bmp'), [r[:LEFT * 4] for r in rows], LEFT)
    write32(os.path.join(PKG, name + '_r.bmp'), [r[LEFT * 4:] for r in rows], w - LEFT)
    print('%s: %d px -> %s_l.bmp %d px + %s_r.bmp %d px' % (name, w, name, LEFT, name, w - LEFT))
