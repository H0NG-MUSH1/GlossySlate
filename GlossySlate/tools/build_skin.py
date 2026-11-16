"""Generate glossyslate.sbs, glossyslate.wps and glossyslate.cfg.

Layering rules that keep Rockbox from wiping graphics (see DESIGN.md):
  * every fill and bitmap that text sits on lives in a %VB (backdrop)
    viewport; text lines restore the backdrop under themselves
  * all screen logic runs in a 1 x 1 px viewport with the 1 px font, so a
    redrawn logic line clears a single pixel only
  * conditionally shown backdrop viewports cover the same rectangle as the
    viewport they replace, so a hidden one is always painted over again
"""
import os, json

import design as D
import build_quickmenu as QM  # status icons and quick menu (pure Python)

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, 'out', 'GlossySlate', '.rockbox')
FM = json.load(open(os.path.join(HERE, 'cache', 'fontmap.json')))['tiles']
BANDS = json.load(open(os.path.join(HERE, 'cache', 'field_bands.json')))
MAN = json.load(open(os.path.join(HERE, 'cache', 'manifest.json')))
FX = MAN['cover_fx']
VERSION = '1.0'

from build_tile_glyphs import TILE_GLYPHS  # glyphs delivered as pictures

# tile glyph for symbol name n (build_tile_glyphs.py puts the delivered ones
# into the font after build_fonts.py)
G = lambda n: chr(TILE_GLYPHS[n] if n in TILE_GLYPHS else FM[n])

FONTS_SBS = [
    (2, '16-GlossySlate-Bold13.fnt', 160),
    (3, '20-GlossySlate-Bold17.fnt', 160),
    (4, '14-GlossySlate-Bold11.fnt', 160),
    (5, '70-GlossySlate-Clock58.fnt', 12),
    (6, '46-GlossySlate-Day46.fnt', 11),
    (7, '113-GlossySlate-Tiles.fnt', 2),
    (8, '84-GlossySlate-Hands.fnt', 2),
    (9, '1-GlossySlate-Dot.fnt', 1),
    (10, '16-GlossySlate-Bold12.fnt', 160),   # quick menu: slider values
]
FONTS_WPS = [
    (2, '16-GlossySlate-Bold13.fnt', 160),
    (3, '20-GlossySlate-Bold17.fnt', 160),
    (4, '14-GlossySlate-Bold11.fnt', 160),
    (5, '70-GlossySlate-Clock58.fnt', 12),
    (9, '1-GlossySlate-Dot.fnt', 1),
    (10, '16-GlossySlate-Bold12.fnt', 60),
    (11, '16-GlossySlate-Regular13.fnt', 160),
]
B13, B17, B11, CLOCK, DAY, TILES, HANDS, DOT, B12, R13 = 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
UI = 1                              # cfg font: 24-GlossySlate-Bold14.fnt
# gloss bar of the fork: start/end/text from %Vg, the 45 %/55 %/edge colours from the cfg
SEL = '%?Lc<%Vs(gloss)%Vg(5896e6,1a55be,ffffff)|%Vs(clear)>'
ART_ROUND = 'if(%St(volume display),=,graphic)'      # album art corners: rounded
LOCK_SCREEN = 'if(%St(battery display),=,graphic)'   # key lock: lock screen
LOCK_NAMES = ['%Sx(Key Lock)', '%Sx(Battery Display)']
USB_SCREENS = '%if(%cs,=,21),%if(%cs,=,22)'          # USB connected / ejected by the computer (fork: ACTIVITY_USBEJECTED)
OPT_NORMAL = 'or(%if(%LT,=,%Sx(Normal)),%if(%LT,=,%Sx(Numeric)))'   # option page: "Normal" highlighted

# Dates come from the fork's %cD tag in the words and order of the language
# (LANG_DATE_FORMAT_LONG/SHORT, full weekday and month names): "long" =
# weekday, day and month; "short" = day, short month and year; "weekday";
# "month" = short month in capitals for the calendar card.
DATE_LONG, DATE_SHORT, DATE_WEEKDAY, DATE_MONTH = '%cD(long)', '%cD(short)', '%cD(weekday)', '%cD(month)'
SECOND_LINE = ('%s%ac%?it<%?if(%St(statusbar),=,off)<%t(5)%ia;%t(5)%id>'
               '%?if(%St(statusbar),=,top)<%id>%?if(%St(statusbar),=,bottom)<%ia>|%d(1)>')


def hdr(kind):
    return ['#  Glossy Slate %s for Rockbox – iPod Classic 6G/7G (fork, 320 x 240)' % VERSION,
            '#  %s. Built from the Glossy Slate design canvas.' % kind,
            '#  Layering notes: see DESIGN.md, section "Skin technique".', '#']


def fonts(lst):
    return ['%%Fl(%d,%s,%d)' % f for f in lst]


def ifchain(pairs, default):
    """%?if(a,=,b)<x|%?if(...)<y|default>> from [(cond, out), ...]."""
    out = default
    for cond, val in reversed(pairs):
        out = '%%?%s<%s|%s>' % (cond, val, out)
    return out


def select(rows, tag, default):
    """Flat lookup instead of a deep if/else chain (keeps parser and render
    recursion shallow on the device): one single-option conditional per row,
    plus one %and() for the default."""
    out = ''
    for texts, val in rows:
        if val:
            out += '%%?%s<%s>' % (any_of(tag, texts), val)
    if default:
        neg = ['%%if(%s,!=,%s)' % (tag, t) for texts, _ in rows for t in texts]
        out += '%%?and(%s)<%s>' % (','.join(neg), default)
    return out


def eq(tag, text):
    return 'if(%s,=,%s)' % (tag, text)


def sx(s):
    return '%%Sx(%s)' % s


def any_of(tag, texts):
    conds = [eq(tag, t) for t in texts]
    return conds[0] if len(conds) == 1 else 'or(%s)' % ','.join('%' + c for c in conds)


# ---------------------------------------------------------------- status bar
# status bar (design 1.4): 21 px white -> grey, then a 1 px dark line
STATUS_DR = ['%%dr(0,0,%d,21,ffffff,979797)', '%%dr(0,21,%d,1,1e1e1e)']
# USB mode: black bar like RetailOS (values from the template)
STATUS_DR_DARK = ['%%%%dr(0,0,%%d,21,%s,%s)' % (D.STATUS_DARK[0][1:].lower(), D.STATUS_DARK[1][1:].lower()),
                  '%%%%dr(0,21,%%d,1,%s)' % D.STATUS_DARK_LINE[1:].lower()]


def statusbar_bg(label, w, dark=False):
    return ['%%Vl(%s,0,0,%d,22,%d)%%VB' % (label, w, DOT)] + [d % w for d in (STATUS_DR_DARK if dark else STATUS_DR)]


