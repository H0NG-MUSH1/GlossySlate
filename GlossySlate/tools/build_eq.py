"""Parts of the graphical equaliser (DESIGN.md 5.13):

    python3 tools/build_eq.py

tools/eq/*.bmp are the parts of the designer's boards "Graphical EQ" (32 bit
with alpha, made by the design's own tools). The core draws them while the
screen is open (apps/menus/eq_menu.c, eq_menu_graphical()), from
.rockbox/wps/<status bar skin>/eq/, in the plugin buffer.

Written there dithered to RGB565 at their place on the screen, the capsule
middles widened to 4 px (build_tempo.write_parts()). Pure Python.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_tempo import write_parts  # noqa: E402

SRC = os.path.join(HERE, 'eq')
OUT = 'eq'                        # below .rockbox/wps/glossyslate/

# name: place on the screen (top left), the anchor of the dither; parts that
# repeat per band are given for band 0
PARTS = {
    'capsule_left': (14, 14), 'capsule_middle': (26, 14), 'capsule_right': (132, 14),
    'capsule_active_left': (14, 14), 'capsule_active_middle': (26, 14),
    'capsule_active_right': (105, 14),
    'icon_low_shelf': (25, 20), 'icon_peak': (25, 20), 'icon_high_shelf': (25, 20),
    'icon_low_shelf_white': (25, 20), 'icon_peak_white': (25, 20),
    'icon_high_shelf_white': (25, 20),
    'key_back': (282, 14), 'divider': (14, 46), 'zero_line': (14, 104),
    'band_selected': (15, 52), 'fader_track': (24, 60), 'fader_fill': (24, 60),
    'knob': (19, 89), 'key': (13, 180), 'key_active': (13, 180),
}


def main():
    write_parts(SRC, OUT, PARTS)


if __name__ == '__main__':
    main()
