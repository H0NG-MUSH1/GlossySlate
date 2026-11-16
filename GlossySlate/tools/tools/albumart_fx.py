"""Album art effect of the fork's %Cd(tilt,perspective,refl_height,refl_opacity,radius).

Same geometry as described for the firmware: corners rounded first, then the
cover is turned about its vertical centre line (positive tilt: right edge
back) and projected with the given perspective distance; each column gets a
mirrored reflection below its own lower edge that fades linearly from
refl_opacity % to 0 over refl_height px.

This is an independent re-implementation (floating point, 4 x 4 supersampling),
written from that description. If the fork ships its own albumart_fx.py with
the firmware's integer maths, use that one instead; the call is the same:

    img, mx, over = render_image(cover, tilt=24, perspective=420,
                                 refl_height=36, refl_opacity=34, radius=8)

img is RGBA, (w + 2*mx) x (h + 2*over + refl_height); draw it at
(cover_x - mx, cover_y - over).
"""
import math

import numpy as np
from PIL import Image

SS = 4  # supersampling per axis


def _rounded_source(img, radius):
    """Premultiplied float RGBA of the cover with anti-aliased round corners."""
    src = np.asarray(img.convert('RGBA'), dtype=np.float64) / 255.0
    h, w = src.shape[:2]
    if radius > 0:
        r = float(radius)
        ys, xs = np.mgrid[0:h * SS, 0:w * SS]
        px = (xs + .5) / SS
        py = (ys + .5) / SS
        dx = np.maximum(np.maximum(r - px, px - (w - r)), 0)
        dy = np.maximum(np.maximum(r - py, py - (h - r)), 0)
        inside = (dx * dx + dy * dy) <= r * r
        cov = inside.reshape(h, SS, w, SS).mean(axis=(1, 3))
        src[..., 3] *= cov
    src[..., :3] *= src[..., 3:4]
    return src


def _sample(src, x, y):
    """Bilinear sample of premultiplied RGBA at pixel coordinates (centres at
    integer + .5); outside the image is transparent."""
    h, w = src.shape[:2]
    pad = np.zeros((h + 2, w + 2, 4))
    pad[1:-1, 1:-1] = src
    fx = x - .5 + 1
    fy = y - .5 + 1
    x0 = np.floor(fx).astype(int)
    y0 = np.floor(fy).astype(int)
    tx = (fx - x0)[..., None]
    ty = (fy - y0)[..., None]
    x0 = np.clip(x0, 0, w + 1)
    y0 = np.clip(y0, 0, h + 1)
    x1 = np.clip(x0 + 1, 0, w + 1)
    y1 = np.clip(y0 + 1, 0, h + 1)
    a = pad[y0, x0] * (1 - tx) + pad[y0, x1] * tx
    b = pad[y1, x0] * (1 - tx) + pad[y1, x1] * tx
    return a * (1 - ty) + b * ty


def geometry(w, h, tilt=0, perspective=420):
    """Margins of the projected cover: (mx, over)."""
    if not tilt:
        return 0, 0
    t = math.radians(tilt)
    c, s, p = math.cos(t), math.sin(t), float(perspective)
    half_w, half_h = w / 2.0, h / 2.0
    k_left = p / (p - half_w * s)
    k_right = p / (p + half_w * s)
    x_ext = max(half_w * c * k_left, half_w * c * k_right)
    k_max = max(k_left, k_right)
    mx = max(0, int(math.ceil(x_ext - half_w - 1e-9)))
    over = max(0, int(math.ceil(half_h * k_max - half_h - 1e-9)))
    return mx, over


def render_image(img, tilt=0, perspective=420, refl_height=0, refl_opacity=34, radius=0):
    w, h = img.size
    src = _rounded_source(img, radius)
    mx, over = geometry(w, h, tilt, perspective)
    out_w, out_h = w + 2 * mx, h + 2 * over + int(refl_height)
    t = math.radians(tilt)
    c, s, p = math.cos(t), math.sin(t), float(perspective)

    ys, xs = np.mgrid[0:out_h * SS, 0:out_w * SS]
    X = (xs + .5) / SS - mx - w / 2.0          # relative to the cover centre
    Y = (ys + .5) / SS - over - h / 2.0
    if tilt:
        xsrc = X * p / (c * p - X * s)
        k = p / (p + xsrc * s)
    else:
        xsrc = X
        k = np.ones_like(X)
    bottom = (h / 2.0) * k                      # lower edge of this column
    below = Y > bottom
    d = Y - bottom
    ysrc = np.where(below, (bottom - d) / k, Y / k)
    fade = np.ones_like(X)
    if refl_height > 0:
        fade = np.where(below, (refl_opacity / 100.0) * np.clip(1 - d / float(refl_height), 0, 1), 1.0)
    else:
        fade = np.where(below, 0.0, 1.0)
    valid = (np.abs(xsrc) <= w / 2.0) & (ysrc >= -h / 2.0) & (ysrc <= h / 2.0)
    smp = _sample(src, xsrc + w / 2.0, ysrc + h / 2.0)
    smp *= (fade * valid)[..., None]
    acc = smp.reshape(out_h, SS, out_w, SS, 4).mean(axis=(1, 3))
    alpha = acc[..., 3:4]
    rgb = np.where(alpha > 1e-6, acc[..., :3] / np.maximum(alpha, 1e-6), 0)
    rgba = np.concatenate([rgb, alpha], axis=-1)
    im = Image.fromarray(np.clip(np.round(rgba * 255), 0, 255).astype(np.uint8), 'RGBA')
    return im, mx, over


if __name__ == '__main__':
    import sys
    cov = Image.open(sys.argv[1])
    im, mx, over = render_image(cov, tilt=24, perspective=420, refl_height=36, refl_opacity=34, radius=8)
    print(im.size, mx, over)
    im.save(sys.argv[2])
