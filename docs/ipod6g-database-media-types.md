# Database: music, podcasts and audiobooks kept apart

As of 11 November 2026. This file describes the current code in the
repository. The change concerns the core of the Rockbox database
(`apps/tagcache.c`). In the code the places carry short comments that point
to this file.

## Behaviour

- The database reads only three folders, each with all its subfolders:

  | Folder | Media type |
  | --- | --- |
  | `/Music` (or `/Musik`) | music |
  | `/Podcasts` | podcasts |
  | `/Audiobooks` | audiobooks |

  Upper and lower case do not matter. Files in other folders do not go into
  the database; other folders are not even searched while scanning.
- Every view of the database shows music only: albums, artists, album
  artists, genres, years, composers, tracks, first letter, search, shuffle,
  user rating, recently added, playback history, "Same as currently played
  track" and custom menus from `tagnavi_custom.config`. Plugins such as
  PictureFlow also see only music, and the album count in the main menu
  counts only music albums.
- Podcasts and audiobooks appear only in their own categories. The list
  looks like the album list: cover, album name, below it the artist (if
  tagged). The special entries "[By Album]", "[All Tracks]" and "[Shuffle]"
  do not exist there; the list starts with the first album. An album opens
  its episodes or chapters.
- The categories are in the database menu ("Music" in the main menu) after
  "Album". The main menu entries "Podcasts" and "Audiobooks" open them
  directly. "Back" in their list leads to the main menu. The next time they
  open where the last visit ended. After a visit to "Podcasts" or
  "Audiobooks", "Music" starts in the database menu itself.
- Below the symbols in the main menu the theme shows the numbers from the
  database: music albums, podcasts (albums below `/Podcasts`) and
  audiobooks (albums below `/Audiobooks`), each without "<Untagged>". As long
  as the database is not ready, the value stays empty.
- The database no longer reads `database.ignore` and `database.unignore`;
  the folders decide. Existing files do no harm and can be deleted.
- Unchanged for all three media types: play count, rating and resume
  position per file, export and import of the statistics
  (`database_changelog.txt`), the cover cache of the album list and the file
  browser (the folders stay visible there as usual).

## Implementation

### Media type per entry

- `add_tagcache()` determines the media type from the path (`media_dirs`,
  `media_dir_of()`) and writes it into the flags of the entry:
  `FLAG_PODCAST` (0x20) or `FLAG_AUDIOBOOK` (0x40); music has neither. The
  commit takes the flags over into the master index. Files outside the
  folders return at once, and `check_dir()` descends only into the folders.
- On the iPod the paths start with the volume: the iPod build knows several
  volumes (`HAVE_MULTIVOLUME`), and `do_tagcache_build()` replaces the root
  `/` with the volume roots, such as `/<HD0>`. A file is then called
  `/<HD0>/Music/…`. So `media_dir_of()` first cuts off the volume part
  (`path_strip_volume()`). Without that no path matched, and the database
  stayed empty on the device (the first firmware with this change).
- New tag: `tag_virt_mediatype` (virtual, numeric, value from
  `enum tagcache_media`: 0 music, 1 podcasts, 2 audiobooks) for conditions
  and `tagnavi.config` (`mediatype`).
- Database version `TAGCACHE_MAGIC` from `TCH 0x10` to `0x11`. An older
  database carries no media type. It would show podcasts and audiobooks as
  music, and the categories would stay empty. So the firmware does not use
  it; the database has to be built once again.
- The first version (commit `3fe3997a69`) also checked the path for
  `/Podcasts/` at its start. On the device that never matched because of the
  volume part; this explains why the categories stayed empty there even
  after a rebuild and podcasts appeared with the music.

### Every search returns one media type

`struct tagcache_search` has the field `media`: bits 0–7 the media type of
the results (`TAGCACHE_MEDIA_ALL` = all), above them the state of the media
map. It replaces the unused field `fd`; the structure keeps its size, so
older plugins keep working (their searches return music).
`tagcache_search()` clears the structure, so the default is music.

- `tagcache_search_set_media(tcs, media)` chooses the media type,
  `tagcache_search_get_media(tcs)` asks for it.
- The condition `mediatype == "n"` (a constant, operator `==`) is not a
  condition per entry; in `tagcache_search_add_clause()` it chooses the media
  type of the search. So the album list of the categories stays a fast,
  sorted search. Any other condition on `mediatype` is checked per entry,
  and the search then covers all media types.
