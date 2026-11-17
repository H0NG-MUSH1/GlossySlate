# More firmware changes (iPod Classic 6G)

This file describes the changes of the fork outside the album list, the
database media types and the popups. Those are described in
[ipod6g-album-list-covers.md](ipod6g-album-list-covers.md),
[ipod6g-database-media-types.md](ipod6g-database-media-types.md) and
[ipod6g-popups.md](ipod6g-popups.md). The Glossy Slate theme lives in
`GlossySlate/`.

## Files

| File | Change outside the album list |
| --- | --- |
| `apps/gui/skin_engine/skin_display.c` | Scales the graphic volume bar to `global_settings.volume_limit`, so the limit that is set always means 100 % bar width. An empty value range is caught. |
| `firmware/drivers/audio/cs42l55.c` | Mutes first when the sample rate changes (`audiohw_set_frequency()`): master digitally with soft ramp, headphone and line analogue; then `CLKCTL2`, 5 ms to settle, old registers back. The CS42L55 is the I2S clock master, and switching with the output open clicked. With a fixed playback frequency of 48 kHz this happened at the first playback after every start (the hardware starts at 44.1 kHz and only then switches; `pcm_apply_settings()` only programs a change), with "Automatic" at every change between 44.1 and 48 kHz. If the output is still muted (start before `audiohw_postinit()`), it only switches. |
| `firmware/common/fat.c` | Protects the bounce buffer (`fat_bounce_buffers`, used on the iPod 6G for every transfer through a buffer that is not aligned for DMA) with a mutex. `read()` and `write()` only hold the read lock of the file system, so two threads could use the buffer at the same time: a write copied its data into it and waited for the ATA driver, another thread read into the same buffer, and the disk got that thread's data. Seen in screen dumps while the database was built: whole 512 byte sectors of cover JPEGs from audio files. It affected every file written while another thread was reading (a bug in stock Rockbox). |
| `apps/gui/skin_engine/skin_render.c` | Notices when a dynamic skin viewport disappears and redraws the skin completely once, so that no white rectangle stays after the volume popup goes away. Draws the progress bars of a line only after the text of the line (see "Volume bar and popup"). The same when a %VB viewport appears: it draws only into the backdrop buffer, so its area is copied from there to the screen afterwards (otherwise the sidebar stayed white except for its text lines after the start, because the first complete picture was made before the selection in the list). |
| `firmware/target/arm/s5l8702/lcd-s5l8702.c` | On the iPod 6G switches the LED backlight off right before `lcd_powersave()` and reports, after a complete LCD transfer, that the picture is ready. The internal transfer during `lcd_awake()` does not count as a finished UI picture. |
| `firmware/target/arm/s5l8702/ipod6g/backlight-6g.c` | Restores the normal PMU dimming level after waking up. Before switching the LED on it waits for a completely transferred picture or at most `HZ / 10` (about 100 ms with `HZ = 100`). A semaphore coordinates the LCD and backlight threads. |
| `firmware/target/arm/s5l8702/ipod6g/backlight-target.h` | Declares `backlight_hw_frame_ready()` and `backlight_hw_frame_pending()` for this coordination. |
| `apps/lang/deutsch.lang`, `apps/lang/english.lang`, `apps/lang/english-us.lang` | Replace ambiguous texts of the sound menu with unambiguous terms. The two additional IDs of the former menu entry "Update album covers" belong to the album list (documented separately) and are unused since it was removed. |
| `manual/configure_rockbox/sound_settings.tex` | Adapts the Haas, AFR and compressor sections to the new English menu names. |
| `docs/VERSION` | Sets the visible version to `4.0 (dev build)`. |
| `tools/version.sh` | Reads `docs/VERSION` as the complete version string; also improves the quoting of the shell variables. |
| `firmware/firmware.make`, `tools/checkwps/checkwps.make` | Pass `SVNVERSION` quoted to `genversion.sh`, so that a version string with spaces does not fall apart into several shell arguments. |

## Volume bar and popup

`apps/gui/skin_engine/skin_display.c:draw_progressbar()` uses the minimum of
the audio driver for the volume tag and as maximum the lower of the driver
maximum and `global_settings.volume_limit`. With a volume limit of 0 dB the
highest reachable value fills the bar completely. This change applies to all
skins with a graphic volume bar.

In `apps/gui/skin_engine/skin_render.c` clearing a hidden viewport sets
`hidden_viewport_cleared`. After the normal render pass a single call with
`SKIN_REFRESH_ALL` follows; `repainting_after_hide` prevents a loop. Without
the complete redraw a light rectangle stayed visible where a temporarily
shown viewport (such as a volume popup) had been.

A skin recognises the minimum volume by the first branch of `%?pv<…|…|…>`
(three branches are needed, otherwise 0 dB falls into the first branch).
`%if(%pv, =, -90)` never matches on the iPod 6G (CS42L55, minimum −60 dB).

When a conditional switches to a branch with a bar, such as `%?pv<…>` when
raising the volume from the minimum, the line counts as changed and
`write_line()` clears it with the background colour. This used to happen
after the bar was drawn already; until the next update a white bar stood in
the popup. So `skin_render.c` collects the bars of a line in `line_bars` and
draws them with `draw_line_bars()` only after `write_line()`. This applies to
all skins; text and bars in the same line therefore lie over the text, not
under it.

## Locking, unlocking and backlight

With the LCD going to sleep immediately, the PMU dimming ramp could still be
running while the panel already went to sleep. So on the iPod 6G
`lcd_sleep()` calls `backlight_hw_kill()` before `lcd_powersave()`.
`backlight_hw_on()` writes the normal PMU dimming level `0x14` again at the
next wake-up before it switches the LED on. This removed the white flash
seen when locking.

When unlocking, `lcd_awake()` first loads the LCD content and sends
`LCD_EVENT_ACTIVATION`. The user interface then draws its new state. To
switch the backlight on, the backlight thread now waits for a complete LCD
transfer. `lcd_waking` keeps the internal transfer in `lcd_awake()` from
giving the signal too early. After at most `HZ / 10` the backlight is
switched on anyway, so that screens without a complete update do not stay
dark. The state variables and functions are in the three iPod and S5L8702
files of the table.

These firmware changes do not depend on the skins.

## Sound menu and documentation

The existing language IDs and the menu structure stay. In the three
language files the texts in `<source>`, `<dest>` and `<voice>` were changed
accordingly. The most important ones:

| Function / language ID | German | English and English (US) |
| --- | --- | --- |
| `LANG_VOLUME_LIMIT` | Maximale Lautstärke | Volume Limit |
| `LANG_SURROUND` | Haas-Stereoverbreiterung | Haas Stereo Widening |
| `LANG_SURROUND_FX1` | Obere Bypass-Grenzfrequenz | Upper Bypass Frequency |
| `LANG_SURROUND_FX2` | Untere Bypass-Grenzfrequenz | Lower Bypass Frequency |
| `LANG_SURROUND_METHOD2` | Effekt nur auf Seitensignal | Process Side Channel Only |
| `LANG_SURROUND_MIX` | Original-/Effektanteil | Dry/Wet Mix |
| `LANG_AFR` | Präsenz-/Hochtondämpfung | Presence/Treble Attenuation |
| `LANG_COMPRESSOR` | Dynamikkompressor | Dynamic Range Compressor |
| `LANG_COMPRESSOR_RATIO` | Kompressionsverhältnis | Compression Ratio |
| `LANG_PBE` | Psychoakustische Bassanhebung | Perceptual Bass Enhancement |

The value `2:1` was not renamed. The sound processing was not changed by
these texts. The sections on Haas stereo widening, treble attenuation and
the compressor in `sound_settings.tex` use the new English names.

## Settings "Status-/Scrollbar"

With a status bar skin of its own, "Status Bar", "Volume Display" and
"Battery Display" in the firmware only affect the built-in status bar, which
a theme with its own status bar skin does not use. Glossy Slate uses them for
its own purposes. So on the iPod 6G they are named in `apps/settings_list.c`
after what they do; cfg names and values stay, so that saved settings and
`%St(...)` in the skins keep working:

| cfg name | Title | Options (cfg value) | Effect in the theme |
| --- | --- | --- | --- |
| `statusbar` | Second Line in Player (`LANG_PLAYER_SECOND_LINE`) | Album and Artist (`off`), Album (`top`), Artist (`bottom`) | second line on the now playing screen and in the mini player |
| `volume display` | Album Art Corners (`LANG_ALBUMART_CORNERS`) | Rounded (`graphic`), Square (`numeric`) | corner masks over covers and the default cover |

The new language IDs are at the end of `english.lang`, `english-us.lang` and
`deutsch.lang`. "Battery Display" (`battery display`) is called "Key Lock"
on the iPod 6G (see "Firmware for Glossy Slate"). "Scroll Bar Width" sets
the width of the knob (see "Lists in the retail style" in
[ipod6g-album-list-covers.md](ipod6g-album-list-covers.md)).

Skins can show option pages of their own for these settings; titles and
options come from the same language texts through `%Sx(...)`. "Backlight on
Lock" shows the normal list (Normal/Off/On), which controls the backlight
when locking.

## Analysis: clicks in some large FLAC files

As of 9 November 2026, without a code change. Examined were FLAC files with
24 bit / 48 kHz and up to about 2 Mbit/s.

- 48 kHz does not overload the iPod 6G: the hardware plays 48 kHz directly
  (`HW_SAMPR_CAPS` with `SAMPR_CAP_48`). With `playback frequency: 48000`
  44.1 kHz tracks are resampled, 48 kHz tracks are not. The PCM buffer holds
  at least 3 s (`MIN_BUFFER_SIZE` in `apps/pcmbuf.c`), so short CPU
  bottlenecks of other threads do not cause dropouts.
- The cause is clipping by the perceptual bass enhancement (`pbe: 25`). Its
  equaliser (`lib/rbcodec/dsp/pbe.c`) raises the level by a net 2.3–2.8 dB
  around 64 Hz, around 2 kHz and above 16 kHz after an overall cut of
  −3.0 dB (−0.5 dB plus the default precut of −2.5 dB). The sound chain ends
  with `clip_sample_16()`, and only after that the CS42L55 sets the volume:
  whatever goes above 0 dBFS is clipped hard, and that is the click.
