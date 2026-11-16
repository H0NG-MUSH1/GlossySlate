"""Tiny Rockbox skin simulator for previews.

Implements the subset of the skin language the Glossy Slate skins use and
mimics the parts of the firmware renderer that matter for layout:
  * %VB viewports draw into a backdrop; foreground text lines first restore
    the backdrop under the whole line (write_line + STYLE_DEFAULT)
  * images and album art are drawn after the text of their viewport
  * fonts are the real .fnt files, bitmaps the real .bmp files
Not a replacement for testing on the device.
"""
import os, re, struct
from PIL import Image
import numpy as np
from tools.fntread import load as load_font
from tools.bmpread import read as read_bmp

TAGS = sorted(set('''ac al ar s t Vf Vb VB Vd VI Vi Vl V xd xl dr Cl Cd C Fl wd we mp mh mv lh bl bp bc
ps mm cs St Sx Sv LT Lt LR LN Lc LV Lo Lb Mc Vs Vg if and or cu cw cd ce cm cY cy cH ck cl cI cM cS cf ca cb cD cP cp
it ia id iA ig in fn fm fp fc fk ff fb pc pr pt pe pp pv pb d ss bs QT'''.split()), key=lambda t: -len(t))


# ------------------------------------------------------------------ parser
def parse_params(s, i):
    """s[i] == '(' -> (list of raw param strings, index after ')')."""
    depth, cur, out = 0, '', []
    i += 1
    while i < len(s):
        ch = s[i]
        if ch == '(':
            depth += 1
        elif ch == ')':
            if depth == 0:
                out.append(cur)
                return [p.strip() for p in out], i + 1
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur)
            cur = ''
        else:
            cur += ch
        i += 1
    raise ValueError('unclosed (')


def parse_tag(s, i):
    """s[i] is the first char after '%'. Returns (('tag', name, params), i)."""
    for t in TAGS:
        if s.startswith(t, i):
            j = i + len(t)
            params = None
            if j < len(s) and s[j] == '(':
                params, j = parse_params(s, j)
            return ('tag', t, params), j
    # escaped characters
    if s[i] in '%<>|;#,()?':
        return ('text', s[i]), i + 1
    raise ValueError('unknown tag at %r' % s[i:i + 12])


def parse_seq(s, i, stops):
    """Parse elements until one of stops (at depth 0). Returns (list, i)."""
    out, text = [], ''
    while i < len(s) and s[i] not in stops:
        ch = s[i]
        if ch == '%':
            if text:
                out.append(('text', text)); text = ''
            if s[i + 1] == '?':
                tag, j = parse_tag(s, i + 2)
                assert s[j] == '<', s[j:j + 20]
                opts = []
                j += 1
                while True:
                    seq, j = parse_seq(s, j, '|>')
                    opts.append(seq)
                    if s[j] == '>':
                        j += 1
                        break
                    j += 1
                out.append(('cond', tag, opts))
                i = j
            else:
                el, i = parse_tag(s, i + 1)
                out.append(el)
        else:
            text += ch
            i += 1
    if text:
        out.append(('text', text))
    return out, i


def parse_skin(src):
    vps = []          # list of dicts
    cur = {'kind': 'default', 'label': None, 'x': 0, 'y': 0, 'w': 320, 'h': 240, 'font': 1, 'lines': [], 'bg': False}
    vps.append(cur)
    for raw in src.split('\n'):
        if raw.startswith('#') or not raw.strip():
            continue
        line = raw
        m = re.match(r'%(Vl|Vi|V)\(', line)
        if m:
            params, j = parse_params(line, m.end() - 1)
            kind = m.group(1)
            if kind in ('Vl', 'Vi'):
                label, params = params[0], params[1:]
            else:
                label = None
            x, y, w, h, f = (params + ['-'] * 5)[:5]
            cur = {'kind': kind, 'label': label, 'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h),
                   'font': 1 if f in ('-', '') else int(f), 'lines': [], 'bg': False, 'fg': None}
            vps.append(cur)
            line = line[j:]
            if not line:
                continue
        seq, i = parse_seq(line, 0, '')
        # viewport-level tags on the declaration line
        cur['lines'].append(seq)
    return vps


