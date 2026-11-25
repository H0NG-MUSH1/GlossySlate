# Fast scrolling in the database

As of 25 November 2026 (`IPOD_6G`).

Turning the wheel briskly for a while in a list of the database (one
rotation a second or faster, for at least a second) shows a square popup in the middle of the screen with the initial of the
selected entry, in the style of the GlossySlate popups. From then on the
wheel goes through the letters instead of the rows, at any speed: every
step of the wheel (4 clicks, 24 to a turn) shows the next or the previous
letter, and the list behind the popup jumps to the first entry with that
letter. The popup stays on the screen from the start to the end, only its
letter changes. 2 s after the last step it goes, and the selection stays on
that entry.

Example: in the album list the selection is on "Elbow", and the wheel is
turned on briskly. After a second the popup shows the letter the list has
reached, say "K", and the list stands on the first album with "K".
Turning on slowly shows "L", "M" … in the same popup, and the list behind
it follows; stopping at "M" leaves the selection on the first album with
"M" when the popup goes.

## Rules

| Point | Behaviour |
| --- | --- |
| Where | every list of the database with tag values or tracks: artists, albums, genres, podcasts, audiobooks, composers, years, track lists sorted by name … The menus of the database (its root, "Cover Flow") have no letters. |
| Start | the wheel has been turned for at least 1 s, and in the last second by at least one rotation (96 clicks): one rotation a second or faster, kept up for a second. The speed is the mean over that second, as single steps vary too much. A little above the speed at which the acceleration of the list sets in (0.85 rotations a second; at one rotation a second it moves 3 rows a step). The turn has to be in one direction, without a pause of more than 0.3 s between two steps and without lifting the finger; each of these starts it anew. Faster turning does not start it sooner than after 1 s; scrolling row by row never starts it. |
| Measuring | in the driver of the wheel (`button_wheel_turned_fast()`, `button-clickwheel.c`), from the clicks of every step and their time in µs: the events of the wheel always say one step, and steps are dropped while the button queue is not empty, so counting events would depend on how fast a list draws. |
| Letters | `A`–`Z` by the first character of the name, upper and lower case alike; digits, signs and other scripts (Ä, Ö, É, Cyrillic …) are `#`. Only letters that occur in the list are shown, in the order of the list. |
| Order | Rockbox sorts by bytes (`strncasecmp()`, `strnatcasecmp()` with "Interpret Numbers"): digits and signs come before "A", names beginning with other scripts after "Z". So `#` can come twice, at the start and at the end; both are shown where they are. |
| Lists in another order | a list whose initials are not grouped (tracks in track order, episodes by date) gets no letters: more than two groups beyond one per letter switch it off. |
| Small lists | fewer than 20 entries (after "[All Tracks]", "[Shuffle]" …): no letters. |
| Large lists | a list larger than the entry cache of the database comes in chunks and unsorted (`retrieve_entries()`); it gets no letters. |
| Special entries | "[All Tracks]", "[Shuffle]" … at the top are not part of the letters; a jump never lands on them. |
| While it is shown | the popup stays; a step of the wheel selects the first entry of the letter, draws the list and the popup with the new letter over it. Neither goes to the LCD by itself (`popup_letter()` only its own area, with the popup in it); the whole screen goes with the next `get_action()` (`GUI_EVENT_ACTIONUPDATE`, `viewportmanager_update()`), list and popup together, so the popup does not flash. When it goes, the list is drawn before the popup is closed, so nothing old is put back. |
| End | 2 s after the last step of the wheel. Any other button closes the popup at once and does nothing else (the selection stays on the letter). The redraws the covers of the album list post when one has been loaded (`BUTTON_REDRAW`, `albumart_list.c`) are no button: they draw the list with the new covers behind the popup. (Taken as a button they closed the popup at once after a jump to albums whose covers were not loaded yet, and the next step of the fast wheel started it again: the popup seemed to flash.) System events (USB, power off) close it and take their way. |
| Wheel at the ends | stays on the first or last letter (no wrap). |

## Cover Flow

