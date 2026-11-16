#!/usr/bin/env python3
# Turns images into the RGB565 pictures that album lists on the iPod 6G
# draw: the default cover (apps/albumart_list_default.h) and those of the
# special entries at their top (apps/albumart_list_special.h):
#
#   python3 tools/ipod6g_albumart_header.py apps/albumart_list_default.h \
#       albumart_list_default=GlossySlate/firmware-assets/albumart_list_default_512.png
#   python3 tools/ipod6g_albumart_header.py apps/albumart_list_special.h \
#       albumart_list_by_album=GlossySlate/firmware-assets/albumart_list_by_album_512.png \
#       albumart_list_all_tracks=GlossySlate/firmware-assets/albumart_list_all_tracks_512.png \
#       albumart_list_random=GlossySlate/firmware-assets/albumart_list_random_512.png
#
# Each image is scaled to ALBUMART_LIST_SIZE (apps/albumart_list.h) with sips
# (macOS) and dithered with a 4 x 4 Bayer matrix, so dark gradients show no
# bands on the RGB565 display.

import os
import re
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIDE = int(re.search(r'#define ALBUMART_LIST_SIZE (\d+)',
                     open(os.path.join(ROOT, 'apps', 'albumart_list.h')).read()).group(1))
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def load_bmp24(path):
    d = open(path, 'rb').read()
    offset = struct.unpack_from('<I', d, 10)[0]
    w, h = struct.unpack_from('<ii', d, 18)
    bpp = struct.unpack_from('<H', d, 28)[0]
    assert bpp in (24, 32), (path, bpp)
    step = bpp // 8
    stride = (w * step + 3) & ~3
    rows = []
    for y in range(abs(h)):
        ry = abs(h) - 1 - y if h > 0 else y
        base = offset + ry * stride
        rows.append([tuple(d[base + x * step + 2 - c] for c in range(3)) for x in range(w)])
    return rows


def scaled(path):
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'thumb.bmp')
        subprocess.run(['sips', '-s', 'format', 'bmp', '-z', str(SIDE), str(SIDE),
                        path, '--out', out], check=True, stdout=subprocess.DEVNULL)
        return load_bmp24(out)


def level(v, bits, x, y):
    levels = (1 << bits) - 1
    t = (BAYER[y & 3][x & 3] + 0.5) / 16
    return min(levels, int(v * levels / 255 + t))


def rgb565(rows):
    return [level(r, 5, x, y) << 11 | level(g, 6, x, y) << 5 | level(b, 5, x, y)
            for y, row in enumerate(rows) for x, (r, g, b) in enumerate(row)]


def main():
    if len(sys.argv) < 3:
        sys.exit('usage: %s <header.h> <name>=<image> ...' % sys.argv[0])
    guard = 'ROCKBOX_' + re.sub(r'\W', '_', os.path.basename(sys.argv[1])).upper()
    out = ['/* %d x %d RGB565 pictures for album lists,' % (SIDE, SIDE),
           ' * made by tools/ipod6g_albumart_header.py from:']
    out += [' *   %s' % arg.split('=', 1)[1] for arg in sys.argv[2:]]
    out += [' */', '#ifndef ' + guard, '#define ' + guard]
    for arg in sys.argv[2:]:
        name, path = arg.split('=', 1)
        rows = scaled(path)
        assert len(rows) == SIDE and len(rows[0]) == SIDE, path
        values = rgb565(rows)
        out.append('static const fb_data %s[ART_PIXELS] = {' % name)
        for i in range(0, len(values), 10):
            out.append('    ' + ' '.join('0x%04x,' % v for v in values[i:i + 10]))
        out.append('};')
    out += ['#endif', '']
    open(sys.argv[1], 'w').write('\n'.join(out))
    print('%s: %d pictures, %d x %d' % (sys.argv[1], len(sys.argv) - 2, SIDE, SIDE))


if __name__ == '__main__':
    main()