# ------------------------------------------------------------------ evaluation
class Ctx:
    def __init__(self, state, sx):
        self.s = state
        self.sx = sx            # english -> localised

    def val(self, tag):
        """(text, intval or None) for a tag element."""
        _, name, p = tag
        s = self.s
        if name == 'Sx':
            return self.sx.get(p[0], p[0].split('@')[0]), None
        if name == 'Sv':                       # fork: value of a setting as its list shows it
            return s.get('setting_values', {}).get(p[0], ''), None
        if name == 'Mc':                       # fork: counts for the main menu sidebar
            v = s.get('counts', {}).get(p[0], '')
            return str(v), (int(v) if str(v) else None)
        if name == 'cD':                       # fork: date in the words of the language
            return s.get('date', {}).get(p[0], ''), None
        if name in ('bs', 'QT'):               # sleep timer, quick menu marker
            return s.get('text', {}).get(name, ''), None
        if name == 'St':
            return str(s['settings'].get(p[0], '')), None
        if name in ('if', 'and', 'or'):
            return ('1' if self.logic(tag) else ''), None
        if name in ('LT', 'Lt'):
            return s.get(name, ''), None
        if name == 'Lc':
            return ('1' if s.get('_lc') else ''), None
        if name == 'LV':                       # fork: value of a switchable entry
            return s.get('LV', ''), None
        if name == 'Lo':                       # fork: entry opens a level
            return ('o' if s.get('Lo') else ''), None
        if name == 'mh':
            return ('h' if s.get('mh') else ''), None
        if name in ('lh', 'bp', 'bc', 'C', 'ps', 'mv'):
            return ('1' if s.get(name) else ''), None
        if name == 'mp':
            return str(s.get('mp', 1)), s.get('mp', 1)
        if name == 'mm':
            return str(s.get('mm', 0)), s.get('mm', 0) + 1
        if name == 'cs':
            return str(s['cs']), s['cs']
        if name == 'bl':
            return str(s.get('bl', 80)), None
        t = s['time']
        rtc = {'cH': ('%02d' % t[0], t[0]), 'ck': (str(t[0]), t[0]), 'cM': ('%02d' % t[1], t[1]),
               'cl': (str(t[0] % 12 or 12), t[0] % 12 or 12), 'cd': ('%02d' % t[3], t[3]), 'ce': ('%2d' % t[3], t[3]),
               'cm': ('%02d' % t[4], t[4]), 'cY': (str(t[5]), t[5]), 'cu': (str(t[2]), t[2]),
               'cf': ('24', 1)}
        if name in rtc:
            return rtc[name]
        if name in s.get('text', {}):
            v = s['text'][name]
            return v, None
        return '', None

    def logic(self, tag):
        _, name, p = tag
        if name == 'if':
            a = self.render_param(p[0])
            op = p[1]
            b = self.render_param(p[2])
            try:
                fa, fb = float(a), float(b)
                return {'=': fa == fb, '!=': fa != fb, '<': fa < fb, '<=': fa <= fb, '>': fa > fb, '>=': fa >= fb}[op]
            except ValueError:
                return {'=': a == b, '!=': a != b}.get(op, False)
        if name in ('and', 'or'):
            # like skin_tokens.c: any tag counts as true when its text is not empty
            vals = []
            for q in p:
                t = parse_tag(q[1:], 0)[0]
                vals.append(self.logic(t) if t[1] in ('if', 'and', 'or') else bool(self.val(t)[0]))
            return all(vals) if name == 'and' else any(vals)

    def render_param(self, raw):
        if raw.startswith('%'):
            seq, _ = parse_seq(raw, 0, '')
            out = ''
            for el in seq:
                if el[0] == 'text':
                    out += el[1]
                elif el[0] == 'tag':
                    out += self.val(el)[0]
            return out
        return raw

    def pick(self, cond_tag, nopts):
        text, iv = self.val(cond_tag)
        if cond_tag[1] in ('if', 'and', 'or') or iv is None:
            truth = bool(text)
            if nopts == 1:
                return 0 if truth else None
            return 0 if truth else nopts - 1
        if iv < 1 or iv > nopts:
            iv = nopts
        return iv - 1


