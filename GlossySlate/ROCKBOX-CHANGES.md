# Glossy Slate – changes to Rockbox

What the design needs but a theme alone cannot do, and what to check before
and after installing.

Checked against the Rockbox source (github.com/Rockbox/rockbox, commit
`2ae4d6c` of 9 November 2026), against the fork for the iPod 6G in this
repository (based on `41a3e60b9c`) and against the notes on the fork's
firmware updates. The firmware side of every point is described in
`docs/ipod6g-*.md`.

**State of the theme (1.0):** `glossyslate.sbs` (4380 elements) and
`glossyslate.wps` (601 elements) pass `lib/skin_parser` of the fork without
errors (section 9). All cfg settings, tags, parameters and file formats
(fonts RB12, BMP 24/32 bit) are checked against the source. The previews
in `previews/` come from a simulator (`tools/preview.py`), not from the
device; the theme itself runs on the iPod Classic 6G with this fork.

---

## 0. What changed on the way to theme 1.0

- **Menus use the firmware lists.** Main menu, settings and system show
  gloss bars, arrows and values as the fork draws them. Rows of the theme's
  own (`%Lb`) are left only on option pages (with a check mark). Reason: a
  `%Lb` row cannot show a value in a second colour, because every row
  viewport clears its line and only the last one may scroll. The firmware
  list can do both in one line.
- **Covers with an effect.** Now playing: `%Cd(24,420,36,34,R)` in
  `%Vl(Player,13,35,118,161,-)` with `%Cl(1,4,116,116,c,c)`. Mini player:
  `%Cd(24,420,36,60,R)`. R = 8 (rounded) or 0 (square), one `%Cd` per
  variant. Rings and corner masks are gone.
- **Default cover with the effect.** For tracks without a cover the theme
  ships precomputed pictures (`cover116_fx.bmp`, `cover100_fx.bmp`, frame 1
  rounded, frame 2 square each), both opaque on their ground and dithered
  once from full precision, so the grey of the cover shows no tinted bands.
- **Picture previews in the sidebar.** "Album Art Corners" shows the default
  cover rounded or square, "Key Lock" the preview from the design board (a
  reduced now playing screen or lock screen) as a fixed picture. Both replace
  the former tile symbols and follow the setting in the menu, and the
  highlighted option on the option page.
- **Texts from the language files.** Every text the theme draws comes from
  the language set on the iPod: `%Sx(...)` for words and sentences, the
  fork's tag `%cD(...)` for dates (section 4, "Translatable texts").
- **Logo tile under System.** The sidebar of the System menu shows the
  Glossy Slate logo tile (`system_logo.bmp`, 88 px, made by
  `tools/build_system_logo.py` from `tools/sources/glossyslate_logo.png`),
  below it the name and the version.
- **cfg:** `selector type: bar (gloss)` with the three gloss colours,
  `list secondary color`, `list value color`, `list arrows`,
  `list arrow color`, `list edge inset` (values in `DESIGN.md` 8.2).

---

## 1. Installing

1. Copy the folder `.rockbox` of the theme into the root of the iPod and
   merge it with the existing `.rockbox` (it holds only new files:
   `themes/glossyslate.cfg`, `wps/glossyslate.*`, `wps/glossyslate/`,
   `fonts/*GlossySlate*`). Delete an older `wps/glossyslate/` first, so that
   no pictures of an older version stay behind. On macOS the folder is
   hidden: show it in the Finder with ⌘⇧. (Cmd-Shift-dot).
2. On the iPod: Settings → Theme Settings → Browse Theme Files →
   `glossyslate`.
3. The pictures of the album list are built into the fork (section 6).

Theme 1.0 needs the fork in this repository. A Rockbox without its changes
does not know `%LV`, `%Lo`, `%Mc`, `%Sv`, `%cD` and `%Cd(…)` with
parameters, rejects the skins and falls back to the default theme.

---

## 2. Check before the first start

