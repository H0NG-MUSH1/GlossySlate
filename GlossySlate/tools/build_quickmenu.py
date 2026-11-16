"""Status bar play icons and the quick menu (DESIGN.md 5.10)
of Glossy Slate, without a browser:

    python3 tools/build_quickmenu.py

writes into .rockbox/wps/glossyslate/:

    status_play.bmp   8 x 10, 4 frames: play, pause, fast forward, rewind
    qs_*.bmp          quick menu art

and the skin code of the quick menu (quickmenu_skin(), used by
build_skin.py). The quick menu parts come from the design board
(tools/quickmenu: BMPs, places in parts.json, rules in
README.md); they are only rearranged into frames here. Pure Python.
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tools import raster as R  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), '.rockbox', 'wps', 'glossyslate')
SYM = json.load(open(os.path.join(HERE, 'sym.json')))['Settings']

DARK = R.hexc('2E3644')
GREY = R.hexc('5B6371')
BORDER = R.hexc('A7AFBB')
WHITE = (255, 255, 255)
BLUE = R.hexc('5896E6')
BLUE_EDGE = R.hexc('174A9E')
BLUE_LIGHT = R.hexc('98BEF0')
P1, P2 = R.hexc('7DB4F0'), R.hexc('1F5FC8')
SHADOW = (20, 30, 50)


def save(name, frames):
    R.write_bmp32(os.path.join(OUT, name), frames)


# ---------------------------------------------------------------- status bar
def status_frame(fills, outline):
    """fills: inside tests; outline: polylines for the 0.8 px contour"""
    c = R.Canvas(8, 10)
    fill = R.coverage(8, 10, lambda x, y: any(f(x, y) for f in fills), 8)
    c.paint(fill, R.vgrad([(0, P1), (1, P2)], 0.6, 9.4))
    c.paint(R.coverage(8, 10, outline, 8), BLUE_EDGE)
    return c


def tri(points):
    return [(points, True)]


def rect_band(x0, y0, x1, y1, r, w):
    outer = R.rrect(x0 - w / 2, y0 - w / 2, x1 + w / 2, y1 + w / 2, r + w / 2)
    inner = R.rrect(x0 + w / 2, y0 + w / 2, x1 - w / 2, y1 - w / 2, max(r - w / 2, 0))
    return lambda x, y: outer(x, y) and not inner(x, y)


def status_icons():
    play = tri([(.6, .6), (7.4, 5), (.6, 9.4)])
    frames = [status_frame([R.fill_inside(play)], R.stroke_inside(play, .8))]
    # pause: two bars with a clear 2 px gap (columns 3 and 4)
    bars = [(.4, .6, 2.6, 9.4), (5.4, .6, 7.6, 9.4)]
    frames.append(status_frame([R.rrect(*b, .6) for b in bars],
                               lambda x, y: any(rect_band(*b, .6, .8)(x, y) for b in bars)))
    ff = [tri([(.4, 1.2), (3.8, 5), (.4, 8.8)]), tri([(4.2, 1.2), (7.6, 5), (4.2, 8.8)])]
    for t in (ff, [[([(8 - x, y) for x, y in p[0][0]], True)] for p in ff]):
        frames.append(status_frame([R.fill_inside(p) for p in t],
                                   lambda x, y, t=t: any(R.stroke_inside(p, .8)(x, y) for p in t)))
    save('status_play.bmp', frames)


def battery_from_sprite():
    """the battery of the status bars from graphics/battery_sprite.bmp (25 states,
    26 x 13 each, made by the UI design): states 1-12 (unknown, 0-100 %)
    -> status_battery.bmp, 13-24 (charging: unknown, 0-100 %) ->
    status_charge.bmp, 25 (charged, plug) -> status_charged.bmp. Three
    files, because %xd(..., %bl) spreads the levels over all frames of an
    image. Skins: %?bp<%?bc<%xd(Charge,%bl)|%xd(Charged)>|%xd(Batt,%bl)>"""
    sprite = R.read_bmp(os.path.join(os.path.dirname(HERE), 'graphics', 'battery_sprite.bmp'))
    assert len(sprite[0]) == 26 and len(sprite) == 25 * 13
    for name, a, b in (('status_battery.bmp', 0, 12), ('status_charge.bmp', 12, 24),
                       ('status_charged.bmp', 24, 25)):
        save(name, [R.canvas_from_rows(sprite[k * 13:(k + 1) * 13]) for k in range(a, b)])


# ---------------------------------------------------------------- quick menu
# ---------------------------------------------------------------- quick menu
# The parts come from the design board "Quick menu" (tools/quickmenu,
# README.md and parts.json: place = top left on the screen). The
# variant "free assignment" is not used.
QS = os.path.join(HERE, 'quickmenu', 'bmp')


def _rows(name):
    """32 bit BMP of the board -> (width, rows of BGRA bytes, top first)"""
    d = open(os.path.join(QS, name + '.bmp'), 'rb').read()
    off = struct.unpack_from('<I', d, 10)[0]
    w, h = struct.unpack_from('<ii', d, 18)
    rows = [d[off + y * w * 4:off + (y + 1) * w * 4] for y in range(abs(h))]
    return w, (rows[::-1] if h > 0 else rows)


def _write(name, w, rows):
    """plain BI_RGB 32 bit BMP, frames stacked top to bottom"""
    data = b''.join(rows[::-1])
    hdr = struct.pack('<2sIHHI', b'BM', 54 + len(data), 0, 0, 54)
    info = struct.pack('<IiiHHIIiiII', 40, w, len(rows), 1, 32, 0, len(data), 2835, 2835, 0, 0)
    open(os.path.join(OUT, name), 'wb').write(hdr + info + data)


def _frames(name, parts):
    w = 0
    rows = []
    for part in parts:
        pw, pr = _rows(part)
        w = w or pw
        assert pw == w, (part, pw, w)
        rows += pr
    _write(name, w, rows)


def _pad_rows(name, part, h, top):
    """the part in a box h px high, from row top (transparent elsewhere)"""
    w, pr = _rows(part)
    empty = bytes(w * 4)
    _write(name, w, [empty] * top + pr + [empty] * (h - top - len(pr)))


# The light surfaces of the board (switches, capsules, back button) are
# gradients in 8 bit. The skin engine rounds every channel of a preloaded
# image (%xl) to RGB565 on its own: red, green and blue then step in
# different rows, and the surface shows tinted bands (pink, green, bluish).
# These parts are therefore written already dithered to RGB565 (4 x 4
# ordered dither, anchored to the screen at the place where the skin draws
# them), with values the skin engine keeps unchanged.
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def _dither_rows(rows, w, x0, y0):
    out = []
    for y, row in enumerate(rows):
        line = bytearray(row)
        for x in range(w):
            if line[x * 4 + 3] == 0:
                continue
            t = (BAYER[(y0 + y) & 3][(x0 + x) & 3] + 0.5) / 16.0
            for c, bits in ((0, 5), (1, 6), (2, 5)):          # B, G, R
                m = (1 << bits) - 1
                n = min(m, int(line[x * 4 + c] * m / 255.0 + t))
                line[x * 4 + c] = (n << (8 - bits)) | (n >> (2 * bits - 8))
        out.append(bytes(line))
    return out


def _frames_dithered(name, parts, x0, y0):
    """like _frames(); every frame is drawn at x0, y0 on the screen (the
    left and right switch lie 152 px apart, a multiple of 4)"""
    w = 0
    rows = []
    for part in parts:
        pw, pr = _rows(part)
        w = w or pw
        assert pw == w, (part, pw, w)
        rows += _dither_rows(pr, w, x0, y0)
    _write(name, w, rows)


# Symbols of the switches by state, as the tiles of the settings show them:
# shuffle off two parallel arrows, on crossed; repeat off one arrow with a
# dashed tail, all (and A-B) the loop, one the loop with a "1" badge at its
# top left corner. The board has only the crossed arrows and the loop; the
# other three are built here from the board's own strokes and arrow heads,
# so stroke width and heads stay those of the board (stroke 2 px plus a
# 27 % edge row, heads 5 x 8 px).
ICON_W, ICON_H = 22, 16
REP_PAD = 2                       # repeat frames: room for the badge left and top
ONE_DIGIT = [(4, 2), (3, 3), (4, 3), (4, 4), (4, 5), (4, 6)]   # "1" cut out of the badge


def _alpha(part):
    w, rows = _rows(part)
    return [[r[x * 4 + 3] for x in range(w)] for r in rows]


def _symbol(alpha, colour):
    """alpha rows -> BGRA rows in one colour"""
    r, g, b = colour
    return [b''.join(bytes((b, g, r, a)) if a else bytes(4) for a in row) for row in alpha]


def _padded(alpha, pad):
    w = len(alpha[0]) + pad
    return [[0] * w for _ in range(pad)] + [[0] * pad + list(row) for row in alpha]


def _bar(alpha, rows, x0, x1, profile):
    """straight stroke over the columns x0..x1; profile: alpha per row, the
    last value goes on to the right"""
    for k, y in enumerate(rows):
        for x in range(x0, x1 + 1):
            p = profile[k]
            alpha[y][x] = max(alpha[y][x], p[min(x - x0, len(p) - 1)])


def _heads(alpha, shuffle, src, dst):
    """the arrow head of the board (columns 17-21, rows src) at row dst"""
    for k, y in enumerate(src):
        for x in range(17, 22):
            alpha[dst + k][x] = max(alpha[dst + k][x], shuffle[y][x])


def shuffle_off_alpha(shuffle):
    """two parallel arrows: the outer strokes of the crossed arrows, straight"""
    a = [[0] * ICON_W for _ in range(ICON_H)]
    _bar(a, (3, 4, 5), 0, 16, [shuffle[y][:5] for y in (3, 4, 5)])
    _bar(a, (10, 11, 12), 0, 16, [shuffle[y][:5] for y in (10, 11, 12)])
    _heads(a, shuffle, range(0, 8), 0)
    _heads(a, shuffle, range(8, 16), 8)
    return a


def repeat_off_alpha(shuffle):
    """one arrow in the middle, its tail three dashes (tile repeatOff)"""
    a = [[0] * ICON_W for _ in range(ICON_H)]
    profile = [[255], [255], [68]]                 # the stroke of the board, rows 3-5
    for x in (0, 2, 4):
        _bar(a, (7, 8, 9), x, x, profile)
    _bar(a, (7, 8, 9), 6, 16, profile)
    _heads(a, shuffle, range(0, 8), 4)
    return a


def repeat_one_alpha(loop):
    """the loop with a badge of 9 px at its top left corner, the "1" cut out
    of it and a gap of 1 px between badge and loop (tile repeatOne)"""
    a = _padded(loop, REP_PAD)
    w, h = len(a[0]), len(a)
    cx = cy = 4.5
    gap = R.coverage(w, h, R.circle(cx, cy, 5.5), 8)
    disc = R.coverage(w, h, R.circle(cx, cy, 4.5), 8)
    for y in range(h):
        for x in range(w):
            v = a[y][x] / 255.0 * (1 - gap[y][x])
            if (x, y) not in ONE_DIGIT:
                v = max(v, disc[y][x])
            a[y][x] = 17 * int(round(v * 15))
    return a


def quickmenu_symbols():
    shuffle = _alpha('icon_shuffle_dark')
    loop = _alpha('icon_repeat_white')
    _, shuffle_on = _rows('icon_shuffle_white')
    _write('qs_shuffle.bmp', ICON_W, _symbol(shuffle_off_alpha(shuffle), DARK) + shuffle_on)
    _write('qs_repeat.bmp', ICON_W + REP_PAD,
           _symbol(_padded(repeat_off_alpha(shuffle), REP_PAD), DARK)
           + _symbol(_padded(loop, REP_PAD), WHITE)
           + _symbol(repeat_one_alpha(loop), WHITE))


def quickmenu_art():
    # light surfaces: dithered at their places on the screen (see BAYER)
    for name, part, x0, y0 in (('qs_capsule_battery.bmp', 'capsule_battery', 14, 14),
                               ('qs_capsule_timer.bmp', 'capsule_timer', 98, 14),
                               ('qs_back.bmp', 'button_back', 282, 14)):
        _frames_dithered(name, [part], x0, y0)
    _frames_dithered('qs_switch.bmp', ['switch_off', 'switch_on'], 13, 148)
    for name, part in (('qs_line.bmp', 'divider'),
                       ('qs_volume.bmp', 'icon_volume'), ('qs_bright.bmp', 'icon_brightness'),
                       ('qs_lock.bmp', 'icon_lock'), ('qs_mini_bat.bmp', 'mini_battery_levels'),
                       ('qs_track.bmp', 'slider_track'), ('qs_moon.bmp', 'icon_moon')):
        _frames(name, [part])
    # sliders like the progress bar of the now playing screen, no knob: a
    # fixed round left end (5 px), the fill behind it and as the slider the
    # round right end of the fill (10 px, straight on its left)
    w, rows = _rows('slider_fill')
    _write('qs_fill_l.bmp', 5, [r[:5 * 4] for r in rows])
    _write('qs_fill_r.bmp', w - 5, [r[5 * 4:] for r in rows])
    _write('qs_cap.bmp', 10, [r[(w - 10) * 4:] for r in rows])
    quickmenu_symbols()
    _frames('qs_arrows.bmp', ['arrow_left_white', 'arrow_left_grey',
                              'arrow_right_white', 'arrow_right_grey'])


# ---------------------------------------------------------------- skin code
B13, B17, B11, DOT, B12, UIF = 2, 3, 4, 9, 10, 1
SWITCH_BG = 'e6e9ee'   # the field under the switches (y 148-216), see backdrop


def quickmenu_fonts():
    return ['%%Fl(%d,16-GlossySlate-Bold12.fnt,160)' % B12]


def quickmenu_logic():
    """the line for %cs = 10 in the screen logic of the sbs. Always the
    layout of the design; its keys work with the assignment of the cfg
    (qs top/bottom brightness, left shuffle, right repeat)."""
    # %mm keeps Rockbox's values: 1 off, 2 all, 3 one, 5 A-B; 4 (repeat
    # shuffled) does not occur in the fork, its case stays empty. "One" has
    # a switch of its own for its symbol (the loop with the "1")
    main = ('%Vd(QsMain)%?ps<%Vd(QsLeftOn)|%Vd(QsLeftOff)>'
            '%?mm<%Vd(QsRightOff)|%Vd(QsRightOn)|%Vd(QsRightOne)||%Vd(QsRightOn)>')
    return ('%%?if(%%cs,=,10)<%%?and(%%mh,%%if(%%St(battery display),=,graphic),%%if(%%cs,!=,21),%%if(%%cs,!=,22))<|'
            '%%VI(Hidden)%%Vd(QsField)%%Vd(QsTop)%%?mh<%%Vd(QsLock)>%s>>' % main)


def quickmenu_images():
    return ['%xl(QsKapB,qs_capsule_battery.bmp,14,14)', '%xl(QsKapT,qs_capsule_timer.bmp,98,14)',
            '%xl(QsMoon,qs_moon.bmp,109,20)',
            '%xl(QsBack,qs_back.bmp,282,14)', '%xl(QsLine,qs_line.bmp,14,58)',
            '%xl(QsVol,qs_volume.bmp,14,75)', '%xl(QsBri,qs_bright.bmp,14,110)',
            '%xl(QsMini,qs_mini_bat.bmp,0,0,12)', '%xl(QsLockI,qs_lock.bmp,0,0)',
            # the tracks lie in the backdrop: fill and knob blend with it there
            '%xl(QsTrk1,qs_track.bmp,40,78)', '%xl(QsTrk2,qs_track.bmp,40,114)',
            '%xl(QsFillL,qs_fill_l.bmp,0,0)', '%xl(QsCap,qs_cap.bmp,0,0)',
            # in the switch viewports (13,148 and 165,148): switch, symbol, arrow
            '%xl(QsSw,qs_switch.bmp,0,0,2)', '%xl(QsShuf,qs_shuffle.bmp,60,6,2)',
            # repeat: 3 frames (off, all, one) with 2 px room for the badge
            '%%xl(QsRep,qs_repeat.bmp,%d,%d,3)' % (60 - REP_PAD, 6 - REP_PAD), '%xl(QsArrL,qs_arrows.bmp,10,29,4)',
            '%xl(QsArrR,qs_arrows.bmp,127,29,4)']


def quickmenu_backdrop():
    """%VB: the field (#F7F8FA -> #EDEFF3 at 55 % -> #DFE3E9, dithered by
    the fork), capsules, back button, rule and slider symbols"""
    return ['%%Vl(QsField,0,0,320,240,%d)%%VB' % DOT,
            '%dr(0,0,320,132,f7f8fa,edeff3)',
            '%dr(0,132,320,108,edeff3,dfe3e9)',
            '%xd(QsKapB)%xd(QsKapT)%xd(QsMoon)%xd(QsBack)%xd(QsLine)%xd(QsVol)%xd(QsBri)%xd(QsTrk1)%xd(QsTrk2)']


def switch_vps(label, x, on, icon, name, value, arrow):
    """the switch with symbol and arrow in the backdrop layer, so that its
    text viewports clear their areas to it. Title 14 px bold 4 px under the
    symbol, value 11 px bold under the title (README.md), 2 px lower than on
    the board: the value line clears its area, and from y 187 on it leaves
    the descenders of the title (g, p, y reach y 186) alone."""
    fg, sub = ('ffffff', 'e4ecf8') if on else ('2e3644', '5b6371')
    frame = (1 if on else 2) + (0 if arrow == 'L' else 2)
    # %Vb: the viewport clears its area to it, the switch shadow blends with it
    return ['%%Vl(%s,%d,148,142,68,%d)%%VB%%Vb(%s)%%xd(QsSw,%d)%s%%xd(QsArr%s,%d)'
            % (label, x - 1, DOT, SWITCH_BG, 2 if on else 1, icon, arrow, frame),
            '%%Vl(%s,%d,167,140,24,%d)%%Vf(%s)' % (label, x, UIF, fg), '%%s%%ac%s' % name,
            '%%Vl(%s,%d,187,140,14,%d)%%Vf(%s)' % (label, x, B11, sub), '%%s%%ac%s' % value]


def quickmenu_viewports():
    L = []
    # top: battery capsule (mini battery, level), sleep timer capsule (moon,
    # the time left or "Off", 6 px after the moon), lock. The level without
    # a space before "%", from x 47: with "100%" the sign then ends 10 px
    # before the capsule's right edge (x 89), as the battery begins 10 px
    # after its left edge (x 14); shorter values stay left-aligned
    L += ['%Vl(QsTop,25,22,18,9,-)', '%xd(QsMini,%bl)',
          '%%Vl(QsTop,47,18,40,16,%d)%%Vf(2e3644)' % B13, '%al%bl%%',
          '%%Vl(QsTop,126,18,42,16,%d)%%Vf(2e3644)' % B13, '%s%al%?bs<%bs|%Sx(Off)>',
          '%Vl(QsLock,178,20,10,12,-)%xd(QsLockI)']
    # volume (wheel) and brightness (MENU brighter, PLAY darker) on the
    # tracks at y 78 and 114 (x 40-250): fixed left end, then fill and cap
    # (as the progress bar of the now playing screen); value 12 px bold right in 46 px
    # from x 260
    L += ['%Vl(QsMain,40,78,5,9,-)%xd(QsFillL)',
          '%Vl(QsMain,45,78,205,9,-)',
          '%pv(0,0,205,9,qs_fill_r.bmp,slider,QsCap)',
          '%%Vl(QsMain,260,74,46,16,%d)%%Vf(2e3644)' % B12, '%ar%pv dB',
          '%Vl(QsMain,40,114,5,9,-)%xd(QsFillL)',
          '%Vl(QsMain,45,114,205,9,-)',
          '%St(0,0,205,9,qs_fill_r.bmp,slider,QsCap,setting,brightness)',
          '%%Vl(QsMain,260,110,46,16,%d)%%Vf(2e3644)' % B12, '%ar%Sx(Level) %St(brightness)']
    # shuffle (LEFT) and repeat (RIGHT)
    # texts from the language (%Sx): titles of their own for the quick menu
    # (the key names the place after '@', the firmware shows the word before
    # it), values as the settings show them
    L += switch_vps('QsLeftOn', 14, True, '%xd(QsShuf,2)', '%Sx(Shuffle@quickmenu)', '%Sx(On)', 'L')
    L += switch_vps('QsLeftOff', 14, False, '%xd(QsShuf,1)', '%Sx(Shuffle@quickmenu)', '%Sx(Off)', 'L')
    rep = '%?mm<%Sx(Off)|%Sx(All)|%Sx(One)||%Sx(A-B)>'     # 4: see quickmenu_logic()
    L += switch_vps('QsRightOn', 166, True, '%xd(QsRep,2)', '%Sx(Repeat@quickmenu)', rep, 'R')
    L += switch_vps('QsRightOne', 166, True, '%xd(QsRep,3)', '%Sx(Repeat@quickmenu)', rep, 'R')
    L += switch_vps('QsRightOff', 166, False, '%xd(QsRep,1)', '%Sx(Repeat@quickmenu)', rep, 'R')
    # never shown: %QT tells Rockbox that the skin draws the quick menu
    L += ['%%Vl(QsNever,0,0,1,1,%d)' % DOT, '%QT']
    return L


def quickmenu_skin():
    return (['#--- quick menu images ---#'] + quickmenu_images(),
            ['#--- quick menu backdrop ---#'] + quickmenu_backdrop(),
            ['#--- quick menu (%cs = 10) ---#'] + quickmenu_viewports())


if __name__ == '__main__':
    status_icons()
    battery_from_sprite()
    quickmenu_art()
    print('art ok:', OUT)
