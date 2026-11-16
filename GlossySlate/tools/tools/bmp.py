"""BMP writers for Rockbox skins.

24 bit: plain BITMAPINFOHEADER, optional ordered dither to RGB565 so that
        gradients do not band on the iPod's 16-bit screen.
32 bit: BITMAPV3INFOHEADER (56 bytes) with BI_BITFIELDS and an alpha mask,
        the same layout adwaitapod ships. Alpha is quantised to 16 steps
        (17 * q) because the skin engine keeps 4 bit alpha. Width is padded
        to an even number of pixels (lcd_bmp() expects even alpha rows).
"""
import struct
from PIL import Image

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def _dither565(im):
    im = im.convert('RGB')
    w, h = im.size
    px = im.load()
    out = Image.new('RGB', (w, h))
    po = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            t = (BAYER4[y & 3][x & 3] + 0.5) / 16.0
            def q(v, bits):
                levels = (1 << bits) - 1
                f = v / 255.0 * levels
                n = int(f)
                if f - n > t:
                    n += 1
                n = min(n, levels)
                return int(round(n * 255.0 / levels))
            po[x, y] = (q(r, 5), q(g, 6), q(b, 5))
    return out


def write_bmp24(im, path, dither=False):
    im = im.convert('RGB')
    if dither:
        im = _dither565(im)
    w, h = im.size
    row = (w * 3 + 3) & ~3
    data = bytearray()
    px = im.load()
    for y in range(h - 1, -1, -1):
        line = bytearray()
        for x in range(w):
            r, g, b = px[x, y]
            line += bytes((b, g, r))
        line += b'\0' * (row - len(line))
        data += line
    hdr = struct.pack('<2sIHHI', b'BM', 14 + 40 + len(data), 0, 0, 54)
    info = struct.pack('<IiiHHIIiiII', 40, w, h, 1, 24, 0, len(data), 2835, 2835, 0, 0)
    with open(path, 'wb') as f:
        f.write(hdr + info + data)


def write_bmp32(im, path):
    im = im.convert('RGBA')
    w, h = im.size
    if w % 2:
        pad = Image.new('RGBA', (w + 1, h), (0, 0, 0, 0))
        pad.paste(im, (0, 0))
        im = pad
        w += 1
    px = im.load()
    data = bytearray()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            r, g, b, a = px[x, y]
            q = int(round(a / 17.0)) * 17
            if q == 0:
                r = g = b = 0
            data += bytes((b, g, r, q))
    hdr = struct.pack('<2sIHHI', b'BM', 14 + 56 + len(data), 0, 0, 70)
    info = struct.pack('<IiiHHIIiiII', 56, w, h, 1, 32, 3, len(data), 3779, 3779, 0, 0)
    info += struct.pack('<4I', 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    with open(path, 'wb') as f:
        f.write(hdr + info + data)
    return w, h