| Point | Why | What to do if it does not fit |
| --- | --- | --- |
| firmware of this fork | Without the new tags the theme does not load (see 1). | Install the firmware of this repository. |
| Do other skins of the system use more fonts of their own? | Rockbox allows at most 12 skin fonts in all (`MAXUSERFONTS`). Glossy Slate loads 10 different ones, plus the UI font. | Do not keep other skins with fonts of their own active at the same time (e.g. a radio skin `.fms`). |
| English texts of the fork's menu entries | The sidebar recognises menu entries by their text (`%Sx(...)`). Expected are "Album Art Corners", "Second Line in Player", "Key Lock", "Square", "Normal", "Podcasts", "Audiobooks" and the theme texts at the end of `english.lang`. If a text is missing, the tile shows the gear without an error, and a missing theme text shows "<ERR>". | Enter the texts of the firmware in `build_skin.py` (`MAIN_TILES`, `setting_tiles`, `LOCK_NAMES`, `OPT_NORMAL`). |
| `statusbar: off` | In the fork this means "second line alternating". | – |

---

## 3. Firmware changes

### Done with the update of 10 November 2026

| No. | Wish | In the fork now | Used by the theme |
| --- | --- | --- | --- |
| 1 | key lock as a menu entry | "Key Lock" in Theme Settings, values Lock Screen/Normal, cfg still `battery display` | option page with picture preview |
| 2 | switch yes/no settings directly | a click switches, the list stays | value in the row (firmware list) |
| 3 | cycle through few values in the row | settings with up to three values switch with a click; exceptions album art corners and key lock | the same; option pages only for album art corners, key lock and more than three values |
| 4 | gloss bar | `selector type: bar (gloss)` with three gloss colours, `%Vs(gloss)` for skins | firmware lists and own rows |
| 5 | tilting the cover | `%Cd(tilt,perspective,…)` | now playing 24°, perspective 420 |
| 6 | reflection under the cover | `%Cd(…,reflection height,opacity,corner radius)` | now playing 36/34 %, mini player 36/60 % |
| 7 | album list: covers of 52 | `ALBUMART_LIST_SIZE` 52, row `max(52, 2 × font height + 4)` | pictures from `firmware-assets/` |
| 8 | artist line in a theme colour | `list secondary color` | `#5B6371` |
| 9 | arrow in firmware lists | `list arrows`, `list arrow color` | on, `#1D2847` |
| 10 | text distance from the edge | `list edge inset` | 8 |
| 11 | short German menu texts | "Cover-Ecken" (Rund/Eckig), "Zweite Zeile", "Tastensperre" | sidebar texts matched |

### Still open

#### 12. Scrolling text in own list rows with several viewports *(optional)*

**Now:** for the selected row all viewports of a `%Lb` row share one
structure (`selected_item_vp` in `apps/gui/bitmap/list-skinned.c`). Only the
viewport drawn last may contain scrolling text. So the theme orders its rows
that way (text viewport last) and does not need the change.

**Needed:** a copy of its own per viewport of the selected row. Only then
would entries over several lines with scrolling text be possible.

#### Done on 10 November 2026 and later

- **13:** `list value color` exists; if it is not given, `list secondary
  color` applies. `glossyslate.cfg` and `build_skin.py` set `5677B0`.
- **15:** was already the case: the name of the selected row scrolls in the
  area before the value.
- **Sidebar with firmware lists:** `%LT`, `%LV` and `%Lo` returned the
  selected entry only while a `%Lb` list was active. Since the firmware
  draws the menus, the tags were empty there. Now the firmware list
  remembers its selected entry (text, value, opens a level); without `%Lb`
  the tags (offset 0) return it.
- **White base in `%VB` (theme):** Rockbox fills the buffer of the `%VB`
  layer with a copy of the screen when the skin loads, and firmware lists
  clear their area with this buffer. Without an area of its own under the
  lists, the old screen showed through (black ground, old list). The `.sbs`
  now creates `%V(0,0,320,240,9)%VB` with a white area as its first `%VB`
  layer (`build_skin.py`).
