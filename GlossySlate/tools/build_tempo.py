"""Parts of the tempo screen (pitch_screen.rock, DESIGN.md 5.12):

    python3 tools/build_tempo.py

tools/tempo/*.bmp are the parts of the designer's boards "Tempo" (32 bit with
alpha, made by the design's own tools). The plugin pitch_screen draws them
itself while the screen is open (apps/plugins/pitch_screen.c); it looks for
them in .rockbox/wps/<status bar skin>/tempo/.

This script writes them there, dithered to RGB565 at their place on the
screen (4 x 4 ordered dither, as build_quickmenu.py does for the quick menu):
the bitmap loader rounds every channel by itself, and the light surfaces
would show tinted bands. The middle of the capsules is widened from 1 to
4 px, so that the plugin can repeat it without repeating one dither column.
The field of the screen is not a picture: the plugin draws it as the same
dithered gradient as the quick menu. Pure Python.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_quickmenu as QM  # noqa: E402  (_dither_rows, _write)

SRC = os.path.join(HERE, 'tempo')
OUT = 'tempo'                     # below .rockbox/wps/glossyslate/

# name: place of the part on the screen (top left), the anchor of the dither
PARTS = {
    'capsule_left': (14, 14), 'capsule_middle': (26, 14), 'capsule_right': (92, 14),
    'icon_mode': (25, 21), 'key_100': (250, 14), 'key_back': (282, 14),
    'divider': (14, 58), 'value_field': (80, 72),
    'icon_slower': (22, 139), 'icon_faster': (276, 138),
    'slider_track': (55, 142), 'slider_fill': (55, 142), 'slider_knob': (167, 137),
    'slider_mark': (159, 155),
    'key': (13, 176), 'key_held': (13, 176),            # right key at 177: same phase
    'arrow_left': (23, 193), 'arrow_right': (292, 193),
    'arrow_left_white': (23, 193), 'arrow_right_white': (292, 193),
    'icon_wheel': (148, 185), 'icon_pitch': (14, 74), 'icon_speed': (14, 110),
}
MIDDLE_W = 4


def read_rows(name, src=SRC):
    """32 bit BMP -> (width, rows of BGRA bytes, top first)"""
    d = open(os.path.join(src, name + '.bmp'), 'rb').read()
    off = struct.unpack_from('<I', d, 10)[0]
    w, h = struct.unpack_from('<ii', d, 18)
    assert struct.unpack_from('<H', d, 28)[0] == 32, name
    rows = [d[off + y * w * 4:off + (y + 1) * w * 4] for y in range(abs(h))]
    return w, (rows[::-1] if h > 0 else rows)


def write_parts(src, out, parts):
    """the parts of a screen, dithered at their places; also used by
    build_eq.py. A capsule middle ('..._middle') is widened to MIDDLE_W."""
    os.makedirs(os.path.join(QM.OUT, out), exist_ok=True)
    for name, (x0, y0) in parts.items():
        w, rows = read_rows(name, src)
        if name.endswith('_middle'):
            # the source is padded to an even width; its first column is the middle
            rows = [r[:4] * MIDDLE_W for r in rows]
            w = MIDDLE_W
        QM._write(os.path.join(out, name + '.bmp'), w, QM._dither_rows(rows, w, x0, y0))
    print('%s: %d parts -> %s' % (out, len(parts), os.path.join(QM.OUT, out)))


def main():
    write_parts(SRC, OUT, PARTS)


if __name__ == '__main__':
    main()