Cover Flow does the same while it browses the covers (not on the back with
the track list): turning the wheel briskly shows the letter of the centre
album, every step of the wheel goes to the next or previous letter, and
Cover Flow jumps without animation to the first album of it, as its jump
key does (`set_current_slide()`). The letter follows the order of the
albums:

| Sort albums by (Cover Flow settings) | Letter |
| --- | --- |
| Artist and name, artist and year (default) | initial of the album artist |
| Name | initial of the album |
| Year | no letters (only digits) |

While the album art cache is still being built (the percentage in the
corner), there are no letters, as the jump key waits for it too: the order
of the albums may still change. The popup is the one of the database lists
(`popup_letter()`), drawn over every frame before it goes to the LCD, so it
stays on the screen while the covers change behind it.

## Look

A square panel of 112 × 112 from the panel parts of the popups (height
112, `popup_parts.h`), centred on the whole screen (x 104, y 64), with its
shadow. The letter: Liberation Sans 2 Bold, 72 px, in the light symbol
colour `#DFE6F3` (like the symbols of the popups and the digits of the lock
screen clock), centred on its ink horizontally; the cap height is centred
vertically, so all letters share one baseline ("Q" reaches below it).

## Implementation

| File | Change |
| --- | --- |
| `firmware/target/arm/ipod/button-clickwheel.c`, `firmware/export/button.h` | `button_wheel_turned_fast()`: the clicks and times of the last 26 steps in a ring; once the turn has lasted 1 s, the clicks since the newest step at least 1 s old must come to 96 a second. If the ring holds no step that old any more, more than 25 steps of at least 4 clicks came within the second: fast enough. Reset by a reversal, a pause of the wheel and lifting the finger. |
| `apps/tree.c` | `fs_after_move()` asks `button_wheel_turned_fast()` after `gui_synclist_do_button()` and starts the letters (a list without letters is not tried again until the wheel pauses or another button comes); `fs_build_runs()` groups the entries by initial; `fs_handle()` takes the actions while the letter is shown (the wheel, the timeout with `get_action()` every 0.1 s, other buttons). The popup is drawn again if something drew over it (`popup_intact()`). |
| `apps/tagtree.c`, `apps/tagtree.h` | `tagtree_fast_scroll_ok()`: a table of tag values or tracks held in memory as a whole (not in chunks); `tagtree_entry_initial()`: the first byte of the name of an entry, 0 for texts of the language (menu and special entries). |
| `apps/gui/popup.c`, `apps/gui/popup.h` | `popup_letter()`: the square panel with the letter, `draw_glyph()` blends a 4 bit mask with the ordered dither of the popups; `popup_intact()`: whether the popup is still untouched, without the side effects of `popup_screen_state()`. |
| `apps/gui/popup_letters.h` | the 27 letters (A–Z, #) as 4 bit alpha masks of their ink boxes, about 31 KB, generated |
| `tools/ipod6g_popup_letters.py` | makes `popup_letters.h` from Liberation Sans 2 Bold (Pillow): `python3 tools/ipod6g_popup_letters.py LiberationSans-Bold.ttf`. The font: <https://github.com/liberationfonts/liberation-fonts/releases> (2.1.5, SIL Open Font License 1.1), the source of the GlossySlate fonts as well. |
| `apps/plugin.h`, `apps/plugin.c` | at the end of the plugin API (version 289): `get_action_data()`, `button_wheel_turned_fast()`, `popup_letter()`, `popup_close()` |
| `apps/plugins/pictureflow/pictureflow.c` | the same logic for Cover Flow (`fs_after_move()` after `show_next_slide()` / `show_previous_slide()`, `fs_handle()` before the actions, the popup before `mylcd_update()`), letters by the sort order of the albums |

The speed and length of the turn that starts the letters
(`FAST_TURN_CLICKS`, `FAST_TURN_USEC`, `FAST_TURN_PAUSE`) are in
`button-clickwheel.c`, the others (`FS_GAP`, `FS_HOLD`, `FS_MIN_ENTRIES`,
`FS_MIN_ALBUMS`) at the top of the code in `tree.c` and `pictureflow.c`. With the new plugin API version every plugin has to be
installed together with the new firmware (an old one is refused).