- **Gloss bar (firmware):** the rows in between had wrong colours (unsigned
  maths in `blend_color()`); fixed.
- **White areas after a change of tile or view (firmware):** when hiding,
  the skin engine filled the area of a `%VB` layer with the background
  colour; foreground viewports hidden afterwards took this colour to the
  screen and were never drawn again (sidebar, a rectangle around
  shuffle/repeat after the volume). Now the engine draws, after hiding,
  first the `%VB` layer, then the hidden areas from the finished buffer,
  then the foreground.
- **Status bar (theme):** `status_play.bmp` has four pictures (play, pause
  with a 2 px gap, fast forward, rewind); `%mp` shows them for playback,
  pause, fast forward and rewind. Made by `tools/build_quickmenu.py` (also
  called from `build_assets.py`).
- **Quick menu (theme, DESIGN.md 5.10):** built after the design "Quick
  menu": pills for battery and sleep timer, lock, back button, sliders for
  volume (wheel) and brightness (MENU brighter, PLAY darker), buttons shuffle
  (left) and repeat (right). The cfg sets `qs top/bottom: brightness`,
  `qs left: shuffle`, `qs right: repeat` for this. Graphics and skin code in
  `tools/build_quickmenu.py` (pure Python, `tools/raster.py`), included in
  `build_skin.py`.
- **Quick menu, second version:** always the view of the design (the
  variant "free assignment" is gone). Buttons, symbols and arrows lie in the
  `%VB` layer; before, the text viewports cut them off. `%QT` stands in a
  viewport that is never shown (`QsNever`), so that Rockbox does not draw its
  built-in quick screen.
- **Battery from the sprite (state 1.2):** the source is
  `graphics/battery_sprite.bmp` (25 states). `battery_from_sprite()` in
  `build_quickmenu.py` writes `status_battery.bmp` (1–12),
  `status_charge.bmp` (13–24, charging with the real level) and
  `status_charged.bmp` (25, plug). All skins (sbs, wps, wrs, quick menu):
  `%?bp<%?bc<%xd(Charge,%bl)|%xd(Charged)>|%xd(Batt,%bl)>`.
- **No clock without playback:** in the main menu the sidebar shows the tile
  of the selected entry when nothing plays. The clock (`SideHome`, `Home`,
  `clockface.bmp`, `clockdot.bmp`, `84-GlossySlate-Hands.fnt`) stays in the
  theme for now but is no longer shown; picture and font are still loaded
  (about 35 KB).
- **Recording (theme):** new recording skin `glossyslate.wrs` after the
  recording design (`tools/build_recording.py`), loaded through
  `wrs: /.rockbox/wps/glossyslate.wrs` in the cfg. Left the status bar with a
  red dot at `%Rr`, the levels `%pL`/`%pR`, below them the list of the
  recording screen (`%Vi(-,0,47,160,193,-)`); right the source `%Ri`, the
  microphone tile, time and size. The firmware shows the rows of the list as
  name and value. The list holds the entries of Rockbox' recording screen
  (volume, gain, left, right, file name), not the entries of the design
  (format, sample rate, channels, source, trigger).
- **Switching directly, new rule:** only yes/no and on/off settings and
  "Repeat"; all others open their option page. (Also fixed: numeric settings
  such as the volume counted as yes/no settings through a bug.)
- **White areas after other screens (firmware):** every skin with `%VB`
  copies the finished backdrop around its UI viewport to the screen after a
  complete redraw and draws the foreground again. Before, after a screen
  without the sidebar half the picture including the status bar stayed
  white. For the theme this means: everything outside the UI viewport must
  be in the `%VB` layer or in foreground viewports; nothing is taken over
  "from the last picture" any more.
