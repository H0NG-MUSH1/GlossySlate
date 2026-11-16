"""Default cover of the now playing screen with the cover effect, without a
browser and without Pillow:

    python3 tools/build_wps_cover.py [size]       # default 116
    python3 tools/build_wps_cover.py mini         # mini player, cover100_fx.bmp

Writes .rockbox/wps/glossyslate/cover<size>_fx.bmp: the default cover
(firmware-assets/albumart_list_default_512.png, scaled to size x size) turned,
rounded and mirrored like the fork's %Cd(24,420,36,34,radius) draws a real
cover. Frame 1 radius 8 (album art corners "Rounded"), frame 2 radius 0 ("Square").

The geometry is the firmware's own integer maths (fx_margins(), fx_render()
in apps/gui/skin_engine/skin_albumart_fx.c), ported line by line, so the
picture has the same size and lies exactly where a real cover would. The
skin draws it at the %Cl box minus (mx, over); the script prints both.

Colours in full precision, RGB565 only at the end: the firmware samples a
cover that is already RGB565. The grey ground of the default cover
(#F6F7F9 -> #E6EAEF) spans only two or three RGB565 steps per channel, and
the channels step at different rows: bands with a pink, a bluish and a
neutral (beside them orange looking) tint. Here the source is scaled and
sampled without rounding and quantised once, with a 4 x 4 ordered dither
anchored to the screen, so the ground stays grey.

Both pictures are opaque. The mini player lies on sidebar.bmp. The now
playing cover lies on the ground of its screen (white, from row 139 the %dr
gradient ffffff -> f4f6f8, which the fork draws dithered in a fixed pattern,
draw_gradient_dithered() in apps/gui/skin_engine/skin_render.c): the cover
and its reflection are mixed with that ground here, and where the cover does
not reach, the picture holds exactly the pixels the firmware draws there.
With alpha the skin engine kept 4 bits and blended every channel with
truncation (blend_two_colors()), which left green dots in the reflection.
"""
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tools.pngread import read_png  # noqa: E402

PKG = os.path.join(os.path.dirname(HERE), '.rockbox', 'wps', 'glossyslate')
SRC = os.path.join(os.path.dirname(HERE), 'firmware-assets', 'albumart_list_default_512.png')
TILT, PERSPECTIVE, REFL_H, REFL_OP = 24, 420, 36, 34
RADII = (8, 0)
COVER_X, COVER_Y = 14, 39          # %Cl box on the screen (DESIGN 6.6)
ONE = 65536
SIN14 = int(round(math.sin(math.radians(TILT)) * 16384))
COS14 = int(round(math.cos(math.radians(TILT)) * 16384))
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
# ground of the now playing screen under the cover (glossyslate.wps, viewport
# PageBg at 0,0): %dr rows as (first row, rows, start colour, end colour)
GROUND = [(22, 117, 0xffffff, 0xffffff), (139, 57, 0xffffff, 0xf4f6f8)]


def cdiv(a, b):
    """C division (truncates toward zero)"""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def fx_scale(x16):
    d14 = PERSPECTIVE * 16384
    den = d14 + ((x16 * SIN14) >> 16)
    return 0 if den <= 0 else cdiv(d14 << 16, den)


def fx_margins(w, h):
    s = max(fx_scale(-(w << 15)), fx_scale(w << 15)) or ONE
    half_w = ((((w << 15) * COS14) >> 14) * s) >> 16
    half_h = ((h << 15) * s) >> 16
    mx = max(0, (half_w - (w << 15) + ONE - 1) >> 16)
    over = max(0, (half_h - (h << 15) + ONE - 1) >> 16)
    return mx, over


def isqrt(v):
    return int(math.isqrt(v))


