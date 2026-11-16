"""Write Rockbox RB12 fonts with 4-bit anti-aliasing (depth 1).

Format (firmware/font.c, firmware/drivers/lcd-16bit-common.c):
  header  'RB12', u16 maxwidth, height, ascent, depth, u32 firstchar,
          defaultchar, size, bits_size, noffset, nwidth  (36 bytes)
  bits    per glyph: height*width nibbles, row-major, low nibble first,
          0 = full ink, 15 = transparent
  pad     to 2 bytes (16-bit offsets) or 4 bytes (32-bit offsets)
  offsets one per code point in [firstchar, firstchar+size)
  widths  one byte per code point
"""
import struct

MAX16 = 0xFFDB


def pack_glyph(alpha_rows, width):
    """alpha_rows: list of rows, each a list of 0..255 coverage values."""
    nib = []
    for row in alpha_rows:
        for x in range(width):
            a = row[x] if x < len(row) else 0
            q = (a * 15 + 127) // 255          # 0..15 coverage
            nib.append(15 - q)                 # Rockbox: 0 = ink
    if len(nib) % 2:
        nib.append(15)
    out = bytearray()
    for i in range(0, len(nib), 2):
        out.append(nib[i] | (nib[i + 1] << 4))
    return bytes(out)


def write_font(path, glyphs, height, ascent, first, last, default):
    """glyphs: {codepoint: (width, alpha_rows)}; codepoints outside the
    dict but inside [first, last] fall back to the default glyph."""
    assert default in glyphs
    bits = bytearray()
    placed = {}
    for cp in sorted(glyphs):
        w, rows = glyphs[cp]
        assert 0 <= w <= 255
        placed[cp] = (len(bits), w)
        bits += pack_glyph(rows, w)
    size = last - first + 1
    long_off = len(bits) >= MAX16
    offsets, widths = [], []
    for cp in range(first, last + 1):
        off, w = placed.get(cp, placed[default])
        offsets.append(off)
        widths.append(w)
    maxw = max(widths)
    hdr = b'RB12' + struct.pack('<4H', maxw, height, ascent, 1)
    hdr += struct.pack('<6I', first, default, size, len(bits), size, size)
    data = bytearray(hdr) + bits
    align = 4 if long_off else 2
    while len(data) % align:
        data.append(0)
    data += struct.pack('<%d%s' % (size, 'I' if long_off else 'H'), *offsets)
    data += bytes(widths)
    with open(path, 'wb') as f:
        f.write(data)
    return len(data)
