"""Reads the Rockbox language files (apps/lang/*.lang) for the previews.

The theme draws texts with %Sx(English text): the firmware looks the English
text up among the strings of english.lang and shows that phrase in the
current language. lookup() builds the same table here, and date() formats
the fork's %cD(long|short|weekday|month) like apps/gui/skin_engine/
skin_tokens.c does. Only an approximation of the firmware for previews:
of target specific strings the first one that is not "none" is taken.
"""
import os
import re

LANG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'apps', 'lang')


def read(name):
    """{phrase id: dest string} of apps/lang/<name>.lang"""
    out, cur, sec = {}, None, None
    for line in open(os.path.join(LANG_DIR, name + '.lang'), encoding='utf-8'):
        s = line.strip()
        if s == '<phrase>':
            cur = {'id': None, 'dest': []}
        elif s == '</phrase>':
            vals = [v for v in cur['dest'] if v != 'none']
            if cur['id'] and vals:
                out[cur['id']] = vals[0]
            cur = None
        elif cur is None:
            continue
        elif s.startswith('id:'):
            cur['id'] = s[3:].strip()
        elif s in ('<source>', '<dest>', '<voice>'):
            sec = s[1:-1]
        elif s.startswith('</'):
            sec = None
        elif sec == 'dest':
            m = re.match(r'([^:]+):\s*(.*)$', s)
            if m:
                v = m.group(2)
                if v.startswith('"') and v.endswith('"'):
                    v = v[1:-1].lstrip('~')
                cur['dest'].append(v)
    return out


class Language:
    def __init__(self, name):
        self.english = read('english')
        self.strings = read(name) if name != 'english' else dict(self.english)

    def str(self, pid):
        return self.strings.get(pid) or self.english.get(pid, '')

    def lookup(self):
        """{English text: text in this language}, as %Sx resolves it (the
        first phrase with that English text wins). Like the firmware, only
        the part before '@' is shown ("Shuffle@quickmenu" -> "Shuffle")."""
        table = {}
        for pid, en in self.english.items():
            if en and en not in table:
                table[en] = self.str(pid).split('@')[0]
        return table

    def date(self, weekday, day, month, year):
        """%cD texts for a date; weekday 0 = Sunday, month 1-12."""
        days = ('SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY')
        months = ('JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST',
                  'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER')
        parts = {'weekday': self.str('LANG_WEEKDAY_FULL_' + days[weekday]),
                 'wd': self.str('LANG_WEEKDAY_' + days[weekday]),
                 'day': str(day),
                 'month': self.str('LANG_MONTH_FULL_' + months[month - 1]),
                 'mon': self.str('LANG_MONTH_' + months[month - 1]),
                 'year': str(year)}

        def fmt(pid):
            return re.sub(r'\{(\w+)\}', lambda m: parts.get(m.group(1), m.group(0)), self.str(pid))

        upper = parts['mon'].upper()
        return {'long': fmt('LANG_DATE_FORMAT_LONG'), 'short': fmt('LANG_DATE_FORMAT_SHORT'),
                'weekday': parts['weekday'], 'month': upper}
