# Quick menu – parts

Single parts cut out of the boards "Quick menu" and "Quick menu · free
assignment" of the design canvas (accent blue), without text. They were
exported by the design's own tools, which are not part of this repository;
`build_quickmenu.py` only rearranges them into the theme's bitmaps.

- `bmp/`: the parts for Rockbox, 32 bit with alpha; `background.bmp` opaque
  with 24 bits (dithered).
- `parts.json`: the same list, machine readable.
- `overview.png`: all parts with their names (white parts are hard to see
  on the light chequerboard).

**Place** is the top left corner of the picture on the 320 × 240 screen,
rounded to whole pixels. Parts with a shadow are larger than the element by
the shadow; "element" gives the place and size without the shadow. Symbols
keep the box of their element so that they can swap places (shuffle and
repeat fit into both switches). Pairs that replace each other (switch
on/off, the two capsules) have the same margins.

## Parts

| File | Size | Place | Element | Note |
| --- | --- | --- | --- | --- |
| `background` | 320 × 240 | 0, 0 | – | field #F7F8FA → #EDEFF3 (55 %) → #DFE3E9, opaque (24 bit) |
| `capsule_battery` | 76 × 25 | 14, 14 | 76 × 24 at 14, 14 | capsule for the battery level, empty (holds mini_battery and text 13 px bold) |
| `capsule_timer` | 73 × 25 | 98, 14 | 73 × 24 at 98, 14 | capsule for the sleep timer, empty (holds icon_moon and text 13 px bold) |
| `mini_battery` | 18 × 9 | 25, 22 | 18 × 9 at 25, 22 | battery in the capsule, level as in the design (82 %) |
| `icon_moon` | 11 × 11 | 109, 20 | 11 × 11 at 109, 20 | sleep timer |
| `icon_lock` | 10 × 12 | 178, 20 | 10 × 12 at 178, 20 | key lock on |
| `button_back` | 24 × 25 | 282, 14 | 24 × 24 at 282, 14 | round "close" button with an arrow |
| `divider` | 292 × 2 | 14, 58 | 292 × 1 at 14, 58 | line #C9CFD8 with 1 px white below |
| `icon_volume` | 16 × 14 | 14, 75 | 16 × 14 at 14, 75 | volume |
| `icon_brightness` | 16 × 16 | 14, 110 | 16 × 16 at 14, 110 | brightness |
| `slider_track` | 210 × 10 | 40, 78 | 210 × 9 at 40, 78 | slider track without fill |
| `slider_fill` | 210 × 9 | 40, 78 | 210 × 9 at 40, 78 | fill over the full width; bar image for %pv/%pb |
| `slider_knob` | 20 × 20 | 160, 72 | 18 × 18 at 161, 72 | knob; its centre sits on the end of the fill |
| `switch_on` | 142 × 68 | 13, 148 | 140 × 66 at 14, 148 | switch on (accent blue), empty |
| `switch_off` | 142 × 68 | 165, 148 | 140 × 66 at 166, 148 | switch off, empty |
| `arrow_left_white` | 5 × 9 | 23, 177 | 5 × 9 at 23, 177 | arrow in the active switch (white 75 %) |
| `arrow_right_white` | 5 × 9 | 292, 177 | 5 × 9 at 292, 177 | as above, right |
| `arrow_left_grey` | 5 × 9 | 23, 177 | 5 × 9 at 23, 177 | arrow in the inactive switch |
| `arrow_right_grey` | 5 × 9 | 292, 177 | 5 × 9 at 292, 177 | arrow in the inactive switch |
| `icon_shuffle_white` | 22 × 16 | 73, 154 | 22 × 16 at 73, 154 | shuffle, on the active switch |
| `icon_shuffle_dark` | 22 × 16 | 73, 154 | 22 × 16 at 73, 154 | shuffle, on the inactive switch |
| `icon_repeat_white` | 22 × 16 | 225, 154 | 22 × 16 at 225, 154 | repeat, on the active switch |
| `icon_repeat_dark` | 22 × 16 | 225, 154 | 22 × 16 at 225, 154 | repeat, on the inactive switch |
| `capsule_left` | 12 × 25 | – | – | capsule in three parts: left end (radius 12) |
| `capsule_middle` | 1 × 25 | – | – | middle, 1 px wide, repeat as often as needed |
| `capsule_right` | 12 × 25 | – | – | right end |
| `mini_battery_levels` | 18 × 108 (12 frames) | – | – | 12 frames like status_battery.bmp: 1 unknown, 2–12 = 0 to 100 %; fill round(level × 14), red below 20 %, red frame at 0 % |

The variant "free assignment" (a button 128 × 42 and a direction cross) is
listed in `parts.json` but not used by the theme, and its pictures are not
in `bmp/`.

## Text (not as pictures, set with the theme's fonts)

The texts come from the language files: titles of their own
(`%Sx(Shuffle@quickmenu)`, `%Sx(Repeat@quickmenu)`; German "Zufall" and
"Wiederholen"), the values of the settings (`%Sx(On)`, …) and "Level" before
the brightness.

| Place | Font | Colour | Position |
| --- | --- | --- | --- |
| capsules (e.g. "82 %", "29:53") | 13 px bold (`16-GlossySlate-Bold13.fnt`) | `#2E3644` | 6 px after the symbol, vertically centred |
| value next to the slider ("−24 dB", "Level 9") | 12 px bold (`16-GlossySlate-Bold12.fnt`) | `#2E3644` | right-aligned, field of 46 px from x 260 |
| switch, title ("Shuffle") | 14 px bold (`24-GlossySlate-Bold14.fnt`) | on: white; off: `#2E3644` | centred below the symbol, 4 px apart |
| switch, value ("On") | 11 px bold (`14-GlossySlate-Bold11.fnt`) | on: white 88 %; off: `#5B6371` | centred below the title; the theme puts its line at y 187, 2 px lower than the board, so that the descenders of the title (g, p, y) stay visible |
| button "free assignment", label | 11 px bold | `#5B6371` | centred, top |
| button "free assignment", value | 14 px bold | `#14171C` | centred, 2 px below |

In the design the texts have a 1 px emboss (white under dark text, dark
blue over white text). Rockbox has no text shadows.

## Layout

- Top row y 14, height 24: battery capsule, timer capsule, lock (8 px
  apart each), back button right-aligned at x 282.
- Divider y 58 (variant "free assignment": y 56), x 14 to 306.
- Slider rows y 72 and y 108, height 20: symbol 16 wide, 10 apart, track
  210 wide from x 40, 10 apart, value. The fill starts at the left of the
  track, the knob sits with its centre on its end.
- Switches y 148, 140 × 66 each, 12 apart. Arrow 8 px from the edge,
  vertically centred (y 177): left in the left switch, right in the right
  one.
- Variant "free assignment": buttons 128 × 42 at (96, 68), (14, 118),
  (178, 118) and (96, 168); direction cross 32 × 32 at (144, 123).
- Accent: only blue was exported. For slate, pink and violet `switch_on` and
  `slider_fill` change (values in `DESIGN.md` 3.4).