class Sim:
    def __init__(self, skin_path, bmpdir, fontdir, ui_font, sx):
        self.vps = parse_skin(open(skin_path, encoding='utf-8').read())
        self.bmpdir, self.fontdir = bmpdir, fontdir
        self.fonts = {1: load_font(os.path.join(fontdir, ui_font))}
        self.images = {}
        self.sx = sx
        self.cl = None
        for vp in self.vps:
            for seq in vp['lines']:
                for el in seq:
                    if el[0] == 'tag' and el[1] == 'Fl':
                        self.fonts[int(el[2][0])] = load_font(os.path.join(fontdir, el[2][1]))
                    if el[0] == 'tag' and el[1] == 'xl':
                        p = el[2]
                        im = read_bmp(os.path.join(bmpdir, p[1]))
                        n = int(p[4]) if len(p) > 4 else 1
                        self.images[p[0]] = (im, int(p[2]) if len(p) > 2 else 0, int(p[3]) if len(p) > 3 else 0, n)
                    if el[0] == 'tag' and el[1] == 'Cl':
                        self.cl = [int(v) for v in el[2][:4]]

    # --- drawing helpers
    def glyph(self, font, cp):
        f = font
        i = cp - f['first']
        if i < 0 or i >= f['size']:
            i = f['default'] - f['first']
        w = f['wids'][i]
        o = f['offs'][i]
        h = f['h']
        a = np.zeros((h, w))
        bits = f['bits']
        for n in range(h * w):
            b = bits[o + n // 2]
            v = (b >> 4) if (n & 1) else (b & 15)
            a[n // w, n % w] = (15 - v) / 15.0
        return a

    def text_width(self, font, s):
        return sum(font['wids'][(ord(c) - font['first']) if 0 <= ord(c) - font['first'] < font['size'] else font['default'] - font['first']] for c in s)

    def draw_text(self, canvas, x, y, s, font, color, clip):
        cx0, cy0, cx1, cy1 = clip
        col = np.array(color, dtype=float)
        for ch in s:
            a = self.glyph(font, ord(ch))
            h, w = a.shape
            for yy in range(h):
                py = y + yy
                if py < cy0 or py >= cy1:
                    continue
                for xx in range(w):
                    px = x + xx
                    if px < cx0 or px >= cx1 or a[yy, xx] <= 0:
                        continue
                    canvas[py, px] = canvas[py, px] * (1 - a[yy, xx]) + col * a[yy, xx]
            x += w

    def blit(self, canvas, im, x, y, clip):
        arr = np.asarray(im, dtype=float)
        cx0, cy0, cx1, cy1 = clip
        h, w = arr.shape[:2]
        for yy in range(h):
            py = y + yy
            if py < cy0 or py >= cy1:
                continue
            for xx in range(w):
                px = x + xx
                if px < cx0 or px >= cx1:
                    continue
                a = arr[yy, xx, 3] / 255.0
                if a <= 0:
                    continue
                canvas[py, px] = canvas[py, px] * (1 - a) + arr[yy, xx, :3] * a

    def subimage(self, label, n):
        im, x, y, cnt = self.images[label]
        h = im.height // cnt
        n = max(0, min(cnt - 1, n))
        return im.crop((0, n * h, im.width, (n + 1) * h)), x, y

    # --- one viewport line
    def exec_seq(self, seq, ctx, st):
        for el in seq:
            if el[0] == 'text':
                if ';' in el[1]:            # sub-lines: preview the first one
                    st['buf'][st['align']] += el[1].split(';')[0]
                    return
                st['buf'][st['align']] += el[1]
            elif el[0] == 'cond':
                k = ctx.pick(el[1], len(el[2]))
                if k is not None:
                    self.exec_seq(el[2][k], ctx, st)
            else:
                _, name, p = el
                if name in ('xl', 'Vf', 'Vb', 'VB', 'Fl', 'Cl', 'we', 'wd', 'Vg'):
                    st['nobreak'] = True
                if name in ('al', 'ac', 'ar'):
                    st['align'] = name
                elif name == 'Vf':
                    st['fg'] = tuple(int(p[0][i:i + 2], 16) for i in (0, 2, 4))
                elif name == 'VB':
                    st['vp']['bg'] = True
                elif name == 'Vd':
                    st['show'].add(p[0])
                elif name == 'VI':
                    st['ui'] = p[0]
                elif name == 'Lb':
                    st.setdefault('lbh', {})['v'] = (p[0], int(p[1]), int(p[2]))
                elif name == 'Vs':
                    st['style'] = p[0]
                elif name == 'Vg':
                    hx = lambda v: tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
                    st['grad'] = (hx(p[0]), hx(p[1]), hx(p[2]) if len(p) > 2 else None)
                elif name == 'dr':
                    x, y, w, h = [int(v) for v in p[:4]]
                    c0 = tuple(int(p[4][i:i + 2], 16) for i in (0, 2, 4))
                    c1 = tuple(int(p[5][i:i + 2], 16) for i in (0, 2, 4)) if len(p) > 5 else c0
                    st['ops'].append(('dr', x, y, w, h, c0, c1))
                elif name == 'xd':
                    label = p[0]
                    if len(p) == 1:
                        n = 0
                    elif p[1].startswith('%'):
                        tag = parse_tag(p[1][1:], 0)[0]
                        cnt = self.images[label][3]
                        if tag[1] == 'bl':
                            n = (cnt - 2) * ctx.s.get('bl', 80) // 100 + 2 - 1
                        else:
                            txt, iv = ctx.val(tag)
                            n = (iv - 1) if iv is not None else (0 if txt else 1)
                    else:
                        n = int(p[1]) - 1
                    st['imgs'].append((label, n))
                elif name == 'Cd':
                    st['art'] = ('fx', p)              # fork: optional effect params
                elif name in ('pb', 'pv') and p:
                    st['ops'].append((name, p))
                elif name in ('s', 't', 'Fl', 'xl', 'Cl', 'wd', 'Vb'):
                    pass
                else:
                    st['buf'][st['align']] += ctx.val(el)[0]

    def render(self, state, list_items=None, art=None):
        ctx = Ctx(state, self.sx)
        back = np.zeros((240, 320, 3)) + 255
        # pass 1: logic (default viewport + 1x1 logic viewport + unlabeled)
        show, ui, lbh = set(), None, {}
        for vp in self.vps:
            if vp['kind'] in ('default', 'V'):
                for seq in vp['lines']:
                    st = {'buf': {'al': '', 'ac': '', 'ar': ''}, 'align': 'al', 'fg': None, 'vp': vp,
                          'show': show, 'ui': ui, 'ops': [], 'imgs': [], 'art': False, 'lbh': lbh}
                    self.exec_seq(seq, ctx, st)
                    ui = st['ui']
        # pass 2: backdrop viewports, then foreground
        layers = [v for v in self.vps if v['kind'] == 'Vl' and v['label'] in show]
        fg_canvas = None
        for want_bg in (True, False):
            if not want_bg:
                fg_canvas = back.copy()
                if ui and list_items:
                    if lbh.get('v'):
                        self.draw_skinned_list(fg_canvas, ui, list_items, state, lbh['v'])
                    else:
                        self.draw_list(fg_canvas, back, ui, list_items, state)
            for vp in layers:
                st = {'buf': {'al': '', 'ac': '', 'ar': ''}, 'align': 'al', 'fg': (13, 15, 19), 'vp': vp,
                      'show': set(), 'ui': None, 'ops': [], 'imgs': [], 'art': False}
                is_bg = any(el[0] == 'tag' and el[1] == 'VB' for seq in vp['lines'] for el in seq)
                if is_bg != want_bg:
                    continue
                canvas = back if want_bg else fg_canvas
                clip = (vp['x'], vp['y'], vp['x'] + vp['w'], vp['y'] + vp['h'])
                font = self.fonts[vp['font']]
                fg = (13, 15, 19)
                line_no = 0
                for ln, seq in enumerate(vp['lines']):
                    st.update(buf={'al': '', 'ac': '', 'ar': ''}, align='al', ops=[], nobreak=False)
                    self.exec_seq(seq, ctx, st)
                    fg = st['fg'] or fg
                    for op in st['ops']:
                        self.do_op(canvas, vp, op, clip, state)
                    if any(st['buf'].values()):
                        line_y = vp['y'] + line_no * font['h']
                        if not want_bg:   # restore backdrop under the line
                            y0, y1 = max(line_y, clip[1]), min(line_y + font['h'], clip[3])
                            canvas[y0:y1, clip[0]:clip[2]] = back[y0:y1, clip[0]:clip[2]]
                        for al, s in st['buf'].items():
                            if not s:
                                continue
                            w = self.text_width(font, s)
                            x = vp['x'] + {'al': 0, 'ac': (vp['w'] - w) // 2, 'ar': vp['w'] - w}[al]
                            self.draw_text(canvas, max(x, vp['x']), line_y, s, font, fg, clip)
                    if not st['nobreak']:
                        line_no += 1
                if st['art'] and art is not None and self.cl:
                    self.draw_art(canvas, art, vp, st['art'][1], clip)
                for label, n in st['imgs']:
                    im, x, y = self.subimage(label, n)
                    self.blit(canvas, im, vp['x'] + x, vp['y'] + y, clip)
        return Image.fromarray(fg_canvas.clip(0, 255).astype(np.uint8))

    def line_no(self, vp, ln):
        # the declaration line holds tags only; lines after it are numbered
        # from 0 the same way Rockbox counts text lines in the viewport
        return max(0, ln - 1) if len(vp['lines']) > 1 and not self._has_text(vp['lines'][0]) else ln

    @staticmethod
    def _has_text(seq):
        return any(el[0] in ('text', 'cond') or (el[0] == 'tag' and el[1] not in ('Vf', 'VB', 'Vb', 'xd', 'dr', 's', 'al', 'ac', 'ar', 'Cd'))
                   for el in seq)

    def do_op(self, canvas, vp, op, clip, state):
        if op[0] == 'dr':
            _, x, y, w, h, c0, c1 = op
            for i in range(h):
                t = i / max(1, h)
                c = np.array(c0) * (1 - t) + np.array(c1) * t
                y0 = vp['y'] + y + i
                if clip[1] <= y0 < clip[3]:
                    x0, x1 = max(clip[0], vp['x'] + x), min(clip[2], vp['x'] + x + w)
                    canvas[y0, x0:x1] = c
        else:
            name, p = op
            x, y, w, h = [int(v) for v in p[:4]]
            frac = state.get('progress', .33) if name == 'pb' else state.get('volume', .6)
            fill = read_bmp(os.path.join(self.bmpdir, p[4]))
            slider = None
            if 'slider' in p:
                slider = self.images[p[p.index('slider') + 1]][0]
            sw = slider.width if slider else 0
            n = int((w - sw) * frac)
            self.blit(canvas, fill.crop((0, 0, n, fill.height)), vp['x'] + x, vp['y'] + y, clip)
            if slider:
                self.blit(canvas, slider, vp['x'] + x + n, vp['y'] + y, clip)


    # --- fork features ---------------------------------------------------
    CFG = {'start': (0x58, 0x96, 0xE6), 'end': (0x1A, 0x55, 0xBE), 'text': (255, 255, 255),
           'top': (0x35, 0x77, 0xD9), 'bottom': (0x21, 0x60, 0xCB), 'edge': (0x17, 0x4A, 0x9E),
           'secondary': (0x5B, 0x63, 0x71), 'arrow': (0x1D, 0x28, 0x47), 'inset': 8, 'arrows': True}

    @classmethod
    def gloss(cls, h, start=None, end=None):
        """Rows of the fork's gloss bar: start -> 45 % -> 55 % -> end, first
        row 38 % towards white, last row in the edge colour."""
        c = cls.CFG
        start = np.array(start or c['start'], float)
        end = np.array(end or c['end'], float)
        top, bot = np.array(c['top'], float), np.array(c['bottom'], float)
        rows = []
        for i in range(h):
            t = (i + .5) / h
            if t < .45:
                col = start + (top - start) * (t / .45)
            elif t < .55:
                col = top + (bot - top) * ((t - .45) / .10)
            else:
                col = bot + (end - bot) * ((t - .55) / .45)
            rows.append(col)
        rows[0] = rows[0] + (255 - rows[0]) * .38
        rows[-1] = np.array(c['edge'], float)
        return np.array(rows)

    _chev = {}

    def chevron(self, color):
        """6 x 10 arrow, stroke 1.8 with round ends (drawn 8x and reduced)."""
        key = tuple(color)
        if key not in self._chev:
            from PIL import ImageDraw
            S = 8
            big = Image.new('L', (6 * S, 10 * S), 0)
            d = ImageDraw.Draw(big)
            pts = [(1 * S, 1 * S), (5 * S, 5 * S), (1 * S, 9 * S)]
            d.line(pts, fill=255, width=int(1.8 * S), joint='curve')
            for x, y in (pts[0], pts[2]):
                r = .9 * S
                d.ellipse((x - r, y - r, x + r, y + r), fill=255)
            a = big.resize((6, 10), Image.LANCZOS)
            im = Image.new('RGBA', (6, 10), tuple(color) + (0,))
            im.putalpha(a)
            self._chev[key] = im
        return self._chev[key]

    def draw_art(self, canvas, art, vp, params, clip):
        """%Cd: plain, or with the fork's effect (tools/albumart_fx.py)."""
        x, y, w, h = self.cl
        vals = [None if (v in ('', '-') or v is None) else int(v) for v in (params or [])] + [None] * 5
        tilt, persp, rh, ro, rad = vals[:5]
        cover = art.convert('RGB').resize((w, h), Image.LANCZOS)
        if not any(v for v in (tilt, rh, rad)):
            self.blit(canvas, cover.convert('RGBA'), vp['x'] + x, vp['y'] + y, clip)
            return
        from tools.albumart_fx import render_image
        im, mx, over = render_image(cover, tilt=tilt or 0, perspective=persp or 420,
                                    refl_height=rh or 0, refl_opacity=34 if ro is None else ro, radius=rad or 0)
        self.blit(canvas, im, vp['x'] + x - mx, vp['y'] + y - over, clip)

    def draw_list(self, canvas, back, ui, items, state):
        """Firmware list as the fork draws it: gloss bar over the full width,
        text from the edge inset, arrow (6 x 10, centre 12 px from the right)
        for entries that open a level, value right-aligned in the secondary
        colour, album rows with a 52 px cover and a second line."""
        c = self.CFG
        vp = next(v for v in self.vps if v['kind'] == 'Vi' and v['label'] == ui)
        if vp['w'] < 10:
            return
        font = self.fonts[1]
        rh = state.get('row_h', font['h'])
        right = vp['x'] + vp['w']
        inset = c['inset'] if vp['x'] == 0 else 0
        text_end = right - (21 if c['arrows'] else inset)
        y = vp['y']
        for text, sel, extra in items:
            extra = extra or {}
            if y + rh > vp['y'] + vp['h']:
                break
            cover_w = extra.get('cover_w', 0)
            x0 = vp['x'] + cover_w
            if sel:
                canvas[y:y + rh, x0:right] = self.gloss(rh)[:, None, :]
            fg = c['text'] if sel else (13, 15, 19)
            sub = c['text'] if sel else c['secondary']
            if 'cover' in extra:
                cov = extra['cover'].resize((cover_w, cover_w))
                self.blit(canvas, cov, vp['x'], y + (rh - cover_w) // 2, (vp['x'], y, right, y + rh))
                tx = x0 + 8
                ty = y + (rh - 2 * font['h']) // 2
                clip = (tx, y, text_end, y + rh)
                self.draw_text(canvas, tx, ty, text, font, fg, clip)
                self.draw_text(canvas, tx, ty + font['h'], extra.get('sub', ''), font, sub, clip)
            else:
                tx = vp['x'] + inset
                ty = y + (rh - font['h']) // 2
                val = extra.get('value', '')
                name_end = text_end
                if val:
                    vw = self.text_width(font, val)
                    self.draw_text(canvas, text_end - vw, ty, val, font, sub, (tx, y, text_end, y + rh))
                    name_end = text_end - vw - 8
                self.draw_text(canvas, tx, ty, text, font, fg, (tx, y, name_end, y + rh))
            if c['arrows'] and extra.get('arrow'):
                ch = self.chevron(c['text'] if sel else c['arrow'])
                self.blit(canvas, ch, right - 12 - 3, y + (rh - 10) // 2, (vp['x'], y, right, y + rh))
            y += rh
        if state.get('scrollknob'):
            ky, kh = state['scrollknob']
            x = right - 7
            canvas[vp['y'] + ky:vp['y'] + ky + kh, x:x + 5] = canvas[vp['y'] + ky:vp['y'] + ky + kh, x:x + 5] * (8 / 15)

    def draw_skinned_list(self, canvas, ui, items, state, lb):
        """%Lb: every viewport labelled like the list config is drawn per item,
        offset to the item's slot; lines are filled (clear or gradient)
        before their text, images come last (list-skinned.c order)."""
        parent = next(v for v in self.vps if v['kind'] == 'Vi' and v['label'] == ui)
        label, iw, ih = lb
        rows = [v for v in self.vps if v['kind'] == 'Vl' and v['label'] == label]
        canvas[parent['y']:parent['y'] + parent['h'], parent['x']:parent['x'] + parent['w']] = 255
        for n, (text, sel, extra) in enumerate(items):
            oy = parent['y'] + n * ih
            if oy + ih > parent['y'] + parent['h']:
                break
            st0 = dict(state, LT=text, _lc=sel, LV=(extra or {}).get('value', ''), Lo=(extra or {}).get('arrow', False))
            ctx = Ctx(st0, self.sx)
            for rv in rows:
                x0, y0 = parent['x'] + rv['x'], oy + rv['y']
                clip = (x0, y0, x0 + rv['w'], y0 + rv['h'])
                font = self.fonts[rv['font']]
                st = {'buf': {'al': '', 'ac': '', 'ar': ''}, 'align': 'al', 'fg': (13, 15, 19), 'vp': rv,
                      'show': set(), 'ui': None, 'ops': [], 'imgs': [], 'art': False}
                line_no = 0
                fg = (13, 15, 19)
                for seq in rv['lines']:
                    st.update(buf={'al': '', 'ac': '', 'ar': ''}, align='al', ops=[], nobreak=False,
                              style=None, grad=None)
                    self.exec_seq(seq, ctx, st)
                    fg = st['fg'] or fg
                    has_text_line = not all(el[0] == 'tag' and el[1] in ('Vf', 'Vb', 'VB') for el in seq)
                    if not has_text_line:
                        continue
                    ly = y0 + line_no * font['h']
                    ya, yb = max(ly, clip[1]), min(ly + font['h'], clip[3])
                    col = fg
                    if st.get('style') == 'gloss' and st.get('grad'):
                        c0, c1, tc = st['grad']
                        grows = self.gloss(font['h'], c0, c1)
                        for i in range(ya, yb):
                            canvas[i, clip[0]:clip[2]] = grows[i - ly]
                        col = tc or fg
                    elif st.get('style') == 'gradient' and st.get('grad'):
                        c0, c1, tc = st['grad']
                        for i in range(ya, yb):
                            t = (i - ly) / max(1, font['h'] - 1)
                            canvas[i, clip[0]:clip[2]] = np.array(c0) * (1 - t) + np.array(c1) * t
                        col = tc or fg
                    else:
                        canvas[ya:yb, clip[0]:clip[2]] = 255
                    for al, s in st['buf'].items():
                        if s:
                            w = self.text_width(font, s)
                            x = x0 + {'al': 0, 'ac': (rv['w'] - w) // 2, 'ar': rv['w'] - w}[al]
                            self.draw_text(canvas, max(x, x0), ly, s, font, col, clip)
                    if not st['nobreak']:
                        line_no += 1
                for lab, k in st['imgs']:
                    im, ix, iy = self.subimage(lab, k)
                    self.blit(canvas, im, x0 + ix, y0 + iy, clip)
