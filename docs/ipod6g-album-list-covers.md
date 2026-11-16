# Album list with covers on the iPod 6G

As of 4 November 2026. This file describes the current code in the
repository.

## Behaviour and data flow

1. `apps/tree.c:update_dir()` recognises album lists of the database through
   `tagtree_album_art_key()` and switches on the cover and artist callbacks
   only there. This also applies to album lists below artists and album
   artists. Other lists and customised list themes keep their usual look.
2. `apps/tagtree.c:retrieve_entries()` stores the album artist for albums
   (otherwise the track artist) in the existing field
   `tagentry.album_name`. `tagtree_album_artist_name()` returns this text for
   the second line. `tagtree_album_art_key()` returns the album seek and, if
   any, the artist or album artist seek. So albums of the same name in
   different hierarchies get separate cache keys.
3. `apps/gui/bitmap/list.c:list_draw()` draws album rows on the iPod 6G like
   the original iPod OS: the 52 × 52 pixel cover fills the row height and
   sits flush with the left edge of the screen, to its right the album title
   and the light grey artist. The selection bar starts to the right of the
   cover and has square ends.
4. `apps/albumart_list.c:albumart_list_draw()` takes a picture from the RAM
   cache or shows the built-in default cover. For pictures that are not
   loaded yet it sends a request to the background thread; the UI thread
   decodes no pictures.
5. While browsing normally, the background thread only loads 52 × 52
   pictures that were made before, from `covers.dat`/`index.dat`. Decoding
   happens only during a refresh (see "Cache and refresh"). It starts by
   itself after every database update and as soon as an album list is opened
   whose cache does not match the database. There is no menu entry for it
   any more.

## Files

| File | Part in this feature |
| --- | --- |
| `apps/SOURCES` | builds `albumart_list.c` only for `IPOD_6G` with the tag cache. |
| `apps/albumart_list.c`, `apps/albumart_list.h` | cache keys, background thread, file format, source search, decoding, drawing and manual cache upkeep. |
| `apps/albumart_list_default.png`, `apps/albumart_list_default.h` | template and embedded RGB565 default cover for missing pictures or pictures not loaded yet. The header file is used at run time. |
| `apps/tree.c` | switches the album view on and connects the list callbacks with tagtree and the cover cache. |
| `apps/albumart_list_special.h`, `apps/albumart_list_by_album.jpg`, `apps/albumart_list_all_tracks.jpg`, `apps/albumart_list_random.jpg` | fixed pictures of the three entries above the albums: "[By Album]" a note, "[All Tracks]" a record, "[Shuffle]" shuffle. The pictures come from Glossy Slate (`GlossySlate/firmware-assets/*_512.png`; `apps/` holds the 53 px versions); `tools/ipod6g_albumart_header.py` turns them into 52 × 52 RGB565 with Bayer dithering, the default cover as well. `tagtree_album_special_entry()` recognises the entries by their table type (`TABLE_ALLSUBENTRIES_SORTED_BY_ALBUMS`, `TABLE_ALLSUBENTRIES`, `extraseek == -1`), so independently of the language; `tree_draw_albumart()` draws them with `albumart_list_draw_special()`. |
| `apps/tagtree.c`, `apps/tagtree.h` | start the cover thread, return album keys and artists and fill in the subtitle when the database list is loaded. |
| `apps/tagcache.c`, `apps/tagcache.h` | find a matching track index for uniquely sorted album tags, so that the album artist can be read. The seek-to-track map avoids the former search per album and keeps the alphabetical order. While the database is rebuilt, the code waits for running readers. `tagcache_get_db_id()` returns the commit counter, number of entries and data size of the database the cover cache belongs to. |
| `apps/gui/list.c`, `apps/gui/list.h` | add optional cover/artist callbacks and a minimum height per row. |
| `apps/gui/bitmap/list.c` | draws the cover, both text lines and the selection bar right of the cover; clears the cover strip left of the list viewport; also works out the horizontal start for long scrolling titles. |
| `apps/tagcache.c` (tag cache thread) | `covers_follow_update()` starts the cover refresh after "Update Now", "Initialize Now" and the automatic update at start, not after a commit deferred to the next start. The former menu entry "Update album covers" (`tc_update_covers` in `apps/menus/settings_menu.c`) is removed; its language IDs stay unused in the `.lang` files so that no IDs move. |
| `apps/lang/english.lang`, `apps/lang/english-us.lang`, `apps/lang/deutsch.lang` | hold the new IDs `LANG_ALBUM_COVERS_UPDATE` and `LANG_ALBUM_COVERS_UPDATE_STARTED`. |

