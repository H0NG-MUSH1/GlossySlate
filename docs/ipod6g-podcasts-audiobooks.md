# Podcasts and audiobooks in the main menu

As of 11 November 2026. This file describes the current code in the
repository.

## Behaviour

- The main menu has the entries "Podcasts" and "Audiobooks" (configuration
  names `podcasts` and `audiobooks` for `root menu order`). They open the
  database categories of the same name: albums from `/Podcasts` and
  `/Audiobooks` in the style of the album list, with covers, without the
  special entries "[By Album]", "[All Tracks]" and "[Shuffle]". Podcasts
  and audiobooks appear nowhere else in the database. The separation is
  described in [ipod6g-database-media-types.md](ipod6g-database-media-types.md).
- "Back" in the list of the category leads to the main menu; below it one
  level up as usual. The next time the list opens, the selection is where
  the last visit ended.
- If the database is not ready, the entries ask, like "Music", whether it
  should be built. If the category is missing from
  `/.rockbox/tagnavi.config`, the entry reports its name and the file.
- Below the symbol in the sidebar the theme shows the number of podcasts or
  audiobooks (albums of that media type in the database).
- The symbol of "Audiobooks" is an open book; "Podcasts" keeps the
  microphone.

## History

1. Commit `3fe3997a69`: the database marked files under `/Podcasts` and
   `/Audiobooks`, and the music views filtered with the condition
   `mediatype == "0"`. That worked on the Mac, but on the iPod the views
   stayed empty. The reason: on the device the paths start with the volume
   (`/<HD0>/Podcasts/…`), so the check for `/Podcasts/` at the start never
   matched. In addition, entries of an older firmware carried no mark.
2. After that the entries opened the folders in the file browser, and
   `database.ignore` kept the folders out of the database.
3. Now: every entry carries its media type, and every search returns one
   media type only (music unless something else is asked for). The firmware
   does not use a database without media types (database version 0x11).
   `database.ignore` is not needed any more.

## Implementation

| File | Part |
| --- | --- |
| `apps/root_menu.c`, `apps/root_menu.h` | `GO_TO_PODCASTS`/`GO_TO_AUDIOBOOKS` go through the database browser; `db_browser_open()` opens the category (`tagtree_open_root_entry()`) and sets the exit level. Like the file browser they count as the "previous browser" (back from the now playing screen). |
| `apps/tree.c`, `apps/tree.h` | `tree_set_id3db_exit_level()`: "Back" on this database level leaves the browser. `root_menu.c` sets it before opening and back to 0 afterwards. |
| `apps/tagtree.c`, `apps/tagtree.h`, `apps/tagnavi.config`, `apps/tagcache.c`, `apps/tagcache.h` | categories and separation, see [ipod6g-database-media-types.md](ipod6g-database-media-types.md). |
| `apps/root_menu.c` | icon of "Audiobooks": `ICON_AUDIOBOOKS`, without a remote display `Icon_Remote_Display_menu` (otherwise `Icon_Voice`). The iPod 6G has no remote display, so the original symbol never appears there; an iconset can draw a book in its place (27). Glossy Slate shows no icons in lists. |
| `apps/lang/*.lang` | `LANG_PODCASTS`, `LANG_AUDIOBOOKS` (at the end of the files). |

An additional icon could not simply be appended: Rockbox divides the height
of an iconset by the fixed number `Icon_Last_Themeable`, so every iconset
would need one more row.

## Setting up the device

See [ipod6g-database-media-types.md](ipod6g-database-media-types.md),
section "Setting up the device": install the zip, build the database once
again.
