"""Small anti-aliased rasterizer in pure Python for theme bitmaps that are
made without a browser (status icons, quick menu).

Shapes are inside tests evaluated on an SS x SS grid per pixel. A layer is a
coverage map (0..1 per pixel); layers are painted with a colour, a vertical
gradient or a function onto an RGBA canvas. SVG paths (M L H V C Q A Z, also
relative) are flattened to polylines for even-odd fills and for strokes with
butt or round caps and round joins.

Output: 32 bit BMP with the 16 alpha steps the Rockbox skin engine keeps.
"""
import math
import struct

SS = 4


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[(0.0, 0.0, 0.0, 0.0)] * w for _ in range(h)]  # premultiplied

    def paint(self, cov, colour):
        """colour: (r, g, b) / (r, g, b, a) 0..255 or f(x, y) -> such"""
        for y in range(self.h):
            row = self.px[y]
            for x in range(self.w):
                c = cov[y][x]
                if c <= 0:
                    continue
                col = colour(x, y) if callable(colour) else colour
                a = c * (col[3] / 255.0 if len(col) > 3 else 1.0)
                r, g, b, da = row[x]
                row[x] = (col[0] * a + r * (1 - a), col[1] * a + g * (1 - a),
                          col[2] * a + b * (1 - a), a + da * (1 - a))

    def erase(self, cov):
        for y in range(self.h):
            for x in range(self.w):
                c = cov[y][x]
                if c > 0:
                    r, g, b, a = self.px[y][x]
                    k = 1 - c
                    self.px[y][x] = (r * k, g * k, b * k, a * k)

    def rgba(self, x, y):
        r, g, b, a = self.px[y][x]
        if a <= 0:
            return (0, 0, 0, 0)
        return (min(255, round(r / a)), min(255, round(g / a)),
                min(255, round(b / a)), a)

    def paste(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                if 0 <= x + ox < self.w and 0 <= y + oy < self.h:
                    r, g, b, a = other.px[y][x]
                    if a <= 0:
                        continue
                    R, G, B, A = self.px[y + oy][x + ox]
                    self.px[y + oy][x + ox] = (r + R * (1 - a), g + G * (1 - a),
                                               b + B * (1 - a), a + A * (1 - a))


def coverage(w, h, inside, ss=SS):
    out = []
    n = ss * ss
    for y in range(h):
        row = []
        for x in range(w):
            c = 0
            for sy in range(ss):
                py = y + (sy + 0.5) / ss
                for sx in range(ss):
                    if inside(x + (sx + 0.5) / ss, py):
                        c += 1
            row.append(c / n)
        out.append(row)
    return out


def combine(a, b, op):
    return [[op(a[y][x], b[y][x]) for x in range(len(a[0]))] for y in range(len(a))]


def subtract(a, b):
    return combine(a, b, lambda p, q: max(0.0, p - q))


def union(a, b):
    return combine(a, b, lambda p, q: min(1.0, p + q - p * q))


def scaled_cov(cov, k):
    return [[v * k for v in row] for row in cov]


# ------------------------------------------------------------------ shapes
def rrect(x0, y0, x1, y1, r):
    def inside(x, y):
        if x < x0 or x > x1 or y < y0 or y > y1:
            return False
        cx = min(max(x, x0 + r), x1 - r)
        cy = min(max(y, y0 + r), y1 - r)
        return (x - cx) ** 2 + (y - cy) ** 2 <= r * r
    return inside


def circle(cx, cy, r):
    return lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def ring(inside_outer, inside_inner):
    return lambda x, y: inside_outer(x, y) and not inside_inner(x, y)


def vgrad(stops, y0, y1):
    """stops: [(t, (r, g, b)), ...] over y0..y1"""
    def f(x, y):
        t = 0.0 if y1 <= y0 else (y + 0.5 - y0) / (y1 - y0)
        t = min(max(t, 0.0), 1.0)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t <= t1:
                k = 0 if t1 <= t0 else (t - t0) / (t1 - t0)
                return tuple(c0[j] + (c1[j] - c0[j]) * k for j in range(3))
        return stops[-1][1]
    return f


def hexc(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


# ------------------------------------------------------------------ SVG paths
def _tokens(d):
    import re
    return re.findall(r'[MmLlHhVvCcQqAaZz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?', d)


def _arc(x1, y1, rx, ry, phi, fa, fs, x2, y2):
    """SVG arc to points (endpoint parameterisation)"""
    if rx == 0 or ry == 0:
        return [(x2, y2)]
    phi = math.radians(phi)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    rx, ry = abs(rx), abs(ry)
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    k = math.sqrt(max(0, num / den)) if den else 0
    if fa == fs:
        k = -k
    cxp, cyp = k * rx * y1p / ry, -k * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a
    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not fs and dt > 0:
        dt -= 2 * math.pi
    elif fs and dt < 0:
        dt += 2 * math.pi
    n = max(4, int(abs(dt) * max(rx, ry) / 2))
    pts = []
    for i in range(1, n + 1):
        t = t1 + dt * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        pts.append((cp * x - sp * y + cx, sp * x + cp * y + cy))
    return pts


def path_polylines(d):
    """[(points, closed)] in path units"""
    tk = _tokens(d)
    i = 0
    out = []
    cur = None
    x = y = sx = sy = 0.0
    cmd = None

    def num():
        nonlocal i
        v = float(tk[i])
        i += 1
        return v
    while i < len(tk):
        if tk[i].isalpha():
            cmd = tk[i]
            i += 1
        rel = cmd.islower()
        c = cmd.upper()
        if c == 'Z':
            if cur:
                out.append((cur, True))
            cur = None
            x, y = sx, sy
            continue
        if c == 'M':
            nx, ny = num(), num()
            if rel:
                nx, ny = x + nx, y + ny
            if cur:
                out.append((cur, False))
            x, y, sx, sy = nx, ny, nx, ny
            cur = [(x, y)]
            cmd = 'l' if rel else 'L'
            continue
        if cur is None:
            cur = [(x, y)]
        if c == 'L':
            nx, ny = num(), num()
            if rel:
                nx, ny = x + nx, y + ny
            x, y = nx, ny
            cur.append((x, y))
        elif c == 'H':
            nx = num()
            x = x + nx if rel else nx
            cur.append((x, y))
        elif c == 'V':
            ny = num()
            y = y + ny if rel else ny
            cur.append((x, y))
        elif c in 'CQ':
            n = 3 if c == 'C' else 2
            pts = []
            for _ in range(n):
                px, py = num(), num()
                if rel:
                    px, py = x + px, y + py
                pts.append((px, py))
            p0 = (x, y)
            steps = 16
            for s in range(1, steps + 1):
                t = s / steps
                if c == 'C':
                    (ax, ay), (bx, by), (ex, ey) = pts
                    u = 1 - t
                    qx = u ** 3 * p0[0] + 3 * u * u * t * ax + 3 * u * t * t * bx + t ** 3 * ex
                    qy = u ** 3 * p0[1] + 3 * u * u * t * ay + 3 * u * t * t * by + t ** 3 * ey
                else:
                    (ax, ay), (ex, ey) = pts
                    u = 1 - t
                    qx = u * u * p0[0] + 2 * u * t * ax + t * t * ex
                    qy = u * u * p0[1] + 2 * u * t * ay + t * t * ey
                cur.append((qx, qy))
            x, y = pts[-1]
        elif c == 'A':
            rx, ry, phi, fa, fs, nx, ny = (num() for _ in range(7))
            if rel:
                nx, ny = x + nx, y + ny
            cur.extend(_arc(x, y, rx, ry, phi, int(fa), int(fs), nx, ny))
            x, y = nx, ny
    if cur:
        out.append((cur, False))
    return out


def _transform(polys, scale, ox, oy):
    return [([(px * scale + ox, py * scale + oy) for px, py in pts], cl) for pts, cl in polys]


def fill_inside(polys):
    """even-odd fill of all sub-paths (closed implicitly)"""
    edges = []
    for pts, _ in polys:
        n = len(pts)
        for k in range(n):
            a, b = pts[k], pts[(k + 1) % n]
            if a[1] != b[1]:
                edges.append((a, b))

    def inside(x, y):
        c = False
        for (ax, ay), (bx, by) in edges:
            if (ay > y) != (by > y):
                if x < ax + (y - ay) * (bx - ax) / (by - ay):
                    c = not c
        return c
    return inside


def stroke_inside(polys, width, cap='round'):
    hw = width / 2.0
    segs = []
    joints = []
    for pts, closed in polys:
        n = len(pts)
        m = n if closed else n - 1
        for k in range(m):
            segs.append((pts[k], pts[(k + 1) % n]))
        # round joins at inner vertices; round caps at the ends if asked
        for k in range(n):
            end = not closed and (k == 0 or k == n - 1)
            if not end or cap == 'round':
                joints.append(pts[k])
    hw2 = hw * hw

    def inside(x, y):
        for (ax, ay), (bx, by) in segs:
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            if L == 0:
                continue
            t = ((x - ax) * dx + (y - ay) * dy) / L
            if 0 <= t <= 1:
                qx, qy = ax + t * dx - x, ay + t * dy - y
                if qx * qx + qy * qy <= hw2:
                    return True
        for jx, jy in joints:
            if (x - jx) ** 2 + (y - jy) ** 2 <= hw2:
                return True
        return False
    return inside


def path_cov(w, h, d, scale, ox, oy, fill=True, stroke=None, cap='round', ss=SS):
    polys = _transform(path_polylines(d), scale, ox, oy)
    if fill:
        return coverage(w, h, fill_inside(polys), ss)
    return coverage(w, h, stroke_inside(polys, stroke * scale, cap), ss)


# ------------------------------------------------------------------ output
def write_bmp32(path, frames):
    """frames: canvases of equal width, stacked top to bottom"""
    w = frames[0].w
    rows = []
    for fr in frames:
        for y in range(fr.h):
            rows.append([fr.rgba(x, y) for x in range(w)])
    h = len(rows)
    data = bytearray()
    for row in reversed(rows):
        for r, g, b, a in row:
            q = int(round(a * 15))
            data += bytes((b, g, r, 17 * q))
    with open(path, 'wb') as f:
        f.write(struct.pack('<2sIHHI', b'BM', 70 + len(data), 0, 0, 70))
        f.write(struct.pack('<IiiHHIIiiII', 56, w, h, 1, 32, 3, len(data), 3779, 3779, 0, 0))
        f.write(struct.pack('<IIII', 0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000))
        f.write(data)


def read_bmp(path):
    """24/32 bit BMP -> rows of (r, g, b, a 0..1)"""
    d = open(path, 'rb').read()
    off = struct.unpack_from('<I', d, 10)[0]
    w, h = struct.unpack_from('<ii', d, 18)
    bpp = struct.unpack_from('<H', d, 28)[0]
    step = bpp // 8
    stride = (w * step + 3) & ~3
    rows = []
    for y in range(abs(h)):
        ry = abs(h) - 1 - y if h > 0 else y
        base = off + ry * stride
        row = []
        for x in range(w):
            p = d[base + x * step: base + x * step + step]
            a = p[3] / 255.0 if step == 4 else 1.0
            row.append((p[2], p[1], p[0], a))
        rows.append(row)
    return rows


def canvas_from_rows(rows):
    c = Canvas(len(rows[0]), len(rows))
    for y, row in enumerate(rows):
        for x, (r, g, b, a) in enumerate(row):
            c.px[y][x] = (r * a, g * a, b * a, a)
    return c
