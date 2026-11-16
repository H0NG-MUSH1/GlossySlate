"""Render previews of the theme in GlossySlate/.rockbox with tools/skinsim.py.

    python3 tools/preview.py                       # English, into GlossySlate/previews
    python3 tools/preview.py --lang deutsch --out /tmp/previews_de

The texts come from the Rockbox language files (apps/lang), the way the
firmware shows them: menu entries by their English name, the theme's own
texts through %Sx, dates through %cD. Needs Pillow and NumPy. The
simulator is not the firmware: check the result on the device.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tools.skinsim import Sim  # noqa: E402
from tools.rblang import Language  # noqa: E402

GS = os.path.dirname(HERE)
RB = os.path.join(GS, '.rockbox')
ASSETS = os.path.join(GS, 'firmware-assets')

# Monday, 9 November 2026, 20:51
TIME = (20, 51, 1, 9, 11, 2026)      # hour, minute, weekday (1 = Monday), day, month, year
WEEKDAY_SUN0 = 1                     # the same weekday, 0 = Sunday
COUNTS = {'albums': 212, 'podcasts': 3, 'audiobooks': 7, 'playlists': 4, 'bookmarks': 2,
          'recordings': 0, 'shortcuts': 1}


def demo_cover(size=232):
    """the fictitious cover of the previews: dusk over the sea, drawn here"""
    y = (np.arange(size) + 0.5)[:, None] / size
    x = (np.arange(size) + 0.5)[None, :] / size
    stops = [(0, (0x14, 0x30, 0x4F)), (.34, (0x3E, 0x3A, 0x68)), (.52, (0xB8, 0x5A, 0x7C)), (.62, (0xF2, 0xA6, 0x5A))]
    img = np.zeros((size, size, 3))
    for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
        t = np.clip((y - p0) / (p1 - p0), 0, 1)
        m = (y >= p0) & (y <= p1)
        img = np.where(m[..., None], np.array(c0) * (1 - t[..., None]) + np.array(c1) * t[..., None], img)
    img = np.where((y > .62)[..., None], img * 0 + np.array((0xF2, 0xA6, 0x5A)), img)
    # sun
    d = np.hypot(x - .5, y - .62)
    sun = np.array((0xFF, 0xF3, 0xDC)) * (1 - (y - .49) / .26)[..., None] + np.array((0xFF, 0xC9, 0x8B)) * ((y - .49) / .26)[..., None]
    img = np.where((d < .13)[..., None], sun, img)
    # sea with light stripes and the sun's glitter
    t = np.clip((y - .62) / .38, 0, 1)
    sea = np.array((0x2B, 0x3D, 0x63)) * (1 - t[..., None]) + np.array((0x0D, 0x1A, 0x2E)) * t[..., None]
    stripe = ((np.arange(size)[:, None] % 8) >= 6) * .14
    glow = np.clip(1 - abs(x - .5) / .14, 0, 1) * .38
    sea = sea * (1 - stripe[..., None]) + np.array((0xFF, 0xD6, 0xAA)) * stripe[..., None]
    sea = sea * (1 - glow[..., None]) + np.array((0xFF, 0xC9, 0x8B)) * glow[..., None]
    img = np.where((y > .62)[..., None], sea, img)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')


def items(names, sel, arrows=True):
    """Menu entries; an entry is a name or (name, value). Entries with a
    value switch directly (no arrow), the others open a level."""
    out = []
    for n in names:
        name, val = (n, '') if isinstance(n, str) else n
        out.append((name, name == sel, {'value': val, 'arrow': arrows and not val}))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--lang', default='english', help='name of a file in apps/lang, without .lang')
    ap.add_argument('--out', default=None, help='output folder (default GlossySlate/previews)')
    args = ap.parse_args()
    out_dir = args.out or os.path.join(GS, 'previews')
    os.makedirs(out_dir, exist_ok=True)

    lang = Language(args.lang)
    sx = lang.lookup()
    missing = set()

    def tr(english):
        """a text of the firmware in the preview language"""
        if english not in sx:
            missing.add(english)
        return sx.get(english, english)

    date = lang.date(WEEKDAY_SUN0, TIME[3], TIME[4], TIME[5])
    base = {'time': TIME, 'date': date, 'counts': COUNTS,
            'settings': {'volume display': 'graphic', 'statusbar': 'off', 'scrollbar': 'right',
                         'battery display': 'numeric', 'brightness': '9'},
            'setting_values': {'statusbar': tr('Album and Artist'), 'scrollbar': tr('Right'),
                               'backlight timeout': '15s'},
            'bl': 82, 'mp': 2, 'mm': 0, 'ps': True, 'C': True,
            'text': {'it': 'Glass Harbour', 'ia': 'The Quiet Arcades', 'id': 'Tidelines', 'fn': 'glass_harbour',
                     'pp': '3', 'pe': '12', 'pc': '1:07', 'pr': '2:18', 'fc': 'FLAC', 'fk': '44.1', 'pv': '-24'}}

    def st(**kw):
        s = json.loads(json.dumps(base))
        s['time'] = TIME
        for k, v in kw.items():
            if k == 'settings':
                s['settings'].update(v)
            else:
                s[k] = v
        return s

    art = demo_cover()
    font = '24-GlossySlate-Bold14.fnt'
    sbs = Sim(os.path.join(RB, 'wps', 'glossyslate.sbs'), os.path.join(RB, 'wps', 'glossyslate'),
              os.path.join(RB, 'fonts'), font, sx)
    wps = Sim(os.path.join(RB, 'wps', 'glossyslate.wps'), os.path.join(RB, 'wps', 'glossyslate'),
              os.path.join(RB, 'fonts'), font, sx)
    shots = []

    def shot(name, sim, state, entries=None):
        shots.append((name, sim.render(state, entries, art)))

    # ---- main menu
    root_play = [tr(n) for n in ('Now Playing', 'Music', 'Playlists', 'Podcasts', 'Audiobooks',
                                 'Recent Bookmarks', 'Settings', 'System')]
    root_stop = [tr('Resume Playback')] + root_play[1:]
    title = tr('iPod')
    now, music, books, settings = tr('Now Playing'), tr('Music'), tr('Audiobooks'), tr('Settings')
    shot('main_menu_now_playing', sbs, st(cs=1, Lt=title, LT=now), items(root_play, now))
    shot('main_menu_now_playing_square', sbs, st(cs=1, Lt=title, LT=now, settings={'volume display': 'numeric'}), items(root_play, now))
    shot('main_menu_default_cover', sbs, st(cs=1, Lt=title, LT=now, C=False), items(root_play, now))
    shot('main_menu_music', sbs, st(cs=1, mp=1, Lt=title, LT=music), items(root_stop, music))
    shot('main_menu_audiobooks', sbs, st(cs=1, mp=1, Lt=title, LT=books), items(root_stop, books))
    shot('main_menu_settings', sbs, st(cs=1, mp=1, Lt=title, LT=settings), items(root_stop, settings))
    shot('main_menu_nothing_playing', sbs, st(cs=1, mp=1, Lt=title, LT=root_stop[0]), items(root_stop, root_stop[0]))

    # ---- settings
    setmenu = [tr(n) for n in ('Playback Settings', 'Sound Settings', 'General Settings', 'Theme Settings',
                               'Voice', 'Time & Date')]
    theme_s, playback, date_s = tr('Theme Settings'), tr('Playback Settings'), tr('Time & Date')
    shot('settings', sbs, st(cs=6, Lt=settings, LT=theme_s), items(setmenu, theme_s))
    shot('settings_date', sbs, st(cs=6, Lt=settings, LT=date_s), items(setmenu, date_s))
    shuffle, repeat = tr('Shuffle'), tr('Repeat')
    play = [(shuffle, tr('On')), (repeat, tr('All')), tr('Crossfade'), tr('Replaygain'),
            (tr('Fade on Stop/Pause'), tr('Yes')), tr('Skip Length')]
    shot('settings_repeat', sbs, st(cs=6, Lt=playback, LT=repeat, LV=tr('All'), mm=1), items(play, repeat))
    shot('settings_shuffle', sbs, st(cs=6, Lt=playback, LT=shuffle, LV=tr('On')), items(play, shuffle))
    corners, second, keylock = tr('Album Art Corners'), tr('Second Line in Player'), tr('Key Lock')
    theme = [tr('Browse Theme Files'), corners, (second, tr('Album and Artist')), (tr('Scroll Bar'), tr('Right')),
             keylock, tr('Colours')]
    shot('settings_second_line', sbs, st(cs=6, Lt=theme_s, LT=second, LV=tr('Album and Artist')), items(theme, second))
    shot('settings_corners_rounded', sbs, st(cs=6, Lt=theme_s, LT=corners), items(theme, corners))
    shot('settings_corners_square', sbs, st(cs=6, Lt=theme_s, LT=corners, settings={'volume display': 'numeric'}), items(theme, corners))
    rounded, square = tr('Rounded'), tr('Square')
    shot('option_corners_rounded', sbs, st(cs=12, Lt=corners, LT=rounded), items([rounded, square], rounded, False))
    shot('option_corners_square', sbs, st(cs=12, Lt=corners, LT=square), items([rounded, square], square, False))
    shot('settings_key_lock_normal', sbs, st(cs=6, Lt=theme_s, LT=keylock), items(theme, keylock))
    shot('settings_key_lock_screen', sbs, st(cs=6, Lt=theme_s, LT=keylock, settings={'battery display': 'graphic'}), items(theme, keylock))
    lockscr, normal = tr('Lock Screen'), tr('Normal')
    shot('option_key_lock_screen', sbs, st(cs=12, Lt=keylock, LT=lockscr), items([lockscr, normal], lockscr, False))
    shot('option_key_lock_normal', sbs, st(cs=12, Lt=keylock, LT=normal), items([lockscr, normal], normal, False))

    # ---- system (%cs 16): logo tile, name and theme version
    sysmenu = [tr(n) for n in ('Rockbox Info', 'Credits', 'Running Time', 'Legal Notices', 'Debug (Keep Out!)')]
    shot('system', sbs, st(cs=16, Lt=tr('System'), LT=sysmenu[0]), items(sysmenu, sysmenu[0]))
    shot('main_menu_system', sbs, st(cs=1, mp=1, Lt=title, LT=tr('System')), items(root_stop, tr('System')))

    # ---- database (tagnavi.config; the firmware translates the names)
    db = [tr(n) for n in ('Album Artist', 'Artist', 'Album', 'Podcasts', 'Audiobooks', 'Genre', 'Year',
                          'Composer', 'First Letter')]
    shot('database', sbs, st(cs=8, Lt=tr('Database'), scrollknob=(3, 160)), items(db, tr('Album')))
    # album list as the fork draws it: 52 px covers, gloss bar, arrows
    special = Image.open(os.path.join(ASSETS, 'albumart_list_random_512.png')).convert('RGBA')
    dflt = Image.open(os.path.join(ASSETS, 'albumart_list_default_512.png')).convert('RGBA')
    alb = [('[%s]' % tr('Shuffle'), False, {'cover': special, 'cover_w': 52, 'arrow': True}),
           ('Tidelines', True, {'cover': art, 'cover_w': 52, 'sub': 'The Quiet Arcades', 'arrow': True}),
           ('Field Recordings', False, {'cover': dflt, 'cover_w': 52, 'sub': 'Juniper Vale', 'arrow': True}),
           ('Low Tide Hymns', False, {'cover': art.transpose(Image.FLIP_LEFT_RIGHT), 'cover_w': 52,
                                      'sub': 'The Quiet Arcades', 'arrow': True})]
    shot('album_list', sbs, st(cs=8, Lt=tr('Album'), row_h=52), alb)

    # ---- USB: playback stopped (mp 1), black status bar
    shot('usb_connected', sbs, st(cs=21, Lt='', mp=1, lh=True, bp=True, bc=True))
    # ejected by the computer (fork: ACTIVITY_USBEJECTED = 22), still charging
    shot('usb_ejected', sbs, st(cs=22, Lt='', mp=1, bp=True, bc=True))
    # hold switch on: white lock on the black bar
    shot('usb_locked', sbs, st(cs=21, Lt='', mp=1, mh=True, bp=True, bc=True))

    # ---- lock screen and quick menu
    lock = {'battery display': 'graphic'}
    shot('lock_screen', sbs, st(cs=1, mh=True, settings=lock, Lt=title, LT=music), items(root_play, music))
    shot('lock_screen_database', sbs, st(cs=8, mh=True, settings=lock, Lt=tr('Database')), items(db, tr('Album')))
    shot('quick_menu', sbs, st(cs=10, Lt='', volume=.62))

    # ---- now playing
    shot('now_playing', wps, st(cs=2, progress=.33))
    shot('now_playing_square', wps, st(cs=2, progress=.33, settings={'volume display': 'numeric'}))
    shot('now_playing_default_cover', wps, st(cs=2, progress=.33, C=False))
    shot('now_playing_default_cover_square', wps, st(cs=2, progress=.33, C=False, settings={'volume display': 'numeric'}))
    shot('now_playing_volume', wps, st(cs=2, mv=True, volume=.62))
    shot('now_playing_locked', wps, st(cs=2, mh=True, ps=False, mm=2))
    shot('now_playing_lock_screen', wps, st(cs=2, mh=True, settings=lock))

    for n, im in shots:
        im.save(os.path.join(out_dir, n + '.png'))
    cols = 4
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * 330, rows * 250), (90, 96, 106))
    for i, (n, im) in enumerate(shots):
        sheet.paste(im, ((i % cols) * 330, (i // cols) * 250))
    sheet.save(os.path.join(out_dir, '_overview.png'))
    print('previews:', len(shots), '->', out_dir)
    if missing:
        print('not in english.lang (shown as given):', ', '.join(sorted(missing)))


if __name__ == '__main__':
    main()