def status_icons(w, white=False, show_play=True, dark=False):
    """Labelled icon viewports for a status bar of width w. Order from the
    right edge: battery, play/pause, lock, spinner (design rule).
    dark: for the black USB bar (suffix K): white lock, light spinner, no
    battery of its own (the USB screens use BatUsb, the theme's battery)."""
    s = str(w) + ('W' if white else '') + ('K' if dark else '')
    L = []
    if not dark:
        L += ['%%Vl(Bat%s,%d,4,26,13,-)' % (s, w - 32),
              '%?bp<%?bc<%xd(Charge,%bl)|%xd(Charged)>|%xd(Batt,%bl)>']
    if show_play:
        L += ['%%Vl(Ply%s,%d,5,8,10,-)' % (s, w - 44),
              # stop, play, pause, fast forward, rewind, then recording and radio
              '%?mp<|%xd(Play,1)|%xd(Play,2)|%xd(Play,3)|%xd(Play,4)|%xd(Play,1)|%xd(Play,2)|%xd(Play,1)|%xd(Play,2)>']
    lock = 'LockW' if (white or dark) else 'Lock'
    L += ['%%Vl(LkA%s,%d,4,10,12,-)%%xd(%s)' % (s, w - 58, lock),
          '%%Vl(LkB%s,%d,4,10,12,-)%%xd(%s)' % (s, w - 46, lock)]
    spin = 'SpinK' if dark else 'Spin'
    anim = ';'.join('%%t(0.1)%%xd(%s,%d)' % (spin, i) for i in range(1, 13))
    for k, x in (('A', w - 76), ('B', w - 62), ('C', w - 64), ('D', w - 50)):
        L += ['%%Vl(Sp%s%s,%d,4,14,14,-)' % (k, s, x), anim]
    return L


def status_logic(w, white=False, show_play=True, dark=False):
    s = str(w) + ('W' if white else '') + ('K' if dark else '')
    play = '%%Vd(Ply%s)' % s if show_play else ''
    out = '%%Vd(%s)%s' % ('BatUsb' if dark else 'Bat' + s, play)
    out += '%%?mh<%%?mp<%%Vd(LkB%s)|%%Vd(LkA%s)>>' % (s, s)
    out += ('%%?lh<%%?mp<%%?mh<%%Vd(SpC%s)|%%Vd(SpD%s)>|%%?mh<%%Vd(SpA%s)|%%Vd(SpB%s)>>>'
            % (s, s, s, s))
    return out


def title_vp(label, w, text):
    # 13 px bold, CSS top 0 / line-height 21 -> baseline at y 15; the 16 px
    # font has its baseline at row 12, so the viewport starts at y 3
    return ['%%Vl(%s,8,3,%d,16,%d)%%Vf(14171c)' % (label, w, B13), '%s%al' + text]


# ---------------------------------------------------------------- shared art
def field_bg(label):
    L = ['%%Vl(%s,0,0,320,240,%d)%%VB' % (label, DOT)]
    for y, h, c0, c1 in BANDS:
        L.append('%%dr(0,%d,320,%d,%s,%s)' % (y, h, c0, c1))
    return L


def lock_screen(prefix):
    """Lock screen (key lock mode "Lock Screen")."""
    # the clock box is drawn into the field: as its own %VB viewport its
    # clear covered the blue field and the rounded corners turned white
    L = field_bg(prefix + 'Field') + ['%xd(LockBox)']
    L += ['%%Vl(%sTop,10,6,10,12,-)%%xd(LockW)' % prefix]
    L += ['%%Vl(%sTop,288,4,26,13,-)' % prefix,
          '%?bp<%?bc<%xd(Charge,%bl)|%xd(Charged)>|%xd(Batt,%bl)>']
    L += ['%%Vl(%sTop,10,23,300,20,%d)%%Vf(ffffff)' % (prefix, B17),
          '%ac' + DATE_LONG]
    L += ['%%Vl(%sTop,60,72,200,70,%d)%%Vf(dfe6f3)' % (prefix, CLOCK),
          '%ac%?cf<%cH:%cM|%cl:%cM>']
    L += ['%%Vl(%sTrack,10,190,300,16,%d)%%Vf(ffffff)' % (prefix, B13),
          '%s%ac%?mp<|► |||>%?it<%it|%fn>',
          '%%Vl(%sTrack,10,208,300,14,%d)%%Vf(dce6f2)' % (prefix, B11),
          SECOND_LINE]
    return L


def lock_logic(prefix):
    return ('%%Vd(%sField)%%Vd(%sTop)%%?mp<|%%Vd(%sTrack)>'
            % (prefix, prefix, prefix))


# ---------------------------------------------------------------- tile maps
def counted(what, none, one, many):
    """Value under the tile from the fork's %Mc(albums|podcasts|...):
    "No ...", "1 ...", "<n> ...", each text from the language (%Sx)."""
    return ('%%?if(%%Mc(%s),=,0)<%s|%%?if(%%Mc(%s),=,1)<%s|%%Mc(%s) %s>>'
            % (what, sx(none), what, sx(one), what, sx(many)))


MAIN_TILES = [
    ([sx('Files')], None, ''),
    # the album count is empty while the database is still loading;
    # None: no tile glyph, the symbol stands without tile (SIDE_PUR)
    # "Music" in the fork's main menu (LANG_FILTER_MUSIC)
    ([sx('Music')], None,
     '%?Mc(albums)<' + counted('albums', 'No music', '1 album', 'albums') + '>'),
    ([sx('Settings')], None, ''),
    # recordings in the recording directory, entries of "Shortcuts":
    # counted by the fork, %Mc(recordings|shortcuts)
    ([sx('Recording')], None,
     '%?Mc(recordings)<' + counted('recordings', 'No recordings', '1 recording', 'recordings') + '>'),
    ([sx('FM Radio')], 'radio', ''),
    # playlists of the playlist directory, bookmarks of "Recent Bookmarks"
    # (shown as "Bookmarks"): counted by the fork, %Mc(playlists|bookmarks)
    ([sx('Playlists')], None,
     '%?Mc(playlists)<' + counted('playlists', 'No playlists', '1 playlist', 'playlists') + '>'),
    ([sx('Plugins')], None, ''),
    # no value: the theme version stands in the sub menu System (TileSys)
    ([sx('System')], None, ''),
    ([sx('Shortcuts')], None,
     '%?Mc(shortcuts)<' + counted('shortcuts', 'No shortcuts', '1 shortcut', 'shortcuts') + '>'),
    ([sx('Recent Bookmarks')], None,
     '%?Mc(bookmarks)<' + counted('bookmarks', 'No bookmarks', '1 bookmark', 'bookmarks') + '>'),
    # podcasts and audiobooks: albums of their media type in the database,
    # empty like the album count while it is not ready
    ([sx('Podcasts')], None,
     '%?Mc(podcasts)<' + counted('podcasts', 'No podcasts', '1 podcast', 'podcasts') + '>'),
    ([sx('Audiobooks')], None,
     '%?Mc(audiobooks)<' + counted('audiobooks', 'No audiobooks', '1 audiobook', 'audiobooks') + '>'),
    # the tile appears only without playback, otherwise the mini player
    ([sx('Now Playing'), sx('Resume Playback')], None, sx('Nothing playing')),
]

# Symbols without tile (DESIGN 5.11): side_symbols.bmp from build_side_symbols.py,
# frames 1 podcasts, 2 music, 3 audiobooks, 4 playlists, 5 settings,
# 6 bookmarks, 7 system, 8 recording, 9 files, 10 plugins, 11 shortcuts.
# Each is a backdrop variant of the sidebar like SideArtR/SideArtS.
SIDE_PUR = [
    ('SidePod', 1, [sx('Podcasts')]),
    ('SideBook', 3, [sx('Audiobooks')]),
    ('SideNote', 2, [sx('Music'), sx('Now Playing'), sx('Resume Playback')]),
    ('SidePlay', 4, [sx('Playlists')]),
    ('SideSet', 5, [sx('Settings')]),
    ('SideInfo', 7, [sx('System')]),
    ('SideBkm', 6, [sx('Recent Bookmarks')]),
    ('SideRec', 8, [sx('Recording')]),
    ('SideFiles', 9, [sx('Files')]),
    ('SidePlug', 10, [sx('Plugins')]),
    ('SideShort', 11, [sx('Shortcuts')]),
]