The general user interface is drawn by the theme (Glossy Slate,
`GlossySlate/`). Lists look like those of the original iPod OS (see "Lists
in the retail style" below). Skin overlays for rounded selection bars do not
fit: made for low rows, they leave white corner pixels or spikes in the high
album rows after the next skin update. The cover view needs no WPS graphics
of its own.

## Cache and refresh

Folder on the device: `/.rockbox/album-list-art/` with exactly two files:

| File | Content |
| --- | --- |
| `covers.dat` | header (`ALC1`, edge length, count) and for every cover its source (path hash, modification time, size) plus 52 × 52 RGB565 pixels, 5420 bytes. Every cover only once, even if it belongs to several keys. |
| `index.dat` | header (`ALI1`, album art setting, commit counter, number of entries and data size of the database, count) and the entries sorted by key: album seek, parent tag, parent seek → cover number, 16 bytes each. |

Why there used to be more than 700 files: the old cache made one file per
key (`ALA3`, the name from the three seeks). So every album was in it once
for the album list and once per album artist, on a test device
356 + 368 = 724 files for 357 album tags (the database counts every
different album tag, for instance of podcasts, audiobooks and singles, as an
album of its own). On FAT32 each 5 KB file took a 16 KB cluster (11 MB). The
pass "albums per artist" ran as a second pass over all albums because of
`tag_artist == 0`. Orphaned files were only deleted by a pass that finished
without any interruption. After a database update the seeks point to other
albums, so the old files could show wrong covers.

Course of a refresh (`refresh_all()`). It runs after every database update
and so also finds new or changed picture files (`cover.jpg` and so on)
without a database change:

1. Everything in the folder except `covers.dat` and `index.dat` is deleted,
   so also files of the old format and remains of interrupted passes.
2. The sources of the existing covers are remembered (`old_sources`).
3. The pass "all albums" (key album, 0, 0), then "albums per album artist"
   (album, `tag_albumartist`, seek). A single run over the master index
   (`tagcache_for_each_entry()` in `apps/tagcache.c`, read in blocks) yields
   the keys with their first track; the pairs (album, parent) already seen
   lie in a hash table in the decode buffer for this. Then the keys are
   sorted by album, so that `covers.dat` follows the order of the album
   list. The source is determined once per first track (path and
   modification time from the database, tags, picture file); most album
   artist keys have the same first track as their album and take over the
   result (`memo_track`, 8 KB). A cover of the same source already written in
   this pass is reused, an unchanged old one is copied from `covers.dat`,
   and only new or changed sources are decoded. Albums without a cover get no
   entry. For embedded covers the path, the track's modification time in the
   database and the picture size form the source, without searching the
   folder; for picture files the path, modification time and file size.
4. At the end the entries are sorted in the decode buffer, `index.new` is
   written, and `covers.new`/`index.new` replace the old files. If nothing
   was decoded and the numbers of covers and entries match the valid old
   files, the old files stay and the new ones are deleted; a database update
   without new pictures so does not rewrite 1.8 MB. An interruption (USB,
   database commit) deletes only the new files; the old ones stay.

While browsing, the background thread looks the key up in `index.dat` by
binary search and reads 5408 bytes from `covers.dat`. If a key with a parent
is missing (e.g. below `canonicalartist`, which has no keys of its own), it
takes the cover of the album itself. If `index.dat` does not match the
current database or album art setting, the rows show the default cover and
the refresh starts by itself (once per database state; again after an
interruption by USB). During a refresh the old files keep serving the list
if they match the database, otherwise the entries made so far.

- RAM: `ART_SLOTS` (24) decoded pictures, about 120 KB (formerly 128 slots,
  about 640 KB), plus the decode buffer (256 KB), 24 KB of source lists and
  8 KB for the track results. In all `albumart_list.o` takes 438 KB instead
  of about 930 KB.
- The source search uses `find_albumart()` and embedded JPEG covers.
  `decode_source()` handles external JPEG and BMP files; another external
  extension is currently handed to the JPEG decoder as well. Covers that
  cannot be read or are missing get the default picture.
- `ART_PENDING` (16) limits visible requests. When scrolling fast, older
  open requests are dropped in favour of new rows. After loading, the
  background thread asks for a redraw.
- The refresh serves visible requests first and pauses after every entry
  for which it had to look up covers (0.1 s during playback); results taken
  over cost only a `yield()`. Before every decode it waits as long as the PCM
  buffer is low (`pcmbuf_is_lowdata()`): Rockbox switches threads only when
  one yields, so a large JPEG must not hold up the codec at a tight moment.
- Formerly the filtered album search of the album artist pass returned one
  album per track (without a duplicate filter): with 3208 tracks 3208
  instead of 289 keys, for each a search over the whole index and reading
  the tags. Checked on the Mac against a real library, the new way returns
  the same 276 + 289 keys with an identical first track.

## Adjusting the view

`list_draw()` works out the positions from the cover size
`ALBUMART_LIST_SIZE` (52, `apps/albumart_list.h`) and `ALBUM_TEXT_GAP` (8, at
the top of `apps/gui/bitmap/list.c`):

- The cover stands at x 0 of the text viewport, so at the left edge for a
  list viewport that starts at the screen edge. If a visible scroll bar is
  on the left, it starts to the right of it.
- The selection bar or row background starts right of the cover (x 52), the
  text `ALBUM_TEXT_GAP` pixels later (`album_text_x`, x 60). `text_pos` for
  the scroll offset uses the same value. The general content inset
  `LIST_EDGE_INSET` does not apply to album rows.

## Lists in the retail style

The theme puts the list viewports at the edge of the screen (Glossy Slate:
`%Vi(Full,0,22,320,218,-)`, in the main menu `%Vi(Half,0,22,160,218,-)` up to
the sidebar). `list_draw()` in `apps/gui/bitmap/list.c` draws on the main
screen:

- **Selection bar** square over the whole viewport width. If the viewport
  starts at the left edge of the screen, text and icons move in by
  `LIST_EDGE_INSET` pixels (theme setting `list edge inset`: Glossy Slate 8,
  0 if not given) and keep the same distance from the right edge; so they
  stand at x 4 to 315 as before (main menu up to 178).
- **Edge strips:** the text viewport `list_text_vp` leaves out a strip on the
  right (scroll bar width or `LIST_EDGE_INSET`), with the scroll bar on the
  left also on the left. Every row continues its background or selection bar
  into these strips with `put_line()` and an empty text. The scrolling text
  of a long title draws only in the text viewport and never over the strip.
- **Scroll bar** after the original: `gui_scrollbar_draw_overlay()` in
  `apps/gui/scrollbar.c` draws only a black knob after all rows,
  `GUI_SCROLLBAR_OVERLAY_GAP` (2) pixels from the list edge, 3 pixels from
  the top and bottom, without a track. Its width is the setting "Scroll Bar
  Width" minus 1, as with the classic Rockbox scroll bar (theme value 6
  gives 5 pixels). It is half transparent (`OVERLAY_KNOB_ALPHA` 8 of 15
  transparency, 13 at the outer ends), so grey over white and dark blue over
  the blue bar. The strip is as wide as the knob plus the gap; left/right
  follows the setting "Scroll Bar".