- **USB mode: logo, ejected, black bar:** an orange logo instead of a tile
  (`usb_logo.bmp`, frame 1). After the computer ejected the drive a second
  screen with an arrow (frame 2) through `%cs` = 22 (`ACTIVITY_USBEJECTED`).
  The firmware notices the eject (`usb_storage_all_ejected()`, SCSI START
  STOP UNIT with the eject bit) and swaps the activity in
  `apps/gui/usb_screen.c`. The status bar is black on both USB screens
  (`SbUsb`), the title "iPod" centred (`TitleUsb`), a light spinner and a
  white lock (viewports with `K`), the battery monochrome (`BatUsb` with
  `ChargeM` and `BattM`). In USB mode the font files are closed; so the
  firmware loads the common characters into the glyph cache of every font
  beforehand.
- **USB screen (theme):** `UsbField` stands before `SbFull` in the `.sbs`;
  before, the blue area covered the status bar in the backdrop buffer. Rule
  of thumb: in the `%VB` layer the later area draws over the earlier one, so
  full-screen fields belong at the front.
- **Battery after a full charge (firmware):** after a complete charge the
  battery counts as full from a measured 90 %; the gauge only rises while
  charging and only falls otherwise (`docs/ipod6g-more-changes.md`).
- **Now playing at the first start (firmware):** a complete redraw of the
  now playing screen copies the finished backdrop to the screen at the end
  and draws the foreground again; before, the gap between the times stayed
  white until the volume was changed once.
- **Translatable texts (firmware and theme, 12 November 2026):** see
  section 4.

#### 14. Cover effect for the substitute picture too *(saves memory)*

**Now:** `%Cd` with an effect draws only real covers. For tracks without a
cover the theme ships precomputed tilted default covers: `cover116_fx.bmp`
and `cover100_fx.bmp` with two frames each, together about 131 KB in RAM
(opaque, 2 bytes a pixel: 116 × 160 and 100 × 142, two frames each).

**Needed:** when there is no cover, apply the effect to a substitute
picture, e.g. `%Cd(…)` with a sixth parameter for a bitmap ID or the fork's
built-in default cover. Then both bitmaps go away, and real and substitute
covers are sure to match.

---

## 4. Done in the fork and used by the theme

- **Scroll bar as an overlay:** a dark knob without a track, stays 1 s after
  the last movement and fades out in 7 steps over 350 ms
  (`apps/gui/scrollbar.c`). Theme: `scrollbar: right`, `scrollbar width: 6`.
- **Podcasts and audiobooks in the main menu:** open their categories of the
  database, in the style of the album list with covers. The database keeps
  music (`/Music`), podcasts (`/Podcasts`) and audiobooks (`/Audiobooks`)
  apart; all other views show only music
  (`docs/ipod6g-database-media-types.md`). The sidebar shows the symbols
  without a tile for them.
- **Empty lines are cleared:** if a dynamic tag of a line returns nothing
  any more (e.g. `%LV` after moving to an entry without a value), the skin
  engine draws the line again anyway. Before, the old text stayed (the state
  of the clip counter under the tile).
- **`%Sv(name)`:** the value of a setting as its option list shows it
  ("10s", "Always On", "Album"); empty for text settings. The theme uses it
  for backlight, second line and scroll bar under the tile.
- **Gradients:** `%dr` with two colours is computed from the skin's 24 bit
  colours and dithered to RGB565 (4 × 4). Before, the firmware interpolated
  the end colours already rounded and truncated every row: flat gradients
  turned into colour casts (a pink band above the progress bar).
- **Font of the artist line:** new theme setting `list secondary font` (a
  file in `/.rockbox/fonts/`, `-` = list font). The firmware draws the second
  line of the album list with it, on the baseline of the list font. The
  theme sets `16-GlossySlate-Regular13.fnt`.
- **Values in the row** only for plain yes/no and on/off settings and for
  "Repeat"; all others open their option page (Inverse/Normal too).
