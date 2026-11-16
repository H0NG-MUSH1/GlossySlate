#!/usr/bin/env python3
# Marks at the end of list rows (apps/gui/bitmap/list.c, IPOD_6G): the
# speaker with three sound waves at the playing track and the dot at
# podcasts and audiobooks not heard yet. Prints them as 4 bit alpha masks in
# the format of list_arrow_mask (0 opaque .. 15 invisible, the first pixel
# in the lower nibble), 16 x 16 supersampled like the arrow.
#
#   python3 tools/ipod6g_list_marks.py            C arrays
#   python3 tools/ipod6g_list_marks.py --ascii    to look at
import math
import sys

SS = 16


def render(w, h, inside):
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            n = 0
            for sy in range(SS):
                for sx in range(SS):
                    if inside(x + (sx + 0.5) / SS, y + (sy + 0.5) / SS):
                        n += 1
            row.append(n / (SS * SS))
        rows.append(row)
    return rows


def speaker(px, py):
    # body and cone, 12 px high, middle at y 6
    if 0.4 <= px <= 2.2 and 4.1 <= py <= 7.9:
        return True
    if 2.2 <= px <= 4.8:
        half = 1.9 + (px - 2.2) / 2.6 * 3.3   # 1.9 px at the body, 5.2 at the end
        if abs(py - 6.0) <= half:
            return True
    # three waves around (4.8, 6), stroke 1.2, +-45 degrees
    dx, dy = px - 4.8, py - 6.0
    r = math.hypot(dx, dy)
    if dx <= 0 or abs(math.degrees(math.atan2(dy, dx))) > 45:
        return False
    return any(abs(r - rr) <= 0.6 for rr in (3.0, 5.6, 8.2))


def dot(px, py):
    return math.hypot(px - 4.0, py - 4.0) <= 3.7


MARKS = [('list_speaker_mask', 'LIST_SPEAKER', 14, 12, speaker),
         ('list_dot_mask', 'LIST_DOT', 8, 8, dot)]


def nibbles(rows):
    out = []
    for row in rows:
        vals = [15 - int(round(a * 15)) for a in row]
        out.append([vals[i] | (vals[i + 1] << 4) for i in range(0, len(vals), 2)])
    return out


if __name__ == '__main__':
    for name, macro, w, h, fn in MARKS:
        rows = render(w, h, fn)
        if '--ascii' in sys.argv:
            print(name)
            for row in rows:
                print(''.join(' .:-=+*#%@'[min(9, int(a * 9.99))] for a in row))
            continue
        print('static const unsigned char %s[%s_H * %s_W / 2]' % (name, macro, macro))
        print('    __attribute__((aligned(4))) =\n{')
        for line in nibbles(rows):
            print('    ' + ', '.join('0x%02x' % b for b in line) + ',')
        print('};')