def fx_corner(radius, w, h, u, v):
    if radius <= 0:
        return ONE
    r = radius << 16
    du = r - u if u < r else (u - ((w << 16) - r) if u > (w << 16) - r else 0)
    dv = r - v if v < r else (v - ((h << 16) - r) if v > (h << 16) - r else 0)
    if du <= 0 or dv <= 0:
        return ONE
    dist = isqrt(du * du + dv * dv)
    return min(ONE, max(0, r - dist + ONE // 2))


def fx_sample(src, w, h, u, v):
    """bilinear like the firmware (same places and 8 bit weights), but on
    the source in full precision: (r, g, b) 0..255 as floats"""
    fu, fv = u - ONE // 2, v - ONE // 2
    x0, y0 = fu >> 16, fv >> 16
    ax, ay = (fu >> 8) & 0xff, (fv >> 8) & 0xff
    x1, y1 = x0 + 1, y0 + 1
    x0, x1 = min(max(x0, 0), w - 1), min(max(x1, 0), w - 1)
    y0, y1 = min(max(y0, 0), h - 1), min(max(y1, 0), h - 1)
    p = (src[y0][x0], src[y0][x1], src[y1][x0], src[y1][x1])
    wt = ((256 - ax) * (256 - ay), ax * (256 - ay), (256 - ax) * ay, ax * ay)
    r = g = b = 0.0
    for q, k in zip(p, wt):
        r += q[0] * k
        g += q[1] * k
        b += q[2] * k
    return (r / ONE, g / ONE, b / ONE)


def fx_render(src, w, h, radius, refl_h=None, refl_op_pc=None):
    """-> (pw, ph, mx, over, colour rows (r, g, b) 0..255, alpha rows 0..255);
    geometry and coverage as in the firmware"""
    refl_h = REFL_H if refl_h is None else refl_h
    refl_op_pc = REFL_OP if refl_op_pc is None else refl_op_pc
    mx, over = fx_margins(w, h)
    pw, ph = w + 2 * mx, h + 2 * over + refl_h
    pix = [[None] * pw for _ in range(ph)]
    alpha = [[0] * pw for _ in range(ph)]
    refl = refl_h << 16
    refl_op = refl_op_pc * ONE // 100
    mid_h = h << 15
    c, s, d = COS14, SIN14, PERSPECTIVE
    for px in range(pw):
        x = ((px - mx) << 16) + ONE // 2 - (w << 15)
        den = d * c - ((x * s) >> 16)
        if den <= 0:
            continue
        xc = cdiv(x * d * 16384, den)
        scale = fx_scale(xc)
        if scale <= 0:
            continue
        u = xc + (w << 15)
        cov_x = min(u, (w << 16) - u) + ONE // 2
        if cov_x <= 0:
            continue
        cov_x = min(cov_x, ONE)
        step = cdiv(ONE << 16, scale)
        half = (mid_h * scale) >> 16
        top, bottom = mid_h - half, mid_h + half
        for py in range(ph):
            y0 = (py - over) << 16
            ym = y0 + ONE // 2
            op, colour = 0, None
            cov = min(y0 + ONE, bottom) - max(y0, top)
            if cov > 0:
                yin = min(max(ym, top), bottom)
                v = (((yin - mid_h) * step) >> 16) + mid_h
                v = min(max(v, 0), h << 16)
                op = (min(cov, ONE) * cov_x) >> 16
                op = (op * fx_corner(radius, w, h, u, v)) >> 16
                colour = fx_sample(src, w, h, u, v)
            if refl > 0 and ym > bottom and ym - bottom < refl:
                e = ym - bottom
                v = (h << 16) - ((e * step) >> 16)
                if v > 0:
                    rop = cdiv(refl_op * (refl - e), refl)
                    rop = (rop * cov_x) >> 16
                    rop = (rop * fx_corner(radius, w, h, u, v)) >> 16
                    rop = (rop * (ONE - op)) >> 16
                    if op == 0:
                        colour = fx_sample(src, w, h, u, v)
                    op += rop
            if op <= 0:
                continue
            a = (min(op, ONE) * 255 + ONE // 2) >> 16
            if a:
                pix[py][px], alpha[py][px] = colour, a
    return pw, ph, mx, over, pix, alpha


def scaled_source(size):
    """area average of the 512 px PNG: rows of (r, g, b) 0..255 as floats,
    not rounded (see above)"""
    big = read_png(SRC)
    n = len(big)
    k = n / size
    out = []
    for y in range(size):
        y0, y1 = y * k, (y + 1) * k
        row = []
        for x in range(size):
            x0, x1 = x * k, (x + 1) * k
            acc = [0.0, 0.0, 0.0]
            area = 0.0
            for sy in range(int(y0), min(n, int(math.ceil(y1)))):
                fy = min(y1, sy + 1) - max(y0, sy)
                for sx in range(int(x0), min(n, int(math.ceil(x1)))):
                    f = fy * (min(x1, sx + 1) - max(x0, sx))
                    p = big[sy][sx]
                    acc[0] += p[0] * f
                    acc[1] += p[1] * f
                    acc[2] += p[2] * f
                    area += f
            row.append(tuple(v / area for v in acc))
        out.append(row)
    return out


def rgb888(q5):
    """RGB565 channels -> 8 bit by bit replication (the skin engine loads
    these values unchanged)"""
    r5, g6, b5 = q5
    return ((r5 << 3) | (r5 >> 2), (g6 << 2) | (g6 >> 4), (b5 << 3) | (b5 >> 2))


def write_bmp24(path, rows):
    h, w = len(rows), len(rows[0])
    stride = (w * 3 + 3) & ~3
    data = bytearray()
    for row in reversed(rows):
        line = bytearray()
        for r, g, b in row:
            line += bytes((b, g, r))
        data += line + bytes(stride - len(line))
    hdr = struct.pack('<2sIHHI', b'BM', 54 + len(data), 0, 0, 54)
    info = struct.pack('<IiiHHIIiiII', 40, w, h, 1, 24, 0, len(data), 2835, 2835, 0, 0)
    open(path, 'wb').write(hdr + info + data)


def ground256(y):
    """the ground of the now playing screen in row y, per channel in 1/256 of
    an RGB565 step, the way draw_gradient_dithered() computes it before its
    dither (threshold 16 * BAYER + 8 at the screen position)"""
    for first, rows, c0, c1 in GROUND:
        if first <= y < first + rows:
            i, out = y - first, []
            for shift, m in ((16, 31), (8, 63), (0, 31)):
                s, e = (c0 >> shift) & 0xff, (c1 >> shift) & 0xff
                if c0 == c1:
                    assert s == 0xff, 'a plain %dr fill: only white is computed here'
                    out.append(m * 256)
                else:
                    num, den = 2 * i + 1, 2 * rows
                    out.append((s * den + (e - s) * num) * m * 256 // (255 * den))
            return out
    raise ValueError('row %d is not on the ground of the now playing screen' % y)


def main(size):
    src = scaled_source(size)
    frames = []
    for radius in RADII:
        pw, ph, mx, over, pix, alpha = fx_render(src, size, size, radius)
        x0, y0 = COVER_X - mx, COVER_Y - over
        for py in range(ph):
            sy = y0 + py
            g256 = ground256(sy)
            row = []
            for px in range(pw):
                sx = x0 + px
                t = 16 * BAYER[sy & 3][sx & 3] + 8
                a = alpha[py][px] / 255.0
                c = pix[py][px]
                q5 = []
                for ch, m in enumerate((31, 63, 31)):
                    v = g256[ch]
                    if a > 0:              # cover or reflection over the ground
                        v += (c[ch] * m * 256 / 255.0 - v) * a
                    q5.append(min(m, int(v + t) >> 8))
                row.append(rgb888(q5))
            frames.append(row)
    name = 'cover%d_fx.bmp' % size
    write_bmp24(os.path.join(PKG, name), frames)
    print('%s: %d x %d per frame, 2 frames, opaque on the ground; draw at the %%Cl box minus (%d, %d)'
          % (name, pw, ph, mx, over))


MINI = 100                         # mini player of the main menu
MINI_X, MINI_Y = 190, 36           # its %Cl box on the screen
MINI_REFL_OP = 60                  # reflection 36 px at 60 % on the blue sidebar


def mini():
    """cover100_fx.bmp: the same effect for the mini player (%Cd(24,420,36,
    60,r) in the sbs), put onto sidebar.bmp at its place and written opaque
    with an RGB565 dither, like the firmware draws real covers there"""
    sys.path.insert(0, HERE)
    from tools import raster as R
    side = R.read_bmp(os.path.join(PKG, 'sidebar.bmp'))
    src = scaled_source(MINI)
    out = []
    for radius in RADII:
        pw, ph, mx, over, pix, alpha = fx_render(src, MINI, MINI, radius,
                                                 REFL_H, MINI_REFL_OP)
        x0, y0 = MINI_X - mx, MINI_Y - over
        for py in range(ph):
            row = []
            for px in range(pw):
                ax, ay = x0 + px, y0 + py
                r0, g0, b0, _ = side[ay][ax - 160]
                a = alpha[py][px] / 255.0
                if a <= 0:
                    row.append((r0, g0, b0))
                    continue
                r, g, b = pix[py][px]
                t = (BAYER[ay & 3][ax & 3] + 0.5) / 16.0
                mix = (r0 + (r - r0) * a, g0 + (g - g0) * a, b0 + (b - b0) * a)
                q5 = [max(0, min(m, int(v * m / 255.0 + t))) for v, m in zip(mix, (31, 63, 31))]
                row.append(rgb888(q5))
            out.append(row)
    write_bmp24(os.path.join(PKG, 'cover100_fx.bmp'), out)
    print('cover100_fx.bmp: %d x %d per frame, 2 frames, opaque on the sidebar; '
          'draw at the %%Cl box minus (%d, %d)' % (pw, ph, mx, over))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'mini':
        mini()
    else:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else 116)