- **Texts:** in the main menu "Database" is now "Music" (`%Sx(Music)`). Top
  settings level in German: "Klang", "Themen", "Aufnahme" (instead of
  "…einstellungen"); "Grundeinstellungen" stays. The skin compares with the
  English text through `%Sx(...)` and adapts by itself.
- **Finer reflection:** the cover effect `%Cd(…)` keeps the opacity with 8
  bits and blends the picture with the background itself when drawing,
  dithered to RGB565 (before 16 steps: at 34 % only 5, visible as broad
  bands). Buffer about 20 % larger.
- **Pictures in own list rows (`%Lb`):** lie over the row, so over the
  selection bar (before, their transparent pixels turned white: a box around
  the check mark of the option pages).
- **No list icons:** "Show Icons" no longer exists, `show icons` is always
  off. The main menu configuration no longer switches the icons on itself.
  Only the folder selection of the database and Disktidy still show icons,
  because they show the selection with them.
- **Pictures with alpha in `%VB`:** are laid over the content of the layer
  (before, blended with the background colour of the viewport: white boxes
  around the symbols without a tile, white corners at the clock box and at
  the preview of the album art corners). They are drawn only when the
  viewport is redrawn completely; a frame that a tag chooses changes in
  `%VB` only then. Note: a `%VB` viewport clears its area with its
  background colour when it is redrawn. So a picture in a `%VB` viewport of
  its own over another layer sees this colour, not the layer below. Pictures
  belong into the viewport that draws the area below them (the clock box is
  now in the field `LkField`), or the viewport gets the colour of the area
  with `%Vb` (buttons in the quick menu: `%Vb(e6e9ee)`).
- **Popups:** the firmware draws messages, progress and yes/no as a glossy
  panel in the style of the tiles (`apps/gui/popup.c`, parts from
  `firmware-assets/popups/`). The theme only sets the fonts: `popup font`
  (13 px bold) and `popup hint font` (11 px bold). The key lock shows no
  popup, only the lock of the status bar or the lock screen; "Bookmark
  Created" is a message without a symbol.
- **Counts in the sidebar:** `%Mc(albums)`, `%Mc(podcasts)`,
  `%Mc(audiobooks)`, `%Mc(playlists)`, `%Mc(bookmarks)`, `%Mc(recordings)`,
  `%Mc(shortcuts)` return the number as text. Playlists are the playlist
  files in the playlist folder, bookmarks the entries of "Recent Bookmarks";
  the firmware counts them again when the main menu appears and when
  "Recent Bookmarks" is written. The database counts the albums (every album
  name once, deleted ones and "<Untagged>" not; counted once per database
  state and media type). It counts podcasts and audiobooks the same way:
  albums below `/Podcasts` and `/Audiobooks`. While the database loads, the
  values are empty (`%?Mc(albums)<…>` asks for this). No numeric value for
  conditions: `%if(%Mc(…),=,0)` compares the number. Any other parameter is
  an error when loading.
- **Album list:** covers 52 × 52 without gaps, with a default cover and
  pictures for the three special entries, gloss bar from x 52, text from
  x 60, artist in `list secondary color`, arrows.
- **Firmware lists:** gloss bar, arrows (`%Lo`), values (`%LV`), inset 8.
- **Settings that switch directly:** shuffle, repeat and yes/no values
  switch with a click.
- **Album art corners** through `volume display` (graphic = rounded,
  numeric = square); the theme uses it to choose between two `%Cd` with a
  corner radius of 8 or 0.
- **Cover effect** `%Cd(tilt,perspective,reflection height,opacity,corner
  radius)` on the now playing screen and in the mini player.
- **Second line** through `statusbar` (off = alternating every 5 s, top =
  album, bottom = artist), in the mini player and on the lock screen.
- **Key lock** as a menu entry through `battery display` (graphic = lock
  screen, numeric = normal).
