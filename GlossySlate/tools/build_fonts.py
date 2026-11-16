"""Build the theme's Rockbox fonts (RB12, 4-bit anti-aliased).

Text fonts are rendered with Chromium exactly like the text of the mockups
(tools/chromefont.py): Arimo as in the design, here from Liberation Sans 2,
which has Arimo's outlines and metrics. Their file names do not use the
reserved names "Liberation" or "Arimo" (SIL OFL 1.1).
Icon and clock fonts are built from alpha renders in cache/glyphs.
"""
import os, glob, json, collections
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from playwright.sync_api import sync_playwright
from tools.fnt import write_font
from tools import chromefont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'GlossySlate', '.rockbox', 'fonts')
EXTRA = os.path.join(HERE, 'out', 'GlossySlate', 'fonts-extra')   # mockup styles the theme does not load
GLY = os.path.join(HERE, 'cache', 'glyphs')
os.makedirs(OUT, exist_ok=True)
os.makedirs(EXTRA, exist_ok=True)
TTF = {
    'Bold': '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    'Regular': '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
}
ASC, DESC = 0.905, 0.212          # hhea metrics of Arimo / Liberation Sans

RANGES = [(0x20, 0x7E), (0xA0, 0x24F), (0x370, 0x3FF), (0x400, 0x4FF),
          (0x2010, 0x2027), (0x2030, 0x203A), (0x2044, 0x2044), (0x20AC, 0x20AC),
          (0x2116, 0x2116), (0x2122, 0x2122), (0x2190, 0x2193), (0x2212, 0x2212),
          (0x2264, 0x2265), (0x25B2, 0x25C4), (0x25CF, 0x25CF)]


def baseline(h, px):
    return int(round((h - (ASC + DESC) * px) / 2 + ASC * px))


def corpus_freq():
    """Character frequencies of the Rockbox texts (apps/lang) in the
    languages that carry the theme's texts."""
    from tools.rblang import read
    freq = collections.Counter()
    for name in ('english', 'deutsch', 'espanol'):
        for t in read(name).values():
            freq.update(t)
    return freq


# Text styles of the mockups: file, weight, size, line box, letter-spacing,
# glyph set, polarity (how the style is mostly used: dark text on light
# ground, light on dark, or both).
STYLES = [
    ('24-GlossySlate-Bold14.fnt', 700, 14, 24, 0.0, None, 'dark'),      # list rows
    ('16-GlossySlate-Bold13.fnt', 700, 13, 16, 0.0, None, 'mixed'),     # status title, values
    ('20-GlossySlate-Bold17.fnt', 700, 17, 20, 0.0, None, 'light'),     # sidebar titles
    ('14-GlossySlate-Bold11.fnt', 700, 11, 14, 0.0, None, 'mixed'),     # second lines, pills
    ('16-GlossySlate-Bold12.fnt', 700, 12, 16, 0.0, None, 'dark'),      # times, dB
    ('16-GlossySlate-Regular13.fnt', 400, 13, 16, 0.0, None, 'dark'),   # album line
    ('70-GlossySlate-Clock58.fnt', 700, 58, 70, -1.5, ' 0123456789:', 'light'),   # lock screen clock
    ('46-GlossySlate-Day46.fnt', 500, 46, 46, -1.0, ' 0123456789', 'dark'),        # calendar day
]
# in the mockups, not (yet) used by the theme: written to fonts-extra/
EXTRA_STYLES = [
    ('16-GlossySlate-Regular12.fnt', 400, 12, 16, 0.0, None, 'dark'),   # help texts
    ('12-GlossySlate-Bold9.fnt', 700, 9, 12, 0.4, None, 'dark'),        # codec pills
    ('12-GlossySlate-Regular9.fnt', 400, 9, 12, 0.0, None, 'dark'),     # recording labels
    ('22-GlossySlate-Bold14x5.fnt', 700, 14.5, 22, 0.75, None, 'light'),  # calendar month
]


