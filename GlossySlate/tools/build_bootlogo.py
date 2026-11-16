"""Boot screen of the iPod 6G, dithered to RGB565:

    python3 tools/build_bootlogo.py

firmware-assets/rockboxlogo_320x240.png is the boot screen in full colour
(the blue field of the sidebar with the Rockbox logo, 320 x 240). The build
turns apps/bitmaps/native/rockboxlogo.320x240x16.bmp into RGB565 with
tools/bmp2rb, which cuts every channel to 5/6/5 bits without a dither: on
the gradient red, green and blue then step at different places, and fine
coloured lines run along it. The sidebar (sidebar.bmp) and the USB screen
(%dr, dithered by the fork) do not show them.

This script writes the BMP already dithered, with the 4 x 4 ordered dither of
the theme (tools/bmp.py), and with 8 bit values that bmp2rb's truncation
turns back into exactly the dithered RGB565 values. The picture fills the
screen from 0,0 (apps/main.c, show_logo_boot()), so the dither is anchored to
the screen like that of the skins. Needs Pillow.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tools.bmp import write_bmp24  # noqa: E402

GS = os.path.dirname(HERE)
SRC = os.path.join(GS, 'firmware-assets', 'rockboxlogo_320x240.png')
OUT = os.path.join(os.path.dirname(GS), 'apps', 'bitmaps', 'native', 'rockboxlogo.320x240x16.bmp')


def main():
    im = Image.open(SRC).convert('RGB')
    assert im.size == (320, 240), 'the boot screen fills the display: 320 x 240'
    write_bmp24(im, OUT, dither=True)
    # what bmp2rb makes of it must be the dithered RGB565 value itself
    px = Image.open(OUT).convert('RGB').load()
    for y in range(240):
        for x in range(320):
            r, g, b = px[x, y]
            for v, bits in ((r, 5), (g, 6), (b, 5)):
                n = v >> (8 - bits)
                assert round(n * 255.0 / ((1 << bits) - 1)) == v, (x, y)
    print('rockboxlogo.320x240x16.bmp: 320 x 240, dithered to RGB565')


if __name__ == '__main__':
    main()
