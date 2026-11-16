"""Render every bitmap of the theme from the design's own CSS/SVG.

Outputs
  out/GlossySlate/.rockbox/wps/glossyslate/*.bmp   skin bitmaps
  cache/glyphs/*.png                               alpha renders for the
                                                   icon and clock fonts
  out/GlossySlate/firmware-assets/*                fork list images
"""
import io, os, json, math
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
import design as D
from tools.bmp import write_bmp24, write_bmp32

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, 'out', 'GlossySlate')
BMP = os.path.join(PKG, '.rockbox', 'wps', 'glossyslate')
FW = os.path.join(PKG, 'firmware-assets')
GFX = os.path.join(PKG, 'graphics')
CACHE = os.path.join(HERE, 'cache')
GLY = os.path.join(CACHE, 'glyphs')
for d in (BMP, FW, GFX, GLY):
    os.makedirs(d, exist_ok=True)

LOCKPREV_BOX = (15, 61, 145, 192)   # sidebar coords: preview 128 x 96 at 16,62, 1 px edge, reflection to 192

PAGE = ('<!doctype html><html><head><meta charset="utf-8"><style>'
        'html,body{margin:0;padding:0;background:transparent}'
        '*{-webkit-font-smoothing:antialiased} svg{display:block}'
        '#r{position:relative;overflow:hidden;font-family:%s}</style></head>'
        '<body><div id="r" style="width:%dpx;height:%dpx">%s</div></body></html>')


def png_b64(im):
    """PNG of a picture as base64, for <img src="data:..."> in an overview"""
    import base64
    buf = io.BytesIO()
    im.save(buf, 'PNG')
    return base64.b64encode(buf.getvalue()).decode('ascii')


# labels of the 25 battery states, in the order of the sprite
BATTERY_LABELS = (['unknown'] + ['%d %%' % (10 * i) for i in range(11)] + ['charging, unknown']
                  + ['charging, %d %%' % (10 * i) for i in range(11)] + ['charged'])


class R:
    def __init__(self, pw):
        self.b = pw.chromium.launch()
        self.p = self.b.new_page(viewport={'width': 400, 'height': 400}, device_scale_factor=1)

    def shot(self, inner, w, h, transparent=True):
        self.p.set_viewport_size({'width': max(w, 50), 'height': max(h, 50)})
        self.p.set_content(PAGE % (D.FONT_STACK, w, h, inner))
        png = self.p.screenshot(clip={'x': 0, 'y': 0, 'width': w, 'height': h},
                                omit_background=transparent)
        return Image.open(io.BytesIO(png)).convert('RGBA')


def ab(x, y, w, h, extra=''):
    return 'position:absolute;left:%spx;top:%spx;width:%spx;height:%spx;%s' % (x, y, w, h, extra)


def svg156(size, markup):
    return '<svg width="%d" height="%d" viewBox="0 0 156 156">%s</svg>' % (size, size, markup)


def tile_html(x, y, size, markup, frame=True, symbol=True, rlen=35, rmask=D.REFLECT_MASK):
    """Tile + reflection exactly like the artboards (78/88 px, radius 14)."""
    bg = D.TILE_BG if frame else 'transparent'
    sym = svg156(size, markup) if symbol else ''
    t = '<div style="%s">%s</div>' % (ab(x, y, size, size, 'border-radius:14px;overflow:hidden;background:%s' % bg), sym)
    t += ('<div style="%s"><div style="width:%dpx;height:%dpx;border-radius:14px;overflow:hidden;'
          'transform:scaleY(-1);background:%s">%s</div></div>'
          % (ab(x, y + size, size, rlen, '-webkit-mask-image:%s;mask-image:%s;overflow:hidden' % (rmask, rmask)),
             size, size, bg, sym))
    return t


def usb_logo_html(x, y, size, ejected):
    """Orange USB logo: disc with shadow, no reflection."""
    return ('<div style="%s">%s</div>'
            % (ab(x, y, size, size, 'border-radius:50%%;overflow:hidden;background:%s;box-shadow:%s,%s'
                  % (D.USB_ORANGE, D.USB_RIM, D.USB_SHADOW)),
               svg156(size, D.usb_logo_symbol(ejected))))