- **Fading in and out:** the knob only appears while the user scrolls
  (`list_scrollbar_touch()` in `apps/gui/list.c` sets `scrollbar_tick` on
  next/previous and page up/down). `LIST_SCROLLBAR_SHOW` (1 s) later it fades
  out in `GUI_SCROLLBAR_FADE_STEPS` (7) steps over `LIST_SCROLLBAR_FADE`
  (350 ms); `gui_synclist_scrollbar_fade()` returns the step.
  `list_do_action_timeout()` shortens the wait until the next step, and
  `gui_synclist_do_button()` then calls `list_scrollbar_update()`. This
  function redraws only the strip: `list_draw()` saves it before the knob in
  `sb_saved`, because redrawing the whole list would restart the scrolling
  text of the selection every time. New lists and reloaded folders
  (`update_dir()` in `apps/tree.c`) show no knob. Screen loops without
  `list_do_action_timeout()` (some plugins) fade out only at the next key
  event or timeout.

Other screens that use the theme's list viewport (e.g. yes/no questions,
time and date) have no inset of their own and now start right at the edge
of the screen.

The row height is set to at least `ALBUMART_LIST_SIZE` in `apps/tree.c` and
checked against the height of two text lines plus 4 pixels in
`apps/gui/list.c`. With the 24 pixel font of Glossy Slate that is exactly 52
pixels; with a larger font the cover is centred vertically in the higher
row, with a smaller one the two text lines stand in the middle of the 52
pixel row. Whoever changes the cover size regenerates
`apps/albumart_list_default.h` and `apps/albumart_list_special.h` with
`tools/ipod6g_albumart_header.py`; the script reads the size from
`apps/albumart_list.h`, and the cache on the device rebuilds itself because
the edge length is in the file header. The colour of the artist is the
theme setting `list secondary color` (Glossy Slate 5B6371, the foreground
colour if not given). In the selected row the artist takes the text colour
of the selection bar from the theme (`line selector text color`) for colour
and gradient bars. When a long title scrolls, its background has to be
redrawn with the row style; otherwise a dark trail of text stays behind.

