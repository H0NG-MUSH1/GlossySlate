#!/usr/bin/env python3
"""Glossy Slate · symbols without a tile for the sidebar.

Renders the symbols of sym_pur.json (156 grid, format like SYM: f = fill
evenodd, s = stroke, w = stroke width) bare onto the blue sidebar, without a
tile and without a reflection: gloss gradient and emboss (shadow 0 1 px), as
32 bit BMPs with alpha for Rockbox. Pillow and NumPy only.

    python3 build_side_symbols.py              # into ./out_side/
    python3 build_side_symbols.py --png        # PNG previews as well

Rockbox reads the alpha channel of 32 bit BMPs (BI_RGB, order B G R A) and
stores it with 4 bits: (255 - a) >> 4. So this script quantises alpha itself
to 16 steps (a = 17 · step, ordered dither), so that edges and shadows arrive
exactly as rendered, and the colours to RGB565.
"""
import json, math, os, re, struct, argparse
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ sizes
GRID = 156
SCALE = 2 / 3            # 156 grid -> 104 px; stroke 6 in the grid = 4 px like the tile symbols
BOX = (28, 66)           # top left corner of the 104 px grid in the sidebar (centre 80/118 = tile centre)
BMP_RECT = (36, 75, 88, 88)     # x, y, width, height of the bitmap in the sidebar (the sidebar starts at x 160)
SS = 16                  # supersampling when rasterising

# ------------------------------------------------------------------ material
# gloss gradient over the height of the symbol (light at the top, gloss edge at 45/55 %)
GLOSS = [(0.00, "#FFFFFF"), (0.45, "#EEF3FA"), (0.55, "#D3DEEC"), (1.00, "#C3D1E3")]
SHADOW = dict(dy=1.0, sigma=0.55, color="#040A18", alpha=0.38)   # emboss like text on blue

# ================================================================== SVG paths
_tok = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")

def _arc_points(p0, rx, ry, phi, large, sweep, p1, step_deg=2.0):
    """Split an SVG arc (endpoint form) into points (SVG 1.1, appendix F.6.5)."""
    if rx == 0 or ry == 0:
        return [p1]
    x1, y1 = p0; x2, y2 = p1
    cphi, sphi = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p = cphi * dx + sphi * dy; y1p = -sphi * dx + cphi * dy
    rx, ry = abs(rx), abs(ry)
    lam = x1p**2 / rx**2 + y1p**2 / ry**2
    if lam > 1:
        s = math.sqrt(lam); rx *= s; ry *= s
    num = rx**2 * ry**2 - rx**2 * y1p**2 - ry**2 * x1p**2
    den = rx**2 * y1p**2 + ry**2 * x1p**2
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        co = -co
    cxp = co * rx * y1p / ry; cyp = -co * ry * x1p / rx
    cx = cphi * cxp - sphi * cyp + (x1 + x2) / 2
    cy = sphi * cxp + cphi * cyp + (y1 + y2) / 2
    def ang(u, v):
        a = math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1])
        return a
    t1 = ang((1, 0), ((x1p - cxp) / rx, (y1p - cyp) / ry))
    dt = ang(((x1p - cxp) / rx, (y1p - cyp) / ry), ((-x1p - cxp) / rx, (-y1p - cyp) / ry))
    if not sweep and dt > 0: dt -= 2 * math.pi
    if sweep and dt < 0: dt += 2 * math.pi
    n = max(2, int(abs(math.degrees(dt)) / step_deg) + 1)
    pts = []
    for i in range(1, n + 1):
        t = t1 + dt * i / n
        x = rx * math.cos(t); y = ry * math.sin(t)
        pts.append((cphi * x - sphi * y + cx, sphi * x + cphi * y + cy))
    return pts