- Relative searches (filters, conditions, numeric tags like the year):
  `build_lookup_list()` skips entries of another media type.
- Direct searches of a unique tag (albums, artists, genres and so on at the
  top level): the tag file is sorted alphabetically, but its entries do not
  say which tracks use them. `build_media_map()` collects, in one pass over
  the index, the positions (seeks) used by tracks of the wanted media type in
  a hash set (the media map). The search then reads the tag file in its
  order and skips everything else (`direct_entry_wanted()`). As before, the
  album list gets a matching track per album for the artist and cover
  (`track_index_ids`); the former album map (`build_track_index_map()`) is
  part of it now.
- Direct searches of titles and file names: every entry belongs to exactly
  one track, and `direct_entry_wanted()` checks its flags.
- Without room for the map (more than ¾ of the slots) the search continues
  relative to the index. The map lies in the duplicate buffer of the search
  (database menu: 16,384 slots, so up to 12,288 different values); searches
  without a buffer of their own (plugins, album count) use a shared map with
  8,192 slots, one search at a time.
- `tagcache_count_albums(media)` counts the albums of a media type, once per
  media type and database state.

Fetching by the number of an entry (`tagcache_retrieve()`,
`tagcache_find_index()`, `tagcache_fill_tags()`) does not filter: playback,
statistics and covers work for all media types.

### Database in RAM after a rebuild

Rockbox reserves the RAM for the database at start, sized for the database
that is on the iPod at that moment, plus 32 KB of reserve
(`allocate_tagcache()`). If it grows more after that, for instance when it
is rebuilt from an empty database (here from 0 to 559 KB), it no longer
fits. Until now `load_ramcache()` then set the database to "not ready", and
it stayed unusable until the next start; the message "Building database…"
stayed, although the database had been written completely. Now
`load_ramcache()` checks the size first (`ramcache_size()`): if the
database does not fit, it gives back the reservation that is too small, and
the database works from the disk until the next start. A larger reservation
at run time would take memory from playback.

### Memory

The only new thing is the shared map of 32 KB (8,192 × 4 bytes) as a static
variable. The database in RAM does not grow (the media type lives in the
existing flags), and nothing is borrowed from the playback buffer. Playback
is not affected.

### Menus

- `apps/tagnavi.config`, main menu of the database:
  ```
  "Podcasts"   -> album ? mediatype == "1" -> title = "fmt_title"
  "Audiobooks" -> album ? mediatype == "2" -> title = "fmt_title"
  ```
  Rockbox translates the names through `LANG_PODCASTS` and
  `LANG_AUDIOBOOKS`. All other views need no condition; they show only music
  by themselves. Custom views for podcasts or audiobooks choose their media
  type with exactly one condition `mediatype == "1"` or `"2"`.
- `apps/tagtree.c`: `mediatype` as a tag; `retrieve_entries()` puts the
  three special entries only in front of lists whose search returns music;
  `tagtree_open_root_entry()` opens an entry of the database menu by its
  English name (`TAGNAVI_PODCASTS`, `TAGNAVI_AUDIOBOOKS`),
  `tagtree_in_root_entry()` tells whether the browser is in it already, and
  `tagtree_open_root()` goes back to the database menu.
- `apps/root_menu.c`: `GO_TO_PODCASTS` and `GO_TO_AUDIOBOOKS` go through the
  database browser like "Music" (with the question whether the database
  should be built if it is missing), and `db_browser_open()` opens the
  category. Context menu of these entries: the database menu.
  `root_menu_media_count()` returns the numbers for `%Mc(…)` from the
  database.
- `apps/tree.c`: `tree_set_id3db_exit_level()`; at level 1 "Back" from the
  category list leads to the main menu. The former folder rule
  (`tree_set_browse_exit_dir()`) is removed.
- Theme Glossy Slate: the numbers of podcasts and audiobooks stand in
  `%?Mc(…)<…>` like the album count (empty as long as the database is not
  ready).

### Heard and unheard

- A podcast episode or audiobook chapter counts as heard as soon as its play
  count is above 0. Rockbox counts a track as played when it ran for at
  least 15 s at a change, skip or stop, or to its end
  (`tagtree_track_finish_event()`, the rule of the runtime data). For
  podcasts and audiobooks the firmware always counts this, even without the
  setting "Gather Runtime Data"; for music it stays with the setting. For
  this `tagtree_buffer_event()` looks up every track in the database while
  buffering (`tagcache_idx`), regardless of the settings; before, this
  happened only with "Gather Runtime Data" or "Auto Resume", and without
  both the counter was not touched (found in a test: an audiobook played for
  16 s, stopped, the dot stayed). The database thread writes the new
  counters at once (`tagcache_flush_numeric()`, `Q_FLUSH_NUMERIC`), not only
  when the disk is idle.