def main_sidebar():
    """%Vd of the sidebar backdrop for the highlighted main menu entry"""
    # flat (select) instead of an if/else chain 11 levels deep
    return select([(texts, '%%Vd(%s)' % label) for label, _, texts in SIDE_PUR],
                  '%LT', '%Vd(SideTile)')

# Sub menu title (%Lt) -> tile: the default of the menus before the gear,
# so that entries whose text changes with their state (hotkeys, sleep
# timer) or contains brackets show the tile of their sub menu as well.
SUBMENU_TILES = [
    ('Crossfeed', 'headphones'),
    ('Equalizer', 'eq'),
    ('Haas Stereo Widening', 'stereo_wide'),
    ('Dynamic Range Compressor', 'compressor'),
    ('Fast-Forward/Rewind', 'seek'),
    ('Crossfade', 'crossfade'),
    ('Replaygain', 'soundcheck'),
    ('Pause on Headphone Unplug', 'unplug'),
    ("What's Playing Screen", 'now_playing'),
    ('Playlists', 'playlist'),
    ('Playlist Viewer Settings', 'playlist'),
    ('Current Playlist', 'playlist'),
    ('File View', 'folder'),
    ('Database', 'database'),
    ('LCD Settings', 'timer'),
    ('Backlight Exemptions', 'timer'),
    ('Display', 'sun'),
    ('Scrolling', 'sun'),
    ('Peak Meter', 'meter'),
    ('System', 'ipod'),
    ('Battery', 'ipod'),
    ('Disk', 'ipod'),
    ('Limits', 'ipod'),
    ('Car Adapter Mode', 'ipod'),
    ('Keyclick', 'ipod'),
    ('USB', 'ipod'),
    ('Startup/Shutdown', 'power'),
    ('Bookmarking', 'bookmark'),
    ('Automatic Resume', 'resume'),
    ('Voice', 'voice'),
    ('Status-/Scrollbar', 'scroll_right'),
    ('Colours', 'palette'),
    ('Line Selector Colours', 'palette'),
    ('File Split Options', 'scissors'),
]