def path_to_polys(d, curve_steps=40):
    """path -> list of (points, closed)."""
    toks = _tok.findall(d)
    i = 0; cmd = None; cur = (0.0, 0.0); start = cur; polys = []; pts = []
    def num():
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]; i += 1
        rel = cmd.islower(); C = cmd.upper()
        ox, oy = cur if rel else (0.0, 0.0)
        if C == "M":
            if pts: polys.append((pts, False))
            cur = (ox + num(), oy + num()); start = cur; pts = [cur]
            cmd = "l" if rel else "L"
        elif C == "L":
            cur = (ox + num(), oy + num()); pts.append(cur)
        elif C == "H":
            cur = ((cur[0] if rel else 0) + num(), cur[1]); pts.append(cur)
        elif C == "V":
            cur = (cur[0], (cur[1] if rel else 0) + num()); pts.append(cur)
        elif C == "C":
            c1 = (ox + num(), oy + num()); c2 = (ox + num(), oy + num()); p = (ox + num(), oy + num())
            for k in range(1, curve_steps + 1):
                t = k / curve_steps; u = 1 - t
                pts.append((u**3 * cur[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t**3 * p[0],
                            u**3 * cur[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t**3 * p[1]))
            cur = p
        elif C == "Q":
            c1 = (ox + num(), oy + num()); p = (ox + num(), oy + num())
            for k in range(1, curve_steps + 1):
                t = k / curve_steps; u = 1 - t
                pts.append((u * u * cur[0] + 2 * u * t * c1[0] + t * t * p[0],
                            u * u * cur[1] + 2 * u * t * c1[1] + t * t * p[1]))
            cur = p
        elif C == "A":
            rx = num(); ry = num(); rot = math.radians(num()); la = int(num()); sw = int(num())
            p = (ox + num(), oy + num())
            pts.extend(_arc_points(cur, rx, ry, rot, la, sw, p)); cur = p
        elif C == "Z":
            if pts: polys.append((pts, True))
            pts = []; cur = start
        else:
            raise ValueError("path command not supported: " + cmd)
    if pts: polys.append((pts, False))
    return polys

# ================================================================== rasterising
def coverage(sym, scale=SCALE, size=None, ss=SS, offset=(0.0, 0.0)):
    """coverage 0..1 of a symbol; grid coordinate g -> pixel g*scale + offset."""
    if size is None:
        n = int(math.ceil(GRID * scale)); size = (n, n)
    W, H = size[0] * ss, size[1] * ss
    k = scale * ss
    def tr(p): return ((p[0] * scale + offset[0]) * ss - 0.5, (p[1] * scale + offset[1]) * ss - 0.5)
    fill = np.zeros((H, W), bool)
    if sym.get("f"):
        for pts, _ in path_to_polys(sym["f"]):
            im = Image.new("1", (W, H), 0)
            ImageDraw.Draw(im).polygon([tr(p) for p in pts], fill=1)
            fill ^= np.asarray(im, bool)            # evenodd
    if sym.get("s") and sym.get("w"):
        im = Image.new("1", (W, H), 0); dr = ImageDraw.Draw(im)
        r = sym["w"] / 2 * k
        for pts, closed in path_to_polys(sym["s"]):
            q = [tr(p) for p in pts] + ([tr(pts[0])] if closed else [])
            for a, b in zip(q[:-1], q[1:]):
                dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
                if L == 0: continue
                nx, ny = -dy / L * r, dx / L * r
                dr.polygon([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)], fill=1)
            for p in q:                               # round ends and corners
                dr.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=1)
        fill |= np.asarray(im, bool)
    return fill.reshape(size[1], ss, size[0], ss).mean(axis=(1, 3))

# ================================================================== material
def hex2rgb(h): h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255

def gauss_blur(a, sigma):
    if sigma <= 0: return a
    r = int(math.ceil(sigma * 3)); x = np.arange(-r, r + 1); k = np.exp(-x**2 / (2 * sigma**2)); k /= k.sum()
    a = np.apply_along_axis(lambda v: np.convolve(v, k, "same"), 0, a)
    return np.apply_along_axis(lambda v: np.convolve(v, k, "same"), 1, a)

def shift_y(a, dy):
    """shift down by dy pixels (linear interpolation)."""
    H = a.shape[0]; y = np.arange(H) - dy
    y0 = np.floor(y).astype(int); f = (y - y0)[:, None]
    def row(i): 
        ok = (i >= 0) & (i < H); out = np.zeros_like(a); out[ok] = a[i[ok]]; return out
    return row(y0) * (1 - f) + row(y0 + 1) * f

def over(top, bot):
    """straight alpha RGBA 'top over bot'."""
    at, ab = top[..., 3:], bot[..., 3:]
    a = at + ab * (1 - at)
    c = np.where(a > 0, (top[..., :3] * at + bot[..., :3] * ab * (1 - at)) / np.maximum(a, 1e-9), 0)
    return np.concatenate([c, a], -1)