- In the lists of podcasts and audiobooks a blue dot stands at the right
  end: at every unheard episode (in the arrow column, 12 px from the edge)
  and at every podcast or audiobook with unheard episodes (left of the
  arrow, 26 px from the edge). The dot is 8 px across, in the accent colour
  of the theme (`line selector gloss bottom color`, `#2160CB`), white in the
  selected row. The episode that is playing counts as heard after 15 s.
- Context menu (hold select) on an episode or a podcast or audiobook:
  **Mark as Unheard**. It resets the play count, play time, "last played"
  and the resume position of the episode or of all episodes
  (`tagcache_mark_unheard()`, directly in the master index and in the
  database in RAM, under the lock of the command queue). If a bookmark
  points to one of these episodes, it is deleted, in the bookmark file of the
  folder and in "Recent Bookmarks" (`bookmark_forget_track()` in
  `apps/bookmark.c`; bookmarks of other episodes stay).
- The state lives in the database. "Initialize Now" resets it, unless it was
  saved before with "Export Modifications" and imported again afterwards.

Code: `tagcache_entry_media()`, `tagcache_entry_heard()`,
`tagcache_count_unheard()`, `tagcache_mark_unheard()`,
`tagcache_numeric_generation()` in `apps/tagcache.c`;
`tagtree_item_mark()`, `tagtree_has_item_marks()`,
`tagtree_can_mark_unheard()`, `tagtree_mark_unheard()` in `apps/tagtree.c`
(the number of unheard episodes per album is remembered until the counters
change next); menu entry `mark_unheard_item` in `apps/onplay.c`
(`LANG_MARK_UNHEARD`, at the end of the `.lang` files). The marks are drawn
in `apps/gui/bitmap/list.c`, see [ipod6g-more-changes.md](ipod6g-more-changes.md)
(marks at the end of the row).

### Bookmarks for podcasts and audiobooks

- Rockbox creates bookmarks only for playlists that belong to a folder or a
  playlist file (`bookmark_is_bookmarkable_state()`,
  `playlist_dynamic_only()`). A playlist from the database belongs to
  neither, so no bookmarks were created on stop any more once podcasts and
  audiobooks went through the database.
- Now, when an episode or chapter is chosen, `play_media_folder()`
  (`apps/tagtree.c`) plays the folder of the file like the file browser,
  starting at this file, through `bookmark_play()` (`apps/tree.c`, the same
  function that resumes a bookmark). The path is the one from the database,
  with the volume, so that the database finds the playing tracks again.
  Music keeps playing as a playlist from the database.
- So the bookmark settings apply on stop (for example: create and update
  automatically, `/bookmark.ignore` in the root, `bookmark.unignore` in
  `/Podcasts` and `/Audiobooks`).
- One bookmark per podcast or audiobook: the bookmark file of the folder
  (`/Podcasts/<name>.bmark`, `/Audiobooks/<name>.bmark`) holds only the
  newest one; `add_bookmark()` takes over no older ones there. In "Recent
  Bookmarks" the setting "unique only" (one per playlist) takes care of
  this; folders with and without the volume part count as the same
  (`bookmark_get_playlist_and_track_hash()`).
- Resuming from the database: choosing the episode or chapter the folder's
  bookmark points to continues playback at its position; any other episode
  starts from the beginning and overwrites the bookmark on stop
  (`bookmark_play_media_folder()` in `apps/bookmark.c`: reads the bookmark
  with `parse_bookmark()`, compares the file name and starts with
  `bookmark_play()`). The folder's bookmark is the first one of its bookmark
  file, otherwise its entry in "Recent Bookmarks" (`most-recent.bmark`):
  with "Bookmark on Stop: Recent only – Yes" Rockbox writes no folder file,
  only this entry; the first version only looked for the folder file and so
  always started from the beginning (`folder_bookmark()`, folders with and
  without the volume part count as the same). Shuffle and repeat stay as
  set, unlike loading through the bookmark list, which takes them from the
  bookmark. "Recent Bookmarks" and the file browser ("Load Last Bookmark")
  stay available as well.

### Changed files

