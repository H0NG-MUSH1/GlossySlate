"""Tile glyphs delivered as finished pictures, into the tile font:

    python3 tools/build_tile_glyphs.py      # after build_fonts.py

tools/sources/tiles/<name>.png are glyphs of the tile font (78 x 113, white
with alpha) made by the designer outside the canvas pipeline: the speaker
of "Sound Settings"/"Volume", the playlist note redrawn after the owner's
icon (17 November 2026; playlist.png is that glyph of the designer's font)
and the 49 motifs of the RetailOS tiles for the settings in
SETTINGS-WITHOUT-TILE.md (one motif for related settings; which setting
shows which tile is in setting_tiles() of build_skin.py). This script puts
them into .rockbox/fonts/113-GlossySlate-Tiles.fnt at the code points of the
designer's font: the speaker and the playlist note replace the canvas ones,
the motifs follow the canvas glyphs (U+E022 on). Glyphs of the font above
the canvas range that are not listed here are removed.

TILE_GLYPHS is also read by build_skin.py (G()). Needs Pillow.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tools.fntread import load  # noqa: E402
from tools.fnt import write_font  # noqa: E402

FONT = os.path.join(os.path.dirname(HERE), '.rockbox', 'fonts', '113-GlossySlate-Tiles.fnt')
SRC = os.path.join(HERE, 'sources', 'tiles')
FIRST = 0xE000                    # blank default glyph (build_fonts.image_font)
CANVAS_LAST = 0xE021              # last glyph build_fonts.py makes from the canvas

TILE_GLYPHS = {
    'speaker': 0xE00E,            # replaces the speaker of the canvas
    'playlist': 0xE006,           # replaces the note of the canvas
    'volume_limit': 0xE022,
    'soundcheck': 0xE023,
    'beep': 0xE024,
    'bass': 0xE025,
    'treble': 0xE026,
    'balance': 0xE027,
    'stereo': 0xE028,
    'stereo_wide': 0xE029,
    'headphones': 0xE02A,
    'dither': 0xE02B,
    'metronome': 0xE02C,
    'compressor': 0xE02D,
    'seek': 0xE02E,
    'skip': 0xE02F,
    'rewind': 0xE030,
    'buffer': 0xE031,
    'fade': 0xE032,
    'single': 0xE033,
    'party': 0xE034,
    'crossfade': 0xE035,
    'next_folder': 0xE036,
    'cd': 0xE037,
    'unplug': 0xE038,
    'remote': 0xE039,
    'tuning_fork': 0xE03A,
    'log': 0xE03B,
    'now_playing': 0xE03C,
    'ipod': 0xE03D,
    'power': 0xE03E,
    'resume': 0xE03F,
    'globe': 0xE040,
    'font': 0xE041,
    'rec_screen': 0xE042,
    'base_skin': 0xE043,
    'backdrop': 0xE044,
    'line_selector': 0xE045,
    'line_separator': 0xE046,
    'palette': 0xE047,
    'main_menu': 0xE048,
    'cfg_file': 0xE049,
    'cfg_save': 0xE04A,
    'audio_file': 0xE04B,
    'plug': 0xE04C,
    'scissors': 0xE04D,
    'prerecord': 0xE04E,
    'rec_folder': 0xE04F,
    'clip_light': 0xE050,
    'trigger': 0xE051,
    'meter': 0xE052,
}


def font_glyphs(path):
    """{code point: (width, alpha rows)} of every glyph of an RB12 font"""
    f = load(path)
    glyphs = {}
    for i in range(f['size']):
        cp = f['first'] + i
        w = f['wids'][i] if f['wids'] else f['maxw']
        o = f['offs'][i] if f['offs'] else i * ((f['h'] * w + 1) // 2)
        if cp != f['default'] and o == f['offs'][f['default'] - f['first']]:
            continue                                  # falls back to the default glyph
        rows = []
        for y in range(f['h']):
            row = []
            for x in range(w):
                n = y * w + x
                b = f['bits'][o + n // 2]
                v = (b >> 4) if (n & 1) else (b & 15)
                row.append((15 - v) * 17)             # 0 = ink in the file
            rows.append(row)
        glyphs[cp] = (w, rows)
    return f, glyphs


def main():
    f, glyphs = font_glyphs(FONT)
    glyphs = {cp: g for cp, g in glyphs.items() if cp <= CANVAS_LAST}
    for name, cp in TILE_GLYPHS.items():
        im = Image.open(os.path.join(SRC, name + '.png')).convert('RGBA')
        assert im.height == f['h'], (name, im.size)
        a = im.split()[3].load()
        glyphs[cp] = (im.width, [[a[x, y] for x in range(im.width)] for y in range(im.height)])
    last = max(glyphs)
    size = write_font(FONT, glyphs, f['h'], f['asc'], FIRST, last, FIRST)
    print('113-GlossySlate-Tiles.fnt: %d glyphs, U+%04X..U+%04X, %d bytes'
          % (len(glyphs) - 1, FIRST + 1, last, size))


if __name__ == '__main__':
    main()