def text_font(page, freq, name, weight, px, h, tracking=0.0, chars=None, polarity='dark', outdir=OUT):
    """Glyphs as Chromium draws them in the mockups (tools/chromefont.py)."""
    cmap = TTFont(TTF['Bold' if weight >= 600 else 'Regular']).getBestCmap()
    if chars is None:
        cps = [cp for a, b in RANGES for cp in range(a, b + 1) if cp in cmap]
    else:
        cps = [ord(c) for c in chars]
    adv, base = chromefont.measure(page, cps, weight, px, h, tracking)
    thr, err = chromefont.best_threshold(adv, freq) if chars is None else (0.5, 0.0)
    # baseline exactly where Chromium puts it in a line box of height h (it
    # rounds ascent and descent first; baseline() above can be 1 px lower)
    b = int(round(base))
    glyphs, _, cbase = chromefont.render(page, cps, weight, px, h, tracking, polarity, b,
                                         threshold=thr, adv=adv, base=base)
    if 0x20 not in glyphs:
        glyphs[0x20] = (max(1, int(px) // 4), [[0] * max(1, int(px) // 4) for _ in range(h)])
    first, last = min(glyphs), max(glyphs)
    path = os.path.join(outdir, name)
    size = write_font(path, glyphs, h, b, first, last, 0x20)
    INFO.append({'datei': name, 'gewicht': weight, 'groesse': px, 'zeile': h, 'laufweite': tracking,
                 'grundlinie': b, 'grundlinie_bis_1_5': baseline(h, px), 'polaritaet': polarity,
                 'rundung_ab': thr, 'breitenfehler_prozent': round(err * 100, 2), 'zeichen': len(glyphs)})
    return name, len(glyphs), size


INFO = []


def split_font(name_top, name_bottom, weight, px, h, cut):
    """The UI text split at row `cut` into two fonts. Skinned list rows use
    them in two stacked viewports so the selection bar can change gradient
    at the gloss edge (Rockbox draws one linear gradient per text line)."""
    f = ImageFont.truetype(TTF[weight], px)
    cmap = TTFont(TTF[weight]).getBestCmap()
    cps = [cp for a, b in RANGES for cp in range(a, b + 1) if cp in cmap]
    b = baseline(h, px)
    top, bot = {}, {}
    for cp in cps:
        ch = chr(cp)
        adv = int(round(f.getlength(ch)))
        if adv <= 0:
            continue
        im = Image.new('L', (adv + 8, h), 0)
        ImageDraw.Draw(im).text((0, b), ch, font=f, fill=255, anchor='ls')
        px_ = im.load()
        rows = [[px_[x, y] for x in range(adv)] for y in range(h)]
        top[cp] = (adv, rows[:cut])
        bot[cp] = (adv, rows[cut:])
    first, last = min(top), max(top)
    s1 = write_font(os.path.join(OUT, name_top), top, cut, min(b, cut), first, last, 0x20)
    s2 = write_font(os.path.join(OUT, name_bottom), bot, h - cut, max(1, b - cut), first, last, 0x20)
    return [(name_top, len(top), s1), (name_bottom, len(bot), s2)]


def image_font(name, pngs, h, first=0xE000):
    """Glyph first+1+i = pngs[i]; first itself is a blank default glyph."""
    glyphs = {first: (2, [[0, 0] for _ in range(h)])}
    for i, p in enumerate(pngs):
        im = Image.open(p).convert('RGBA')
        assert im.height == h, (p, im.size)
        a = im.split()[3]
        px_ = a.load()
        glyphs[first + 1 + i] = (im.width, [[px_[x, y] for x in range(im.width)] for y in range(h)])
    path = os.path.join(OUT, name)
    size = write_font(path, glyphs, h, h, first, first + len(pngs), first)
    return name, len(glyphs), size


def main():
    built = []
    freq = corpus_freq()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={'width': 400, 'height': 400}, device_scale_factor=1)
        for name, weight, px, h, tracking, chars, pol in STYLES:
            built.append(text_font(page, freq, name, weight, px, h, tracking, chars, pol))
        for name, weight, px, h, tracking, chars, pol in EXTRA_STYLES:
            built.append(text_font(page, freq, name, weight, px, h, tracking, chars, pol, EXTRA))
        browser.close()
    json.dump(INFO, open(os.path.join(HERE, 'cache', 'fonts.json'), 'w'), ensure_ascii=False, indent=1)
    # 1 px font: keeps line clears in background viewports to a single row
    from tools.fnt import write_font as wf
    wf(os.path.join(OUT, '1-GlossySlate-Dot.fnt'), {0x20: (1, [[0]])}, 1, 1, 0x20, 0x20, 0x20)
    built.append(('1-GlossySlate-Dot.fnt', 1, 0))

    tiles = json.load(open(os.path.join(HERE, 'cache', 'manifest.json')))['tiles']
    built.append(image_font('113-GlossySlate-Tiles.fnt',
                            [os.path.join(GLY, 'tile_%s.png' % n) for n in tiles], 113))
    hands = [os.path.join(GLY, 'hands', 'h%dm%d.png' % (h, m)) for h in range(12) for m in range(60)]
    built.append(image_font('84-GlossySlate-Hands.fnt', hands, 84))
    json.dump({'tiles': {n: 0xE001 + i for i, n in enumerate(tiles)}},
              open(os.path.join(HERE, 'cache', 'fontmap.json'), 'w'))
    for b in built:
        print('%-34s %5d glyphs %8d bytes' % b)


if __name__ == '__main__':
    main()