## Loading time

When it opens, the album list is still built from the tag cache. For the
top, alphabetically sorted album list `tagcache.c` builds a seek-to-track map
from the master index; this happens again on every opening and can still
cause a visible loading indicator with large databases. After that
`retrieve_entries()` fetches the artists. Existing cover files are loaded
separately in the background. Whoever wants to optimise the start time
should measure these phases separately before changing the cache size or the
picture decoding.

## Removing the feature

1. In `apps/tree.c` remove the two callbacks and the block in
   `update_dir()`; in `apps/tagtree.c` remove the initialisation and the
   album specific key/subtitle functions.
2. Remove the `IPOD_6G` additions in `apps/gui/list.c`, `apps/gui/list.h`
   and `apps/gui/bitmap/list.c`. Keep the rest of the list logic.
3. Remove `tagcache_search_track_index()` and its helper data and branches
   in `apps/tagcache.c` as well as the declaration in `apps/tagcache.h`.
   Check the additional wait for `Q_REBUILD`: it was added for parallel
   cover cache readers and is not needed without them.
4. Remove `covers_follow_update()` and the include of `albumart_list.h` in
   `apps/tagcache.c`, as well as `tagcache_get_db_id()` in
   `apps/tagcache.c`/`.h`. The two language IDs of the former menu entry stay
   (unused) in the `.lang` files.
5. Remove `albumart_list.c` from `apps/SOURCES` and delete
   `apps/albumart_list.c`, `.h`, `_default.h` and `_default.png`. Optionally
   delete only the device specific folder `/.rockbox/album-list-art/`
   afterwards.

After removing it, build the firmware and the matching language files
together. The database, music files, the theme and other Rockbox changes do
not need to be deleted for this.