- **Closing popups cleanly:** after the volume popup the skin redraws
  completely once; `%pv` is scaled to `volume limit`.
- **Translatable texts:** every text the theme draws itself comes from the
  language files (`apps/lang`, phrases `LANG_THEME_*` and the date phrases at
  the end). Words and sentences through `%Sx(English text)`, for instance
  `%Sx(No music)`, `%Mc(albums) %Sx(albums)`, `%Sx(Random order)`, the USB
  texts and the title "Now playing"; the quick menu has titles of its own
  (`%Sx(Shuffle@quickmenu)`, `%Sx(Repeat@quickmenu)`: German "Zufall" and
  "Wiederholen"; the firmware shows only the text before `@`) and the values
  of the settings (`%Sx(On)`, `%Sx(All)`). Dates through the new tag
  `%cD(long|short|weekday|month)`: the firmware fills the date format of the
  language (`LANG_DATE_FORMAT_LONG`/`_SHORT`, e.g. "Monday, 9 November",
  "Montag, 9. November", "lunes, 9 de noviembre") and knows the full
  weekday and month names; `month` is the short month in capitals for the
  calendar card. The English text in `%Sx` must not contain commas or
  brackets: a comma separates parameters, and the skin would not load.
  German, English, English (US) and Spanish carry the texts; other languages
  show them in English. Details: `docs/ipod6g-more-changes.md`,
  "Translatable theme texts".

---

## 5. Still open in the theme (possible without firmware changes)

| Point | Approach |
| --- | --- |
| the firmware's cover effect in the generator | `tools/tools/albumart_fx.py` is an implementation of its own (floating point, 4 × 4 supersampling). `build_wps_cover.py` already uses the firmware's integer maths for both default covers (`cover116_fx.bmp`, and `cover100_fx.bmp` with `mini`); the album art corners preview (`artprev.bmp`) could follow. |
| removing the precomputed default covers | once point 14 is done: drop `cover116_fx`/`cover100_fx` from `build_assets.py` and the `%?C<|…>` branches from `build_skin.py`. |
| remains of option pages that can no longer be reached | `setting_tiles(opt=True)` still knows pictures for shuffle, repeat and scroll bar. They do no harm; removing them makes the `.sbs` a bit smaller. |
| recording with the sidebar | `%cs` = 3, microphone tile, running time and size. |
| low battery | a message of its own at a low `%bl`, if wanted. |
| accents slate, pink, violet | make bitmaps, cfg colours (the gloss colours too) and `SEL` per accent (values in `DESIGN.md` 3.4), as cfg files of their own. The key lock preview contains the blue progress bar and stays the same. |

---

## 6. Firmware pictures for the album list

Built into the fork. Content of `firmware-assets/` for later changes:

| File | Purpose |
| --- | --- |
| `albumart_list_default.png` | default cover 52 × 52 (square, no border) as a replacement for `apps/albumart_list_default.png` |
| `albumart_list_by_album.jpg` | template 53 × 53 for "[By Album]" |
| `albumart_list_all_tracks.jpg` | template 53 × 53 for "[All Tracks]" |
| `albumart_list_random.jpg` | template 53 × 53 for "[Shuffle]" |
| `*_512.png` | the same pictures in 512 × 512 as the source for other sizes |

Procedure in the fork:

1. Copy the three JPGs to `apps/` and run `tools/ipod6g_albumart_header.py`
   (writes `apps/albumart_list_special.h`).
2. Copy `albumart_list_default.png` to `apps/` and make
   `apps/albumart_list_default.h` from it as before.
3. The theme supplies the default cover for the mini player and the now
   playing screen itself (`cover100_fx.bmp`, `cover116_fx.bmp`, the same
   picture with the effect).

---

## 7. Checking on the device

From the notes on the firmware update:

| What | Look for |
| --- | --- |
| now playing with a cover | tilt and reflection complete, nothing cut off, no remains after a track change |
| now playing without a cover | default cover in the same place as a real cover (position, tilt, reflection, corners) |
| switching the corners | the option page opens, covers on the now playing screen and in the mini player change between rounded and square |
| switching the key lock | the option page opens, the lock screen appears or only the lock |
| playback menu | shuffle and repeat switch with a click, the value in the row changes at once |
| volume popup over the cover | after closing, the cover with its reflection is completely back |
| buffer time of playback | unchanged |

From the theme:

| What | Look for |
| --- | --- |
| the theme loads | no fallback to the default theme |
| album art corners preview | in the menu matching the setting; on the option page the picture changes between rounded and square while scrolling |
| key lock preview | in the menu matching the setting (value "Normal" or "Lock Screen"); on the option page the picture changes while scrolling, value "Screen unchanged" or "Clock and title" |
| sidebar after switching with a click | the value under the tile follows the value in the row (shuffle, repeat) |
| long names next to values | how far "Second Line in Player" and "Scroll Bar" are shortened, and whether the selected row scrolls |
| scrolling text in the selected menu row | scrolls in the row, the gloss bar stays complete behind it |
| mini player | cover with reflection, nothing cut off at the bottom; title and second line below it free |
| lock screen with hold on and off | in the main menu, database and now playing; after unlocking the list is completely back |
| title of the half status bar | switches to the short width during disk access; no flicker |
| album rows | 52 px high, covers without gaps, the gloss runs on behind the scrolling text |
| sidebar tiles | the right tile for every menu entry in each language |
| texts in another language | after changing the language (Settings → General Settings → Language) the sidebar, lock screen, USB screens and quick menu show the texts in that language, the date in its order; no "<ERR>" |
| battery gauge | 12 steps; the first step = level unknown |
| memory | bitmaps in RAM about 0.59 MB, plus the `%Cd` buffer of 160 KB, together about 0.74 MB; buffer time of playback unchanged |
| track info | Rockbox returns labels as "[Title]" in lines of their own; whether the brackets can be cut off cleanly with `%ss` is open |

---

## 8. Possible without changes to Rockbox (done in the theme)

- Sidebar per selected entry: `%LT` returns the selected entry in normal
  viewports too.
- Own list rows on option pages with a check mark: `%Lb` with `%Lc`.
- Cover sizes: exactly one `%Cl` per skin. Now playing 116 × 116, status
  bar skin 100 × 100. Buffer cost per buffered track about 27 + 20 KB.
- Rounded or square cover corners through two `%Cd` and
  `%?if(%St(volume display), =, graphic)`.
- Picture previews in the sidebar (album art corners, key lock): a complete
  sidebar with a picture per variant; in the menu `%St(...)` chooses, on the
  option page `%LT`.
- Status bar with a left-aligned title and symbols that move up on the
  right: conditional viewports depending on `%mp`, `%mh` and `%lh`.
- Loading indicator: `%lh` with 12 phases of `%t(0.1)`.
- Status bar in USB mode: `%cs` = 21, after the eject 22.
- Lock screen over all menus: the UI area on an invisible viewport (`%VI`);
  on a change Rockbox redraws the list itself (`sb_skin_get_info_vp()`).
- Analogue clock without a stack of pictures: the hand positions as
  characters of a font.
- Blue field without a full-screen bitmap: 16 `%dr` gradients.

## 9. Checker

Compile `tools/check/main.c` against the skin parser of this repository
(`lib/skin_parser` with the entries of the fork's tags):

```
gcc -O1 -w -D__PCTOOL__ -I lib/skin_parser GlossySlate/tools/check/main.c \
    lib/skin_parser/{skin_parser,skin_buffer,skin_debug,skin_scan,tag_table}.c -o checkskin
./checkskin GlossySlate/.rockbox/wps/glossyslate.sbs
```

It prints the number of elements, or the line and column of the first
error. Compiled against stock Rockbox it reports errors at the fork's tags.