- Recalculated (the PBE's equaliser applied to the files on a computer):
  loud, heavily compressed recordings clip by up to +2.5 dBFS, in one track
  in almost every second; quieter recordings never. With a precut of
  −4.5 dB only single samples were left.
- Remedy in the settings: bass enhancement off, or its precut at −4.5 dB plus
  the dynamic range compressor as a limiter (it is the last stage after the
  PBE).

## Headset remote while idle

If the remote is switched off or no headphones are plugged in, the Mikey
thread (`firmware/target/arm/s5l8702/ipod6g/mikey-6g.c`) checks every 0.5 s
again, as in stock Rockbox. With the remote switched off it woke up 10 times
a second, only so that switching on took effect after 0.1 instead of 0.5 s.
Switching off still takes effect at once, because `mikey_button_read()`
checks the setting itself; with headphones plugged in and the remote
switched on the thread polls every 20 ms as before.

## Headset remote: no play/pause when plugging in (16 November 2026)

After a restart, plugging in the headphones started the last playback by
itself. While the plug is pushed in and Mikey's detection engine arms, the
center button register (reg4) can read pressed and released again. The
"armed" guard only caught a reading that starts pressed; a
released-pressed-released flicker counted as one click and sent play/pause
(two flickers even "next"), and with nothing playing Rockbox resumes the
last playlist on play/pause (`apps/misc.c`). The settings were not the
cause: "Pause on Headphone Unplug: Pause" never resumes on plugging in.

`firmware/target/arm/s5l8702/ipod6g/mikey-6g.c`: like the volume buttons'
window (200 ms), no center press counts within 1 s after (re)arming
(`MIKEY_CENTER_ARM_POLLS`, 50 polls of 20 ms), and a press still held when
the window closes has to be released first. Re-arming happens on every
insertion, after recording from the jack microphone and when the remote is
switched on again. Clicks after that second work as before.

Checked on the Mac with the driver file itself and stand-ins for I2C and the
kernel: insertion flicker (once and twice), a click and a double click 1.2 s
after plugging in, and a press held through the window. The previous driver
gave play/pause or "next" for the flickers, this one nothing; the real
clicks give the same buttons as before.

## USB: noticing the eject

When the computer ejects the drive (Finder "Eject": SCSI START STOP UNIT
with the eject bit), the USB screen shows "Ejected – The cable can now be
disconnected." The iPod stays in USB mode until the cable is pulled.

| File | Change |
| --- | --- |
| `firmware/usbstack/usb_storage.c` | `usb_storage_all_ejected()`: true when all drives of this connection are ejected (`ejected[]`, which Rockbox kept already but did not pass on). `connection_active` holds from `usb_storage_init_connection()` until `usb_storage_disconnect()`, so that the old state does not apply briefly after plugging in again |
| `firmware/export/usb.h` | declaration |
| `apps/misc.h` | `ACTIVITY_USBEJECTED` after `ACTIVITY_USBSCREEN`: `%cs` = 22 (at the end of the list, no values moved) |
| `apps/gui/usb_screen.c` | The loop in `handle_usb_events()` wakes up every 0.5 s and asks; at the first "true" it replaces `ACTIVITY_USBSCREEN` with `ACTIVITY_USBEJECTED` (same stack depth), and the status bar skin redraws. Before `font_disable_all()`, `usb_screen_cache_glyphs()` loads letters, umlauts, digits and punctuation into the glyph cache of every loaded font, because in USB mode the font files are closed and the second screen comes only later |

If an operating system sends no START STOP UNIT when ejecting, the first
screen stays. Design: `GlossySlate/DESIGN.md`, 6.8.

## Firmware for Glossy Slate

Made after `GlossySlate/ROCKBOX-CHANGES.md` (section 0 there lists
everything the theme needs). All parts are inside `#ifdef IPOD_6G`.

| Area | Implementation |
| --- | --- |
| Theme settings | New, only through the cfg: `list secondary color` (artists of the album rows, values of settings), `list arrows` and `list arrow color`, `list edge inset`, `line selector gloss top/bottom/edge color`; `selector type` knows `bar (gloss)`. Fields at the end of `struct user_settings` (`apps/settings.h`). The firmware has no values of its own: colours are `-` if not given (`LIST_COLOR_FROM_THEME`) and then follow the foreground colour or the gradient of the selection bar; arrows off, inset 0. A theme cfg without the value resets it to that when it loads. |
| Key lock | `battery display` is called "Key Lock" on the iPod 6G (Lock Screen/Normal) and is back in the menu Status-/Scrollbar. |
| Switching directly | `option_cycles()`/`option_cycle()` in `apps/gui/option_select.c`: yes/no and on/off settings (`(flags & F_BOOL_SETTING) == F_BOOL_SETTING`, because `F_BOOL_SETTING` shares bits with `F_T_INT`) and "Repeat" switch on with a click in the menu (`apps/menu.c`, case `MT_SETTING`), with callback and saving as on the option page. All other settings open their option page. |
| Values and arrows in lists | New list callbacks `callback_get_item_value` and `callback_item_opens` (`apps/gui/list.h`), set in `apps/menu.c` and `apps/tree.c`. Values in `list value color` (`list secondary color` if not given). After drawing a firmware list, `gui_synclist_draw()` remembers its selected entry (`skinlist_note_drawn_selection()`); without an active `%Lb` list `%LT`, `%LV` and `%Lo` return it, so that skins next to firmware menus know the selected entry. In very narrow viewports (hidden UI viewport) the room for the arrow and the inset are left out. `list_draw()` writes the name of a row with a value into a narrower viewport and the value right-aligned next to it; the arrow, 6 × 10, as a 4 bit alpha mask in the right edge strip. For `%Lb` rows there are `%LV` (value) and `%Lo` (opens a level), `apps/gui/bitmap/list-skinned.c`. |
| Gloss bar | `STYLE_GLOSS` in `apps/gui/line.c`: gradient over the colours at 45 % and 55 %, first row 38 % lighter, last row the edge colour. `deco_height`/`deco_offset` in `struct line_desc` let the title line of an album row continue the gradient of the whole row. In skins `%Vs(gloss)`. `blend_color()` computes the colour channels signed; unsigned it gave values above 16 bits and striped rows. |
| Battery after a full charge | `level_after_full_charge()` in `firmware/powermgmt.c`, see "Performance, scrolling text and battery gauge" below. |
| Complete redraw with `%VB` | For every skin with a backdrop layer (status bar, now playing, recording), a complete redraw ends with a copy of the finished backdrop buffer to the screen around the UI viewport (`backdrop_around()`; everywhere without a UI viewport or with the hidden 1 × 1 one) and a second pass for the foreground (`layered_full` in `skin_render()`). Otherwise the screen shows the backdrop only where a viewport clears itself: after a screen without the status bar skin or a clear without the backdrop, the sidebar and parts of the status bar stayed white, and on the now playing screen at the first start the gap between the times. `sb_skin_peek_info_vp()` returns the UI viewport of the status bar skin without the redraw that `sb_skin_get_info_vp()` triggers on a change. |
| Recording list | With the recording skin the list shows "name: value" as the name on the left and the value on the right (`reclist_get_label()`, `reclist_get_value()` in `apps/recorder/recording.c`). |
| Hiding with `%VB` | After a viewport is hidden, `skin_render()` redraws in three steps: only the `%VB` layer, then the areas of all viewports hidden in this frame from the finished backdrop buffer, then the foreground (`render_layers`, `hidden_areas`). Before, hidden foreground viewports took the background colour of a `%VB` layer just hidden and stayed white. |
| Tilting and mirroring covers | `%Cd(tilt,perspective,reflection height,opacity,corner radius)`, `apps/gui/skin_engine/skin_albumart_fx.c`. Integer maths (16.16, `fp14_sin/cos`), computed once per cover, buffer in the skin buffer the size of the `%Cl` box plus margin and reflection, RGB565 with 8 bit opacity per pixel. `skin_aa_fx_draw()` blends the picture row by row with the backdrop buffer itself (`lcd_get_backdrop()`, without it with the background colour) and dithers to RGB565 (4 × 4, aligned to the screen); with the 4 bit alpha of the skin engine the reflection at 34 % had only 5 steps, visible as broad bands. Without parameters `%Cd` draws as before. |
| Font of the artist line | Theme setting `list secondary font` (`list_secondary_font_file`, default `-`). `list_secondary_font_apply()` in `apps/gui/list.c` loads it in `settings_apply()` (160 glyph cache; `font_load_ex()` shares a file a skin has loaded already, by its path). `apps/gui/bitmap/list.c` draws the artist line of the album list with it, moved by the difference of the ascents onto the baseline of the list font. |
| Values in the row | `option_cycles()` (`apps/gui/option_select.c`): switching directly and a value in the row only for bool settings with `LANG_SET_BOOL_YES/NO` or `LANG_ON/OFF` and for "Repeat"; "Inverse/Normal" opens its option page. |
| Menu texts | Main menu: `db_browser` with `LANG_FILTER_MUSIC` ("Music") instead of `LANG_TAGCACHE`. `deutsch.lang`: "Wiedergabeliste(n)" is "Playlist(s)" everywhere (all 25 texts, display and voice, e.g. "Aktuelle Playlist", "Max. Playlist-Länge", "Playlist-Verzeichnis zurücksetzen"), "Neueste Lesezeichen" is "Neue Lesezeichen" (`LANG_BOOKMARK_MENU_RECENT_BOOKMARKS`), and the title of the main menu in the status bar is "iPod" instead of "Rockbox" (`LANG_ROCKBOX_TITLE`, used only there). |
| Empty database menus | `tagtree.c`: an entry that loads a menu which defines nothing (`==>` to an empty menu) is not shown in the list (`root_item_hidden()` in `load_root()`). This concerns "Custom menu" (`"Custom menu" ==> "custom"`): Rockbox' place for views of one's own from `/.rockbox/tagnavi_custom.config`; without that file it showed an empty white list. With the file the entry appears again. `tagtree_open_root_entry()` counts hidden entries for the row. `deutsch.lang` (only translations, no new IDs): `LANG_SOUND_SETTINGS` "Klang", `LANG_THEME_MENU` "Themen", `LANG_RECORDING_SETTINGS` "Aufnahme". |
| Pictures in `%Lb` rows | The pictures of a row of one's own are laid over the row (`wps_images_over()`, `DRMODE_FG`, in `apps/gui/bitmap/list-skinned.c`), so over the selection bar; before, their transparent pixels were blended with the background (a white box around the check mark). The list is cleared first and every row drawn once; the second call of `wps_display_images()` per row is gone. |
| No list icons | Menu entry "Show Icons" removed (`apps/menus/theme_menu.c`), `settings_apply()` always sets `show_icons` off. `main_menu_config.rock` no longer switches the icons on itself (rows show "On"/"Off"). `db_folder_select` and `disktidy` still switch them on briefly for their selection. |
| Album list | covers 52 × 52 (`ALBUMART_LIST_SIZE`), pictures from Glossy Slate, see [ipod6g-album-list-covers.md](ipod6g-album-list-covers.md). |
| Empty skin lines | `skin_render_line()`: if a tag returns nothing (`NULL`), this counts as a change for a matching refresh type, and the line is written again and so cleared. Before, only a tag with text reported a change; the old text stayed (e.g. "Yes" of the clip counter under the sidebar tile after moving to an entry without a value). |
| `%Sv(name)` | New skin tag (`SKIN_TOKEN_SETTING_VALUE`, "Sv"): the current value of an int, bool or table setting, formatted with `option_get_valuestring()` as in its option list. Parsed like `%St` (`parse_setting_and_lang()`). |
| Gradients of `%dr` | `parse_drawrectangle()` also keeps the colours as 0xRRGGBB (`struct draw_rectangle`: `start_rgb`, `end_rgb`); `draw_gradient_dithered()` in `skin_render.c` draws gradients row by row from them, colour at the middle of the row, 4 × 4 ordered dither to RGB565, aligned to the screen. `lcd_gradient_fillrect()` interpolated the RGB565 end colours and truncated every row; on flat gradients the channels stepped at different rows (white → `#F4F6F8`: a pink band, then bluish). Solid areas unchanged. |
| Pictures with alpha in `%VB` | The `%VB` layer has no background of its own; Rockbox blended the transparent pixels of a picture there with the background colour of the viewport (white boxes around the symbols on the blue sidebar, white corners at the clock box). Now `skin_render_viewport()` lays the pictures of a `%VB` viewport over what the layer already holds after clearing (`wps_display_images_over()`, `DRMODE_FG`, `apps/gui/skin_engine/skin_display.c`). For partial updates it does not draw them again (the layer keeps them; blended twice the edges would get darker), unless a line of the viewport was written again. So a picture whose frame a tag chooses changes in `%VB` only with the next complete redraw. |
| Marks at the end of the row | `callback_item_mark` (`enum list_item_mark`, `apps/gui/list.h`): `apps/gui/bitmap/list.c` draws a speaker with three sound waves (14 × 12, arrow colour) at the right end of the track that is playing or paused, and a dot (8 × 8, accent colour `line selector gloss bottom color`) at unheard podcasts and audiobooks; white in the selected row. Without an arrow in the arrow column (centre 12 px from the edge), with an arrow left of it (26 px); album rows of a list with marks then end 35 px before the edge. Masks as 4 bit alpha from `tools/ipod6g_list_marks.py`. `tree_item_mark()` in `apps/tree.c`: database through `tagtree_item_mark()` (the playing track through `tagcache_idx` of the `mp3entry`), file browser by the path (volume part cut off). When the track changes, passes 15 s or counters change, `dirbrowse()` redraws the list while idle. Heard status: [ipod6g-database-media-types.md](ipod6g-database-media-types.md). |
| Popups | messages, progress and yes/no as a glossy panel centred on the whole screen (`apps/gui/popup.c`), see [ipod6g-popups.md](ipod6g-popups.md). |
| Counts in the sidebar | Skin tag `%Mc(albums\|podcasts\|audiobooks\|playlists\|bookmarks\|recordings\|shortcuts)`: recordings are the audio files in the recording folder (`rec path`, otherwise `/Recordings`; `count_recordings()`, counted like playlists), shortcuts the entries of "Shortcuts" (`shortcuts_get_count()` in `apps/shortcuts.c`, in memory since the start, not counted). Playlists are the playlist files in the playlist folder (`playlist catalog directory`, otherwise `/Playlists`), bookmarks the entries of `/.rockbox/most-recent.bmark` (lines with `>`), counted by `count_playlists()` and `count_recent_bookmarks()` in `apps/root_menu.c`. Counting happens not by time but when the number may have changed: every time the main menu appears (`root_menu_media_count_changed(-1)` before `do_menu()`; changes through the file browser, playlist catalogue, bookmark list and USB happen in other screens), and when `apps/bookmark.c` writes or deletes the file of "Recent Bookmarks" (`bookmark_file_changed()`; stopping in the main menu creates a bookmark there). The number of albums of music, podcasts and audiobooks (`tagcache_count_albums(media)` in `apps/tagcache.c`, once per database state and media type, without deleted entries and "<Untagged>"; `root_menu_media_count()` in `apps/root_menu.c`; media types see [ipod6g-database-media-types.md](ipod6g-database-media-types.md)). Empty while the database loads. Tag in `lib/skin_parser/tag_table.c`, evaluation in `skin_parser.c`/`skin_tokens.c`. |
| Date in the language | Skin tag `%cD(long\|short\|weekday\|month)`, see "Translatable theme texts" below. |
| Language | New IDs at the end of the `.lang` files: `LANG_KEYLOCK`, `LANG_KEYLOCK_SCREEN`, `LANG_KEYLOCK_NORMAL`, `LANG_SECOND_LINE_ALBUM`, `LANG_SECOND_LINE_ARTIST`, `LANG_INVERT_CURSOR_GLOSS`. German changed: "Cover-Ecken" (Rund/Eckig), "Zweite Zeile" (Im Wechsel). |

## Version and build

`docs/VERSION` holds the complete string `4.0 (dev build)`. `tools/version.sh`
uses it directly if the file exists. The two make files quote `SVNVERSION`
when passing it to the version script, so that the spaces in the version
are kept. If `docs/VERSION` is removed, the script falls back to the version
derived from Git.

## Limits for later changes

- The skins and their bitmaps form one theme package (`GlossySlate/`).
  Remove single graphics only when no `%xl`/`%xd` reference points to them
  any more.
- The code in `skin_display.c` and `skin_render.c` is not limited to
  `IPOD_6G`. Check changes there with other skins and targets as well. The
  PMU and LCD special handling is specific to the iPod.
- When changing the order of unlocking, test "LCD Sleep: Immediately" as
  well as normal waking up, locking, the now playing screen and the album
  list.
- The firmware and the installed `.lng` files must come from the same build.
  Otherwise string IDs can show valid but wrong menu texts.

## Performance, scrolling text and battery gauge (12 November 2026)

The iPod 6G runs at 54 MHz when not boosted. Rockbox threads give up the CPU
only voluntarily; the scroll thread (25 steps a second at speed 14, so every
40 ms) waits as long as the user interface computes. In the menu the list
wakes up once a second, the status bar skin is evaluated and the whole
display transferred: if that takes too long, the scrolling text stutters
once a second.

| File | Change |
| --- | --- |
| `apps/gui/skin_engine/skin_parser.c`, `skin_render.c` | `%Vd(label)` looked up its viewports at every update with `strcmp()` over all viewports, for chosen and hidden branches: with Glossy Slate 130 `%Vd` against 130 viewports, about 17,000 comparisons per update, about 10 ms at 54 MHz. After loading, every name now gets a single string (`intern_viewport_labels()`), and the renderer compares offsets. |
| `apps/gui/statusbar-skinned.c`, `skin_engine.c` | Measures every update of the status bar skin; "System › Debug › Skin engine usage" shows the last one and the longest since the screen was last opened ("SBS update"). |
| `apps/gui/skin_engine/skin_albumart_fx.c` | Blending of the cover effect: ÷255 as an exact multiplication/shift instead of three divisions per half transparent pixel, at every redraw. Reflection: the reciprocal once per cover instead of a 64 bit division per pixel, exact with a correction (checked for all heights 1–64 and opacities 0–100 %, 478 million cases). The one-off computation runs boosted (216 MHz). No `yield()`: the cover lies in the buffer of the buffering thread, which can move while another thread runs. The graphics stay the same pixel for pixel. |
| `firmware/powermgmt.c` | Battery gauge: when the charger is plugged in, Rockbox switches to the charging table (`percent_to_volt_charge`) at once, but the smoothed voltage follows only over about a minute (128 readings every 0.5 s, without a reset on the iPod 6G). So the level dropped to about half when plugging in and rose too high when unplugging. `level_one_way()`: while charging the level only rises, without charging it only falls; at a change it stays until the measured value overtakes it in the right direction. A full battery on the charger may go to 100 %. Full charge: on the charger without charging (the charger chip has finished, the theme shows the plug) the battery counts as full from a measured 90 % (`FULL_REST`) and reports 100 % (`level_after_full_charge()`); before, only from 99 %, which was never reached with the voltage sagging after the end of charging. After unplugging, the gauge starts at 100 % and moves smoothly to the measured value. The battery capacity that is set only affects the remaining time, not the level. |

Charging bolt in USB mode: `%bc` is the status pin of the charger chip
(`charging_state()`). Rockbox allows 500 mA only once the computer has
configured the iPod (`usb_charging_maxcurrent()`), before that 100 mA, which
the device needs itself in USB mode; the chip then reports no charging. No
bolt with a battery that is not full: the configuration has not happened yet
or did not happen (cable, hub, sleeping computer). With a full battery it is
correctly off.

## Languages English, English (US) and Spanish (12 November 2026)

Brought in line with the changes of the German language (`deutsch.lang`).
New entries are at the end of the files; IDs do not move.

| File | Change |
| --- | --- |
| `english.lang`, `english-us.lang` | Title of the main menu "iPod" (`LANG_ROCKBOX_TITLE`, the source stays "Rockbox"). English (US): the missing entry `LANG_HEADSET_REMOTE_CONTROL` added. |
| `espanol.lang` | The 19 entries of the fork added (podcasts "Podcasts", audiobooks "Audiolibros", key lock, album art corners, second line, "Marcar como no escuchado", popup hints "Botón central" / "otro botón", headset remote "Mando del auricular" and others). As in German "Playlist" instead of "lista de reproducción" (27 texts, Spanish used "playlist" already), short menu names "Sonido" and "Temas", title "iPod". The 9 entries whose English source the fork changed (compressor, Haas stereo widening, volume limit, presence/treble attenuation) with the new source and a new translation. |

Not taken over: the shorter German menu names "Klang", "Aufnahme", "Themen"
in English. The theme finds these menu entries through `%Sx(Sound
Settings)` and so on; `%Sx` looks up the built-in English text
(`lang_english_to_id()`). A changed English text would lose the tiles in the
sidebar in every language, and "Recording" exists already as a main menu
entry. The full English names fit into the list.

## Translatable theme texts (12 November 2026)

Every text the theme draws itself comes from the language files, so the
theme follows the language set on the iPod. German, English, English (US)
and Spanish carry the texts; other languages show the English ones.

| File | Change |
| --- | --- |
| `apps/lang/english.lang`, `english-us.lang`, `deutsch.lang`, `espanol.lang` | 62 new phrases at the end of the files (no IDs move): the full weekday and month names `LANG_WEEKDAY_FULL_*`, `LANG_MONTH_FULL_*`, the date formats `LANG_DATE_FORMAT_LONG` and `LANG_DATE_FORMAT_SHORT`, and `LANG_THEME_*`, the texts of the theme (counts in the sidebar such as "No music", "1 album", "albums", the values "Random order", "Repeat list", "Level", the USB screens, "Now playing", the quick menu titles `LANG_THEME_QS_SHUFFLE` and `LANG_THEME_QS_REPEAT`). |
| `lib/skin_parser/tag_table.c`, `tag_table.h` | New skin tag `%cD` (`SKIN_TOKEN_RTC_LOCALE_DATE`) among the clock tags. |
| `apps/gui/skin_engine/skin_parser.c`, `wps_internals.h` | `parse_locale_date()`: the parameter `long`, `short`, `weekday` or `month` (`enum skin_locale_date`). |
| `apps/gui/skin_engine/skin_tokens.c` | `locale_date()`: `long` and `short` fill the format of the language, `weekday` is the full weekday name, `month` the short month name in capitals (`locale_upcase()`, ASCII and the Latin-1 letters, e.g. "MÄR"). `%Sx` shows a text only up to an `@` (see below). |

The theme draws its texts with `%Sx(English text)`: the firmware looks the
English text up among the built-in English strings (`lang_english_to_id()`)
and shows the phrase in the current language. Rules for these phrases:

- The English text is the key. Changing it in `english.lang` breaks the
  theme in every language; the `desc` of every theme phrase says so.
- No commas or brackets in the English text: inside a skin tag a comma
  separates parameters. `%Sx(After disconnecting, Rockbox is ready again.)`
  makes the parser fail with "Too many arguments given", and the whole
  status bar skin would not load.
- The English text has to be unique among the English strings, otherwise
  `%Sx` finds the first phrase with that text. This is why the counts use
  lower-case words ("albums") next to the menu titles ("Albums").
- Where the same English word needs a translation of its own, the key names
  its place after `@`: `%Sx(Shuffle@quickmenu)` finds `LANG_THEME_QS_SHUFFLE`
  (English "Shuffle@quickmenu", German "Zufall"), not `LANG_SHUFFLE`
  (German "Zufallswiedergabe"), which the sidebar needs to recognise the
  settings entry. When the firmware shows a `%Sx` text, it stops at the
  first `@` (`SKIN_TOKEN_TRANSLATEDSTRING` in `skin_tokens.c`), so English
  shows "Shuffle". No other language string contains an `@`.

Dates need more than words: the order differs ("Monday, 9 November",
"Monday, November 9", "Montag, 9. November", "lunes, 9 de noviembre"), and
the English "May" is the full and the short month name at once, so `%Sx`
cannot tell them apart. So the firmware formats the date itself. The formats
name their parts in braces: `{weekday}`, `{wd}` (short weekday), `{day}`
(1–31), `{month}`, `{mon}` (short month), `{year}`; everything else is
copied. Braces instead of `%`: `tools/updatelang` compares the `%`
specifiers of a translation with the English ones while building and
replaces a translation that differs with the English text, and the order of
the parts has to differ between languages.

| Format | English | English (US) | German | Spanish |
| --- | --- | --- | --- | --- |
| `LANG_DATE_FORMAT_LONG` | `{weekday}, {day} {month}` | `{weekday}, {month} {day}` | `{weekday}, {day}. {month}` | `{weekday}, {day} de {month}` |
| `LANG_DATE_FORMAT_SHORT` | `{day} {mon} {year}` | `{mon} {day}, {year}` | `{day}. {mon} {year}` | `{day} {mon} {year}` |

The quick menu titles are phrases of their own (`%Sx(Shuffle@quickmenu)`,
`%Sx(Repeat@quickmenu)`; German "Zufall" and "Wiederholen" as in the design,
English "Shuffle" and "Repeat", Spanish "Aleatorio" and "Repetir"); the
values are those of the settings (`%Sx(On)`, `%Sx(All)`, …), as the settings
menu shows them. Its value line moved down by 2 px (y 187), so that it no
longer clears the descenders of the title (g, p, y).

Memory: the new strings add less than 2 KB to each language file, which is
loaded once; the skin gets smaller (`%cD` replaces the long `%?cu<…>` and
`%?cm<…>` chains: the status bar skin has 3674 instead of 3985 elements).
Nothing is taken from the playback buffer.

## Boot screen, playlists and macOS dot files (16 November 2026)

| File | Change |
| --- | --- |
| `apps/bitmaps/native/rockboxlogo.320x240x16.bmp`, `apps/bitmaps/native/SOURCES` | The boot screen of the iPod 6G is a picture of the whole display (blue field with the Rockbox logo). `SOURCES` picks it only for `IPOD_6G`; other targets of 320 to 479 pixels keep `rockboxlogo.320x98x16.bmp`. The BMP is made by `GlossySlate/tools/build_bootlogo.py` from `GlossySlate/firmware-assets/rockboxlogo_320x240.png` (full colour): `bmp2rb` cuts every channel to 5/6/5 bits without a dither, so on the gradient red, green and blue stepped at different places and fine coloured lines ran along it (seen on the device, 16 November 2026). The BMP therefore holds values already dithered to RGB565 (the 4 × 4 ordered dither of the theme's bitmaps, anchored to the screen), which `bmp2rb` keeps unchanged. |
| `apps/main.c` | `show_logo_boot()`: on the iPod 6G the logo starts at the top (centred, 0 for a full screen picture) instead of 10 px down, which left a black bar at the top and cut off 10 rows at the bottom. The version (`rbversion`, from `docs/VERSION`) is still written at run time, white without a box, 6 px above the bottom edge. |
| `apps/gui/statusbar-skinned.c` | `sb_skin_update()`: if an update chose another UI viewport (`%VI`) than the one the lists were laid out with, `sb_skin_get_info_vp()` takes it over at once and a `BUTTON_REDRAW` lays the list on the screen out again. Lists ask for their viewport only when they are set up again. After a new language the skins are reloaded, the UI viewport is the default one (the whole screen) until the next update, and the popup "Language loaded" holds updates back; the list of "General Settings" was laid out full width over the sidebar and stayed so until the menu level changed. |
| `apps/playlist.c` | `playlist_directory_tracksearch()` (inserting a folder into a playlist, also through the playlist catalogue) skips names starting with a dot. It loads the folder with `SHOW_ALL`, so the browser's filter of dot files did not apply: the `._name` companions macOS writes next to every file it copies (they end in `.mp3` as well, but hold no audio) went into playlists and did not play. Folders like `.Trashes` are skipped too. |
| `apps/tagcache.c` | `check_dir()` skips dot files and folders while building the database, for the same reason. A database built before keeps such entries until it is initialised again. |
| `apps/root_menu.c` | `count_playlists()` and `count_recordings()` skip dot files and hidden files: a `._name.m3u8` was counted as a playlist and stayed after the playlist itself was deleted, so the sidebar showed one too many. |
| `apps/fileop.c`, `apps/playlist_catalog.c`, `apps/playlist.c` | The sidebar counts playlists and recordings anew after every file operation of the browser (delete, rename, copy, move, new folder; public wrappers around the former functions), after a playlist was created or added to through the catalogue (`catalog_add_to_a_playlist()`) and after `playlist_save()`, besides every time the main menu appears. |

## Repeat without "Shuffle" (16 November 2026)

The repeat setting had a mode "Shuffle" (repeat shuffled): at the end of the
playlist it was shuffled anew and played again. Shuffle is a setting of its
own, so the fork drops the mode: repeat has Off, All, One and A-B, in the
settings and in the quick menu. Who wants the list repeated in random order
switches on repeat "All" and shuffle; at the end the list starts again in
the same shuffled order (repeat shuffled drew a new order every round).

| File | Change |
| --- | --- |
| `apps/settings.h` | `REPEAT_SHUFFLE` is gone from the repeat modes; `REPEAT_AB` is 3 inside the firmware. |
| `apps/settings_list.c` | the setting `repeat` offers `off, all, one, ab`. A config file with `repeat: shuffle` leaves the setting as it is (at the start: Off). |
| `apps/playlist.c` | `get_next_index()`, `playlist_check()` and `playlist_next()` no longer know the mode (shuffling anew at the end of the playlist). |
| `apps/gui/statusbar.c`, `firmware/usbstack/iap/platform.c` | the mode left the status bar icon and the table for accessories (iAP). |
| `apps/gui/skin_engine/skin_tokens.c` | `%mm` keeps the values of Rockbox (0 off, 1 all, 2 one, 4 A-B; as a condition 1, 2, 3 and 5), so that skins keep working; 3 (repeat shuffled) does not occur. |
| `apps/bookmark.c` | bookmark files keep the numbers of Rockbox as well (A-B is written as 4); a bookmark with repeat shuffled (3) is read as repeat all. |
| `apps/lang/*.lang` | `LANG_THEME_REPEAT_SHUFFLED` ("Repeat shuffled", text under the tile) is marked deprecated, so that the ids after it do not move. |
| `manual/` | repeat setting, config file values and `%mm` without "Shuffle". |
| `GlossySlate/` | the cases for 4 in the theme's `%?mm<…>` stay empty: no shuffle symbol in the repeat tile, no "Repeat shuffled" below it, no value "Shuffle" in the quick menu. |

## Sidebar and list fixes (17 November 2026)

| Seen on the device | Cause | Change |
| --- | --- | --- |
| "-44 dB" stayed under the tile after going from Volume one level up to Sound Settings | a line made of `%?if(...)<text>` conditionals with one branch was not written again when one of them turned false | `skin_render.c`, `skin_render_line()`: a single branch conditional that turns false marks the line for writing (and stops a scrolling text there) |
| "No Files" (e.g. EQ presets without a preset) had a white frame | `update_dir()` drew the empty list into the frame buffer, not onto the display; the popup puts its whole area, shadow included, onto the display | `tree.c`: on the first load of `dirbrowse()` an empty filtered folder is not drawn, it only gets the popup and goes back |
| Time Format: the clock stayed centred on the full width, the tile of the option page was cut in half | the theme drew the Time & Date screen (`%cs` 17) full width; `time_screen()` lays out its clock and menu once from that, and the option page used the menu's full width viewport | theme: `%cs` 17 gets the half layout with the calendar card |
| Recording › Trigger: no symbol in the tile until a value changed | `rectrigger()` clears the screen; the skin rewrites only lines that change, and the tile was the same as one level up | `recording_menu.c`: a full update of the status bar skin after the clear |
| option page: after scrolling past the last entry to the first the selection bar was cut at both ends, no check mark | the rows of a skinned list (`%Lb`) are drawn one after the other with the same skin elements; a line is written only if its conditionals changed since the row before, and the first row was selected like the last one drawn before it | `list-skinned.c` / `skin_render.c`: every line of a row is written (`skin_render_write_all_lines()`) |

The trigger screen itself works as in Rockbox: the wheel changes the value of
the highlighted entry, |<< and >>| move between the entries, Select keeps the
values and Menu restores the old ones.

## Tempo screen in the GlossySlate design (17 November 2026)

The pitch screen ("Tempo") was three lines of text from adwaitapod. With
GlossySlate it shows the designer's screen in the style of the quick menu
(GlossySlate/DESIGN.md 5.12).

| File | Change |
| --- | --- |
| `apps/plugins/pitch_screen.c` | `gs_load()`, `gs_draw()`, `gs_unload()` (iPod 6G): the parts come from `.rockbox/wps/<status bar skin>/tempo/` into the plugin buffer while the screen is open, the field is computed there (the dithered gradient of the quick menu). Without the parts the screen is drawn as before. Keys, values, limits and speech are unchanged; a key is drawn held between `ACTION_PS_NUDGE_LEFT/RIGHT` and its `...OFF`. |
| `apps/plugin.h`, `apps/plugin.c` | `font_load_ex()` at the end of the plugin API, `PLUGIN_API_VERSION` + 1. `font_load()` asks for the largest font buffer: a theme font the skin had loaded with a glyph cache would be loaded again, bigger, and stay so. With `font_load_ex(path, 0, 160)` the plugin shares the skin's font (only its reference count goes up) and gives it back when it closes. |
| `apps/lang/*.lang` | `LANG_TEMPO_PERCENT` ("Percent"), `LANG_TEMPO_HOLD` ("Hold"), `LANG_TEMPO_TIMESTRETCH` ("Timestretch"; `LANG_TIMESTRETCH` is "Abspielgeschwindigkeit" in German, too long for the capsule) and `LANG_DECIMAL_SEPARATOR` ("." / ","), at the end of English, English (US), German and Spanish. |

Memory: about 90 KB of parts and 150 KB for the field, in the plugin buffer
(2 MB, not the playback buffer), free again when the screen closes.

## Graphical EQ in the GlossySlate design (17 November 2026)

The graphical EQ was a list of sliders in the system font. With GlossySlate
it shows the designer's screen: the ten bands side by side as vertical
faders (GlossySlate/DESIGN.md 5.13).

| File | Change |
| --- | --- |
| `apps/menus/eq_menu.c` | `eqgs_load()`, `eqgs_draw()`, `eqgs_unload()` (iPod 6G). The screen stays in the core; only its drawing changes, values, steps and keys are those of `eq_menu_graphical()`. The parts come from `.rockbox/wps/<status bar skin>/eq/` into the plugin buffer (`plugin_get_buffer()`, as the skin parser and the folder selection use it) while the screen is open; if the buffer is not whole (a plugin stays loaded) or the parts are missing, the old drawing is used. The fonts are shared with the skin (`font_load_ex()` with its glyph cache). |
| `apps/lang/*.lang` | `LANG_GRAPHICAL_EQ_GAIN` ("Gain"; German `LANG_GAIN` is "Verstärkg."), `LANG_GRAPHICAL_EQ_FREQUENCY` ("Frequency"), at the end of English, English (US), German and Spanish. |

Memory: about 60 KB of parts and 150 KB for the field in the plugin buffer
(2 MB, not the playback buffer) while the screen is open.

## Cover Flow from Rockpod (17 November 2026)

PictureFlow is replaced by the Cover Flow of Rockpod
(https://github.com/nuxcodes/rockpod, Nux Li, GPL v2 or later like
Rockbox), and the database opens it from its first entry, "Cover Flow".

Rockpod's changes to `pictureflow.c` were taken over by a three-way merge
(Rockpod's base 58b186d6d, Rockpod's master 0a3446e72, this tree), without
conflicts:

- seven covers in view, the side covers parallel with one tilt and an
  automatic spacing, the centre cover in front when it passes the next one;
- the colours of the theme instead of black and white (background,
  foreground, selector), covers and reflections fade to the background;
- the status bar of the theme with the title "Cover Flow" (switchable);
  the covers are drawn below it;
- the animation advances by elapsed time, speeds adjustable; album and
  artist fade from cover to cover;
- covers dithered to RGB565 (4 x 4 Bayer), a cache of 100 covers, cache
  version 5 (the album art cache is built again once);
- the track list shows titles only, without disc and track number; the
  selected row is drawn like the menus (selector type);
- Menu (short) closes the track list before it closes Cover Flow; the
  backlight follows the settings (the option "Backlight" is gone).

Left out, because they depend on other Rockpod changes: dynamic colours
from the album art (`dynamic_colors_resolve()`), the SSD storage mode
(`global_settings.storage_mode`) and `skin_render_inhibit_flush()`. The
latter kept the status bar from pushing the framebuffer to the LCD while
PictureFlow drew; since "gui: simplify screen updates" (c0a8303a9c) the
status bar only does that from `get_action()`, and Cover Flow asks for the
buttons before it draws a frame, so the LCD gets complete frames only. The
plugin API is unchanged.

| File | Change |
| --- | --- |
| `apps/plugins/pictureflow/pictureflow.c` | Rockpod's Cover Flow as above; the display settings with texts of their own instead of English strings and reused labels; the menus titled "Cover Flow" and "Settings" instead of the English "PictureFlow (Settings)"; the fork's selector "bar (gloss)" in the track list. |
| `apps/tagtree.c`, `apps/tagtree.h` | New entry type `%plugin` in `tagnavi.config` (iPod 6G): `"Name" %plugin "plugin"` runs the plugin (as in `viewers.config`, `filetype_load_plugin()`) on top of the database view, which keeps its place; "Play" in the plugin goes to the now playing screen. `tagtree_is_plugin_entry()`. |
| `apps/tree.c` | No context menu on such an entry (nothing to play or insert). |
| `apps/tagnavi.config` | `"Cover Flow" %plugin "pictureflow"` as the first entry of the database. |
| `apps/lang/*.lang` | `LANG_COVER_FLOW` ("Cover Flow", title and database entry), `LANG_COVER_FLOW_SIDE_INSET`, `LANG_COVER_FLOW_PARALLEL`, `LANG_COVER_FLOW_SCROLL_SPEED`, `LANG_COVER_FLOW_TRANSITION_SPEED`, `LANG_COVER_FLOW_TEXT_CROSSFADE`, at the end of English, English (US), German and Spanish. `LANG_ONPLAY_PICTUREFLOW` (context menu, hotkey, playlist viewer) says "Cover Flow" in these four languages. |
| `docs/CREDITS` | Nux Li. |
| `manual/plugins/pictureflow.tex` | Cover Flow, the database entry and the display settings. |

Memory: as before in the plugin buffer (2 MB, not the playback buffer); the
album art cache takes an eighth of what is left after the album index (at
least three covers) instead of a quarter.

## No white noise after boot (17 November 2026)

With headphones plugged in, the iPod played loud white noise after every
boot, also in USB mode, until something had been played; after a pause or
stop it stayed quiet.

`audio_init()` applies the sound settings (`sound_settings_apply()`) right
after it created the audio thread, and that thread runs `pcm_postinit()`
only afterwards. `audiohw_postinit()` wrote 0 into the headphone and line
out volume registers then: 0 dB, far above the volume set (for example
−37 dB), until the next cold playback start set the volume again
(`sound_set_volume()` in `audio_start_playback()`). A volume at its
minimum, which the CS42L55 stores as the mute bit, was unmuted as well.

Besides, I2S0 sends silence only once it has played: stopped (`I2STXCOM`
`0xa`) it keeps sending what it last had, after a boot whatever it came up
with. So the boot now ends in the state a playback leaves behind.

| File | Change |
| --- | --- |
| `firmware/drivers/audio/cs42l55.c` | `audiohw_postinit()` (iPod 6G) leaves the headphone and line out registers alone once `audiohw_set_volume()` / `audiohw_set_lineout_volume()` wrote them (`hp_volume_set`, `lineout_volume_set`, cleared in `audiohw_preinit()`). |
| `firmware/target/arm/s5l8702/pcm-s5l8702.c` | `sink_dma_postinit()` (iPod 6G) instead of `audiohw_postinit()` as the sink's postinit: it starts I2S0, queues three 2 KB blocks of zero samples (about 35 ms), stops after 20 ms while they still flow, as a playback stops, and only then calls `audiohw_postinit()`. |

## Cover Flow: track list on the back of the cover (17 November 2026)

Selecting an album in Cover Flow no longer zooms into a list over the whole
screen: the cover turns to the left about its vertical axis, and its back
shows the titles in the GlossySlate design, while the other covers stay
visible around it (GlossySlate/DESIGN.md 5.14).

| File | Change |
| --- | --- |
| `apps/plugins/pictureflow/pictureflow.c` | `PF_GLOSSY` (iPod 6G, RGB565 320 × 240): the opening and closing animation (`pfg_cover_frame()`: 6 frames loosening, 16 frames turning, by the clock), the turned card with PictureFlow's camera (`pfg_card()`), the back (`pfg_draw_back()`) instead of `show_track_list()`'s list, fixed rows from the top (`reset_track_list()`), the track length from the database (`track_data.length`), scroll lines in a box of their own (`set_scroll_line_in()`). The buffers (scene behind, back, texture, about 360 KB) come from the end of the slide cache in the plugin buffer (`pfg_reserve()`); without room the old list stays. Titles found during an opening that is turned back are given back (`free_borrowed_tracks()`), so the cover loader is not left locked. The knob is that of the lists (`gui_scrollbar_draw_overlay()`: alpha, width, size, shown for 1 s on scrolling, then faded out), and the list stops at its ends. The playing title has the speaker of the database lists before its time (`track_data.idx_id` against `tagcache_idx` of the playing track, as `tagtree_item_mark()`; the mask comes from `tools/ipod6g_list_marks.py` through the generator). The loosening blends channel by channel (`pfg_blend()`; red and blue blended in one word turned the reflection yellow). |
| `apps/plugins/pictureflow/pictureflow_glossy.h` | generated by `GlossySlate/tools/build_pictureflow.py`: sizes and colour rows of the back. |

## The inline remote does not light the display (18 November 2026)

Pausing or skipping with the earphone remote switched the display on, in
every screen (noticed in Cover Flow). Every pressed button lights it in
`button_tick()`; the remote's buttons, `BUTTON_MULTIMEDIA_*` from the Mikey
driver, were not left out. "Caption backlight" only concerns track changes
without a button press, in the now playing screen.

| File | Change |
| --- | --- |
| `firmware/drivers/button.c` | `button_tick()` (`HAVE_MIKEY_REMOTE`): a press or repeat of a `BUTTON_MULTIMEDIA` button is posted as before but switches neither the backlight nor the button light on, and "first keypress enables backlight only" does not eat it. The buttons of the iPod light the display as before. |
| `manual/configure_rockbox/playback_options.tex` | Headset Remote Control: the remote does not switch the display on. |

## Cover Flow: the theme's default cover (18 November 2026)

Albums without a picture (none in the folder, none embedded, or one that
cannot be read) showed PictureFlow's "?" in Cover Flow, also while a cover
was still loading. Now they show the default cover of the theme, the same
note on grey as in the album list, the mini player and the now playing
screen (GlossySlate/DESIGN.md 5.14).

| File | Change |
| --- | --- |
| `apps/plugins/pictureflow/pictureflow.c` | `create_empty_slide()` reads `cover_flow.bmp` from the bitmap folder of the status bar skin (`WPS_DIR/<sbs_file>/`, as the tempo screen and the EQ find their parts) and only without it `pictureflow_emptyslide.bmp`. The picture is read at every start and the cached slide (`emptyslide.pfraw`) is written only when it differs (`pfraw_holds()`), so a change of theme shows at once without writing at every start. |
| `GlossySlate/tools/build_pictureflow.py` | also writes `.rockbox/wps/glossyslate/cover_flow.bmp`: the default cover from `firmware-assets/albumart_list_default_512.png`, 128 × 128 (PictureFlow's slide width at 320 × 240), scaled in full precision and dithered to RGB565 once (helpers of `build_wps_cover.py`). |
| `GlossySlate/.rockbox/wps/glossyslate/cover_flow.bmp` | new, 24 bit, opaque. |
| `manual/plugins/pictureflow.tex` | albums without album art show the theme's default cover. |
