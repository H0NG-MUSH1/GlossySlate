# Glossy Slate – design specification

Rockbox theme for the iPod Classic 6G/7G (own fork, 320 × 240 pixels,
RGB565). It grew out of adwaitapod and is refined in the design language of
Apple's RetailOS (data sheet "Glossy Slate"). This document describes the
design so that it can be rebuilt 1:1 or extended with new elements in the
same style. All sizes in display pixels, all colours as hex values.

The values come from the Glossy Slate design canvas. Where the finished
theme deviates on purpose because Rockbox cannot do something, this is noted
in section 9 and in `ROCKBOX-CHANGES.md`.

State: theme 1.0 of 16 November 2026, built for the fork after its firmware
update (gloss bars, values and arrows in lists, tilted and mirrored covers),
with translatable texts since 12 November 2026.

---

## 1. Principles

- **Light only.** There is no dark theme. White lists on the left, a blue
  sidebar on the right, dark glossy tiles as picture carriers.
- **Glass and gloss, but calm.** Areas have soft vertical gradients.
  Highlighted elements (selection, tiles, clock box) carry a gloss edge in
  the middle: lighter at the top, clearly darker from about 50 %.
- **Two zones.** In menus the list is on the left (160 px), the sidebar on
  the right (160 px) with the title, tile and value of the selected entry.
  Only long lists (database, files, playlist), the now playing screen, the
  lock screen and USB mode use the full width.
- **One typeface.** A grotesque in the style of Helvetica (Arimo in the
  design, Rockbox fonts derived from it in the theme). Almost everything is
  bold; only the album line on the now playing screen and the calendar day
  are regular.
- **Symbols in one language.** All tile symbols lie in a 156 grid, have the
  same stroke widths and the same colour.
- **No ornament.** No frames around lists, no lines between rows, no
  shadows under text in lists.
- **Every word from the language.** The texts the theme draws itself come
  from the Rockbox language files (`%Sx`, `%cD`), so the theme follows the
  language set on the iPod.

---

## 2. Grid and basic sizes

| Element | Value |
| --- | --- |
| screen | 320 × 240 |
| status bar | area 0–21, line in row 21, height 22 |
| content area | from y 22, 218 high |
| list in menus | x 0–159, rows 24 high, 9 rows visible |
| sidebar | x 160–319, full height 240 (it also lies under the status bar) |
| full width list | x 0–319, rows 24 high |
| album row | 52 high (2 × 24 + 4), cover 52 × 52 |
| text padding | 8 on the left (`list edge inset`); with an arrow the text ends 21 before the right edge |
| corner radius | tiles 14, covers and clock box 8, pills 7, battery 2.5 |
| status symbol spacing | 4 between two symbols, 6 to the right edge |

---

## 3. Colours

### 3.1 Base colours

| Name | Hex | Use |
| --- | --- | --- |
| text | `#0D0F13` | list text, title on the now playing screen |
| status bar text | `#14171C` | title in the status bar |
| secondary | `#5B6371` | secondary information, "3 of 12", album line, help texts |
| dark symbol | `#2E3644` | lock, times, artist on the now playing screen |
| arrow | `#1D2847` | arrow at the end of the row (not selected) |
| value in the row | `#5677B0` | value on the right of list rows (not selected); `list value color` |
| white | `#FFFFFF` | background of lists, text on blue |
| second line on blue | `#DCE6F2` | artist/album below titles in the sidebar |
| light symbol | `#DFE6F3` | symbols on tiles, clock digits |
| bar | `#DDE2E9` | lower end of the status bar (up to 1.3) |
| line | `#1E1E1E` | line under the status bar (up to 1.3 `#9AA3B0`) |
| tile | `#07080C` | darkest tone of the tiles |
| tile edge | `#8E9CAE` | top light edge of the tiles |
| field top | `#B8D7F1` | top tone of the blue sidebar |
| field bottom | `#273B3F` | bottom tone of the blue sidebar |
| selection | `#2160CB` | solid colour of the accent (blue) |
| signal red | `#D9352F` | clock centre, recording dot |
| battery green | `#418522` | core tone of the battery fill |
| artist in the album list | `#5B6371` | second line of the album list (`list secondary color`) |

### 3.2 Gradients

All gradients run from top to bottom; percentages refer to the height of
the element.

| Name | Definition |
| --- | --- |
| status bar | from 1.4: `#FFFFFF` → `#979797` over rows 0–20, below it 1 px `#1E1E1E` (`%dr(0,0,w,21,ffffff,979797)`, `%dr(0,21,w,1,1e1e1e)`; up to 1.3 `#FFFFFF` → `#F2F4F7` 45 % → `#DDE2E9`, line `#9AA3B0`) |
| sidebar | three layers, see 3.3 |
| tile | `#8E9CAE 0–1 px`, `#778496 4 %`, `#606C79 14 %`, `#454F5B 24 %`, `#282E37 35 %`, `#151821 45 %`, `#0B0E14 50 %`, `#07080C 100 %` |
| black tile (album pictures) | `#4A525E 0–1 px`, `#2B3039 4 %`, `#1A1E25 40 %`, `#0B0E14 50 %`, `#07080C 100 %` |
| selection bar (blue) | `#5896E6 0 %` → `#3577D9 45 %` / `#2160CB 55 %` → `#1A55BE 100 %` |
| selection bar in the theme | as in the design: `selector type: bar (gloss)` in firmware lists, `%Vs(gloss)` in rows of the theme's own; top pixel row 38 % lighter towards white, bottom row in the edge colour `#174A9E` |
| now playing background | `#FFFFFF 0–58 %` → `#EBEEF2 100 %` |
| progress track | `#AEB6C1 0 %` → `#D5DAE1 40 %` → `#F1F3F6 100 %`, inner shadow 0 1 1.5 px black 28 %, 1 px white at the bottom |
| progress fill | `#8EC0F4 0 %` → `#5698E8 45 %` / `#2F70D6 55 %` → `#3D82E0 100 %`, 1 px white 45 % at the top, 1 px `rgba(0,20,70,.25)` at the bottom |
| battery fill | `#A9E38F 0 %`, `#D4F7BA 18 %`, `#7DBE5A 42 %`, `#418522 67 %`, `#4E9B2A 100 %` |
| battery fill below 20 % | `#F2A196 0 %`, `#FBD0C8 18 %`, `#E36A5A 42 %`, `#B8281C 67 %`, `#C63A2B 100 %` |
| battery case inside | `#46474B` → `#8F9396` |
| battery pole | `#9A9DA3` → `#5E6065` |
| pill | `#FFFFFF` → `#DCE1E8`, border 1 px `#AEB5C0` |
| default cover | `#F6F7F9` → `#E6EAEF`, note `#B8C0CB` |

### 3.3 The blue sidebar

Three layers on top of each other (top first):

1. **Inner shadow on the left** (only in the sidebar next to the list):
   horizontal, black 46 % at 0 px, 31 % at 6 px, 14 % at 12 px, 2 % at
   18 px, 0 % from 24 px.
2. **Diagonal darkening:** angle 137°, colour `rgb(10,16,32)` with opacity
   0 % → 12 % (20 %) → 23 % (40 %) → 40 % (60 %) → 66 % (80 %) → 100 %.
3. **Vertical base gradient:** `#B8D7F1` 0 px, `#9CCBF2` 40, `#A2CAF4` 80,
   `#87B4DA` 120, `#638DB2` 160, `#426792` 200, `#273B3F` 240.

The lock screen and USB mode use the same field over the whole width,
without the inner shadow.

### 3.4 Accent colours

The theme ships blue. The other three accents are planned in the design and
are made from the same five values.

| Accent | bar 0 % / 45 % / 55 % / 100 % | edge | light symbol | dark symbol |
| --- | --- | --- | --- | --- |
| blue | `#5896E6` `#3577D9` `#2160CB` `#1A55BE` | `#174A9E` | `#7DB4F0` | `#1F5FC8` |
| slate | `#8F9BAC` `#6E7C90` `#5A687C` `#4F5C6F` | `#3D4757` | `#A9B4C2` | `#56637A` |
| pink | `#EE8FB4` `#DA5A8D` `#C8427C` `#BB3A72` | `#97295A` | `#F5A9C6` | `#C13F78` |
| violet | `#A88EEC` `#8466DD` `#6E4FD0` `#6244C4` | `#4B3299` | `#BBA3F2` | `#6648C8` |