def setting_tiles(tag, opt=False):
    """Symbol and value for a settings entry named by tag (%LT in menus,
    %Lt on option screens). On option screens the highlighted option (%LT)
    picks the variant."""
    if opt:
        shuffle = '%%?%s<%s|%s>' % (any_of('%LT', [sx('On'), sx('Yes')]), G('shuffle'), G('shuffleOff'))
        repeat = ifchain([(eq('%LT', sx('Off')), G('repeatOff')), (eq('%LT', sx('One')), G('repeatOne'))], G('repeat'))
        scroll = ifchain([(eq('%LT', sx('Off')), G('scroll_off')), (eq('%LT', sx('Left')), G('scroll_left'))], G('scroll_right'))
    else:
        shuffle = '%%?ps<%s|%s>' % (G('shuffle'), G('shuffleOff'))
        # %mm keeps Rockbox's values (1 off, 2 all, 3 one, 5 A-B); 4, repeat
        # shuffled, does not occur in the fork: its case stays empty
        repeat = '%%?mm<%s|%s|%s||%s>' % (G('repeatOff'), G('repeat'), G('repeatOne'), G('repeat'))
        scroll = ifchain([(eq('%St(scrollbar)', 'off'), G('scroll_off')), (eq('%St(scrollbar)', 'left'), G('scroll_left'))], G('scroll_right'))
    v_shuffle = '%%?ps<%s|%s>' % (sx('Random order'), sx('In order'))
    v_repeat = '%%?mm<%s>' % '|'.join(sx(t) if t else '' for t in ('Play once', 'Repeat list', 'Repeat track',
                                                                    '', 'Repeat A-B'))
    rows = [
        ([sx('Playback Settings')], G('play'), ''),
        ([sx('Sound Settings')], G('speaker'), ''),
        ([sx('General Settings')], G('sliders'), ''),
        ([sx('Theme Settings')], G('brush'), ''),
        ([sx('Recording Settings')], G('mic'), ''),
        ([sx('Voice')], G('voice'), ''),
        ([sx('Database')], G('database'), ''),
        ([sx('Bookmarking')], G('bookmark'), ''),
        ([sx('Reset Settings'), sx('Manage Settings')], G('reset'), ''),
        ([sx('Shuffle')], shuffle, v_shuffle),
        ([sx('Repeat')], repeat, v_repeat),
        ([sx('Volume')], G('speaker'), '%pv dB'),
        ([sx('Brightness')], G('sun'), sx('Level') + ' %St(brightness)'),
        # the backlight timeout as its option list shows it (fork: %Sv)
        ([sx('Backlight')], G('timer'), '%Sv(backlight timeout)'),
        ([sx('Equalizer')], G('eq'), ''),
        ([sx('Second Line in Player'), sx('Status Bar')], G('secondline'), '%Sv(statusbar)'),
        ([sx('Scroll Bar')], scroll, '%Sv(scrollbar)'),
        ([sx('Album Art')], G('art_round'), ''),
        ([sx('Display'), sx('LCD Settings')], G('sun'), ''),
        # RetailOS tiles of the settings without a tile of their own
        # (SETTINGS-WITHOUT-TILE.md, T001-T224; one motif for related settings,
        # sub menus show the tile of the entry that opens them). '%LV': the
        # value as the firmware list shows it, empty for entries that open
        # a level. Not possible as %Sx: "Backlight (While Plugged In)" and
        # "Sleep (After Backlight Off)" (brackets); entries whose text changes
        # with their state (context items, hotkeys, start/cancel sleep timer)
        # have no fixed text. They get their tile through SUBMENU_TILES.
        ([sx('Volume Limit')], G('volume_limit'), '%LV'),
        ([sx('Bass'), sx('Bass Cutoff'), sx('Perceptual Bass Enhancement')], G('bass'), '%LV'),
        ([sx('Treble'), sx('Treble Cutoff'), sx('Presence/Treble Attenuation')], G('treble'), '%LV'),
        ([sx('Balance')], G('balance'), '%LV'),
        ([sx('Channel Configuration'), sx('Channels'), sx('Mono mode')], G('stereo'), '%LV'),
        ([sx('Stereo Width'), sx('Haas Stereo Widening'), sx('Upper Bypass Frequency'), sx('Lower Bypass Frequency'), sx('Process Side Channel Only'), sx('Dry/Wet Mix')], G('stereo_wide'), '%LV'),
        ([sx('Crossfeed'), sx('Direct Gain'), sx('Cross Gain'), sx('High-Frequency Attenuation'), sx('High-Frequency Cutoff')], G('headphones'), '%LV'),
        ([sx('Dithering')], G('dither'), '%LV'),
        ([sx('Timestretch')], G('metronome'), '%LV'),
        ([sx('Dynamic Range Compressor'), sx('Threshold'), sx('Makeup Gain'), sx('Compression Ratio'), sx('Knee'), sx('Attack Time'), sx('Release Time')], G('compressor'), '%LV'),
        ([sx('Enable EQ'), sx('Graphical EQ'), sx('Precut'), sx('Simple EQ Settings'), sx('Advanced EQ Settings'), sx('Save EQ Preset'), sx('Browse EQ Presets'), sx('Reset EQ')], G('eq'), '%LV'),
        ([sx('Play Selected First')], G('shuffle'), '%LV'),
        ([sx('Fast-Forward/Rewind'), sx('FF/RW Min Step'), sx('FF/RW Accel')], G('seek'), '%LV'),
        ([sx('Anti-Skip Buffer')], G('buffer'), '%LV'),
        ([sx('Fade on Stop/Pause')], G('fade'), '%LV'),
        ([sx('Single Mode')], G('single'), '%LV'),
        ([sx('Party Mode')], G('party'), '%LV'),
        ([sx('Crossfade'), sx('Enable Crossfade'), sx('Fade-In Delay'), sx('Fade-In Duration'), sx('Fade-Out Delay'), sx('Fade-Out Duration'), sx('Fade-Out Mode')], G('crossfade'), '%LV'),
        ([sx('Replaygain'), sx('Replaygain Type'), sx('Prevent Clipping')], G('soundcheck'), '%LV'),
        ([sx('Track Skip Beep')], G('beep'), '%LV'),
        ([sx('Auto-Change Directory'), sx('Constrain Auto-Change')], G('next_folder'), '%LV'),
        ([sx('Cuesheet Support')], G('cd'), '%LV'),
        ([sx('Pause on Headphone Unplug'), sx('Disable resume on startup if phones unplugged')], G('unplug'), '%LV'),
        ([sx('Headset Remote Control')], G('remote'), '%LV'),
        ([sx('Skip Length'), sx('Prevent Track Skipping')], G('skip'), '%LV'),
        ([sx('Rewind Across Tracks'), sx('Rewind Before Resume'), sx('Rewind on Pause')], G('rewind'), '%LV'),
        ([sx('Frequency')], G('tuning_fork'), '%LV'),
        ([sx('Logging')], G('log'), '%LV'),
        ([sx("What's Playing Screen"), sx('WPS Hotkey'), sx('While Playing Screen')], G('now_playing'), '%LV'),
        ([sx('Playlists'), sx('Sort Playlists'), sx('Playlist Viewer Settings'), sx('Recursively Insert Directories'), sx('Current Playlist'), sx('Show Icons'), sx('Show Indices'), sx('Track Display'), sx('Warn When Erasing Dynamic Playlist'), sx('Keep Current Track When Replacing Playlist'), sx('Show Shuffled Adding Options'), sx('Show Queue Options')], G('playlist'), '%LV'),
        ([sx('File View'), sx('Sort Case Sensitive'), sx('Sort Directories'), sx('Sort Files'), sx('Interpret numbers when sorting'), sx('Show Files'), sx('Show Filename Extensions'), sx('Follow Playlist'), sx('Show Path'), sx('Always remember last folder'), sx('Start File Browser at /'), sx('File Browser Hotkey')], G('folder'), '%LV'),
        ([sx('System'), sx('Battery'), sx('Disk'), sx('Limits'), sx('Volume Adjustment Mode'), sx('Number of Volume Steps'), sx('Use Shortcuts Menu Instead of Quick Screen'), sx('Use Morse Code Input'), sx('Car Adapter Mode'), sx('Serial Bitrate'), sx('Accessory Power Supply'), sx('Line Out'), sx('Keyclick'), sx('USB'), sx('Battery Capacity'), sx('Charge During USB Connection'), sx('Disk Spindown'), sx('Directory Cache'), sx('Max Entries in File Browser'), sx('Max Playlist Size'), sx('Glyphs To Cache'), sx('Delay Before Resume'), sx('Headphone Keyclick'), sx('Speaker Keyclick'), sx('Keyclick Repeats'), sx('USB HID'), sx('USB Keypad Mode'), sx('USB-DAC'), sx('USB Mode')], G('ipod'), '%LV'),
        ([sx('Startup/Shutdown'), sx('Show Shutdown Message'), sx('Start Screen'), sx('Idle Poweroff'), sx('Default Sleep Timer Duration'), sx('Start Sleep Timer on Boot'), sx('Restart Sleep Timer on Keypress'), sx('Clear settings when hold switch is on during startup')], G('power'), '%LV'),
        ([sx('Automatic Resume'), sx('Automatic Track Change Only')], G('resume'), '%LV'),
        ([sx('Language')], G('globe'), '%LV'),
        ([sx('Load to RAM'), sx('Auto Update'), sx('Initialize Now'), sx('Update Now'), sx('Gather Runtime Data'), sx('Export Modifications'), sx('Import Modifications'), sx('Select directories to scan')], G('database'), '%LV'),
        ([sx('Backlight on Lock'), sx('Caption Backlight'), sx('First Buttonpress Enables Backlight Only'), sx('Backlight Exemptions'), sx('Enabled'), sx('Settings')], G('timer'), '%LV'),
        ([sx('Composite Video Output'), sx('Scrolling'), sx('Default Codepage'), sx('Scroll Speed Setting Example'), sx('Scroll Start Delay'), sx('Scroll Step Size Setting Example Text'), sx('Bidirectional Scroll Limit'), sx('Screen Scrolls Out of View'), sx('Disable main menu scrolling'), sx('Screen Scroll Step Size'), sx('Paged Scrolling'), sx('List Wraparound'), sx('List Order')], G('sun'), '%LV'),
        ([sx('Peak Meter'), sx('Peak Release'), sx('Peak Hold Time'), sx('Clip Hold Time'), sx('Clip Counter'), sx('Scale'), sx('Minimum of Range'), sx('Maximum of Range')], G('meter'), '%LV'),
        ([sx('Bookmark on Stop'), sx('Update on Stop'), sx('Load Last Bookmark'), sx('Maintain a List of Recent Bookmarks?')], G('bookmark'), '%LV'),
        ([sx('Voice Menus'), sx('Voice Directories'), sx('Use Directory .talk Clips'), sx('Voice Filenames'), sx('Use File .talk Clips'), sx('Say File Type'), sx('Announce Battery Level'), sx('Voice Prompt Volume')], G('voice'), '%LV'),
        ([sx('Browse Theme Files')], G('brush'), '%LV'),
        ([sx('Font')], G('font'), '%LV'),
        ([sx('Recording Screen')], G('rec_screen'), '%LV'),
        ([sx('Base Skin')], G('base_skin'), '%LV'),
        ([sx('Clear Backdrop')], G('backdrop'), '%LV'),
        ([sx('Status-/Scrollbar'), sx('Scroll Bar Width')], G('scroll_right'), '%LV'),
        ([sx('Line Selector Type')], G('line_selector'), '%LV'),
        ([sx('Line Separator')], G('line_separator'), '%LV'),
        ([sx('Colours'), sx('Line Selector Colours'), sx('Line Separator Colour'), sx('Background Colour'), sx('Foreground Colour'), sx('Reset Colours'), sx('Primary Colour'), sx('Secondary Colour'), sx('Text Colour')], G('palette'), '%LV'),
        ([sx('Main Menu')], G('main_menu'), '%LV'),
        ([sx('Browse .cfg Files')], G('cfg_file'), '%LV'),
        ([sx('Save .cfg File'), sx('Save Sound Settings'), sx('Save Theme Settings')], G('cfg_save'), '%LV'),
        ([sx('Format'), sx('Encoder Settings')], G('audio_file'), '%LV'),
        ([sx('Source')], G('plug'), '%LV'),
        ([sx('File Split Options'), sx('Split Measure'), sx('What to do when Splitting'), sx('Split Time'), sx('Split Filesize')], G('scissors'), '%LV'),
        ([sx('Prerecord Time')], G('prerecord'), '%LV'),
        ([sx('Clear Recording Directory')], G('rec_folder'), '%LV'),
        ([sx('Clipping Light')], G('clip_light'), '%LV'),
        ([sx('Trigger')], G('trigger'), '%LV'),
    ]
    default = G('gear') if opt else select([([sx(t)], G(n)) for t, n in SUBMENU_TILES], '%Lt', G('gear'))
    glyph = select([(r[0], r[1]) for r in rows], tag, default)
    # anything not listed: no value. A plain yes/no or on/off setting shows
    # its value in the row already; under the tile only descriptions
    value = select([(r[0], r[2]) for r in rows], tag, '')
    return glyph, value