def render_side(sym, gloss=GLOSS, shadow=SHADOW):
    """bare symbol for the sidebar -> RGBA float (H, W, 4), size BMP_RECT."""
    bx, by, BW, BH = BMP_RECT
    off = (BOX[0] - bx, BOX[1] - by)
    cov = coverage(sym, size=(BW, BH), offset=off)
    # top and bottom edge of the symbol from the paths (more exact than from pixels)
    half = (sym.get("w") or 0) / 2
    ys = [p[1] for pts, _ in path_to_polys(sym["f"]) for p in pts] if sym.get("f") else []
    yl = [(p[1] - half, p[1] + half) for pts, _ in path_to_polys(sym["s"]) for p in pts] if sym.get("s") else []
    top = min(ys + [u for u, _ in yl]) * SCALE + off[1]
    bottom = max(ys + [v for _, v in yl]) * SCALE + off[1]
    yy = (np.arange(BH) + 0.5)[:, None]
    t = np.clip((yy - top) / (bottom - top), 0, 1)
    stops = [(p, hex2rgb(c)) for p, c in gloss]
    col = np.zeros((BH, 1, 3))
    for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
        m = (t >= p0) & (t <= p1)
        f = np.where(m, (t - p0) / max(p1 - p0, 1e-9), 0)
        col = np.where(m[..., None], c0 * (1 - f[..., None]) + c1 * f[..., None], col)
    glyph = np.concatenate([np.broadcast_to(col, (BH, BW, 3)), cov[..., None]], -1)
    # emboss
    sh = gauss_blur(shift_y(cov, shadow["dy"]), shadow["sigma"]) * shadow["alpha"]
    shadow_rgba = np.concatenate([np.broadcast_to(hex2rgb(shadow["color"]), (BH, BW, 3)), sh[..., None]], -1)
    out = over(glyph, shadow_rgba)
    return out, dict(top=top, bottom=bottom)

# ================================================================== Rockbox output
BAYER8 = (np.array([[0,32,8,40,2,34,10,42],[48,16,56,24,50,18,58,26],[12,44,4,36,14,46,6,38],[60,28,52,20,62,30,54,22],
                    [3,35,11,43,1,33,9,41],[51,19,59,27,49,17,57,25],[15,47,7,39,13,45,5,37],[63,31,55,23,61,29,53,21]]) + 0.5) / 64

def quantize(rgba, x0=0, y0=0):
    """alpha to 16 steps (a = 17·n), colour to RGB565, both with an ordered dither.
    x0/y0: position on the screen, so that the dither pattern fits the grid."""
    H, W, _ = rgba.shape
    th = np.roll(np.roll(np.tile(BAYER8, (H // 8 + 2, W // 8 + 2)), -(y0 % 8), 0), -(x0 % 8), 1)[:H, :W]
    a = np.floor(np.clip(rgba[..., 3], 0, 1) * 15 + th).clip(0, 15)
    a8 = (a * 17).astype(np.uint8)
    out = np.zeros((H, W, 4), np.uint8)
    for ch, bits in ((0, 5), (1, 6), (2, 5)):
        mx = (1 << bits) - 1
        q = np.floor(np.clip(rgba[..., ch], 0, 1) * mx + th).clip(0, mx).astype(int)
        out[..., ch] = (q << (8 - bits)) | (q >> (2 * bits - 8))
    out[..., 3] = a8
    out[a8 == 0, :3] = 0
    return out

def write_bmp32(path, rgba8):
    """32 bit BMP, BITMAPINFOHEADER, BI_RGB, bottom up, pixels B G R A."""
    H, W, _ = rgba8.shape
    bgra = rgba8[::-1, :, [2, 1, 0, 3]].tobytes()
    hdr = struct.pack("<2sIHHI", b"BM", 54 + len(bgra), 0, 0, 54)
    info = struct.pack("<IiiHHIIiiII", 40, W, H, 1, 32, 0, len(bgra), 2835, 2835, 0, 0)
    with open(path, "wb") as fh:
        fh.write(hdr + info + bgra)

NAMES = {"podcast_rings": "side_podcast", "note": "side_note", "audiobook": "side_audiobook", "playlists": "side_playlists", "settings": "side_settings", "bookmarks": "side_bookmarks", "info": "side_info", "recording": "side_recording", "files": "side_files", "plugins": "side_plugins", "shortcuts": "side_shortcuts"}

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", default=os.path.join(HERE, "sym_pur.json"))
    ap.add_argument("--out", default="out_side")
    ap.add_argument("--png", action="store_true", help="write PNG previews with alpha")
    args = ap.parse_args()
    syms = json.load(open(args.json, encoding="utf-8"))
    os.makedirs(args.out, exist_ok=True)
    frames = []
    for key, name in NAMES.items():
        rgba, _ = render_side(syms[key])
        q = quantize(rgba, 160 + BMP_RECT[0], BMP_RECT[1])
        write_bmp32(os.path.join(args.out, name + ".bmp"), q)
        if args.png: Image.fromarray(q, "RGBA").save(os.path.join(args.out, name + ".png"))
        frames.append(q)
    strip = np.concatenate(frames, 0)       # frames stacked vertically for %xl(...,11)
    write_bmp32(os.path.join(args.out, "side_symbols.bmp"), strip)
    if args.png: Image.fromarray(strip, "RGBA").save(os.path.join(args.out, "side_symbols.png"))
    print("written:", ", ".join(sorted(os.listdir(args.out))))

if __name__ == "__main__":
    main()