| File | Part |
| --- | --- |
| `apps/tagcache.h` | `tag_virt_mediatype`, `enum tagcache_media`, field `media`, `tagcache_search_set_media()`, `tagcache_search_get_media()`, `tagcache_count_albums(media)` |
| `apps/tagcache.c` | flags, `TAGCACHE_MAGIC` 0x11, `media_dirs`/`media_dir_of()` (with the volume part), scanning only the media folders, without `database.ignore`, media map and filter in every search path, album count per media type, `load_ramcache()` no longer switches off a database that grew |
| `apps/tagtree.c`, `apps/tagtree.h` | tag `mediatype`, no special entries for podcasts and audiobooks, opening categories directly, heard status (counting always on, marks, mark as unheard) |
| `apps/onplay.c`, `apps/lang/*.lang` | "Mark as Unheard" (`LANG_MARK_UNHEARD`) |
| `apps/bookmark.c` | one bookmark per podcast/audiobook, folders with/without the volume count as the same |
| `apps/tagnavi.config` | entries "Podcasts" and "Audiobooks" |
| `apps/root_menu.c`, `apps/root_menu.h` | main menu entries open the categories, numbers from the database; folder counting removed |
| `apps/tree.c`, `apps/tree.h` | exit level of the database browser instead of an exit folder |
| `GlossySlate/.rockbox/wps/glossyslate.sbs`, `GlossySlate/tools/build_skin.py` | `%?Mc(podcasts)<…>`, `%?Mc(audiobooks)<…>` |

## Limitations

- If a music album and a podcast or audiobook have exactly the same album
  name, they share the name in the database and so the cover of the album
  list. The lists themselves stay apart.
- `mediatype` chooses the media type only as a single condition with `==`;
  in an or-chain (`|`) it does not act as a choice.
- With more than 12,288 different values in a list (6,144 in plugins)
  Rockbox searches more slowly relative to the index; without a matching
  duplicate buffer entries can then appear twice, as before with relative
  searches.

## Test

On the Mac with the database tool (`tools/database`, the same code with
`IPOD_6G`), the database built again from a copy of a real iPod library
(read only), plus an audio file in the root folder and one in an unrelated
folder:

- 3,141 music tracks, 31 podcast episodes, 36 audiobook chapters, 0 files
  outside the media folders.
- For every media type and every tag (album, artist, album artist, genre,
  composer, canonical artist, title, file name) the list as in the database
  menu and as in plugins against the truth worked out from the paths:
  nothing missing, nothing foreign, no duplicates, order of the tag file
  kept. Album list: 269 music albums, 4 podcasts, 3 audiobooks, each with a
  track of the right media type.
- Filtered search (album artist → track) and years per media type, album
  count (268, 4, 3; without "<Untagged>").
- A database of version 0x10 is rejected; a map that is too small falls back
  to the relative search, without foreign media types.
- A database built on the iPod (firmware with the volume fix), read on the
  Mac: 3,208 entries, all paths start with `/<HDD0>/`, 3,141 music, 31
  podcasts, 36 audiobooks, 269/4/3 albums, no wrong media type.

Limits of the test on the Mac:

- The tool is built without `HAVE_MULTIVOLUME` (`firmware/export/config.h`
  switches it off for `__PCTOOL__`) and scans from `/`. Paths with a volume
  part as on the device do not occur there. So the recognition of the media
  folders is also checked with the original code of `path_strip_volume()`
  and `media_dir_of()`: `/<HD0>/Music/…`, `/<0>/musik/…`,
  `/<HD0>/Podcasts/…`, `/<HD0>/Audiobooks/…` are recognised,
  `/<HD0>/iPod_Control/Music/…`, `/<HD0>/Musical/…`, the volume root and the
  files in it are not; paths without a volume as before.
- On the device the database runs in RAM (`tagcache_ram: on`); these paths
  are built the same way in the code but cannot be checked on the Mac.

## Setting up the device

1. Unzip `rockbox.zip` of the build into `/` of the iPod (firmware, plugins
   and `/.rockbox/tagnavi.config`).
2. Restart. "Music", "Podcasts" or "Audiobooks" report "Database is not
   ready" and ask to initialise it; confirm with "Yes". Or choose
   **Initialize Now** in the database settings (also by holding "Music" in
   the main menu). Play counts and ratings of the old database are lost,
   unless they were saved with the old firmware through "Export
   Modifications" before; "Import Modifications" reads them back afterwards.
3. Optional: delete `database.ignore` in `/Podcasts` and `/Audiobooks`.