def tile_block(label, title, glyph, value):
    """Sidebar tile: frame in the backdrop, symbol as a glyph of the tile
    font, title 17 px bold (CSS top 18 / lh 18), value 13 px bold (top 202)."""
    return ['%%Vl(%s,201,79,78,113,%d)%%Vf(dfe6f3)' % (label, TILES), '%al' + glyph,
            '%%Vl(%s,165,17,150,20,%d)%%Vf(ffffff)' % (label, B17), '%s%ac' + title,
            '%%Vl(%s,165,202,150,16,%d)%%Vf(ffffff)' % (label, B13), '%s%ac' + value]


# ---------------------------------------------------------------- SBS
def build_sbs():
    L = hdr('Status bar skin (.sbs): menus, lists, sidebar, lock screen, USB')
    L += fonts(FONTS_SBS)
    L += ['#--- images ---#',
          '%xl(Sidebar,sidebar.bmp,0,0)',
          '%xl(TileFrame,tileframe.bmp,41,79)',
          '%xl(SideSym,side_symbols.bmp,36,75,11)',
          '%xl(ClockFace,clockface.bmp,20,48)',
          '%xl(ClockDot,clockdot.bmp,0,0)',
          '%xl(Calendar,calendar.bmp,22,68)',
          # no cover: same effect precomputed, frame 1 round, frame 2 square;
          # drawn at (cover x - mx, cover y - over) inside the cover viewport
          # default cover of the mini player, turned like the playing screen's
          # (build_wps_cover.py mini: box 190,36 minus over 3 -> 190,33)
          '%xl(Cover100,cover100_fx.bmp,1,0,2)',
          '%xl(ArtPrev,artprev.bmp,41,79,2)',
          '%%xl(LockPrev,lockprev.bmp,%d,%d,2)' % tuple(MAN['lockprev']),
          # System: the logo tile on the sidebar, opaque (build_system_logo.py)
          '%xl(SysLogo,system_logo.bmp,36,51)',
          '%xl(Batt,status_battery.bmp,0,0,12)', '%xl(Charge,status_charge.bmp,0,0,12)', '%xl(Charged,status_charged.bmp,0,0)',
          '%xl(Play,status_play.bmp,0,0,4)', '%xl(Spin,status_spinner.bmp,0,0,12)',
          '%xl(Lock,status_lock.bmp,0,0)', '%xl(LockW,status_lock_white.bmp,0,0)',
          '%xl(SpinK,status_spinner_light.bmp,0,0,12)',   # black USB bar
          # USB screens: monochrome battery (RetailOS), same frames as Batt/Charge
          '%xl(BattM,status_battery_mono.bmp,0,0,12)', '%xl(ChargeM,status_charge_mono.bmp,0,0,12)',
          '%xl(HomeSpk,home_speaker.bmp,0,0)', '%xl(HomeShf,home_shuffle.bmp,30,0,2)',
          '%xl(HomeRep,home_repeat.bmp,62,0,5)',
          '%xl(UsbLogo,usb_logo.bmp,0,0,2)', '%xl(LockBox,lock_box.bmp,60,62)',
          '%xl(Check,row_check.bmp,2,8)',
          '%Cl(1,3,100,100,c,c)',
          '#--- UI viewports ---#',
          '%Vi(Half,0,22,160,218,-)',
          '%Vi(Full,0,22,320,218,-)',
          '%%Vi(Hidden,0,0,1,1,%d)' % DOT]
    L[L.index('%Cl(1,3,100,100,c,c)'):L.index('%Cl(1,3,100,100,c,c)')] = QM.quickmenu_images()

    # ------------- screen logic (1 x 1 px viewport) -------------
    # without playback the tile of the item too; the clock (SideHome, Home)
    # stays in the skin for now but is not shown
    main_side = ('%%?mp<%s%%Vd(TileMain)|'
                 '%%?%s<%%Vd(SideCover)%%Vd(Cover)%%Vd(CoverText)|%s%%Vd(TileMain)>>'
                 % (main_sidebar(), any_of('%LT', [sx('Now Playing'), sx('Resume Playback')]), main_sidebar()))
    # long title (104 px, up to the play icon) unless lock or spinner need the room
    # Menus use the firmware list: since the fork it draws the gloss bar,
    # arrows (%Lo) and values (%LV) itself, in one line that can scroll.
    # Own rows (%Lb) cannot show a value in a second colour: every row
    # viewport clears its line, and only the last one may scroll.
    half = ('%VI(Half)%Vd(SbHalf)%?or(%mh,%lh)<%Vd(TitleHalf)|%Vd(TitleHalfL)>'
            + status_logic(160))
    half_opt = half.replace('%VI(Half)', '%VI(Half)%Lb(OptRow,160,24)')
    is_art = any_of('%LT', [sx('Album Art Corners'), sx('Volume Display')])
    is_art_page = any_of('%Lt', [sx('Album Art Corners'), sx('Volume Display')])
    opt_square = any_of('%LT', [sx('Square'), sx('Numeric')])
    # key lock: the preview of the key lock design board as a picture (frame
    # 1 Normal, frame 2 Lock Screen); option names as the fork shows them
    is_lock = any_of('%LT', LOCK_NAMES)
    is_lock_page = any_of('%Lt', LOCK_NAMES)
    set_side = ('%%?%s<%%Vd(SideCal)%%Vd(Cal)|%%?%s<%%?%s<%%Vd(SideArtR)|%%Vd(SideArtS)>%%Vd(TileArt)|'
                '%%?%s<%%?%s<%%Vd(SideLockS)|%%Vd(SideLockN)>%%Vd(TileLock)|'
                '%%Vd(SideTile)%%Vd(TileSet)>>>' % (eq('%LT', sx('Time & Date')), is_art, ART_ROUND, is_lock, LOCK_SCREEN))
    opt_side = ('%%?%s<%%?%s<%%Vd(SideArtS)|%%Vd(SideArtR)>%%Vd(TileArtOpt)|'
                '%%?%s<%%?%s<%%Vd(SideLockN)|%%Vd(SideLockS)>%%Vd(TileLockOpt)|%%Vd(SideTile)%%Vd(TileOpt)>>'
                % (is_art_page, opt_square, is_lock_page, OPT_NORMAL))
    full = '%VI(Full)%Vd(SbFull)%Vd(TitleFull)' + status_logic(320)
    # key lock "Lock Screen" (battery display = graphic) covers every
    # menu screen except USB; "Normal" only adds the lock to the status bar.
    # A UI viewport change makes Rockbox redraw the list (sb_skin_get_info_vp),
    # so hiding it behind the 1 x 1 viewport is safe.
    # USB: 21 = connected, 22 = ejected by the computer (fork: ACTIVITY_USBEJECTED)
    locked = 'and(%mh,%if(%St(battery display),=,graphic),%if(%cs,!=,21),%if(%cs,!=,22))'
    def unless_locked(body):
        return '%%?%s<|%s>' % (locked, body)
    L += ['#--- screen logic ---#', '%%V(0,0,1,1,%d)' % DOT,
          '%%?%s<%%VI(Hidden)%s>' % (locked, lock_logic('Lk')),
          '%%?if(%%cs,=,1)<%s>' % unless_locked(half + main_side),
          '%%?if(%%cs,=,6)<%s>' % unless_locked(half + set_side),
          '%%?if(%%cs,=,12)<%s>' % unless_locked(half_opt + opt_side),
          '%%?if(%%cs,=,16)<%s>' % unless_locked(half + '%Vd(SideSys)%Vd(TileSys)'),
          # Time & Date (time_screen): the calendar card, as when the entry is
          # highlighted in the settings. time_screen() lays out its clock and
          # menu once from the UI viewport; full width, the option page
          # "Time Format" opened in that menu covered half of its tile.
          '%%?if(%%cs,=,17)<%s>' % unless_locked(half + '%Vd(SideCal)%Vd(Cal)'),
          # USB: black bar, the battery with its level (BatUsb), never the plug;
          # 22 after the host ejected the drive
          '%%?or(%s)<%%VI(Hidden)%%Vd(UsbField)%%Vd(SbUsb)%%Vd(TitleUsb)%%?if(%%cs,=,22)<%%Vd(UsbAus)|%%Vd(Usb)>%s>'
          % (USB_SCREENS, status_logic(320, dark=True)),
          QM.quickmenu_logic(),
          '%%?and(%s)<%s>' % (','.join('%%if(%%cs,!=,%d)' % c for c in (1, 6, 10, 12, 16, 17, 21, 22)), unless_locked(full))]

    # ------------- backdrop layer -------------
    L += ['#--- backdrop layer (%VB) ---#']
    # White base under everything. Rockbox fills the backdrop buffer with a
    # copy of the screen when the skin loads, and firmware lists clear their
    # area with that buffer; without a base the old screen shows through.
    L += ['%s' % '# white base of the backdrop layer: the lists clear their area with it',
          '%%V(0,0,320,240,%d)%%VB' % DOT, '%dr(0,0,320,240,ffffff)']
    L += QM.quickmenu_backdrop()
    # USB field first: the status bar of the USB screen is drawn over it
    L += field_bg('UsbField')
    L += statusbar_bg('SbUsb', 320, dark=True)   # black like RetailOS
    L += statusbar_bg('SbFull', 320) + statusbar_bg('SbHalf', 160)
    # one complete sidebar per mode, all on the same rectangle, so a mode
    # that is switched off is always painted over by the next one
    L += ['%%Vl(SideCover,160,0,160,240,%d)%%VB%%xd(Sidebar)' % DOT,
          '%%Vl(SideTile,160,0,160,240,%d)%%VB%%xd(Sidebar)%%xd(TileFrame)' % DOT,
          '%%Vl(SideSys,160,0,160,240,%d)%%VB%%xd(Sidebar)%%xd(SysLogo)' % DOT]
    L += ['%%Vl(%s,160,0,160,240,%d)%%VB%%xd(Sidebar)%%xd(SideSym,%d)' % (label, DOT, n)
          for label, n, _ in SIDE_PUR]
    L += [
          '%%Vl(SideHome,160,0,160,240,%d)%%VB%%xd(Sidebar)%%xd(ClockFace)' % DOT,
          '%%Vl(SideCal,160,0,160,240,%d)%%VB%%xd(Sidebar)%%xd(Calendar)' % DOT,
          '%%Vl(SideArtR,160,0,160,240,%d)%%VB%%xd(Sidebar)%%xd(ArtPrev,1)' % DOT,
          '%%Vl(SideArtS,160,0,160,240,%d)%%VB%%xd(Sidebar)%%xd(ArtPrev,2)' % DOT,
          '%%Vl(SideLockN,160,0,160,240,%d)%%VB%%xd(Sidebar)%%xd(LockPrev,1)' % DOT,
          '%%Vl(SideLockS,160,0,160,240,%d)%%VB%%xd(Sidebar)%%xd(LockPrev,2)' % DOT]
    L += lock_screen('Lk')

    # ------------- own list rows: option pages (check mark) -------------
    # Three viewports with the same label: inset filler, right end with the
    # check, text. The text viewport comes last on purpose: for the selected
    # row list-skinned.c copies every viewport into one shared struct, and a
    # scrolling line keeps pointing at that struct.
    L += ['#--- list rows of the option pages ---#',
          '%%Vl(OptRow,0,0,8,24,%d)' % UI, SEL,
          '%%Vl(OptRow,140,0,20,24,%d)' % UI, SEL + '%?Lc<%xd(Check)>',
          '%%Vl(OptRow,8,0,132,24,%d)%%Vf(0d0f13)' % UI, SEL + '%s%LT']

    # ------------- status bar text + icons -------------
    L += ['#--- status bar ---#']
    L += (title_vp('TitleHalf', 72, '%Lt') + title_vp('TitleHalfL', 104, '%Lt')
          + title_vp('TitleFull', 232, '%Lt'))
    # USB: light title "iPod" on the black bar, centred on the screen (Fork:
    # the viewport is symmetric about x 160 and ends before the icons at 244)
    L += ['%%Vl(TitleUsb,76,3,168,16,%d)%%Vf(%s)' % (B13, D.TEXT_STATUS_LIGHT[1:].lower()), '%s%aciPod']
    L += status_icons(160) + status_icons(320) + status_icons(320, dark=True)
    # USB mode: the cable is always in; a full battery would show the plug
    # all the time, so here the battery with its level, bolt while charging;
    # monochrome on the black bar
    i = L.index('%Vl(Bat320,288,4,26,13,-)')
    L[i + 2:i + 2] = ['%Vl(BatUsb,288,4,26,13,-)', '%?bc<%xd(ChargeM,%bl)|%xd(BattM,%bl)>']

    # ------------- main menu sidebar -------------
    L += ['#--- main menu: home page (nothing playing) ---#',
          '%Vl(Home,200,16,82,14,-)%xd(HomeSpk)%xd(HomeShf,%ps)%xd(HomeRep,%mm)']
    hands = '%?cl<' + '|'.join(
        '%?cM<' + '|'.join(chr(0xE001 + (k % 12) * 60 + m) for m in list(range(1, 60)) + [0]) + '>'
        for k in range(1, 13)) + '>'
    L += ['%%Vl(Home,198,66,84,84,%d)%%Vf(14161b)' % HANDS, '%al' + hands,
          '%Vl(Home,237,105,6,6,-)%xd(ClockDot)',
          '%%Vl(Home,165,184,150,14,%d)%%Vf(dce6f2)' % B11, '%ac' + DATE_WEEKDAY,
          '%%Vl(Home,165,201,150,20,%d)%%Vf(ffffff)' % B17, '%ac' + DATE_SHORT]
    L += ['#--- main menu: now playing (cover 100 px) ---#',
          # cover 100 at 190,36, turned 24 deg like the playing screen
          # (perspective 420), reflection 36 px at 60 % on blue: 100 x 142 from y 33
          '%Vl(Cover,189,33,102,142,-)',
          '%%?%s<%%Cd(24,420,36,60,%d)|%%Cd(24,420,36,60,0)>%%?C<|%%?%s<%%xd(Cover100,1)|%%xd(Cover100,2)>>'
          % (ART_ROUND, D.COVER_RADIUS, ART_ROUND),
          '%%Vl(CoverText,168,185,144,16,%d)%%Vf(ffffff)' % B13, '%s%ac%?it<%it|%fn>',
          '%%Vl(CoverText,168,203,144,14,%d)%%Vf(dce6f2)' % B11, SECOND_LINE]
    L += ['#--- main menu: tiles ---#']
    glyph = select([(t, G(n) if n else '') for t, n, v in MAIN_TILES], '%LT', G('gear'))
    value = select([(t, v) for t, n, v in MAIN_TILES], '%LT', '')
    L += tile_block('TileMain', '%LT', glyph, value)

    # ------------- settings -------------
    L += ['#--- settings ---#']
    g, v = setting_tiles('%LT')
    L += tile_block('TileSet', '%LT', g, v)
    L += ['%%Vl(Cal,190,77,100,16,%d)%%Vf(ffffff)' % B13, '%ac' + DATE_MONTH,
          '%%Vl(Cal,190,107,100,46,%d)%%Vf(0e1016)' % DAY, '%ac%cd',
          '%%Vl(Cal,165,17,150,20,%d)%%Vf(ffffff)' % B17, '%s%ac%LT',
          '%%Vl(Cal,165,207,150,20,%d)%%Vf(ffffff)' % B17, '%ac' + DATE_SHORT]
    L += ['#--- album art corners: default cover as preview ---#']
    L += tile_block('TileArt', '%LT', '', '%%?if(%%St(volume display),=,graphic)<%s|%s>' % (sx('Rounded'), sx('Square')))[2:]
    L += tile_block('TileArtOpt', '%Lt', '', '%LT')[2:]
    L += ['#--- key lock: preview from the design board as a picture ---#']
    L += tile_block('TileLock', '%LT', '', '%%?%s<%s|%s>' % (LOCK_SCREEN, sx('Lock Screen'), sx('Normal')))[2:]
    # option page as on the board: option name as title, what it does below
    L += tile_block('TileLockOpt', '%LT', '', '%%?%s<%s|%s>' % (OPT_NORMAL, sx('Screen unchanged'), sx('Clock and title')))[2:]
    g, v = setting_tiles('%Lt', opt=True)
    L += ['#--- option pages ---#']
    L += tile_block('TileOpt', '%Lt', g, '%LT')
    # the logo tile lies in the backdrop (SideSys, 88 px at 196,51), the name
    # 17 px bold and the version 13 px bold in a lighter blue below it
    L += ['#--- System: logo tile in the backdrop (SideSys), name and version below it ---#',
          '%%Vl(TileSys,165,151,150,20,%d)%%Vf(ffffff)' % B17, '%s%acGlossy Slate',
          '%%Vl(TileSys,165,173,150,16,%d)%%Vf(dce6f2)' % B13, '%s%ac' + sx('Version') + ' ' + VERSION]

    # ------------- USB -------------
    # logo 88 px at 116,64 like the tile before, the bitmap has room for the shadow
    pl, pt, pr, pb = D.USB_PAD
    def logo_vp(label, frame):
        return '%%Vl(%s,%d,%d,%d,%d,-)%%xd(UsbLogo,%d)' % (label, 116 - pl, 64 - pt, pl + 88 + pr, pt + 88 + pb, frame)
    L += ['#--- USB mode: connected (%cs = 21) ---#',
          '%%Vl(Usb,10,35,300,20,%d)%%Vf(ffffff)' % B17, '%ac' + sx('Connected'),
          logo_vp('Usb', 1),
          '%%Vl(Usb,10,190,300,16,%d)%%Vf(ffffff)' % B13, '%ac' + sx('Do not disconnect.'),
          '%%Vl(Usb,10,208,300,14,%d)%%Vf(dce6f2)' % B11, '%ac' + sx('Eject on the computer before disconnecting.')]
    L += ['#--- USB mode: ejected by the computer (%cs = 22) ---#',
          '%%Vl(UsbAus,10,35,300,20,%d)%%Vf(ffffff)' % B17, '%ac' + sx('Ejected'),
          logo_vp('UsbAus', 2),
          '%%Vl(UsbAus,10,190,300,16,%d)%%Vf(ffffff)' % B13, '%ac' + sx('The cable can now be disconnected.'),
          '%%Vl(UsbAus,10,208,300,14,%d)%%Vf(dce6f2)' % B11, '%ac' + sx('Rockbox is ready again after disconnecting.')]
    L += ['#--- quick menu (%cs = 10) ---#'] + QM.quickmenu_viewports()
    return '\n'.join(L) + '\n'


