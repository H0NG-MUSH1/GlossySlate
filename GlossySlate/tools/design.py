"""Design tokens and SVG snippets shared by the asset and font builders.
All values are taken from the artboards of the Glossy Slate design canvas."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SYM = json.load(open(os.path.join(HERE, 'sym.json')))
SYM_EXTRA = json.load(open(os.path.join(HERE, 'sym_extra.json')))

FONT_STACK = "'Liberation Sans', Arimo, Helvetica, Arial, sans-serif"

# ---- colours -------------------------------------------------------------
TEXT = '#0D0F13'
TEXT_STATUS = '#14171C'
SECONDARY = '#5B6371'
ICON_DARK = '#2E3644'
SYMBOL = '#DFE6F3'
LINE = '#1E1E1E'           # line under the status bar (up to 1.3: #9AA3B0)
WHITE = '#FFFFFF'
SUBLINE = '#DCE6F2'

ACCENT = {  # blue
    'bar': 'linear-gradient(180deg, #5896E6 0%, #3577D9 45%, #2160CB 55%, #1A55BE 100%)',
    'edge': '#174A9E', 'p1': '#7DB4F0', 'p2': '#1F5FC8', 'solid': '#2160CB',
    'fill': 'linear-gradient(180deg, #8EC0F4 0%, #5698E8 45%, #2F70D6 55%, #3D82E0 100%)',
    'sel_start': '5896E6', 'sel_end': '1A55BE',
}

STATUS_BG = 'linear-gradient(180deg, #FFFFFF 0px, #979797 21px)'   # up to 1.3: #FFFFFF -> #F2F4F7 45 % -> #DDE2E9
SIDEBAR_BG = ('linear-gradient(90deg, rgba(0,0,0,.46) 0px, rgba(0,0,0,.31) 6px, rgba(0,0,0,.14) 12px, '
              'rgba(0,0,0,.02) 18px, rgba(0,0,0,0) 24px), '
              'linear-gradient(137deg, rgba(10,16,32,0) 0%, rgba(10,16,32,.12) 20%, rgba(10,16,32,.23) 40%, '
              'rgba(10,16,32,.4) 60%, rgba(10,16,32,.66) 80%, rgba(10,16,32,1) 100%), '
              'linear-gradient(180deg, #B8D7F1 0px, #9CCBF2 40px, #A2CAF4 80px, #87B4DA 120px, '
              '#638DB2 160px, #426792 200px, #273B3F 240px)')
FIELD_BG = ('linear-gradient(137deg, rgba(10,16,32,0) 0%, rgba(10,16,32,.12) 20%, rgba(10,16,32,.23) 40%, '
            'rgba(10,16,32,.4) 60%, rgba(10,16,32,.66) 80%, rgba(10,16,32,1) 100%), '
            'linear-gradient(180deg, #B8D7F1 0px, #9CCBF2 40px, #A2CAF4 80px, #87B4DA 120px, '
            '#638DB2 160px, #426792 200px, #273B3F 240px)')
TILE_BG = ('linear-gradient(180deg, #8E9CAE 0px, #8E9CAE 1px, #778496 4%, #606C79 14%, #454F5B 24%, '
           '#282E37 35%, #151821 45%, #0B0E14 50%, #07080C 100%)')
WPS_BG = 'linear-gradient(180deg, #FFFFFF 0%, #FFFFFF 58%, #EBEEF2 100%)'
TRACK_BG = 'linear-gradient(180deg, #AEB6C1 0%, #D5DAE1 40%, #F1F3F6 100%)'
TRACK_SHADOW = 'inset 0 1px 1.5px rgba(0,0,0,.28), 0 1px 0 #FFFFFF'
FILL_SHADOW = 'inset 0 1px 0 rgba(255,255,255,.45), inset 0 -1px 0 rgba(0,20,70,.25)'
REFLECT_MASK = 'linear-gradient(180deg, rgba(0,0,0,.7) 0%, rgba(0,0,0,0) 100%)'

# Default cover (user supplied note, recoloured)
COVER_BG = 'linear-gradient(180deg, #F6F7F9 0%, #E6EAEF 100%)'
COVER_NOTE = '#B8C0CB'
COVER_RADIUS = 8          # 'Rounded' on the now playing screen, the mini player and the album art corners preview


def note_path():
    return open(os.path.join(HERE, 'note.d')).read()


def default_cover_svg(size):
    return ('<div style="width:%dpx;height:%dpx;background:%s">'
            '<svg width="%d" height="%d" viewBox="0 0 1190 1190"><path d="%s" fill="%s"/></svg></div>'
            % (size, size, COVER_BG, size, size, note_path(), COVER_NOTE))


# ---- tile symbols (viewBox 0 0 156 156) ------------------------------------
def sym_markup(s, color=SYMBOL):
    """Markup for the {f, s, w} symbol objects from Main/Settings."""
    out = ''
    if s.get('s1'):
        out += '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="%s" stroke-linejoin="round"/>' % (
            s['s1'], color, s.get('w', 8), s.get('cap', 'round'))
    if s.get('h'):
        # crossing: cut s1 where s passes over it (mask instead of halo colour)
        pass
    if s.get('s'):
        out += '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="%s" stroke-linejoin="round"/>' % (
            s['s'], color, s.get('w', 8), s.get('cap', 'round'))
    if s.get('f'):
        out += '<path d="%s" fill="%s" fill-rule="evenodd"/>' % (s['f'], color)
    if s.get('badge'):
        out += ('<circle cx="30" cy="40" r="22" fill="#000" fill-opacity="0"/>'
                '<circle cx="30" cy="40" r="17" fill="%s"/>' % color)
    return out


def shuffle_markup(color=SYMBOL):
    s = SYM['Settings']['shuffle']
    return ('<defs><mask id="cut" maskUnits="userSpaceOnUse" x="0" y="0" width="156" height="156">'
            '<rect width="156" height="156" fill="#fff"/>'
            '<path d="%s" fill="none" stroke="#000" stroke-width="28"/></mask></defs>'
            '<path d="%s" fill="none" stroke="%s" stroke-width="18" stroke-linecap="butt" mask="url(#cut)"/>'
            '<path d="%s" fill="none" stroke="%s" stroke-width="18" stroke-linecap="butt"/>'
            '<path d="%s" fill="%s"/>' % (s['h'], s['s1'], color, s['s'], color, s['f'], color))


def repeat_one_markup(color=SYMBOL):
    s = SYM['Settings']['repeatOne']
    # the "1" badge: light disc with the digit cut out, ring around it cut out
    return ('<defs><mask id="badge" maskUnits="userSpaceOnUse" x="0" y="0" width="156" height="156">'
            '<rect width="156" height="156" fill="#fff"/><circle cx="30" cy="40" r="22" fill="#000"/></mask>'
            '<mask id="digit" maskUnits="userSpaceOnUse" x="0" y="0" width="156" height="156">'
            '<rect width="156" height="156" fill="#fff"/>'
            '<text x="30" y="48.6" text-anchor="middle" font-family="%s" font-size="24" font-weight="700" fill="#000">1</text></mask></defs>'
            '<g mask="url(#badge)"><path d="%s" fill="none" stroke="%s" stroke-width="18" stroke-linecap="butt"/>'
            '<path d="%s" fill="%s"/></g>'
            '<circle cx="30" cy="40" r="17" fill="%s" mask="url(#digit)"/>'
            % (FONT_STACK, s['s'], color, s['f'], color, color))


def plain(s, color=SYMBOL):
    return sym_markup(s, color)


# New symbols in the same stroke language (stroke 8, fills #DFE6F3)
NEW_SYMBOLS = {
    # USB mode: 30-pin dock connector after the template "USB connected" (circle centre 160,90),
    # x2 into the 156 grid (X = 2x - 242, Y = 2y - 102); slots and key ring cut out
    'dock': '<defs><mask id="dockm" maskUnits="userSpaceOnUse" x="0" y="0" width="156" height="156"><rect width="156" height="156" fill="#fff"/><path d="M38 36H41V56H38ZM115 36H118V56H115Z" fill="#000"/><rect x="63" y="67" width="30" height="10" rx="5" fill="none" stroke="#000" stroke-width="3"/></mask></defs><g mask="url(#dockm)" fill="{c}"><rect x="32" y="32" width="92" height="26" rx="3"/><rect x="22" y="56" width="112" height="34" rx="4"/><rect x="66" y="90" width="24" height="16"/><rect x="69" y="104" width="18" height="20" rx="2"/></g>',
    # shortcuts: star
    'star': '<path d="M78 24L93.5 57.5L130 61.6L103 86.4L110.4 122.4L78 104.2L45.6 122.4L53 86.4L26 61.6L62.5 57.5Z" fill="{c}" stroke="{c}" stroke-width="8" stroke-linejoin="round"/>',
    # bookmarks: bookmark ribbon
    'bookmark': '<path d="M46 26H110A6 6 0 0 1 116 32V132L78 106L40 132V32A6 6 0 0 1 46 26Z" fill="{c}"/>',
    # playback settings: play triangle in a ring
    'play': '<path d="M26 78a52 52 0 1 0 104 0a52 52 0 1 0 -104 0Z" fill="none" stroke="{c}" stroke-width="8"/><path d="M66 52L106 78L66 104Z" fill="{c}" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>',
    # themes: brush
    'brush': '<path d="M112 22L134 44L84 94L62 72Z" fill="{c}"/><path d="M56 80L76 100C76 118 62 132 40 132C30 132 24 130 20 126C30 122 34 114 36 104C38 90 46 82 56 80Z" fill="{c}"/>',
    # voice: speech bubble
    'voice': '<defs><mask id="vm" maskUnits="userSpaceOnUse" x="0" y="0" width="156" height="156"><rect width="156" height="156" fill="#fff"/><path d="M50 60H106M50 80H90" stroke="#000" stroke-width="9" stroke-linecap="round"/></mask></defs><path mask="url(#vm)" d="M38 30H118A14 14 0 0 1 132 44V92A14 14 0 0 1 118 106H72L44 128V106H38A14 14 0 0 1 24 92V44A14 14 0 0 1 38 30Z" fill="{c}"/>',
    # configurations / general: sliders
    'sliders': '<path d="M34 46H122M34 78H122M34 110H122" stroke="{c}" stroke-width="8" stroke-linecap="round"/><path d="M58 46m-12 0a12 12 0 1 0 24 0a12 12 0 1 0 -24 0M98 78m-12 0a12 12 0 1 0 24 0a12 12 0 1 0 -24 0M70 110m-12 0a12 12 0 1 0 24 0a12 12 0 1 0 -24 0" fill="{c}"/>',
    # key lock: padlock
    'lock': '<defs><mask id="lm" maskUnits="userSpaceOnUse" x="0" y="0" width="156" height="156"><rect width="156" height="156" fill="#fff"/><path d="M78 92V108" stroke="#000" stroke-width="10" stroke-linecap="round"/></mask></defs><path d="M54 70V54A24 24 0 0 1 102 54V70" fill="none" stroke="{c}" stroke-width="12"/><path mask="url(#lm)" d="M42 66H114A8 8 0 0 1 122 74V124A8 8 0 0 1 114 132H42A8 8 0 0 1 34 124V74A8 8 0 0 1 42 66Z" fill="{c}"/>',
    # second line: two text lines, the second highlighted
    'secondline': '<path d="M30 54H126" stroke="{c}" stroke-width="12" stroke-linecap="round"/><path d="M30 84H126" stroke="{c}" stroke-opacity=".5" stroke-width="12" stroke-linecap="round"/><path d="M30 114H96" stroke="{c}" stroke-opacity=".5" stroke-width="12" stroke-linecap="round"/>',
    # album art corners: picture, rounded / square
    'art_round': '<rect x="26" y="30" width="104" height="96" rx="22" fill="none" stroke="{c}" stroke-width="8"/><circle cx="58" cy="60" r="10" fill="{c}"/><path d="M34 112L68 80L88 98L104 84L122 102V112A10 10 0 0 1 112 118H40Z" fill="{c}"/>',
    'art_square': '<rect x="26" y="30" width="104" height="96" fill="none" stroke="{c}" stroke-width="8"/><circle cx="58" cy="60" r="10" fill="{c}"/><path d="M30 114L68 80L88 98L104 84L126 106V122H30Z" fill="{c}"/>',
    # Equalizer (bars from the wide design tile, scaled into 156)
    'eq': '<g transform="translate(9 6) scale(.53 1)"><path transform="translate(0 -6)" fill="{c}" d="M15 59a3 3 0 0 1 3 -3H32a3 3 0 0 1 3 3V122H15ZM45 69a3 3 0 0 1 3 -3H62a3 3 0 0 1 3 3V122H45ZM75 83a3 3 0 0 1 3 -3H92a3 3 0 0 1 3 3V122H75ZM105 93a3 3 0 0 1 3 -3H122a3 3 0 0 1 3 3V122H105ZM135 87a3 3 0 0 1 3 -3H152a3 3 0 0 1 3 3V122H135ZM165 73a3 3 0 0 1 3 -3H182a3 3 0 0 1 3 3V122H165ZM195 61a3 3 0 0 1 3 -3H212a3 3 0 0 1 3 3V122H195ZM225 51a3 3 0 0 1 3 -3H242a3 3 0 0 1 3 3V122H225Z"/></g>',
    # scroll bar (from the option board "scroll bar")
    'scroll_off': '<path d="M28 44H128M28 68H128M28 92H128M28 116H96" stroke="{c}" stroke-width="8" stroke-linecap="round"/>',
    'scroll_left': '<path d="M24 40a6 6 0 0 1 12 0V88a6 6 0 0 1 -12 0Z" fill="{c}"/><path d="M52 44H134M52 68H134M52 92H134M52 116H110" stroke="{c}" stroke-width="8" stroke-linecap="round"/>',
    'scroll_right': '<path d="M120 40a6 6 0 0 1 12 0V88a6 6 0 0 1 -12 0Z" fill="{c}"/><path d="M22 44H104M22 68H104M22 92H104M22 116H80" stroke="{c}" stroke-width="8" stroke-linecap="round"/>',
    # theme sign (System)
    'logo': '<path fill="{c}" fill-rule="evenodd" d="M22 78a56 56 0 1 0 112 0a56 56 0 1 0 -112 0ZM34 78a44 44 0 1 0 88 0a44 44 0 1 0 -88 0ZM38 78a40 40 0 1 0 80 0a40 40 0 1 0 -80 0ZM50 78a28 28 0 1 0 56 0a28 28 0 1 0 -56 0ZM54 78a24 24 0 1 0 48 0a24 24 0 1 0 -48 0ZM72 78a6 6 0 1 0 12 0a6 6 0 1 0 -12 0Z"/>',
    # calendar (fallback glyph, the real calendar card is a bitmap)
    'calendar': '<rect x="28" y="34" width="100" height="92" rx="12" fill="none" stroke="{c}" stroke-width="8"/><path d="M28 60H128" stroke="{c}" stroke-width="8"/><path d="M54 24V44M102 24V44" stroke="{c}" stroke-width="8" stroke-linecap="round"/>',
}


def tile_symbol(name, color=SYMBOL):
    m, e = SYM['Main'], SYM['Settings']
    if name in m:
        return plain(m[name], color)
    if name == 'shuffle':
        return shuffle_markup(color)
    if name == 'repeatOne':
        return repeat_one_markup(color)
    if name in e:
        return plain(e[name], color)
    if name in ('podcast', 'book'):
        return SYM_EXTRA[name].replace('#DFE6F3', color)
    if name == 'usb':
        return ('<path fill="{c}" d="M78 16L91 38H65ZM66 126a12 12 0 1 0 24 0a12 12 0 1 0 -24 0ZM38 62a9 9 0 1 0 18 0a9 9 0 1 0 -18 0ZM100 44H118V62H100Z"/>'
                '<path d="M78 36V116M78 102L47 84V70M78 90L109 72V60" fill="none" stroke="{c}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>').replace('{c}', color)
    return NEW_SYMBOLS[name].replace('{c}', color)


# ---- USB logos (design handover "USB logos") ---------------------------------
# Orange glossy circle after the templates "Connected" / "Ejecting" (gradient
# measured from the template, light inner edge, soft shadow downwards as in
# the template, no reflection). On it the 30-pin connector 'dock' in black,
# scaled 0.78 about the centre (share of the circle as in the template) and
# 0.3 px higher, so that its horizontal edges sit on pixels.
# Ejected: an arrow pointing down instead of the cable, with a narrow gap
# under the neck as in the template.
USB_ORANGE = ('linear-gradient(180deg, #FFF7B4 0%, #FEEBA8 8%, #FFE08E 14%, #FFD36B 20%, #FFC04F 25%, '
              '#FFAE29 30%, #FE9900 34%, #FD8500 39%, #EB7200 45%, #E36500 52%, #DE5E00 60%, '
              '#DC6100 68%, #E76400 76%, #F16A00 85%, #F17400 92%, #F58400 100%)')
USB_RIM = 'inset 0 0 0 1px rgba(255,190,80,.5)'
USB_SHADOW = '0 2px 6px rgba(0,0,0,.5)'
USB_PAD = (6, 4, 6, 8)        # room for the shadow: left, top, right, bottom
USB_CONNECTOR = '#000000'
DOCK_CABLE = '<rect x="69" y="104" width="18" height="20" rx="2"/>'
DOCK_ARROW = '<rect x="69" y="109.5" width="18" height="17"/><path d="M60 126H96L78 144Z"/>'


def usb_logo_symbol(ejected=False, mid='usbm'):
    """Connector for the USB logo (viewBox 0 0 156 156), cable or arrow."""
    s = (NEW_SYMBOLS['dock'].replace('{c}', USB_CONNECTOR)
         .replace('id="dockm"', 'id="%s"' % mid).replace('url(#dockm)', 'url(#%s)' % mid))
    if ejected:
        assert DOCK_CABLE in s
        s = s.replace(DOCK_CABLE, DOCK_ARROW)
    return '<g transform="translate(78 77.47) scale(.78) translate(-78 -78)">%s</g>' % s


# ---- status bar in USB mode (design handover "status bar USB") ---------------
# black like RetailOS (measured from the template), light title (fork:
# centred), light spinner and white lock. The battery stays the theme's,
# no light copy.
# 21 px gradient, template #26292C -> #101213; the end values lie on RGB565
# steps and keep blue exactly one step above red in every row (no colour band)
STATUS_DARK = ('#292C31', '#101018')
STATUS_DARK_LINE = '#000000'             # 1 px below
TEXT_STATUS_LIGHT = '#EEF3F5'
ICON_LIGHT = '#E6EAF0'
# monochrome battery like the RetailOS template (measured from the template):
# light outline, 1 px dark gap all round, light grey fill with a darker
# bottom row; bolt and plug dark with a light edge. Used by the theme on the
# USB screens (design handover "battery monochrome")
BATT_MONO = {'outline': '#E4E4E4', 'gap': '#141414', 'pole': '#D2D2D2',
             'fill': 'linear-gradient(180deg,#E0E0E0 0%,#D2D2D2 25%,#C9C9C9 55%,#D0D0D0 85%,#9A9A9A 100%)',
             'symbol': '#1A1A1A', 'symbol_edge': 'rgba(255,255,255,.75)'}