"Light symbol → dark symbol" is the gradient of the play symbol in the
status bar, the edge its 0.8 px outline. For another accent these change:
the `line selector` colours in the cfg (start, end, `gloss top`,
`gloss bottom`, `gloss edge`), `SEL` in `build_skin.py` (`%Vg` of the
theme's own rows), `status_play.bmp`, `wps_fill.bmp`, `wps_vfill.bmp`,
`wps_cap.bmp` and the active states in `wps_shuffle.bmp` and
`wps_repeat.bmp` (the dot of repeat "One": `ACCENT` in
`build_wps_repeat.py`).

---

## 4. Typography

### 4.1 Typeface

- Design: **Arimo** (metrically compatible with Helvetica and Arial).
- Theme: **GlossySlate Sans**, rendered from Liberation Sans 2.1.5 (the same
  metrics and drawing as Arimo), 4 bit anti-aliasing, licence SIL OFL 1.1
  (`.rockbox/fonts/GlossySlate-OFL.txt`). "Liberation" and "Arimo" are
  reserved font names and must not be used for derived fonts.
- Character set of the text fonts: Latin including Extended-A/B, Greek,
  Cyrillic, typographic punctuation, €, arrows, the minus sign.
- Rendered with Chromium like the mockups (`tools/tools/chromefont.py`,
  called by `build_fonts.py`), no longer with Pillow: the same shapes,
  spacing and smoothing as in the mockup. The integer advance widths are
  rounded per font so that German and English texts are as wide as in the
  mockup (deviation 0.2–2.6 %). The baseline of bold 13 and regular 13 is in
  row 12, of bold 17 in row 15 (before 13 and 16). So the titles of the
  status bar (`TitleHalf`, `TitleHalfL`, `TitleFull`, "Now playing" in the
  `.wps`) start at y 3.
- More styles of the mockups (regular 12, bold 9, regular 9, bold 14.5) are
  written by `build_fonts.py` to `out/GlossySlate/fonts-extra/`; the theme
  does not load them. The theme loads 10 fonts; with the UI font 11 of the
  12 places of Rockbox are taken, so every further font needs a place of
  its own.

### 4.2 Font sizes

| Role | Size | Style | Line height | Colour | Rockbox file |
| --- | --- | --- | --- | --- | --- |
| clock (lock screen) | 58 | bold, −1.5 spacing | 70 | `#DFE6F3` | `70-GlossySlate-Clock58.fnt` (digits and ":" only) |
| calendar day | 46 | regular, −1 spacing | 46 | `#0E1016` | `46-GlossySlate-Day46.fnt` (digits only) |
| sidebar title, now playing title, date | 17 | bold | 18–20 | white / `#0D0F13` | `20-GlossySlate-Bold17.fnt` |
| list row | 14 | bold | 24 | `#0D0F13`, selected white | `24-GlossySlate-Bold14.fnt` (UI font) |
| status bar, value in the sidebar, artist | 13 | bold | 16 | `#14171C` / white / `#2E3644` | `16-GlossySlate-Bold13.fnt` |
| album on the now playing screen | 13 | regular | 16 | `#5B6371` | `16-GlossySlate-Regular13.fnt` |
| times below the progress bar | 12 | bold | 16 | `#2E3644` | `16-GlossySlate-Bold12.fnt` |
| small: "3 of 12", second lines, weekday | 11 | bold | 14 | `#5B6371` / `#DCE6F2` | `14-GlossySlate-Bold11.fnt` |
| help text on option pages (design only) | 12 | regular | 16 | `#5B6371` | – |

The number in front of the file name is the height of the font in pixels in
Rockbox (the line height), not the font size.

### 4.3 Typesetting rules

- Titles in lists and bars left-aligned, centred in the sidebar.
- Long texts scroll (Rockbox scrolling text); they are not shortened with
  "…". Exception: if a value stands in the row, the firmware shortens the
  name in front of it (value 8 px after the name, right-aligned).
- Remaining time with a real minus sign (U+2212): "−2:18".
- Dates in the format of the language: the fork's tag `%cD` fills the date
  formats of the language files ("Monday, 9 November", "Montag,
  9. November", "lunes, 9 de noviembre"; short "9 Nov 2026", US "Nov 9,
  2026").
- Emboss: in the design text on blue has a shadow 0 1 px
  `rgba(4,10,24,.16–.38)`, text on the selection bar 0 −1 px
  `rgba(8,20,60,.45)` and the status bar title 0 1 px white 90 %. Rockbox
  has no text shadows; the theme leaves them out.

---

## 5. Components

### 5.1 Status bar

- Height 22, gradient and line as in 3.2. The same on every screen; USB mode
  has a black version (6.8). On the lock screen it is replaced by a lock at
  the top left and the battery at the top right, directly on the blue field.
- **Title** always left-aligned from x 8, 13 px bold `#14171C`. At half
  width (menus with the sidebar) 104 wide; 72 wide when the lock or the
  loading symbol is visible.
- **Symbols on the right**, from the outside in, 4 px apart, 6 px from the
  edge:

| Order | Symbol | Size | x (full width / half) | y | visible when |
| --- | --- | --- | --- | --- | --- |
| 1 | battery | 26 × 13 (body 24, pole 2) | 288 / 128 | 4 | always |
| 2 | play/pause | 8 × 10 | 276 / 116 | 5 | playing or paused |
| 3 | lock | 10 × 12 | 262 / 102 (without play 274 / 114) | 4 | key lock on |
| 4 | loading symbol | 14 × 14 | moves up, 4 px left of the last symbol | 4 | disk access |

- **Play** is a triangle with the accent gradient (`#7DB4F0` → `#1F5FC8`)
  and a 0.8 px outline `#174A9E`; pause two bars in the same style with a
  2 px gap, fast forward and rewind two triangles each in the same 8 × 10
  field.
- **Lock** `#2E3644`: shackle 1.6 px stroke, body 8.4 × 6.4, radius 1.2.
  White on blue.
- **Loading symbol** (spinner) after the template: 12 spokes, steps of 30°,
  one step every 0.1 s.
- **Battery**: case 1 px `#505153`, radius 2.5, fill width
  `round(level × 22)`, then a 1 px divider `#4E4F52`. Red below 20 %, frame
  and pole `#B02A1A` at 0 %. The states "charging" (bolt) and "charged"
  (plug) are pictures of their own.

### 5.2 List row

- Height 24, text 14 px bold from x 8, `#0D0F13`, white background.
- **Selected:** selection bar over the whole row width with the gloss
  gradient of the accent, 1 px light at the top (white 38 %), 1 px accent
  edge at the bottom, white text. In the theme the firmware draws the bar
  (`bar (gloss)`), square over the full width.
- **Arrow** at the end of the row for entries with a further level: 6 × 10,
  stroke 1.8, round ends, centre 12 px from the right edge, `#1D2847`,
  selected white. In the theme the firmware draws it (`list arrows: on`):
  folders, database entries except tracks, menu entries except settings that
  switch directly. Entries of plain choice lists have no arrow.
- **Value** instead of the arrow only for plain yes/no and on/off settings
  and for "Repeat" (Off/All/One …): right-aligned, 14 px bold, `#5677B0`,
  selected white 92 %. A click switches on, no sub page opens. All other
  settings (also second line, scroll bar and yes/no pairs with words of
  their own like Inverse/Normal) show the arrow and open their option page;
  a value in the row would push out the often long names. In the theme the
  firmware draws the value in `list value color`, selected white.
- **Speaker** at the end of the row of the track that is playing (paused
  too), in the database and the file browser: 14 × 12 with three sound
  waves, centre 12 px from the right edge, `#1D2847` like the arrow,
  selected white.
- **Blue dot** at unheard podcast episodes and audiobook chapters and at
  podcasts and audiobooks with unheard episodes: 8 px across, accent
  `#2160CB`, selected white; without an arrow 12 px from the right edge,
  next to the arrow 26 px. No mark on the left (see below).
- **Check mark** on option pages: 11 × 9, stroke 2, white, only in the
  selected row; the chosen option is the selected one.
- No dividers, no icons on the left.

### 5.3 Scroll bar

- A dark pill without a track over the list: 5 wide, 2 from the right edge
  of the list, 3 from the top and bottom, black 47 %, round ends (radius
  2.5).
- Length = visible / all rows × track height, position accordingly.
- Appears only while scrolling, stays 1 s, then fades out in 7 steps over
  350 ms. Freshly opened lists show no bar.
- The side follows the setting "Scroll Bar" (Off, Left, Right).

### 5.4 Sidebar

| Element | Position (relative to the sidebar, x 160) | Style |
| --- | --- | --- |
| title | centred, 150 wide from x 5, y 18 | 17 px bold white |
| tile | x 41, y 79, 78 × 78 | see 5.5 |
| reflection | directly below the tile, 35 high | mirrored tile, mask black 70 % → 0 |
| value | centred, y 202 | 13 px bold white |

Variants of the sidebar:

- **Mini player** (main menu, "Now Playing" selected): cover 100 × 100 at
  x 30, y 36, corners as set (rounded = radius 8), tilted as on the now
  playing screen (24°, perspective 420; picture 100 × 142 from y 33),
  reflection 36 high (60 % → 0). The matching default cover
  (`cover100_fx.bmp`) is computed by `build_wps_cover.py mini` with the same
  formula, opaque on the sidebar. In the design there is also an outline of
  1 px `rgba(4,10,24,.35)`, the theme has none (see 9). Below it the title
  13 px bold white (y 185) and the second line 11 px bold `#DCE6F2`
  (y 203). With "alternating" two dots 4 × 4 at y 222 (active white,
  inactive white 40 %).
- **Home page** (nothing playing): at the top at y 16 three small symbols
  (speaker, shuffle, repeat; active white, inactive white 45 %), below them
  an analogue clock 124 × 124 (light face, dark hands `#14161B`, centre
  6 × 6 red `#D9352F`), below it the weekday 11 px bold `#DCE6F2` (y 184,
  `%cD(weekday)`) and the date 17 px bold white (y 201, `%cD(short)`). The
  clock moves in minute steps, the hour hand moves along.
- **Calendar card** ("Time & Date"): card 100 × 90 at x 30, y 74, radius 14,
  gradient white → `#E6EDF7`, shadow 0 3.5 7 px black 45 %. A red header
  with the month in capitals 13 px bold white ("NOV", `%cD(month)`), the day
  46 px regular `#0E1016`. Value below: the date 17 px bold (`%cD(short)`).
- **Symbol without a tile** (main menu: music, podcasts, audiobooks,
  playlists, settings, system and "Now Playing" without playback): the symbol
  stands bare on the blue field in the place of the tile, without a tile and
  without a reflection; the title like every title. Music and "Now Playing"
  show the note (`note`), podcasts the rings (`podcast_rings`), audiobooks
  the book (`audiobook`), playlists `playlists`, settings `settings`, system
  `info`. Sizes and material in 5.11. The tile symbols (`podcast`, `book`,
  `playlist`, `gear`, `info`) stay in the tile font; entries without a
  symbol of their own still show `gear`.
- **Album art corners** (picture preview instead of a symbol): the default
  cover 78 × 78 in the place of the tile (x 41, y 79), corners as set
  (radius 8 or square), reflection 35 high (60 % → 0), no outline. Title
  "Album Art Corners", value "Rounded" / "Square". On the option page the
  preview shows the selected option.
- **Key lock** (picture preview instead of a symbol, from the board "Option ·
  Key lock"): a reduced screen 128 × 96 at x 16, y 62, radius 14, outline
  1 px `rgba(4,10,24,.45)`. The content is the respective screen at scale
  0.4: for "Normal" the now playing screen with the fictitious cover "Glass
  Harbour" and the lock in the status bar, for "Lock Screen" the clock box
  "20:51" and the title. Reflection 34 high (55 % → 0). The picture contains
  no words of the user interface (no screen title, no "3 of 12", no date),
  so it is the same in every language. In the settings menu the title is
  "Key Lock", the value the chosen option; on the option page the title is
  the selected option, the value "Screen unchanged" or "Clock and title".
  The preview is a fixed picture; it does not show the playing cover or the
  real time.
- **System** (sub menu "System"): the Glossy Slate logo tile 88 × 88 at
  x 36, y 51 (a dark glossy tile with three list rows, the middle one a blue
  selection bar with an arrow), without a reflection and without a title
  above it. Below it "Glossy Slate" 17 px bold white (y 151) and
  "Version 1.0" 13 px bold `#DCE6F2` (y 173; the word from the language,
  `%Sx(Version)`). The tile is a finished picture
  (`tools/sources/glossyslate_logo.png`, 480 × 480); `tools/build_system_logo.py`
  scales it down and puts it onto the sidebar, opaque and dithered
  (`system_logo.bmp`).

### 5.5 Tile

- 78 × 78 (sidebar), radius 14, tile gradient from 3.2. (Up to 1.3 also
  88 × 88 in USB mode; the orange logo stands there now, 6.8.) In the
  design the equaliser has a wide tile 130 × 78 with eight bars; in the
  theme the same picture is squeezed into the 78 tile.
- Symbol in `#DFE6F3`, drawn in a 156 × 156 grid and scaled to the tile
  size (78 = factor 0.5).
- Reflection as in 5.4.
- The three album pictures (special entries of the album list) are tiles
  without a radius on black ground (gradient "black tile") with blue symbols
  (`#7DB4F0` → `#3577D9` over y 26–130 of the grid).

### 5.6 Symbols

Grid 156 × 156, origin at the top left. Rules:

- **Lines** 8 wide, round ends and corners.
- **Arrows** (shuffle, repeat, off variants) 18 wide, blunt ends, arrow
  heads as filled triangles with a base of 48. Reset is a circular arrow of
  its own (see the table).
- **Areas** filled; cut-outs are punched out (mask), never painted over with
  the background colour.
- Content within about x 18–138 and y 16–140; optical centre at 78/78.
- Crossing lines (shuffle): the lower line is cut out with a 28 wide strip
  along the upper one.

| Name | Meaning | Detail |
| --- | --- | --- |
| `folder` | files | |
| `database` | database | |
| `gear` | settings | slim gear: base circle 44, tooth tips 57, hole 24 |
| `mic` | recording | |
| `radio` | radio | |
| `playlist` | playlists | the note redrawn after the owner's icon (17 November 2026): three lines of equal length, stem and lines equally strong (10), a straight flag, the head flush with the stem; a finished glyph (`tools/sources/tiles/playlist.png`) replacing the canvas one. The main menu shows the symbol without a tile (`playlists`, 5.11) |
| `plugins` | plugins | |
| `info` | system | |
| `podcast` | podcasts | a microphone of its own, stroke 8 |
| `book` | audiobooks | book after the template |
| `star` | shortcuts | |
| `bookmark` | bookmarks | |
| `play` | playback settings, now playing | triangle in a ring |
| `speaker` | volume | |
| `sun` | brightness | |
| `timer` | backlight | |
| `eq` | equaliser | bars |
| `shuffle` / `shuffleOff` | shuffle on / off | off = two parallel arrows |
| `repeatOff` / `repeat` / `repeatOne` | repeat off / all / one | off = one arrow; one = disc r 17 with a punched-out "1" at the top left at (30, 40) |
| `reset` | reset, manage settings | anticlockwise circular arrow: arc around (78, 78), radius 39.6, stroke 13, straight ends, from 12 o'clock over left, bottom, right to 45° top right (106, 50); head a triangle (122, 34), (90, 66), (90, 34), right angle at the top left, covering the end of the arc; dot r 10.5 in the middle. Corners of the head on even values, exactly on pixels in the 78 tile (state 1.5) |
| `calendar` | time & date (fallback) | the real picture is the calendar card |
| `art_round` / `art_square` | album art / album art corners | the theme uses only `art_round` (setting "Album Art"); the album art corners show a picture preview |
| `scroll_off` / `scroll_left` / `scroll_right` | scroll bar | |
| `lock` | key lock | design only; replaced by the picture preview in the theme (5.4) |
| `secondline` | second line | |
| `sliders` | general settings | |
| `brush` | theme settings | |
| `voice` | voice | |
| `logo` | theme sign (system) | concentric rings; since 1.0 the system sidebar shows the logo tile `system_logo.bmp` instead (5.4) |
| `usb` | USB mode | |

Symbols without a tile (5.11), in the 156 grid, stroke 6:

| Name | Meaning | Detail |
| --- | --- | --- |
| `note` | database (music), nothing playing | after the template: a double note with a slanted beam, heads 14.5 : 11 rotated by −14.5° |
| `podcast_rings` | podcasts | the podcast logo: a person (round head, tapering body) in four rings open at the bottom, the rings thinner further in; traced from the logo as filled outlines (no stroke), the same box as before (x 19–137, y 17–138) |
| `audiobook` | audiobooks | after the template: a book slanted from the front, the back cover as an L, the spine rolled in at the top; the gap between page and cover is cut out |
| `playlists` | playlists | three lines of equal length (stroke 9.5, round ends, 22 apart), on the right a note of the `note` family |
| `settings` | settings | a filled gear with 8 teeth, one tooth at the top; hub r 17 cut out |
| `info` | system | a filled disc r 60, the "i" cut out |
| `bookmarks` | Recent Bookmarks | a bookmark ribbon |

Their paths are in `tools/sym_pur.json` and as SVG in `tools/symbols/`.

**Tiles of the settings (RetailOS, 17 November 2026):** the 224 settings
that had no tile of their own (`SETTINGS-WITHOUT-TILE.md`, T001–T224) show
49 new motifs and 11 existing tiles: one motif for related settings, and
the entries of a sub menu show the tile of the entry that opens it, as the
original iPod firmware does. The motifs are finished glyphs from the
designer (`tools/sources/tiles/<name>.png`, 78 × 113, white with alpha),
put into the tile font at U+E022–U+E052 by `tools/build_tile_glyphs.py`
(with the speaker of Sound Settings/Volume at U+E00E and the playlist note
at U+E006). Revised on the evening of 17 November: bass and treble show the
speaker with a slow wave and with three quick waves (no clefs), the dynamic
range compressor and its entries the wave with an arrow from above and one
from below (the tile of the first delivery, the owner's wish), and
`audio_file` the new playlist note cut out of the sheet. On 18 November the
speaker of bass and treble moved to exactly the place of the speaker of
Sound Settings (before 8 units to the left), and the wave took the place of
its sound arcs (x 104–142): bass height ±20, stroke 8; treble height ±16,
stroke 5, so the three waves stay apart at 78 px. `setting_tiles()` in
`build_skin.py` assigns them by the menu text, with the value of the entry
(`%LV`) under the tile; `SUBMENU_TILES` gives entries without a fixed text
the tile of their sub menu (`%Lt`). The status bar skin grows to about
69 KB (4380 elements).

The paths of all tile symbols are in `tools/sym.json`,
`tools/sym_extra.json` and `tools/design.py` (`NEW_SYMBOLS`). Only the names
that `build_assets.py` lists go into the tile font.

### 5.7 Cover

| Place | Size | Corners | Effect | Frame |
| --- | --- | --- | --- | --- |
| album list | 52 × 52, without gaps one below the other, flush left | square | – | none |
| mini player (sidebar) | 100 × 100 | as set, rounded = radius 8 | reflection 36 high, 60 % | none (design 1 px `rgba(4,10,24,.35)`) |
| now playing | 116 × 116 | as set, rounded = radius 8 | tilted 24°, perspective 420, reflection 36 high, 34 % | none (design 1 px `rgba(13,15,19,.14)`) |
| album art corners preview | 78 × 78 | radius 8 / square | reflection 35 high, 60 % | none |

- **Default cover** for albums without a picture: a note after the template
  (double eighth note with a beam, position and size as in the original) in
  `#B8C0CB` on `#F6F7F9` → `#E6EAEF`. As a file square and without a border.
  For tracks without a cover it is shipped precomputed with the same effect
  for the now playing screen and the mini player (`cover116_fx.bmp`,
  `cover100_fx.bmp`; frame 1 rounded, frame 2 square). `cover100_fx.bmp` and
  the album art corners preview (`artprev.bmp`) are blended onto the
  sidebar, opaque and dithered (`tools/build_side_reflections.py`): with 16
  alpha steps their reflection showed broad bands. `tools/build_wps_cover.py`
  computes both covers with the geometry of the firmware's integer maths but
  with colours in full precision, and quantises to RGB565 only once, with a
  4 × 4 ordered dither. The grey ground of the cover spans only two or three
  RGB565 steps per channel; rounded per channel it fell into bands with a
  pink, bluish and (beside them) orange looking tint, most visible on the
  tilted display (fixed on 16 November 2026). `cover116_fx.bmp` is opaque
  too: cover and reflection are mixed with the ground of the now playing
  screen, which the fork draws dithered in a fixed pattern (white, from row
  139 the gradient to `#F4F6F8`); where the cover does not reach, the picture
  holds exactly those pixels. With alpha the firmware blended with
  truncation per channel, which left green dots in the reflection.
- **Special entries** of the album list: "[By Album]" (two sleeves, the
  front one with a black record), "[All Tracks]" (three lines and an eighth
  note), "[Shuffle]" (shuffle symbol).
- **Effect** (firmware of the fork, `%Cd(tilt,perspective,reflection
  height,opacity,corner radius)`): first the corners are rounded. Then the
  cover turns about its vertical centre axis; a positive tilt pushes the
  right edge back. For a column at the distance x from the centre,
  X = x · cos α · P / (P + x · sin α) and the vertical scale
  k = P / (P + x · sin α) (P = perspective). The reflection starts at the
  bottom edge of each column and runs linearly from the opacity to 0 over
  the reflection height. So the 116 cover of the now playing screen takes
  116 × 160 (4 px overhang at the top and bottom, 36 px reflection).
- Rebuilt outside the firmware (previews, default covers):
  `tools/tools/albumart_fx.py`, call
  `render_image(cover, tilt=24, perspective=420, refl_height=36,
  refl_opacity=34, radius=8)`.

### 5.8 Progress, volume, pills

- Progress: track 292 × 9 at x 14, y 200, radius 5; fill with the accent
  gloss; the end of the fill as a 10 px cap. The round left end of the fill
  (5 px) stands fixed in a viewport of its own (`wps_fill_l.bmp`), bar and
  cap start behind it (`wps_fill_r.bmp`); otherwise the straight left edge
  of the cap stood out of the rounding of the track in the first seconds.
  The volume the same way (`wps_vfill_l/_r.bmp`).
- Times below at y 214: elapsed on the left, remaining with "−" on the
  right, 12 px bold `#2E3644`. In the middle small shuffle and repeat
  symbols (14 × 10, active `#2160CB`, off `#A9B0BA`). Repeat "One" is the
  loop of "All" with a dot of 1.8 px radius at its top left corner and a
  gap of about 1 px to the loop, without a "1" (too small at 14 × 10; the
  quick menu shows the "1"); `build_wps_repeat.py` makes it.
- Volume (while it is being changed, 1.5 s): quiet speaker at x 14, track
  252 wide from x 34, loud speaker at x 292, centred below it "−24 dB". The
  volume is always shown graphically.
- Pills for format and sample rate: height 14, radius 7, border `#AEB5C0`,
  gradient white → `#DCE1E8`, text 11 px bold `#3B4350`. Format 44 wide,
  rate 56 wide, 4 apart.

### 5.9 Clocks

- **Digital** (lock screen): box 200 × 90, radius 8, tile gradient, digits
  58 px bold `#DFE6F3`, spacing −1.5, centred.
- **Analogue** (home page): face 124 × 124, light, with minute marks and the
  numbers 12/3/6/9, dark hands, red centre.

### 5.10 Quick menu

From the parts of the board "Quick menu" (`tools/quickmenu/`: pictures,
places in `parts.json`, rules in `README.md`):

- Field `#F7F8FA` → `#EDEFF3` (55 %) → `#DFE3E9`, in the theme as two `%dr`
  gradients (the fork dithers them), not as a picture.
- Top row y 14: battery capsule (76 × 24 at 14) with a mini battery by level
  (`qs_mini_bat.bmp`, 12 frames) and the level 13 px bold `#2E3644`, without
  a space before the sign ("82%"), left-aligned from x 47: with "100%" the
  sign ends 10 px before the capsule's right edge, as the battery begins 10
  px after its left edge (the board had "82 %" 6 px after the battery, and
  "100 %" ran up to 4 px before the edge); sleep timer
  capsule (73 × 24 at 98) with the moon at 109, 20 and 6 px behind it the
  time left or "Off" (`%Sx(Off)`); lock at 178, 20 only with the key lock
  on; back button at 282.
- Divider y 58, x 14–306.
- Sliders y 72 and 108: symbol at x 14, track 210 × 9 from x 40, y 78 / 114
  (lies in the backdrop). Without a knob, built like the progress bar of the
  now playing screen: a fixed round left end (`qs_fill_l.bmp`, 5 px), behind
  it the fill (`qs_fill_r.bmp`) and as the slider the round right end of the
  fill (`qs_cap.bmp`, 10 px), all from `slider_fill`. Value 12 px bold
  `#2E3644` right-aligned in 46 px from x 260 ("−24 dB", "Level 9").
- Switches 140 × 66 at 14 / 166, y 148 (picture 142 × 68 with the shadow):
  on in the accent with a white symbol, title white, value `#E4ECF8`; off
  light with a dark symbol, title `#2E3644`, value `#5B6371`. Symbol 22 × 16
  at the top centre (y 154), title 14 px bold 4 px below it, value 11 px
  bold below the title (line at y 187, so that it leaves the descenders of
  the title alone), arrow 8 px from the outer edge at y 177. The symbol
  follows the value as the tiles of the settings do: shuffle off two
  parallel arrows, on crossed; repeat off one arrow with a dashed tail, all
  and A-B the loop, one the loop with a "1" badge at its top left corner (9
  px, the "1" cut out, 1 px apart from the loop; it reaches 2 px beyond the
  symbol box, `qs_repeat.bmp` therefore has 24 × 18 px frames). The board has
  only the crossed arrows and the loop; `build_quickmenu.py` builds the
  other three from their strokes and heads, so stroke and heads stay those
  of the board. "One" has a switch of its own (`QsRightOne`), because its
  symbol lies in the backdrop like the switch. The titles are phrases
  of their own (`%Sx(Shuffle@quickmenu)`, `%Sx(Repeat@quickmenu)`: German
  "Zufall" and "Wiederholen" as on the board, English "Shuffle" and
  "Repeat"), the values are those of the settings in the current language
  (`%Sx(On)`, `%Sx(All)` …).
- The light surfaces of the board (switches, capsules, back button) are
  gradients in 8 bit; the skin engine rounds every channel of an `%xl` image
  to RGB565 by itself, and they showed tinted bands. `build_quickmenu.py`
  writes them dithered to RGB565 at their places on the screen (4 × 4
  ordered dither; the two switches lie 152 px apart, a multiple of 4).
- The variant "free assignment" is not used.

### 5.11 Symbol without a tile

For entries whose symbol should stand bare on the blue sidebar.

| Element | Value |
| --- | --- |
| grid | 156 × 156 like all symbols, content about x 18–138, y 16–140 |
| scale | 2/3: the grid becomes 104 × 104, the content about 80 × 83 |
| position | grid at x 28, y 66 in the sidebar (absolute x 188); centre 80 / 118 like the tile |
| stroke | rings 6 in the grid = 4 px on the display, as wide as stroke 8 on the 78 tile; list bars and note stems 9.5 |
| area | vertical gloss gradient over the height of the symbol: `#FFFFFF 0 %` → `#EEF3FA 45 %` / `#D3DEEC 55 %` → `#C3D1E3 100 %` |
| emboss | shadow 0 1 px, blur σ 0.55 px (CSS `drop-shadow(0 1px 1.1px …)`), `#040A18` 38 % |
| tile, reflection | none |
| title | as for the tile (17 px at y 18) |
| value | 13 px at y 202: music "268 albums" / "1 album" / "No music", podcasts "4 podcasts" / "1 podcast" / "No podcasts", audiobooks "3 audiobooks" / "1 audiobook" / "No audiobooks", "Now Playing" without playback "Nothing playing" (each in the current language) |
| bitmap | 88 × 88 at x 36, y 75 in the sidebar (absolute x 196), 32 bit with alpha |

Because Rockbox cannot shade text, the emboss is part of the bitmap. Alpha
is quantised to 16 steps beforehand (a = 17 · step), the colours to RGB565;
so the device shows exactly the preview.

---

### 5.12 Tempo screen

The pitch screen (plugin `pitch_screen.rock`, "Tempo" in German) in the
style of the quick menu, from the designer's boards "Tempo" (parts in
`tools/tempo/`, written dithered into `.rockbox/wps/glossyslate/tempo/` by
`tools/build_tempo.py`). The skin does not draw it: the plugin loads the
parts into its own buffer while the screen is open (about 90 KB plus the
field, 150 KB, all freed when it closes) and draws them itself
(`apps/plugins/pitch_screen.c`, iPod 6G); without the parts, with another
theme, it draws its old text screen.

- Field: the gradient of the quick menu, `#F7F8FA` → `#EDEFF3` (55 %) →
  `#DFE3E9`, dithered exactly like the skin's `%dr`.
- Top row y 14: mode capsule at x 14 (play/pause symbol, because Play
  switches the mode, then "Percent" or "Semitone" 13 px bold `#2E3644`), in
  timestretch mode the capsule "Timestretch" 8 px after it. The capsules
  grow with the text (left end, 4 px middle repeated, right end). Round keys
  "100 %" (hold Select) at x 250 and "close" (Menu) at x 282. Divider y 58.
- Percent and semitone: field 160 × 50 at 80, 72 with "Rate" (11 px bold
  `#5B6371`) and the value (17 px bold `#14171C`, "112,0 %" or "+2,71");
  slider 210 wide at 55, 142 between tortoise and hare; keys 128 × 42 at
  14 and 178, y 176 ("Hold" / "−2 %", "+2 %"), the wheel between them.
- Timestretch: two rows like the quick menu at y 72 and 108 (note: pitch on
  the wheel, metronome: speed on left/right), values 12 px bold
  right-aligned up to x 306; at the stretch limit the speed in `#B8281C`
  and "Limit" below it. Keys "Speed" / "Pitch Down", "Pitch Up".
- A key turns blue (`key_held.bmp`, white text and arrow) while left or
  right is held.
- Slider: logarithmic, 100 % in the middle, 50 % and 200 % at the ends
  (place = 0.5 + log2(value / 100 %) / 2), semitones ±12 at the ends; the
  centre of the knob sits on the end of the fill, a mark under 100 %.
- Numbers with the decimal separator of the language
  (`LANG_DECIMAL_SEPARATOR`), a space before "%" and a real minus (U+2212).
- Fonts are the theme's, shared with the skin (`font_load_ex()` with the
  skin's glyph cache of 160, so nothing is loaded twice).

### 5.13 Graphical equaliser

The graphical EQ (Settings › Sound › Equaliser › Graphical EQ) in the style
of the quick menu, from the designer's boards "Graphical EQ" (parts in
`tools/eq/`, written dithered into `.rockbox/wps/glossyslate/eq/` by
`tools/build_eq.py`). It is part of the core (`eq_menu_graphical()` in
`apps/menus/eq_menu.c`, iPod 6G), not a plugin: while the screen is open it
loads the parts into the plugin buffer (about 60 KB plus the field, 150 KB),
like the skin parser uses it, so nothing comes from the playback buffer.
Without the parts, or while a plugin stays loaded, it draws its old screen.
Keys, steps and limits are unchanged (wheel: value, left/right: band,
Select: next edit mode, Menu: close).

- Field and top row as on the tempo screen (5.12): capsule at x 14 with
  the symbol and name of the filter type of the selected band (low shelf,
  peak, high shelf; the words of the language file), blue while the type is
  edited; close key at x 282; divider y 46.
- Ten bands side by side, centre of band i at x 29 + 29 · i: track 10 × 88
  from y 60, the 0 dB line at y 104 across all bands behind the tracks, the
  fill from the line to the gain (1.83 px per dB, ±24 dB at the ends, the
  rounded end of the fill picture at the value). The selected band stands on
  a light column 28 × 120 and has the knob; its frequency below (y 154,
  "125", "1k", "3,5k") is dark, the others grey.
- Three keys 92 × 42 at x 14, 114, 214, y 180: gain ("+3,5 dB"), frequency
  ("125 Hz"), Q ("1,0") of the selected band; the key of the edit mode is
  blue.
- Numbers with the decimal separator of the language, a real minus.

### 5.14 Cover Flow: the track list on the back of the cover

PictureFlow ("Cover Flow") from the designer's board "PictureFlow", after
the photos of RetailOS's Cover Flow. The skin does not draw it: the plugin
composes it (`apps/plugins/pictureflow/pictureflow.c`, `PF_GLOSSY`, iPod
6G) from rows of colours that `tools/build_pictureflow.py` writes from
`tools/pictureflow/` (`parts.json` and the three pieces of the scroll bar)
into `apps/plugins/pictureflow/pictureflow_glossy.h`. All of it is
composed in 24 bit and dithered to RGB565 at its place on the screen,
like the skin's `%dr`; no picture is loaded.

- Opening an album: 6 frames loosen the cover (its reflection and the
  album text fade), 16 frames turn it to the left about its vertical axis,
  eased (θ = 180° · (1 − cos(π · j / 16)) / 2), PictureFlow's camera
  (distance 240); the card grows from the cover to the back 252 × 213 at
  x 34, y 27. Back the same frames in reverse. The frames follow the
  clock (30 per second, about 0.7 s), so a slow frame is skipped, not
  stretched.
- Unlike the board, the cover flow stays visible around the back: behind
  the card is PictureFlow's scene without the centre cover (side covers on
  the theme's background), not the blurred and lightened cover. So the
  field and its 1 px frame (`#0D0F13` 24 %, open below) lie on the theme's
  background, opaque: over the sharp covers they would let them show
  through.
- Field 250 wide at x 35, from y 28 out of the screen at the bottom. Head
  44 high, accent blue 62 % → 74 %, 1 px white 30 % on top; album 17 px
  bold white at y 32, artist 13 px `#DCE6F2` at y 52, both up to x 273,
  cut with "…".
- 7 rows of 24 from y 72, white 76 %. Title 14 px bold `#0D0F13` from x 47
  up to x 225 (less where a long time begins), cut with "…"; time m:ss
  (h:mm:ss) right-aligned at x 273, `#2E3644`. The selected row is the
  gloss bar of the lists, opaque, white texts; its title scrolls within
  x 47–225 when it is too long.
- Every second title from the second on (2nd, 4th, …) has a grey stripe
  (`rgba(46,54,68,.07)`); the stripes belong to the titles and move with
  them, and below the last title they go on. The board had them on the
  1st, 3rd, … title.
- More than 7 titles: the knob of the lists (not the board's pill), the
  same in every respect: black, alpha 8 of 15 (its ends 13 at the sides),
  as wide as "scrollbar width" less one, 2 px from the field's right edge,
  3 px from the ends of the list (y 75–237); shown when the selection
  moves, for 1 s, then faded out in 7 steps within 0.35 s.
- The list stops at its first and last title (no wrap-around).
- The playing title has the speaker of the database lists (14 × 12, from
  `tools/ipod6g_list_marks.py`) 6 px before its time, vertically centred,
  in the theme's "list arrow color", on the selected row in the
  selector's text colour; the title ends 8 px before it.
- While the titles are being looked up: "Loading..." (`LANG_WAIT`) 14 px
  bold `#5B6371`, centred, at y 72.
- Short albums start at the top as well; the list moves on by a row when
  the selection reaches its end.
- Albums without a picture (none in the folder, none embedded, or one that
  cannot be read) show the theme's default cover, also while their cover
  is still loading: `.rockbox/wps/glossyslate/cover_flow.bmp`, 128 × 128
  (PictureFlow's slide width at 320 × 240), opaque, square, without a
  reflection (PictureFlow adds its own as for every cover).
  `tools/build_pictureflow.py` writes it from the same 512 px template as
  the other default covers, scaled in full precision and dithered to RGB565
  once. The plugin finds it in the bitmap folder of the status bar skin;
  with a theme without it, PictureFlow's "?" stays.
- Memory: the scene behind (320 × 240), the back without its rows and the
  back as the texture for the turn (252 × 213 each), about 360 KB taken
  from the slide cache in the plugin buffer, never from the playback
  buffer. The fonts are those the status bar skin loads (shared).

## 6. Screens

All coordinates absolute.

### 6.1 Main menu

- List on the left (8 entries), sidebar on the right.
- Sidebar by the selected entry: tile with symbol and title; for "Now
  Playing" / "Resume Playback" the mini player. When nothing is playing, the
  sidebar shows a symbol there as well: the note without a tile with
  "Nothing playing" (the home page with the clock stays in the skin but is
  not shown). "System" has no value: the theme version stands in the
  sub menu System, below the logo tile (5.4).
- The entry "Database" is called "Music" in the fork (`%Sx(Music)`); in the
  settings it stays "Database".
- Music, podcasts and audiobooks: symbol without a tile (5.11), as the value
  the number of albums, podcasts or audiobooks from the fork's
  `%Mc(albums|podcasts|audiobooks)`. The database counts all three: albums
  of the media type (folders `/Music`, `/Podcasts`, `/Audiobooks`), without
  "<Untagged>". While the database loads, the value stays empty
  (`%?Mc(…)<…>`).
- Playlists and Recent Bookmarks: likewise "No playlists", "1 playlist",
  "4 playlists" and "No bookmarks", "1 bookmark", "3 bookmarks"
  (`%Mc(playlists|bookmarks)`).
- Recording, files, plugins and shortcuts: symbol without a tile (5.11,
  frames 8–11 of `side_symbols.bmp`: microphone, folder, four tiles, star).
  As the value for recording "No recordings" / "1 recording" / "5
  recordings" (audio files in the recording folder), for shortcuts "No
  shortcuts" / "1 shortcut" / "2 shortcuts" (`%Mc(recordings|shortcuts)`);
  files and plugins without a value. So in the main menu only "Volume Limit"
  (not in the menu) and the radio (no tuner) still have a tile.
- Every count is the number followed by a word from the language
  (`%Mc(albums) %Sx(albums)`); "No …" and "1 …" are phrases of their own.
- Radio playing (design; the iPod 6G has no tuner): a tile with a station
  dial, below it the station name and frequency.

### 6.2 Settings and sub menus with the sidebar

- The same grid as the main menu. The tile shows the selected entry, below
  it a description of the value (e.g. "Random order", "Level 9", "Rounded",
  "10s" for the backlight, "Album and Artist" for the second line). Plain
  yes/no or on/off values stand only in the row, not again below the tile.
  The fork's `%Sv(name)` fetches values of settings as their option list
  shows them. Shuffle and repeat change their symbol with the value.
  Repeat has the modes Off, All, One and A-B: the fork has no repeat
  "Shuffle" (shuffle is a setting of its own). `%mm` keeps the values of
  Rockbox (1 off, 2 all, 3 one, 5 A-B), so the case for 4 stays empty in
  every `%?mm<…>`, and frame 4 of `wps_repeat.bmp` and `home_repeat.bmp`
  (the same arrows as "All") is never shown.
- Settings that switch directly (shuffle, repeat, yes/no values) show the
  value in the row and switch on with a click; the sidebar shows the same
  value.
- "Time & Date" shows the calendar card instead of the tile, "Album Art
  Corners" and "Key Lock" their picture preview (5.4).
- System: the logo tile, below it "Glossy Slate" and "Version …" (5.4).

### 6.3 Option pages

- Exist only for album art corners, key lock and settings with more than
  three values (except repeat). The pages for shuffle, repeat, second line
  and scroll bar can no longer be reached.
- List on the left with a check mark in the selected row, sidebar with the
  title of the setting, the tile of the selected option and its name as the
  value.
- Pictures of their own: album art corners (default cover rounded/square,
  title "Album Art Corners", value the selected option) and key lock
  (picture preview Normal or Lock Screen, title the selected option, value
  "Screen unchanged" or "Clock and title"). The help text below the list
  from the design is left out in the theme.

### 6.4 Long lists (full width)

Database, files, playlist, track info, bookmarks, plugins: a list over the
width of 320, otherwise as in 5.2. Playlist with the number 12 px on the
left (20 wide, right-aligned) and a play triangle at the playing track.
Track info with the label 11 px `#5B6371` above the value 14 px.

### 6.5 Album list

- Rows 52 high. Covers 52 × 52 at x 0, without gaps. Selection bar with
  gloss from x 52 to the right edge, the cover never in the bar. Arrow at the
  end of the row.
- Text from x 60 (8 after the cover): line 1 the album title (14 px bold),
  line 2 the artist (13 px regular, `16-GlossySlate-Regular13.fnt` through
  `list secondary font`, on the baseline of the list font), together
  vertically centred (top at 2). Entries without an artist (special
  entries) on one line, centred.
- At the top the three special entries "[By Album]", "[All Tracks]",
  "[Shuffle]" with their album pictures.

### 6.6 Now playing

| Element | Position | Style |
| --- | --- | --- |
| status bar | 0–21 | title "Now playing" (`%Sx(Now playing)`) |
| cover | x 14, y 39, 116 × 116, tilted with reflection (picture 116 × 160 from y 35, reflection down to y 195) | 5.7; the top left corner 13 px below the status bar as in the original; with the full reflection and the fixed progress bar 116 is the largest cover edge; the area below stays free |
| position "3 of 12" | x 144, y 36 | 11 px bold `#5B6371` (`%Sx(of)`) |
| title | x 144, y 56, 164 wide | 17 px bold `#0D0F13` |
| artist | x 144, y 79 | 13 px bold `#2E3644` |
| album | x 144, y 98 | 13 px regular `#5B6371` |
| pills format / rate | x 144 / 192, y 120 | 5.8 |
| progress | x 14, y 200, 292 × 9 | 5.8 |
| times, shuffle, repeat | y 214 / 217 | 5.8 |

Without tags the file name and folder stand in place of title and artist.
The volume display replaces the progress bar while the volume is being
changed.

### 6.7 Key lock

Two options:

- **Normal:** only the buttons are locked, the current screen stays, the
  status bar shows the lock.
- **Lock Screen:** the blue field over the whole area. White lock at the top
  left (x 10, y 6), battery at the top right (x 288, y 4). Date 17 px bold
  white, centred at y 23 (`%cD(long)`, "Monday, 9 November"). Clock box at
  x 60, y 62. At the bottom the playing title with "► " 13 px bold white
  (y 190) and the second line 11 px bold `#DCE6F2` (y 208). Without playback
  the title block is left out.

The choice opens an option page; the sidebar shows the picture preview from
5.4 there.

### 6.8 USB mode

A blue field and a black status bar like RetailOS: 21 px gradient `#292C31`
→ `#101018`, below it 1 px `#000000` (`SbUsb`). Title "iPod" bold 13 in
`#EEF3F5`, centred (viewport `TitleUsb` 76, 3, 168 × 16, symmetric about
x 160 and ending before the symbols from x 244). A light spinner
(`status_spinner_light.bmp`), a white lock (`status_lock_white.bmp`); the
symbols carry the suffix `K` (`SpA320K`, `LkA320K` …). The battery is
monochrome like the RetailOS template: outline `#E4E4E4`, 1 px dark gap
`#141414`, light grey fill, bolt `#1A1A1A` with a light edge (`BATT_MONO` in
`design.py`; `status_charge_mono.bmp` while charging,
`status_battery_mono.bmp` otherwise, 12 frames each like the coloured ones).
It always shows the level (`BatUsb`); the plug for "full on the charger" does
not exist in USB mode, because the cable is always plugged in there.

Two screens, logo 88 px (an orange glossy circle with a black 30-pin
connector, shadow downwards, no reflection) in the viewport 110, 60,
100 × 100, circle at 116, 64 (`usb_logo.bmp`, 2 frames):

| | connected (`%cs` 21, `Usb`) | ejected (`%cs` 22, `UsbAus`) |
| --- | --- | --- |
| title (17 px bold white, y 35) | Connected | Ejected |
| logo | frame 1, connector with cable | frame 2, arrow pointing down |
| line (13 px bold white, y 190) | Do not disconnect. | The cable can now be disconnected. |
| line (11 px bold `#DCE6F2`, y 208) | Eject on the computer before disconnecting. | Rockbox is ready again after disconnecting. |

The texts are `%Sx(...)` phrases (`LANG_THEME_USB_*`), so they appear in the
current language. The second screen appears as soon as the computer has
ejected the drive (firmware: `ACTIVITY_USBEJECTED`, see `ROCKBOX-CHANGES.md`).
The iPod stays in USB mode until the cable is pulled.

### 6.9 More designs

- **Battery low:** blue field, title "Battery low", a large battery with a
  red fill and a reflection, "7 % left" and "Please charge soon."
- **Recording:** status bar with a red dot, levels L/R as green bars, list of
  the recording settings with values in `#5677B0`, sidebar with the
  microphone tile, running time and file size.
- **Radio:** a station dial 88–108 MHz in a tile with a red needle,
  frequency and station name below it.

---

## 7. New elements in the same style

1. **Colour:** only values from section 3. Derive new tones between two
   existing ones, never more saturated than the accent.
2. **Area:** light = white or the status bar gradient; dark = the tile
   gradient; stage = the blue field. Highlighting always with a gloss edge
   at 45–55 %.
3. **Symbol:** in the 156 grid with stroke 8 (arrows 18), colour `#DFE6F3`
   on tiles, the accent gradient on black. Cut-outs by mask.
4. **Tile:** 78 in the sidebar, 88 as a single picture, radius 14, always
   with a reflection 35 high.
5. **Text:** sizes from 4.2, bold; secondary information in `#5B6371` or
   `#DCE6F2`. Never a fixed word in the skin: add a phrase at the end of the
   language files (English text without commas or brackets, unique among the
   English strings) and draw it with `%Sx(...)`. If the English text exists
   already but needs a translation of its own, add the place after `@`
   ("Shuffle@quickmenu"); the firmware shows only the part before it.
6. **Status symbol:** at most 14 high, placed in the row on the right, 4 px
   apart.
7. **Giving a new menu entry a tile:** add the symbol in `tools/design.py`
   (`NEW_SYMBOLS`) and to the tile list in `build_assets.py`, then map the
   English menu text (`%Sx(...)`) to the symbol in `build_skin.py`
   (`MAIN_TILES` or `setting_tiles`). Then run the tools again (section 8.4).

---

## 8. Implementation in Rockbox

### 8.1 Files

| File | Content |
| --- | --- |
| `.rockbox/themes/glossyslate.cfg` | theme settings |
| `.rockbox/wps/glossyslate.sbs` | status bar skin: all menus, sidebar, lock screen, USB, quick menu |
| `.rockbox/wps/glossyslate.wps` | now playing, volume, lock screen over the now playing screen |
| `.rockbox/wps/glossyslate.wrs` | recording screen |
| `.rockbox/wps/glossyslate/*.bmp` | 60 bitmaps of the skins (24 bit with dithering or 32 bit with alpha) |
| `.rockbox/wps/glossyslate/cover_flow.bmp` | default cover of Cover Flow (5.14), loaded by `pictureflow.rock` |
| `.rockbox/wps/glossyslate/tempo/*.bmp` | 23 parts of the tempo screen (5.12), loaded by `pitch_screen.rock` while it is open |
| `.rockbox/wps/glossyslate/eq/*.bmp` | 21 parts of the graphical EQ (5.13), loaded by the core while the screen is open |
| `.rockbox/fonts/*.fnt` | 11 fonts (RB12, 4 bit anti-aliasing) |
| `.rockbox/wps/glossyslate/side_symbols.bmp` | symbols without a tile (5.11): frames 1 podcasts, 2 music, 3 audiobooks, 4 playlists, 5 settings, 6 bookmarks, 7 system, 8 recording, 9 files, 10 plugins, 11 shortcuts, 88 × 88 each (the symbol for the volume limit, drawn but never used, was taken out on 16 November 2026) |
| `firmware-assets/` | pictures for the fork's album list and popups, the boot screen in full colour (`rockboxlogo_320x240.png`) |
| `graphics/` | the battery sprite all battery bitmaps are made from |
| `previews/` | previews from the skin simulator (English) |
| `tools/` | the generator that makes all files above from the design values |

### 8.2 Settings in the cfg

| Line | Meaning |
| --- | --- |
| `font: 24-GlossySlate-Bold14.fnt` | UI font, 24 high = row height |
| `selector type: bar (gloss)` with start `5896E6`, end `1A55BE`, text `FFFFFF` | gloss bar of the firmware lists (fork) |
| `line selector gloss top/bottom/edge color: 3577D9 / 2160CB / 174A9E` | colours at 45 % and 55 % of the bar height and the bottom pixel row |
| `list secondary color: 5B6371` | artists in album rows |
| `list value color: 5677B0` | values in firmware lists |
| `list secondary font: /.rockbox/fonts/16-GlossySlate-Regular13.fnt` | fork: font of the artist line in the album list (regular instead of bold); the now playing screen loads the same file, so it costs no further font place |
| `list arrows: on`, `list arrow color: 1D2847` | arrow at the end of the row, selected in the selection text colour |
| `list edge inset: 8` | distance of text and symbols from the left edge |
| `popup font`, `popup hint font` | fonts of the fork's popups (13 px and 11 px bold) |
| `foreground color: 0D0F13`, `background color: FFFFFF` | lists |
| `scrollbar: right`, `scrollbar width: 6` | the fork's overlay knob, 5 px wide |
| `statusbar: off` | in the fork: second line alternating (`top` = album, `bottom` = artist) |
| `volume display: graphic` | in the fork: album art corners rounded (`numeric` = square) |
| `battery display: numeric` | in the fork: key lock "Normal" (`graphic` = lock screen) |
| `show icons: off` | no list icons; always off in the fork anyway, the menu entry "Show Icons" is gone |
| `qs top/bottom: brightness`, `qs left: shuffle`, `qs right: repeat` | assignment of the quick menu (5.10) |

### 8.3 Skin technique

- **Layers.** Everything text stands on is drawn in backdrop viewports
  (`%VB`). When Rockbox writes a text line, it restores the backdrop below
  it, so the graphics stay.
- **Logic in 1 × 1 px.** All screen logic is in a viewport of 1 × 1 px with
  a 1 px font; a redraw clears only one pixel there.
- **Changing backdrops** take the same rectangle. When one is hidden, the
  next one paints over the same area.
- **Tile symbols as a font.** All symbols are characters in
  `113-GlossySlate-Tiles.fnt` and are coloured with `%Vf(dfe6f3)`. The tile
  frame with the reflection is a bitmap. This saves memory and allows the
  symbol to be chosen by conditions.
- **Pictures with alpha in the backdrop** (`%VB`): the fork lays them over
  what the viewport drew before (areas, pictures before them). But a `%VB`
  viewport of its own clears its area with its background colour; a picture
  in it then sees this colour instead of the layer below. So the clock box
  stands in the field of the lock screen (`LkField`), and the buttons of the
  quick menu have `%Vb(e6e9ee)`, the colour of the field below them.
- **Symbols without a tile** are bitmaps with alpha, not characters of the
  tile font, because the gloss gradient and the emboss need more than one
  colour. Per symbol a complete sidebar in the backdrop (`SidePod`,
  `SideNote`, `SideBook`, `SidePlay`, `SideSet`, `SideInfo` …: field plus
  `%xd(SideSym,n)` from `%xl(SideSym,side_symbols.bmp,36,75,11)`), chosen
  like the picture previews through `%LT`. The tile viewport stays but shows
  no character for these entries.
- **Picture previews** (album art corners, key lock) are a complete sidebar
  per variant (`SideArtR`/`SideArtS`, `SideLockN`/`SideLockS`): field plus a
  picture with two frames. `lockprev.bmp` is blended onto the field and
  opaque (2 bytes per pixel, no 4 bit alpha steps in the reflection). In the
  menu the setting decides (`%St(...)`), on the option page the selected
  option (`%LT`).
- **Clock hands as a font.** `84-GlossySlate-Hands.fnt` holds all 720 hand
  positions (12 hours × 60 minutes); only a few of them are in memory at the
  same time.
- **Blue field without a bitmap.** The lock screen and USB paint the field
  as 16 horizontal bands of 15 px with `%dr` gradients.
- **Gradients** (`%dr` with two colours) are computed by the fork from the
  24 bit colours and dithered to RGB565. Without that, flat gradients turned
  into colour casts (white → `#F4F6F8` showed a pink band above the progress
  bar).
- **Menus** (main menu, settings, system) use the firmware lists: since the
  update the fork draws gloss bars, arrows (`%Lo`) and values (`%LV`) there
  itself, in one line that can scroll. Rows of the theme's own (`%Lb`)
  cannot show a value in a second colour: every row viewport clears its
  line, and only the last one may scroll.
- **Option pages** use rows of their own (`%Lb`) of three viewports: inset on
  the left, right end with the check mark, text. The text viewport comes last
  on purpose, otherwise scrolling text jumps in the selected row. The bar is
  `%Vs(gloss)` with the colours from `%Vg`.
- **Long lists** are drawn by the firmware (only so are there covers in the
  album list).
- **Covers with an effect.** `%Cd` with parameters draws tilt, reflection
  and corners. Each skin has two `%Cd` (rounded and square), and the setting
  `volume display` chooses. Without a cover (`%?C<|…>`) the skin shows the
  precomputed default cover with the same effect.
- **Key lock.** With "Lock Screen" the UI area is put on an invisible
  viewport and the field with the clock is shown (all menus except USB, and
  on the now playing screen). Rockbox redraws the list itself after
  unlocking.
- **Texts.** No word is fixed in the skins. `%Sx(English text)` shows the
  phrase in the current language (the menu titles of Rockbox and the theme
  phrases `LANG_THEME_*` at the end of the language files); dates come from
  `%cD(long|short|weekday|month)`. The English text inside `%Sx` must not
  contain a comma (it would separate parameters, and the skin would not
  load) or brackets. A key can name its place after `@`
  (`%Sx(Shuffle@quickmenu)`): the firmware shows only the text before it, so
  the same English word can have a translation of its own there.
- **Cover sizes:** exactly one `%Cl` per skin – status bar skin 100 × 100,
  now playing 116 × 116.
- **Memory:** bitmaps in RAM about 0.59 MB (status bar skin 417 KB, now
  playing 173 KB; of this the default covers with the effect 157 KB, album
  art corners preview 35 KB opaque, key lock preview 67 KB). Plus the buffers
  of the `%Cd` effects (8 bit opacity per pixel): now playing 2 × 55 KB, mini
  player 2 × 41 KB. Together about 0.75 MB, plus small font caches.

### 8.4 Tools

The folder `tools/` makes the theme from the design values. Requirements:
Python 3, Pillow, NumPy, fontTools, Playwright with Chromium, Liberation
Sans 2 in `/usr/share/fonts/truetype/liberation/`.

```
cd tools
python3 build_assets.py    # bitmaps, album pictures, glyph templates (into cache/ and out/)
python3 build_fonts.py     # fonts
python3 build_skin.py      # sbs, wps, cfg
python3 build_side_symbols.py --png   # symbols without a tile (5.11) from sym_pur.json, into out_side/
python3 build_wps_cover.py            # default cover of the now playing screen with the effect (cover116_fx.bmp), without Pillow
python3 build_bar_ends.py             # progress/volume: fixed left end (wps_fill.bmp, wps_vfill.bmp from sources/)
python3 build_quickmenu.py            # status symbols and quick menu pictures from quickmenu/bmp, battery from graphics/
python3 build_side_reflections.py     # mini player default cover and album art corners preview opaque on the sidebar
                                      # (sources with alpha in sources/, copy them there after build_assets.py)
python3 build_recording.py            # recording screen (wrs and its bitmaps)
python3 build_system_logo.py          # logo tile of the System menu opaque on the sidebar (from sources/glossyslate_logo.png)
python3 build_bootlogo.py             # boot screen of the fork dithered to RGB565 (into apps/bitmaps/native/rockboxlogo.320x240x16.bmp)
python3 build_tile_glyphs.py          # tile glyphs delivered as pictures (sources/tiles/) into the tile font, after build_fonts.py
python3 build_tempo.py                # parts of the tempo screen (tempo/) dithered into .rockbox/wps/glossyslate/tempo/
python3 build_eq.py                   # parts of the graphical EQ (eq/) dithered into .rockbox/wps/glossyslate/eq/
python3 build_wps_repeat.py           # repeat "One" of the now playing screen (frame 3 of wps_repeat.bmp), after build_assets.py
python3 build_pictureflow.py          # colour rows of the back of the cover in Cover Flow (pictureflow/) into apps/plugins/pictureflow/pictureflow_glossy.h,
                                      # and the default cover of Cover Flow (.rockbox/wps/glossyslate/cover_flow.bmp)
python3 preview.py                    # previews (skin simulator) of .rockbox/ into previews/
python3 preview.py --lang deutsch --out /tmp/de   # the same in another language of apps/lang
```

`build_assets.py`, `build_fonts.py` and `build_skin.py` write into
`tools/out/GlossySlate/` and need the renders in `tools/cache/` that
`build_assets.py` makes with Chromium; copy the results into `.rockbox/`.
`build_quickmenu.py`, `build_bar_ends.py`, `build_side_reflections.py`,
`build_wps_cover.py`, `build_wps_repeat.py` and `build_recording.py` are
pure Python and write
straight into `.rockbox/`; run on an unchanged tree they reproduce the
files in it byte for byte. `build_system_logo.py` likewise, with Pillow and
NumPy; it puts the logo onto `sidebar.bmp`, so run it again after a new
sidebar. `build_bootlogo.py` (Pillow) writes the boot screen of the fork,
outside the theme: `bmp2rb` would cut the gradient to RGB565 without a
dither, so the BMP is dithered beforehand.

- `tools/albumart_fx.py` rebuilds the cover effect (previews, album art
  corners preview). It is an implementation of its own in floating point;
  `build_wps_cover.py` uses the firmware's integer maths instead.
- `tools/rblang.py` reads the language files for the previews: `%Sx` the
  way the firmware resolves it, and the dates of `%cD`.
- `lock_preview_normal.html` and `lock_preview_lock.html` are the previews
  from the board "Option · Key lock"; `build_assets.py` renders them onto the
  sidebar (`lockprev.bmp`). They contain no words of the user interface.
- `check/main.c` is a small checker based on `lib/skin_parser`; it reports
  syntax errors with line and column. Compile it with the parser of this
  repository; the stock Rockbox parser does not know the fork's tags:
  `gcc -O1 -w -D__PCTOOL__ -I ../../lib/skin_parser check/main.c ../../lib/skin_parser/{skin_parser,skin_buffer,skin_debug,skin_scan,tag_table}.c -o checkskin`

---

## 9. Deviations of the theme from the design

Done since the firmware update and no longer deviating: gloss bar, values
and arrows in lists, switching with a click, tilted and mirrored covers, the
reflection in the mini player, the album list with covers of 52, arrows and
gloss bar, the value colour `#5677B0` (`list value color`).

| Design | Theme today | Reason |
| --- | --- | --- |
| name and value fit into the row | long names are shortened in front of the value (e.g. "Second Line in Player" next to "Album and Artist" in 160 px) | the firmware shortens the name, the value comes first |
| 1 px outline around the cover in the mini player and on the now playing screen | none | the outline does not tilt along and would need bitmaps of its own per corner variant |
| key lock preview shows the screen | a fixed picture with an example title and 20:51, without words | skins cannot draw a screen reduced; words would be in one language only |
| help text below the list on option pages | none | the list reaches down to the bottom |
| text shadows (emboss) | none | Rockbox has no text shadows |
| battery low, recording with the sidebar | firmware screens with the status bar | not yet done in the theme |
| quick menu | design 5.10 | made from the parts of the board (`build_quickmenu.py`), texts from the language files; without "free assignment"; value line 2 px lower |
| radio | left out | no tuner in the iPod 6G |

All points that need firmware are listed in `ROCKBOX-CHANGES.md`.