# ---------------------------------------------------------------- WPS
def wps_bg_strip(label, kind):
    """Strip y 196..235 of the WPS page with its gradient, plus the track."""
    L = ['%%Vl(%s,0,196,320,44,%d)%%VB' % (label, DOT),
         # page gradient #FFFFFF (58 %) -> #EBEEF2 (100 %), rows 196..239
         '%dr(0,0,320,44,f4f6f8,ebeef2)']
    if kind == 'prog':
        L += ['%xd(Track)']
    else:
        L += ['%xd(VTrack)%xd(VolLow)%xd(VolHigh)']
    return L


def build_wps():
    L = hdr('Playback skin (.wps)')
    L += ['%wd']
    L += fonts(FONTS_WPS)
    L += ['#--- images ---#',
          '%xl(Batt,status_battery.bmp,0,0,12)', '%xl(Charge,status_charge.bmp,0,0,12)', '%xl(Charged,status_charged.bmp,0,0)',
          '%xl(Play,status_play.bmp,0,0,4)', '%xl(Spin,status_spinner.bmp,0,0,12)',
          '%xl(Lock,status_lock.bmp,0,0)', '%xl(LockW,status_lock_white.bmp,0,0)',
          '%xl(LockBox,lock_box.bmp,60,62)',
          # default cover with the effect, from build_wps_cover.py (box 116 at
          # 14,39 minus mx 0, over 4 -> 14,35 = viewport 13,35 plus 1,0)
          '%xl(Cover116,cover116_fx.bmp,1,0,2)',
          '%xl(Track,wps_track.bmp,14,4)', '%xl(VTrack,wps_vtrack.bmp,34,4)',
          '%xl(VolLow,wps_vol_low.bmp,14,2)', '%xl(VolHigh,wps_vol_high.bmp,292,1)',
          '%xl(Cap,wps_cap.bmp,0,0)',
          # fixed round left ends of the bars (build_bar_ends.py): the cap is
          # straight on the left and stood out of the track near the start
          '%xl(FillL,wps_fill_l.bmp,0,0)', '%xl(VFillL,wps_vfill_l.bmp,0,0)',
          '%xl(WShuf,wps_shuffle.bmp,0,0,2)', '%xl(WRep,wps_repeat.bmp,22,0,5)',
          '%xl(PillC,wps_pill_codec.bmp,0,0)', '%xl(PillR,wps_pill_rate.bmp,48,0)',
          '%Cl(1,4,116,116,c,c)']
    lockmode = eq('%St(battery display)', 'graphic')
    player = ('%Vd(PageBg)%Vd(Player)' + status_logic(320) +
              '%?mv(1.5)<%Vd(VolBg)%Vd(Vol)|%Vd(ProgBg)%Vd(Prog)>')
    L += ['#--- screen logic ---#', '%%V(0,0,1,1,%d)' % DOT,
          '%%?mh<%%?%s<%s|%s>|%s>' % (lockmode, lock_logic('Lk'), player, player)]
    L += ['#--- backdrop layer ---#',
          '%%Vl(PageBg,0,0,320,196,%d)%%VB' % DOT,
          ] + [d % 320 for d in STATUS_DR] + [
          '%dr(0,22,320,117,ffffff)', '%dr(0,139,320,57,ffffff,f4f6f8)',
          '%xd(PillC)%xd(PillR)']
    # pills sit at x 144 / 192, y 120 -> relative to PageBg
    L[-1] = '%%Vl(PageBg,144,120,104,14,%d)%%VB%%xd(PillC)%%xd(PillR)' % DOT
    L += wps_bg_strip('ProgBg', 'prog') + wps_bg_strip('VolBg', 'vol')
    L += lock_screen('Lk')
    L += ['#--- status bar ---#']
    L += ['%%Vl(Player,8,3,232,16,%d)%%Vf(14171c)' % B13, '%al' + sx('Now playing')]   # like title_vp
    L += status_icons(320)
    # cover 116 at 14,39, tilted 24 deg (perspective 420) with a 36 px
    # reflection at 34 %: the image is 116 x 160 from y 35 (13 px under the
    # status bar, as on the original), so the viewport covers x 13-130,
    # y 35-195 and the whole reflection ends at the progress area (y 196);
    # nothing is drawn under the cover before it
    L += ['#--- cover 116 px, tilted, full reflection down to the progress bar (y 196), 13 px below the status bar ---#',
          '%Vl(Player,13,35,118,161,-)',
          '%%?%s<%%Cd(24,420,36,34,%d)|%%Cd(24,420,36,34,0)>%%?C<|%%?%s<%%xd(Cover116,1)|%%xd(Cover116,2)>>'
          % (ART_ROUND, D.COVER_RADIUS, ART_ROUND)]
    L += ['#--- track info ---#',
          '%%Vl(Player,144,36,164,14,%d)%%Vf(5b6371)' % B11, '%pp %Sx(of) %pe',
          '%%Vl(Player,144,56,164,20,%d)%%Vf(0d0f13)' % B17, '%s%?it<%it|%fn>',
          '%%Vl(Player,144,79,164,16,%d)%%Vf(2e3644)' % B13, '%s%?ia<%ia|%d(1)>',
          '%%Vl(Player,144,98,164,16,%d)%%Vf(5b6371)' % R13, '%s%?id<%id|%d(2)>',
          '%%Vl(Player,144,120,44,14,%d)%%Vf(3b4350)' % B11, '%ac%fc',
          '%%Vl(Player,192,120,56,14,%d)%%Vf(3b4350)' % B11, '%ac%fk kHz']
    L += ['#--- progress ---#',
          '%Vl(Prog,14,200,5,9,-)%xd(FillL)',
          '%Vl(Prog,19,200,287,9,-)', '%pb(0,0,287,9,wps_fill_r.bmp,slider,Cap)',
          '%%Vl(Prog,14,214,80,16,%d)%%Vf(2e3644)' % B12, '%al%pc',
          '%%Vl(Prog,226,214,80,16,%d)%%Vf(2e3644)' % B12, '%ar−%pr',
          '%Vl(Prog,142,217,36,10,-)%xd(WShuf,%ps)%xd(WRep,%mm)']
    L += ['#--- volume (while changing) ---#',
          '%Vl(Vol,34,200,5,9,-)%xd(VFillL)',
          '%Vl(Vol,39,200,247,9,-)', '%pv(0,0,247,9,wps_vfill_r.bmp,slider,Cap)',
          '%%Vl(Vol,14,214,292,16,%d)%%Vf(2e3644)' % B12, '%ac%pv dB']
    return '\n'.join(L) + '\n'


