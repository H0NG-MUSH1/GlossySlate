#!/usr/bin/env python3
# Converts a TrueType font into a Rockbox font (.fnt, RB12, 4 bit
# anti-aliasing) without Rockbox's convttf, which needs FreeType at build
# time. Needs freetype-py (pip install freetype-py), which brings FreeType.
#
#   python3 tools/ipod6g_ttf2fnt.py Arimo-Bold.ttf 14 18 18-Arimo-Bold14.fnt
#
# arguments: TrueType file, pixel size (em), line height, output file.
# The glyphs are rendered with light hinting (vertical only, like the
# FreeType default of many systems), placed on a common baseline in cells of
# their hinted advance width and stored with the 16 coverage steps of
# Rockbox. Character set: Latin (with Latin-1 and Extended-A/B), Greek,
# Cyrillic, general punctuation, euro and a few symbols - those the font
# has. Rockbox fonts have no kerning.
import struct
import sys

import freetype

RANGES = [(0x20, 0x7E), (0xA0, 0x24F), (0x370, 0x3FF), (0x400, 0x4FF),
          (0x2010, 0x2027), (0x2030, 0x203A), (0x2044, 0x2044), (0x20AC, 0x20AC),
          (0x2116, 0x2116), (0x2122, 0x2122), (0x2190, 0x2193), (0x2212, 0x2212),
          (0x2264, 0x2265), (0x25B2, 0x25C4), (0x25CF, 0x25CF)]
MAX16 = 0xFFDB


def pack_glyph(rows, width):
    nib = []
    for row in rows:
        for x in range(width):
            a = row[x]
            nib.append(15 - (a * 15 + 127) // 255)   # Rockbox: 0 = ink
    if len(nib) % 2:
        nib.append(15)
    return bytes(nib[i] | (nib[i + 1] << 4) for i in range(0, len(nib), 2))


def write_font(path, glyphs, height, ascent, default=0x20):
    first, last = min(glyphs), max(glyphs)
    bits = bytearray()
    placed = {}
    for cp in sorted(glyphs):
        w, rows = glyphs[cp]
        placed[cp] = (len(bits), w)
        bits += pack_glyph(rows, w)
    size = last - first + 1
    long_off = len(bits) >= MAX16
    offsets, widths = [], []
    for cp in range(first, last + 1):
        off, w = placed.get(cp, placed[default])
        offsets.append(off)
        widths.append(w)
    data = bytearray(b'RB12' + struct.pack('<4H', max(widths), height, ascent, 1))
    data += struct.pack('<6I', first, default, size, len(bits), size, size)
    data += bits
    while len(data) % (4 if long_off else 2):
        data.append(0)
    data += struct.pack('<%d%s' % (size, 'I' if long_off else 'H'), *offsets)
    data += bytes(widths)
    open(path, 'wb').write(data)
    return len(glyphs), len(data)


def convert(ttf, px, height, out):
    face = freetype.Face(ttf)
    face.set_pixel_sizes(0, px)
    asc = face.size.ascender / 64.0
    desc = -face.size.descender / 64.0
    # the line height centres ascender plus descender
    base = int(round((height - (asc + desc)) / 2 + asc))
    flags = freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_LIGHT
    glyphs = {}
    for a, b in RANGES:
        for cp in range(a, b + 1):
            if not face.get_char_index(cp):
                continue
            face.load_char(chr(cp), flags)
            g = face.glyph
            adv = int(round(g.advance.x / 64.0))
            if adv <= 0:
                continue
            bm = g.bitmap
            rows = [[0] * adv for _ in range(height)]
            for y in range(bm.rows):
                ty = base - g.bitmap_top + y
                if not 0 <= ty < height:
                    continue
                for x in range(bm.width):
                    tx = g.bitmap_left + x
                    if 0 <= tx < adv:
                        v = bm.buffer[y * bm.pitch + x]
                        rows[ty][tx] = max(rows[ty][tx], v)
            glyphs[cp] = (adv, rows)
    if 0x20 not in glyphs:
        w = max(1, px // 4)
        glyphs[0x20] = (w, [[0] * w for _ in range(height)])
    return write_font(out, glyphs, height, base)


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.exit('usage: %s <font.ttf> <pixel size> <line height> <out.fnt>' % sys.argv[0])
    n, size = convert(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    print('%s: %d glyphs, %d bytes' % (sys.argv[4], n, size))