def save24(im, name, dither=True):
    write_bmp24(im.convert('RGB'), os.path.join(BMP, name), dither=dither)


def save32(im, name):
    return write_bmp32(im, os.path.join(BMP, name))


def stack(frames):
    w = max(f.width for f in frames)
    h = frames[0].height
    out = Image.new('RGBA', (w, h * len(frames)), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.paste(f, (0, i * h))
    return out


def main():
    # start clean: no stale bitmaps from older builds (only when building,
    # so importing this module for its helpers deletes nothing)
    for f in os.listdir(BMP):
        if f.endswith('.bmp'):
            os.remove(os.path.join(BMP, f))
    manifest = {}
    with sync_playwright() as pw:
        r = R(pw)

        # ---------------- sidebar background (160 x 240) -----------------
        side = r.shot('<div style="%s"></div>' % ab(0, 0, 160, 240, 'background:%s' % D.SIDEBAR_BG), 160, 240, False)
        side.save(os.path.join(CACHE, 'sidebar.png'))
        save24(side, 'sidebar.bmp')

        # ---------------- tile frame + reflection on the sidebar ----------
        frame = r.shot('<div style="%s"></div>%s' % (ab(0, 0, 160, 240, 'background:%s' % D.SIDEBAR_BG),
                                                      tile_html(41, 79, 78, '', symbol=False)), 160, 240, False)
        save24(frame.crop((41, 79, 41 + 78, 79 + 113)), 'tileframe.bmp')

        # ---------------- tile glyphs (alpha for the icon font) ------------
        names = ['folder', 'database', 'gear', 'mic', 'radio', 'playlist', 'plugins', 'info',
                 'podcast', 'book', 'star', 'bookmark', 'play', 'speaker', 'sun', 'timer', 'eq',
                 'shuffle', 'shuffleOff', 'repeatOff', 'repeat', 'repeatOne', 'reset', 'calendar',
                 'art_round', 'scroll_off', 'scroll_left', 'scroll_right',
                 'secondline', 'brush', 'voice', 'sliders', 'logo']
        # album art corners and key lock show picture previews instead of a symbol
        for n in names:
            im = r.shot(tile_html(0, 0, 78, D.tile_symbol(n, '#FFFFFF'), frame=False), 78, 113, True)
            im.save(os.path.join(GLY, 'tile_%s.png' % n))
        manifest['tiles'] = names

        # ---------------- clock face (home page) ---------------------------
        clock_svg = open(os.path.join(HERE, 'clock_face.svg')).read()
        face = r.shot('<div style="%s"></div><div style="%s">%s</div>'
                      % (ab(0, 0, 160, 240, 'background:%s' % D.SIDEBAR_BG),
                         ab(24, 52, 112, 112, 'filter:drop-shadow(2px 3px 3px rgba(0,0,0,.4))'), clock_svg),
                      160, 240, False)
        save24(face.crop((20, 48, 20 + 124, 48 + 124)), 'clockface.bmp')
        # hands: 720 glyphs (12 h x 60 min), 84 x 84 around the centre (80,108)
        hands_dir = os.path.join(GLY, 'hands')
        os.makedirs(hands_dir, exist_ok=True)
        if not os.path.exists(os.path.join(hands_dir, 'h11m59.png')):
            for h in range(12):
                cells = ''
                for m in range(60):
                    ha = h * 30 + m * 0.5
                    ma = m * 6
                    cells += ('<svg style="position:absolute;left:%dpx;top:0" width="84" height="84" viewBox="-42 -42 84 84">'
                              '<defs><filter id="f%d" x="-50%%" y="-50%%" width="200%%" height="200%%">'
                              '<feDropShadow dx=".8" dy="1.3" stdDeviation=".6" flood-color="#000" flood-opacity=".35"/></filter></defs>'
                              '<g filter="url(#f%d)"><path transform="rotate(%s)" d="M2.6 4L1.6 -12L0 -25L-1.6 -12L-2.6 4Z" fill="#000"/>'
                              '<path transform="rotate(%s)" d="M2 5L1.2 -18L0 -37L-1.2 -18L-2 5Z" fill="#000"/></g>'
                              '<circle r="3.4" fill="#000"/></svg>' % (m * 84, m, m, ha, ma))
                strip = r.shot(cells, 84 * 60, 84, True)
                for m in range(60):
                    strip.crop((m * 84, 0, m * 84 + 84, 84)).save(os.path.join(hands_dir, 'h%dm%d.png' % (h, m)))

        # red centre dot over the hands
        save32(r.shot('<svg width="6" height="6" viewBox="-3 -3 6 6"><circle r="1.4" fill="#D9352F"/></svg>', 6, 6), 'clockdot.bmp')

        # ---------------- calendar card (time & date) ----------------------
        cal = r.shot('<div style="%s"></div><div style="%s"><div style="height:22px;background:linear-gradient(180deg,#FA7C76 0%%,#D23B26 100%%);box-shadow:inset 0 -1px 0 rgba(120,20,15,.35)"></div></div>'
                     % (ab(0, 0, 160, 240, 'background:%s' % D.SIDEBAR_BG),
                        ab(30, 74, 100, 90, 'border-radius:14px;overflow:hidden;box-shadow:0 3.5px 7px rgba(0,0,0,.45);background:linear-gradient(180deg,#FFFFFF 0%,#E6EDF7 100%)')),
                     160, 240, False)
        save24(cal.crop((22, 68, 22 + 116, 68 + 108)), 'calendar.bmp')

        # ---------------- key lock: board preview as a fixed picture --------
        # Markup copied from the key lock option artboard (mini screen 128 x 96 at
        # 16,62 with its 1 px edge, 34 px reflection, fictitious cover). Baked
        # onto the sidebar, so it is opaque: 2 bytes/px in RAM, no 4-bit alpha
        # steps in the reflection. Frame 1 = Normal, frame 2 = Lock Screen.
        # No words of the user interface in it (no title, track number or
        # date): the picture is the same in every language.
        frames = []
        for variant in ('normal', 'lock'):
            markup = open(os.path.join(HERE, 'lock_preview_%s.html' % variant), encoding='utf-8').read()
            im = r.shot('<div style="%s"></div>%s' % (ab(0, 0, 160, 240, 'background:%s' % D.SIDEBAR_BG), markup),
                        160, 240, False)
            frames.append(im.crop(LOCKPREV_BOX))
        save24(stack(frames), 'lockprev.bmp')
        manifest['lockprev'] = list(LOCKPREV_BOX[:2])

        # ---------------- default covers ----------------------------------
        # The fork draws real covers with the %Cd effect (tilt, reflection,
        # round corners). Tracks without a cover get the same effect
        # precomputed here; frame 1 = round corners, frame 2 = square.
        from tools.albumart_fx import render_image
        fx = {}
        # the cover of the now playing screen (cover116_fx.bmp) comes from
        # build_wps_cover.py with the firmware's own maths
        for name, size, kw in (('cover100_fx.bmp', 100, dict(tilt=0, refl_height=36, refl_opacity=60)),
                               ('artprev.bmp', 78, dict(tilt=0, refl_height=35, refl_opacity=60))):
            base = r.shot(D.default_cover_svg(size), size, size, False).convert('RGB')
            frames = []
            for radius in (D.COVER_RADIUS, 0):
                im, mx, over = render_image(base, radius=radius, **kw)
                frames.append(im)
            save32(stack(frames), name)
            fx[name] = [mx, over]
        manifest['cover_fx'] = fx
        big = r.shot(D.default_cover_svg(512), 512, 512, False)
        big.convert('RGB').save(os.path.join(FW, 'albumart_list_default_512.png'))
        r.shot(D.default_cover_svg(52), 52, 52, False).convert('RGB').save(os.path.join(FW, 'albumart_list_default.png'))

        # ---------------- status bar icons --------------------------------
        # play, pause (2 px gap), fast forward, rewind: build_quickmenu.py
        # (pure Python, same geometry for all four frames)
        import build_quickmenu as QM
        QM.OUT = BMP
        QM.status_icons()
        lock = ('<svg width="10" height="12" viewBox="0 0 10 12"><path d="M2.6 5.2V3.6A2.4 2.4 0 0 1 7.4 3.6V5.2" fill="none" stroke="{c}" stroke-width="1.6"/>'
                '<rect x=".8" y="5" width="8.4" height="6.4" rx="1.2" fill="{c}"/></svg>')
        save32(r.shot(lock.replace('{c}', D.ICON_DARK), 10, 12), 'status_lock.bmp')
        save32(r.shot(lock.replace('{c}', '#FFFFFF'), 10, 12), 'status_lock_white.bmp')

        # spinner, 12 phases; light copy for the black USB bar
        op = [1, .2, .2, .2, .2, .2, .2, .28, .36, .48, .62, .8]
        for color, name in ((D.ICON_DARK, 'status_spinner.bmp'), (D.ICON_LIGHT, 'status_spinner_light.bmp')):
            frames = []
            for k in range(12):
                spokes = ''.join('<path transform="rotate(%d)" d="M0 -3.3V-6.2" stroke="%s" stroke-width="1.5" stroke-linecap="round" stroke-opacity="%s"/>'
                                 % (i * 30, color, op[i]) for i in range(12))
                frames.append(r.shot('<svg width="14" height="14" viewBox="-7 -7 14 14"><g transform="rotate(%d)">%s</g></svg>' % (k * 30, spokes), 14, 14))
            save32(stack(frames), name)

        # battery: 12 frames for %bl (unknown, 0..100) + 2 charger frames
        GREEN = 'linear-gradient(180deg, #A9E38F 0%, #D4F7BA 18%, #7DBE5A 42%, #418522 67%, #4E9B2A 100%)'
        RED = 'linear-gradient(180deg, #F2A196 0%, #FBD0C8 18%, #E36A5A 42%, #B8281C 67%, #C63A2B 100%)'
        POLE = 'linear-gradient(180deg, #9A9DA3 0%, #5E6065 100%)'

        def batt(lvl, bolt=False, plug=False, unknown=False):
            w = 0 if unknown else round(lvl / 100 * 22)
            empty = (lvl == 0 and not bolt) and not unknown
            frame = '#B02A1A' if empty else '#505153'
            pole = '#B02A1A' if empty else POLE
            fill = RED if lvl < 20 else GREEN
            cut = '1px 0 0 #4E4F52' if 0 < w < 22 else 'none'
            extra = ''
            if bolt:
                extra = '<svg style="position:absolute;left:0;top:0" width="22" height="11" viewBox="0 0 22 11"><path d="M12.4 .8L7.6 6.2H10.6L9.6 10.2L14.4 4.8H11.4Z" fill="#22401B" stroke="rgba(230,255,220,.6)" stroke-width=".7" stroke-linejoin="round"/></svg>'
            if plug:
                extra = '<svg style="position:absolute;left:0;top:0" width="22" height="11" viewBox="0 0 22 11"><path d="M4.5 5.5H8.5M15 7.6H12A2.1 2.1 0 0 1 12 3.4H15ZM15 4.4H17.5M15 6.6H17.5" fill="#22401B" stroke="#22401B" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
            html = ('<div style="%s"><div style="width:%dpx;height:11px;background:%s;box-shadow:%s"></div>%s</div>'
                    '<div style="%s"></div>' % (
                        ab(0, 0, 24, 13, 'box-sizing:border-box;border:1px solid %s;border-radius:2.5px;overflow:hidden;background:linear-gradient(180deg,#46474B 0%%,#8F9396 100%%)' % frame),
                        w, fill, cut, extra, ab(24, 4, 2, 5, 'border-radius:0 1px 1px 0;background:%s' % pole)))
            return r.shot(html, 26, 13)
        lv = [batt(0, unknown=True)] + [batt(l) for l in range(0, 101, 10)]
        save32(stack(lv), 'status_battery.bmp')
        save32(stack([batt(60, bolt=True), batt(100, plug=True)]), 'status_charge.bmp')

        # monochrome variant after the RetailOS battery (template on the black
        # bar): light outline, dark gap all round, light grey fill, no colour.
        # Same 25 frames in the same order as graphics/battery_sprite.
        BM = D.BATT_MONO

        def batt_mono(lvl, bolt=False, plug=False, unknown=False):
            w = 0 if unknown else round(lvl / 100 * 20)
            extra = ''
            if bolt:
                extra = ('<svg style="position:absolute;left:1px;top:1px" width="22" height="11" viewBox="0 0 22 11">'
                         '<path d="M12.4 .8L7.6 6.2H10.6L9.6 10.2L14.4 4.8H11.4Z" fill="%s" stroke="%s" stroke-width=".7" '
                         'stroke-linejoin="round"/></svg>' % (BM['symbol'], BM['symbol_edge']))
            if plug:
                extra = ('<svg style="position:absolute;left:1px;top:1px" width="22" height="11" viewBox="0 0 22 11">'
                         '<path d="M4.5 5.5H8.5M15 7.6H12A2.1 2.1 0 0 1 12 3.4H15ZM15 4.4H17.5M15 6.6H17.5" fill="%s" stroke="%s" '
                         'stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>' % (BM['symbol'], BM['symbol']))
            html = ('<div style="%s"></div><div style="%s"></div>%s<div style="%s"></div>' % (
                ab(0, 0, 24, 13, 'box-sizing:border-box;border:1px solid %s;border-radius:2.5px;background:%s'
                   % (BM['outline'], BM['gap'])),
                ab(2, 2, w, 9, 'border-radius:1px;background:%s' % BM['fill']),
                extra,
                ab(24, 4, 2, 5, 'border-radius:0 1px 1px 0;background:%s' % BM['pole'])))
            return r.shot(html, 26, 13)
        mono = ([batt_mono(0, unknown=True)] + [batt_mono(l) for l in range(0, 101, 10)]
                + [batt_mono(0, bolt=True, unknown=True)] + [batt_mono(l, bolt=True) for l in range(0, 101, 10)]
                + [batt_mono(100, plug=True)])
        sprite = stack(mono)
        write_bmp32(sprite, os.path.join(GFX, 'battery_sprite_mono.bmp'))
        # USB screens (black bar): the monochrome battery in the theme, same
        # 12 frames as status_battery / status_charge for %xd(...,%bl):
        # 1 unknown, 2-12 0..100 %; the plug (frame 25) is not used there
        save32(stack(mono[:12]), 'status_battery_mono.bmp')
        save32(stack(mono[12:24]), 'status_charge_mono.bmp')
        sprite.save(os.path.join(GFX, 'battery_sprite_mono.png'))
        cells = ''.join(
            '<div style="display:flex;flex-direction:column;align-items:center;gap:4px;width:104px">'
            '<img src="data:image/png;base64,%s" style="width:104px;height:52px;image-rendering:pixelated">'
            '<span style="font:700 11px/14px %s;color:#C9CDD3">%d · %s</span></div>'
            % (png_b64(f.resize((104, 52), Image.NEAREST)), D.FONT_STACK, i + 1, lab)
            for i, (f, lab) in enumerate(zip(mono, BATTERY_LABELS)))
        sheet = ('<div style="position:absolute;left:0;top:0;width:1056px;height:300px;'
                 'background:linear-gradient(180deg,%s,%s);'
                 'box-sizing:border-box;padding:20px;display:flex;flex-wrap:wrap;gap:16px 10px;align-content:flex-start">'
                 '%s</div>' % (D.STATUS_DARK[0], D.STATUS_DARK[1], cells))
        r.shot(sheet, 1056, 300, False).convert('RGB').save(os.path.join(GFX, 'battery_sprite_mono_overview.png'))

        # ---------------- home page: small white status icons --------------
        spk = ('<svg width="16" height="14" viewBox="0 0 16 14"><path d="M1 5H3.4L7 2V12L3.4 9H1Z" fill="#FFFFFF"/>'
               '<path d="M9.6 4.6A3.4 3.4 0 0 1 9.6 9.4M11.8 2.6A6.2 6.2 0 0 1 11.8 11.4" fill="none" stroke="#FFFFFF" stroke-width="1.4" stroke-linecap="round"/></svg>')
        save32(r.shot(spk, 16, 14), 'home_speaker.bmp')
        shf = ('<svg width="18" height="14" viewBox="0 0 14 10" style="opacity:{o}"><path d="M1 2.5H3.2C6 2.5 7 7.5 9.8 7.5H11.5M1 7.5H3.2C6 7.5 7 2.5 9.8 2.5H11.5" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>'
               '<path d="M11 .4L13.6 2.5L11 4.6ZM11 5.4L13.6 7.5L11 9.6Z" fill="{c}"/></svg>')
        rep = ('<svg width="18" height="14" viewBox="0 0 14 10" style="opacity:{o}"><path d="M2 6.5V4.2A2 2 0 0 1 4 2.2H10.5M12 3.5V5.8A2 2 0 0 1 10 7.8H3.5" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>'
               '<path d="M10 .2L12.6 2.2L10 4.2ZM4 5.8L1.4 7.8L4 9.8Z" fill="{c}"/>{one}</svg>')
        one = '<circle cx="7" cy="5" r="2.3" fill="{c}"/><text x="7" y="6.4" text-anchor="middle" font-family="Liberation Sans" font-size="3.6" font-weight="700" fill="{bg}">1</text>'

        def shuffle_icon(c, o, w, size=(18, 14)):
            return r.shot(shf.replace('{c}', c).replace('{o}', str(o)).replace('{w}', str(w)).replace('width="18" height="14"', 'width="%d" height="%d"' % size), *size)

        def repeat_icon(c, o, w, one_badge, bgc, size=(18, 14)):
            s = rep.replace('{one}', one if one_badge else '').replace('{c}', c).replace('{o}', str(o)).replace('{w}', str(w)).replace('{bg}', bgc)
            return r.shot(s.replace('width="18" height="14"', 'width="%d" height="%d"' % size), *size)
        # %ps frames: 1 = on, 2 = off ; %mm frames: off, all, one, shuffle, a-b
        save32(stack([shuffle_icon('#FFFFFF', 1, 1.4), shuffle_icon('#FFFFFF', .45, 1.4)]), 'home_shuffle.bmp')
        save32(stack([repeat_icon('#FFFFFF', .45, 1.4, False, '#000'), repeat_icon('#FFFFFF', 1, 1.4, False, '#000'),
                      repeat_icon('#FFFFFF', 1, 1.4, True, '#5A7FA6'), repeat_icon('#FFFFFF', 1, 1.4, False, '#000'),
                      repeat_icon('#FFFFFF', 1, 1.4, False, '#000')]), 'home_repeat.bmp')
        # WPS versions 14 x 10, accent / grey; frame 3 (one) is the plain loop
        # here, build_wps_repeat.py adds its dot (too small for a "1")
        save32(stack([shuffle_icon(D.ACCENT['solid'], 1, 1.6, (14, 10)), shuffle_icon('#A9B0BA', 1, 1.6, (14, 10))]), 'wps_shuffle.bmp')
        save32(stack([repeat_icon('#A9B0BA', 1, 1.6, False, '#fff', (14, 10)), repeat_icon(D.ACCENT['solid'], 1, 1.6, False, '#fff', (14, 10)),
                      repeat_icon(D.ACCENT['solid'], 1, 1.6, False, '#fff', (14, 10)), repeat_icon(D.ACCENT['solid'], 1, 1.6, False, '#fff', (14, 10)),
                      repeat_icon(D.ACCENT['solid'], 1, 1.6, False, '#fff', (14, 10))]), 'wps_repeat.bmp')

        # ---------------- USB logos (88 + shadow, alpha) -------------------
        # 2 frames: 1 verbunden, 2 am Computer ausgeworfen (Fork: %cs = 22)
        pl, pt, pr, pb = D.USB_PAD
        usb = [r.shot(usb_logo_html(pl, pt, 88, ej), pl + 88 + pr, pt + 88 + pb, True) for ej in (False, True)]
        save32(stack(usb), 'usb_logo.bmp')

        # ---------------- lock screen clock box (alpha corners) ------------
        box = r.shot('<div style="%s"></div>' % ab(0, 0, 200, 90, 'border-radius:8px;background:%s' % D.TILE_BG), 200, 90, True)
        save32(box, 'lock_box.bmp')

        # ---------------- WPS progress + volume ---------------------------
        def track(w):
            return r.shot('<div style="%s"></div>' % ab(0, 0, w, 9, 'border-radius:5px;background:%s;box-shadow:%s' % (D.TRACK_BG, D.TRACK_SHADOW)), w, 10, True)

        def fill(w):
            return r.shot('<div style="%s"></div>' % ab(0, 0, w, 9, 'border-radius:5px;background:%s;box-shadow:%s' % (D.ACCENT['fill'], D.FILL_SHADOW)), w, 9, True)
        save32(track(292), 'wps_track.bmp')
        f = fill(292)
        save32(f, 'wps_fill.bmp')
        save32(f.crop((292 - 10, 0, 292, 9)), 'wps_cap.bmp')
        save32(track(252), 'wps_vtrack.bmp')
        f = fill(252)
        save32(f, 'wps_vfill.bmp')
        save32(spk.replace('#FFFFFF', D.ICON_DARK) and r.shot(
            '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M1 4.2H3.2L6.4 1.6V10.4L3.2 7.8H1Z" fill="%s"/></svg>' % D.ICON_DARK, 12, 12), 'wps_vol_low.bmp')
        save32(r.shot(spk.replace('#FFFFFF', D.ICON_DARK), 16, 14), 'wps_vol_high.bmp')

        # codec / sample-rate pills
        pill = 'box-sizing:border-box;border:1px solid #AEB5C0;border-radius:7px;background:linear-gradient(180deg,#FFFFFF 0%,#DCE1E8 100%)'
        save32(r.shot('<div style="%s"></div>' % ab(0, 0, 44, 14, pill), 44, 14), 'wps_pill_codec.bmp')
        save32(r.shot('<div style="%s"></div>' % ab(0, 0, 56, 14, pill), 56, 14), 'wps_pill_rate.bmp')

        # ---------------- list row chevron / check (opaque, bar baked in) ---
        def bar_rows():
            # what Rockbox paints for the selected row: two linear gradients
            # (rows 0-11 and 12-23), see lcd_gradient_fillrect_part()
            def grad(c0, c1, n):
                c0 = [int(c0[i:i + 2], 16) for i in (0, 2, 4)]
                c1 = [int(c1[i:i + 2], 16) for i in (0, 2, 4)]
                return [tuple(int(c0[k] + (c1[k] - c0[k]) * i / n) for k in range(3)) for i in range(n)]
            return grad('5896e6', '3577d9', 12) + grad('2160cb', '1a55be', 12)
        rows = bar_rows()
        chev = '<svg width="6" height="10" viewBox="0 0 6 10"><path d="M1 1L5 5L1 9" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        check = '<svg width="11" height="9" viewBox="0 0 11 9"><path d="M1.2 4.6L4.1 7.4L9.8 1.4" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'

        def on_bar(svg, w, h, y0):
            bg = Image.new('RGBA', (w, h))
            for yy in range(h):
                for xx in range(w):
                    bg.putpixel((xx, yy), rows[y0 + yy] + (255,))
            bg.alpha_composite(r.shot(svg, w, h))
            return bg

        def on_white(svg, w, h):
            bg = Image.new('RGBA', (w, h), (255, 255, 255, 255))
            bg.alpha_composite(r.shot(svg, w, h))
            return bg
        # 32 bit with alpha: drawn after the row text, over the selection gradient
        # arrows in lists come from the firmware now (list arrows: on)
        save32(r.shot(check, 12, 9), 'row_check.bmp')

        # ---------------- fork list images (53 x 53 JPG templates) ---------
        special = {
            'by_album': '<rect x="50" y="26" width="80" height="80" rx="8" fill="url(#g)" fill-opacity=".55"/><rect x="26" y="50" width="80" height="80" rx="8" fill="url(#g)"/><circle cx="66" cy="90" r="27" fill="#07080C"/><circle cx="66" cy="90" r="8" fill="url(#g)"/>',
            'all_tracks': '<g fill="url(#g)"><path d="M22 32H92V48H22ZM22 62H92V78H22ZM22 92H62V108H22Z"/><path d="M104 30H116V111.1H104Z"/><path d="M116 30C119 42 140 50 140 72C140 81 137 88 132 94C134 88 135 83 134 78C132 67 125 61 116 59Z"/><ellipse cx="97.5" cy="114" rx="19" ry="14" transform="rotate(-20 97.5 114)"/></g>',
            'random': '<defs><mask id="cut" maskUnits="userSpaceOnUse" x="0" y="0" width="156" height="156"><rect width="156" height="156" fill="#fff"/><path d="M55.9 97.9L58.9 94.8L61.7 91.3L64.5 87.7L67.2 83.9L69.9 80L72.5 76.1L75.2 72.3L78 68.7L80.8 65.2L83.7 62.1" fill="none" stroke="#000" stroke-width="28"/></mask></defs><path d="M20 54H38C66 54 74 106 101 106" fill="none" stroke="url(#g)" stroke-width="18" mask="url(#cut)"/><path d="M20 106H38C66 106 74 54 101 54" fill="none" stroke="url(#g)" stroke-width="18"/><path d="M100 30L138 54L100 78ZM100 82L138 106L100 130Z" fill="url(#g)"/>',
        }
        grad = '<defs><linearGradient id="g" gradientUnits="userSpaceOnUse" x1="0" y1="26" x2="0" y2="130"><stop offset="0" stop-color="#7DB4F0"/><stop offset="1" stop-color="#3577D9"/></linearGradient></defs>'
        sbg = 'linear-gradient(180deg, #4A525E 0px, #4A525E 1px, #2B3039 4%, #1A1E25 40%, #0B0E14 50%, #07080C 100%)'
        for k, mk in special.items():
            for size, ext in ((53, 'jpg'), (512, 'png')):
                im = r.shot('<div style="width:%dpx;height:%dpx;background:%s"><svg width="%d" height="%d" viewBox="0 0 156 156">%s%s</svg></div>'
                            % (size, size, sbg, size, size, grad, mk), size, size, False).convert('RGB')
                if ext == 'jpg':
                    im.save(os.path.join(FW, 'albumart_list_%s.jpg' % k), quality=95)
                else:
                    im.save(os.path.join(FW, 'albumart_list_%s_512.png' % k))

        # ---------------- blue field (lock screen, USB) without a bitmap -----
        # 16 bands of 15 rows; each band is one vertical %dr gradient between
        # the mean colours of its first and last row (the diagonal darkening of
        # the design averages out across the width)
        fld = np.asarray(r.shot('<div style="width:320px;height:240px;background:%s"></div>' % D.FIELD_BG,
                                320, 240, False).convert('RGB')).astype(float)
        hx = lambda c: '%02x%02x%02x' % tuple(int(round(v)) for v in c)
        bands = [[y, 15, hx(fld[y].mean(0)), hx(fld[y + 14].mean(0))] for y in range(0, 240, 15)]
        json.dump(bands, open(os.path.join(CACHE, 'field_bands.json'), 'w'))
        r.b.close()
    json.dump(manifest, open(os.path.join(CACHE, 'manifest.json'), 'w'))
    print('assets ok')


if __name__ == '__main__':
    main()