CFG = """#
#   Glossy Slate {v} – Rockbox theme for iPod Classic 6G/7G (fork)
#   Design: Glossy Slate (RetailOS look, light only)
#   Fonts: GlossySlate Sans, derived from Liberation Sans 2 (SIL OFL 1.1)
#
wps: /.rockbox/wps/glossyslate.wps
sbs: /.rockbox/wps/glossyslate.sbs
wrs: /.rockbox/wps/glossyslate.wrs
font: /.rockbox/fonts/24-GlossySlate-Bold14.fnt
iconset: -
viewers iconset: -
show icons: off
ui viewport: -
backdrop: -
foreground color: 0D0F13
background color: FFFFFF
#
#-- Selection bar with a gloss edge (fork): start -> 45 % -> 55 % -> end,
#   top row 38 % lighter, bottom row in the edge colour --#
selector type: bar (gloss)
line selector start color: 5896E6
line selector end color: 1A55BE
line selector text color: FFFFFF
line selector gloss top color: 3577D9
line selector gloss bottom color: 2160CB
line selector gloss edge color: 174A9E
#
#-- Firmware lists (fork): second colour for artists and values, arrows, inset --#
list secondary color: 5B6371
list secondary font: /.rockbox/fonts/16-GlossySlate-Regular13.fnt
popup font: /.rockbox/fonts/16-GlossySlate-Bold13.fnt
popup hint font: /.rockbox/fonts/14-GlossySlate-Bold11.fnt
list arrows: on
list arrow color: 1D2847
list value color: 5677B0
list edge inset: 8
#
#-- Scroll bar: the fork's overlay knob, 6 = 5 px wide --#
scrollbar: right
scrollbar width: 6
#
#-- Second line (fork): off = alternating, top = album only, bottom = artist only --#
statusbar: off
#
#-- Album art corners (fork): graphic = rounded, numeric = square --#
volume display: graphic
#
#-- Key lock (fork, setting battery display): numeric = Normal
#   (lock in the status bar), graphic = lock screen with clock and title --#
battery display: numeric
#
#-- Quick menu (DESIGN.md 5.10): wheel volume, MENU/PLAY brightness,
#   left shuffle, right repeat. Other assignments: the "free" view --#
qs top: brightness
qs bottom: brightness
qs left: shuffle
qs right: repeat
#
scroll speed: 14
scroll delay: 1500
scroll step: 1
""".format(v=VERSION)


def main():
    os.makedirs(os.path.join(PKG, 'wps'), exist_ok=True)
    os.makedirs(os.path.join(PKG, 'themes'), exist_ok=True)
    open(os.path.join(PKG, 'wps', 'glossyslate.sbs'), 'w', encoding='utf-8').write(build_sbs())
    open(os.path.join(PKG, 'wps', 'glossyslate.wps'), 'w', encoding='utf-8').write(build_wps())
    open(os.path.join(PKG, 'themes', 'glossyslate.cfg'), 'w', encoding='utf-8').write(CFG)
    print('skins ok')


if __name__ == '__main__':
    main()
