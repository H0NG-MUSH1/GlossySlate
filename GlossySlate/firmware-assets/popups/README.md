# Glossy Slate – popups: design handover to the firmware

This is the design brief the popups were built from. What the firmware does
in the end, and where it differs from this brief, is described in
[docs/ipod6g-popups.md](../../../docs/ipod6g-popups.md); for instance there
is no loading circle and no lock symbol, and the parts are stored with 8 bit
alpha in the firmware.

Stock Rockbox draws popups as a plain box with a border in the theme's
colours. This design gives them the glossy panel of the tiles. A skin cannot
style popups, so this is done in the firmware. The design canvas has the
board "Popups".

The volume is not part of it: the theme already shows it as a bar on the
now playing screen.

| Kind | Rockbox | Example |
| --- | --- | --- |
| message | `splash()` / `splashf()` in `apps/gui/splash.c` | "Settings Saved" |
| message with symbol | the same calls, symbol depending on the message (section 5) | "Settings Saved" with a check mark |
| progress | `splash_progress()` | "Building database…" |
| yes/no | `gui_syncyesno_run()` in `apps/gui/yesno.c` | "Reset all settings?" |

## 1. Design

| Part | Value |
| --- | --- |
| panel | radius 12, border 1 px `#05070A`, top row 1 px `#8E9CAE`, plus 1 px light inside (white 18 %) |
| gradient (vertical) | `#6A7686` (2 px) → `#4C5664` (22 %) → `#323A46` (44 %) → `#1C2028` (50 %) → `#11141A` (78 %) → `#0B0D12` (100 %) |
| shadow | 0 4 10 black 42 % and 0 1 2 black 35 %; included in the pictures, margin left 12, top 9, right 12, bottom 16 |
| text | 13 px bold white, centred, line spacing 16 (`16-GlossySlate-Bold13.fnt`) |
| second text | 11 px bold `#C5CFDD` (`14-GlossySlate-Bold11.fnt`), only for button hints |
| symbol | 48 × 48, `#DFE6F3` as on the tiles |
| bar | 8 high, radius 4. Track `#07080C` → `#1A1E26` with an inner shadow and a 1 px light edge below. Fill in accent blue like the slider fill (`#8EC0F4` → `#5698E8` 45 % → `#2F70D6` 55 % → `#3D82E0`) |
| button "Yes" | 26 high, radius 13, gloss bar blue `#5896E6` → `#1A55BE`, edge `#174A9E`, text white 13 px bold |
| button "No" | the same shape in slate `#6A7484` → `#3A424E`, edge `#262C35` |

## 2. Layout

The panel (W × H, without the shadow) lies centred on the whole screen:
`x = (320 − W) / 2`, `y = (240 − H) / 2`. So popups have to be drawn in the
full screen viewport. In the menus the UI viewport of the skin is only
160 px wide.

Padding left and right 14, top and bottom 12.

| Kind | Width W | Height H | Content (position relative to the panel) |
| --- | --- | --- | --- |
| message, n = 1–5 lines | text + 28, at least 120, at most 240 (line break at 212) | 24 + 16 n: 40, 56, 72, 88, 104 | line i at y = 12 + 16 i |
| message with symbol, n = 1–2 | text + 28, at least 132, at most 240 | 104 / 120 | symbol at ((W − 48) / 2, 16), line i at y = 74 + 16 i |
| progress, n = 1–3 | text + 28, at least 208, at most 240 | 24 + 16 n + 16: 56, 72, 88 | lines from y = 12; bar at (14, 12 + 16 n + 8), width W − 28 |
| yes/no, n = 1–3 | 240 | 80 + 16 n: 96, 112, 128 | question from y = 12; buttons at y = 12 + 16 n + 12, x = 14 and x = 124, 102 × 26 each, text centred in them; hint 11 px below at y + 30 |

Yes/no: Rockbox shows `LANG_CONFIRM_WITH_BUTTON` ("SELECT = Yes") and
`LANG_CANCEL_WITH_ANY` ("Any Other = No") with it. In the design "Yes" and
"No" stand in the buttons, below them "Center button" and "Other button".
With a time limit the time left follows the hint, e.g. "Other button (10)".
The answer afterwards ("Reset done") is a message.

## 3. Drawing with the parts

For every height the panel is split into three parts. The gradient is
vertical, so the middle can be put side by side as often as needed:

```
left   panel_hH_left    at (x − 12, y − 9)              26 wide
middle panel_hH_middle  W − 28 times from (x + 14, y − 9)  1 wide
right  panel_hH_right   at (x + W − 14, y − 9)          26 wide
```

All three are H + 25 high (with the shadow). Checked: for W = 150, 190 and
240 the assembled picture is the same as the rendered panel within 2 colour
steps.

Bars and buttons the same way: track and fill each left 4, middle 1, right
4 (track 9 high with the light edge, fill 8). If the fill is narrower than
8 px, draw only the left part and cut it off on the right. Buttons: left 14,
middle 1, right 14, or the finished 102 × 26.

Other heights were exported by the design's own tools, which are not part
of this repository.

## 4. Loading circle

`symbol_loading` has 12 frames of 48 × 48, stacked vertically, like the
loading indicator of the status bar. Advance a frame every 0.1 s while
waiting.

## 5. Symbol per message (proposal)

`splashf()` often gets a language ID. The symbol can be chosen by it:

| Symbol | Messages |
| --- | --- |
| `symbol_done` | `LANG_SETTINGS_SAVED` ("Settings Saved"), `LANG_RESET_DONE_CLEAR` ("Reset done") |
| `symbol_locked` | `LANG_KEYLOCK_ON` ("Buttons Locked") |
| `symbol_unlocked` | `LANG_KEYLOCK_OFF` ("Buttons Unlocked") |
| `symbol_warning` | `LANG_TAGCACHE_BUSY` ("Database is not ready"), `LANG_FAILED` |
| `symbol_loading` | `LANG_WAIT` ("Loading…") |
| `symbol_info` | other messages, if wanted |

All other messages stay messages without a symbol.

## 6. Memory

Nothing the theme loads into RAM may disturb playback. In memory (RGB565
with 4 bit alpha):

| Parts | about |
| --- | --- |
| panels, all 9 heights | 135 KB (8–20 KB per height) |
| symbols without the loading circle | 28 KB |
| loading circle (12 frames) | 69 KB |
| buttons in three parts | 3 KB (finished buttons another 13 KB) |
| bars | below 1 KB |

Proposal: keep only the heights 40, 56 and 72 at all times (31 KB) and load
the others when a popup opens. Without the loading circle this comes to
about 65 KB.

## 7. Checking on the device

| What | Look for |
| --- | --- |
| message over the list and the sidebar | soft shadow, no hard steps. The display has 16 bits, alpha only 4 bits |
| line break | long messages break at 212 px, the panel grows in steps of 16 |
| progress | the bar fills without flicker (Rockbox redraws up to 20 times a second) |
| yes/no | center button = yes, any other button = no; time left visible if set |
| after closing | the screen below is completely back (as with the fork's volume popup) |

## 8. Content of this folder

| File | Purpose |
| --- | --- |
| `*.png` | all parts (PNG with alpha) |
| `parts.json` | sizes of all parts and the margin for the shadow |

`tools/ipod6g_popup_parts.py` turns the parts into
`apps/gui/popup_parts.h`.
