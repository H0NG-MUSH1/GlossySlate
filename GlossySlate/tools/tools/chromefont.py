"""Render Rockbox font glyphs with Chromium, the engine the mockups are drawn with.

Each glyph is laid out like the mockup text (same family, size, weight,
letter-spacing, line box, -webkit-font-smoothing: antialiased) but alone and
at a whole-pixel origin, so the bitmap is what the mockup shows for that
glyph.

Rockbox fonts have whole-pixel advances and no kerning. The CSS advance
(including letter-spacing) is rounded at a threshold chosen per font so that
typical German and English menu texts keep the width they have in the mockup
(see best_threshold).

Coverage: Skia draws light text on dark grounds a little heavier than dark
text on light grounds (gamma). 'dark' takes the glyphs from black on white
(coverage = 1 - v), 'light' from white on black (coverage = v), 'mixed' is
the mean of both. Rockbox blends linearly, so 'dark' and 'light' reproduce the
mockup exactly for their case.
"""
import io
import math

from PIL import Image

FAMILY = "'Arimo','Liberation Sans','Helvetica Neue',Helvetica,Arial,sans-serif"
PAD = 10            # room around each glyph for overhangs
COLS = 40


def _style(weight, px, h, tracking, color):
    return ("font-family:%s;font-weight:%d;font-size:%spx;line-height:%dpx;letter-spacing:%spx;"
            "-webkit-font-smoothing:antialiased;white-space:pre;color:%s" % (FAMILY, weight, px, h, tracking, color))


def measure(page, cps, weight, px, h, tracking=0.0):
    """Fractional CSS advances {cp: width} and the baseline of a line box h."""
    style = _style(weight, px, h, tracking, '#000')
    probe = ''.join('<span data-cp="%d">&#%d;</span>' % (cp, cp) for cp in cps)
    page.set_content('<html><body style="margin:0">'
                     '<div id="m" style="position:absolute;left:0;top:0;%s">%s</div>'
                     '<div id="b" style="position:absolute;left:0;top:0;height:%dpx;%s">x<span id="bl" '
                     'style="display:inline-block;width:0;height:0;vertical-align:baseline"></span></div>'
                     '</body></html>' % (style, probe, h, style))
    page.evaluate('document.fonts.ready')
    adv = page.evaluate("""() => Object.fromEntries([...document.querySelectorAll('#m span')]
                           .map(s => [s.dataset.cp, s.getBoundingClientRect().width]))""")
    base = page.evaluate("""() => document.getElementById('bl').getBoundingClientRect().top
                            - document.getElementById('b').getBoundingClientRect().top""")
    return {int(k): v for k, v in adv.items()}, base


def round_adv(a, threshold):
    f = math.floor(a)
    return int(f + (1 if a - f >= threshold else 0))


def best_threshold(adv, freq, lo=0.40, hi=0.60):
    """Rounding threshold that keeps the width of a text corpus (character
    frequencies freq) closest to the CSS width."""
    tot = sum(n * adv[ord(c)] for c, n in freq.items() if ord(c) in adv)
    best = None
    t = lo
    while t <= hi + 1e-9:
        s = sum(n * round_adv(adv[ord(c)], t) for c, n in freq.items() if ord(c) in adv)
        err = abs(s - tot) / tot
        if best is None or err < best[1] - 1e-12:
            best = (round(t, 2), err)
        t += 0.01
    return best


def _shot(page, cps, weight, px, h, tracking, color, bg, cellw):
    cellh = h + 2 * PAD
    cols = min(COLS, len(cps))
    rows_n = int(math.ceil(len(cps) / cols))
    W, H = cols * cellw, rows_n * cellh
    style = _style(weight, px, h, tracking, color)
    cells = ''.join('<div style="position:absolute;left:%dpx;top:%dpx;height:%dpx;%s">&#%d;</div>'
                    % ((i % cols) * cellw + PAD, (i // cols) * cellh + PAD, h, style, cp)
                    for i, cp in enumerate(cps))
    page.set_viewport_size({'width': W, 'height': H})
    page.set_content('<html><body style="margin:0;background:%s;width:%dpx;height:%dpx">%s</body></html>'
                     % (bg, W, H, cells))
    page.evaluate('document.fonts.ready')
    img = Image.open(io.BytesIO(page.screenshot(clip={'x': 0, 'y': 0, 'width': W, 'height': H}))).convert('L')
    return img.load(), cols, cellh


def render(page, cps, weight, px, h, tracking=0.0, polarity='dark', target_baseline=None,
           threshold=0.5, adv=None, base=None):
    """Return ({cp: (advance, rows)}, baseline, chromium_baseline).
    rows: h lists of 0..255 coverage, glyph origin at x 0."""
    if adv is None or base is None:
        adv, base = measure(page, cps, weight, px, h, tracking)
    base_px = int(round(base))
    tb = base_px if target_baseline is None else target_baseline
    shift = tb - base_px
    cellw = int(math.ceil(max(adv.values()))) + 2 * PAD
    shots = []
    if polarity in ('dark', 'mixed'):
        shots.append((_shot(page, cps, weight, px, h, tracking, '#000000', '#FFFFFF', cellw), True))
    if polarity in ('light', 'mixed'):
        shots.append((_shot(page, cps, weight, px, h, tracking, '#FFFFFF', '#000000', cellw), False))
    out = {}
    for i, cp in enumerate(cps):
        a = round_adv(adv[cp], threshold)
        if a <= 0:
            continue
        grid = []
        for r in range(h):
            src = r - shift
            vals = [0] * a
            if 0 <= src < h + PAD:
                for (px_, cols, cellh), invert in shots:
                    x0 = (i % cols) * cellw + PAD
                    y0 = (i // cols) * cellh + PAD
                    for c in range(a):
                        v = px_[x0 + c, y0 + src]
                        vals[c] += (255 - v) if invert else v
                vals = [int(round(v / len(shots))) for v in vals]
            grid.append(vals)
        out[cp] = (a, grid)
    return out, tb, base
