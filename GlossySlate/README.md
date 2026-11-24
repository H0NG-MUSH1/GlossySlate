# Glossy Slate – theme and firmware for the iPod Classic

This package contains the **Glossy Slate** theme together with the
**custom Rockbox firmware** it needs. The theme uses features that exist
only in this firmware, so install both: the theme does not work with stock
Rockbox.

| | |
| --- | --- |
| Theme | Glossy Slate 1.0 |
| Firmware | Rockbox `4.0 (dev build)`, a fork of Rockbox commit `41a3e60b9c` |
| Device | iPod Classic (Rockbox target `ipod6g`), tested on a 6th generation iPod Classic |

> Use at your own risk. **Back up your iPod first**, at least the folder
> `.rockbox` (it holds your settings and your database).

---

## 1. Before you start

- **Rockbox bootloader:** the iPod must already start Rockbox, or you
  install the Rockbox bootloader first, as the
  [Rockbox manual](https://www.rockbox.org/manual.shtml) for the iPod
  Classic describes (Windows: Rockbox Utility; macOS and Linux: `mks5lboot`).
  This package contains no bootloader.
- **FAT32:** Rockbox works only on iPods formatted with FAT32 (set up with
  iTunes for Windows). An iPod formatted on a Mac (HFS+) has to be
  converted first.
- **Hidden folders:** the folder `.rockbox` starts with a dot. In the macOS
  Finder press **⌘ ⇧ .** (Cmd-Shift-dot) to see it. Windows shows it
  normally.

## 2. What is in this package

| Path | Content | Copy to the iPod? |
| --- | --- | --- |
| `.rockbox/` | the firmware (`rockbox.ipod`, codecs, plugins, languages …) **and** the theme (`themes/glossyslate.cfg`, `wps/glossyslate.*`, `wps/glossyslate/`, `fonts/*GlossySlate*`) | **yes**, merged into `/.rockbox` (see 3.) |
| `README.md` | this guide | no |
| `previews/` | pictures of the theme | no |
| `DESIGN.md`, `ROCKBOX-CHANGES.md`, `SETTINGS-WITHOUT-TILE.md` | design specification and what the theme needs from the firmware | no |
| `tools/`, `graphics/`, `firmware-assets/` | sources and tools to rebuild the theme | no |
| `GlossySlate.zip` | this package as one file | no |

Unzip `GlossySlate.zip` on your computer, **not** on the iPod. Only the
contents of `.rockbox/` go onto the iPod.

## 3. Installing (first installation and update)

1. Connect the iPod to the computer (in Rockbox it appears as a USB drive).
2. **Merge** the package's `.rockbox` folder into the folder `.rockbox` on
   the iPod: new files are added, files of the package replace older ones,
   and everything else on the iPod (settings, database, bookmarks) stays.
   **Never replace or delete the whole folder** – that would delete your
   settings and your database (see 4.).

   **macOS** – do not drag the folder in the Finder: when a folder of the
   same name exists, the Finder offers "Replace", which deletes the
   `.rockbox` folder on the iPod with everything in it. Use the Terminal
   instead (replace `IPOD` with the name of your iPod in the Finder, and
   the first path with the place where you unzipped the package):

   ```sh
   rsync -rt --exclude='.DS_Store' ~/Downloads/GlossySlate/.rockbox/ "/Volumes/IPOD/.rockbox/"
   ```

   The slashes at the end of both paths matter: they copy the *contents*
   of the folder into the folder on the iPod.

   **Windows** – copy the folder `.rockbox` from the package into the root
   of the iPod drive. Explorer merges folders of the same name; when it
   asks about files that already exist, choose **"Replace the files in the
   destination"** (this affects only the files of the package).

   **Linux:**

   ```sh
   cp -r GlossySlate/.rockbox/. /media/$USER/IPOD/.rockbox/
   ```

   If no `.rockbox` folder exists on the iPod yet (first installation),
   simply copy the package's `.rockbox` folder into the root of the iPod.

3. **Updating from an older Glossy Slate:** delete the folder
   `/.rockbox/wps/glossyslate/` on the iPod before step 2, so that no
   pictures of the older version stay behind. It contains only theme
   pictures.
4. Eject the iPod on the computer, then unplug it. If Rockbox shows
   **"Boot changed – Reboot now?"**, choose yes: the iPod starts the new
   firmware.
5. Check the firmware: *System › Rockbox Info* (in the main menu) must
   show the version **4.0 (dev build)**.
6. Choose the theme: *Settings › Theme Settings › Browse Theme Files ›
   glossyslate*.
7. **Build the database again** – required once when you come from stock
   Rockbox or from an older build of this firmware (it uses a new database
   version and ignores the old one): *Settings › General Settings ›
   Database › Initialize Now*. *Load to RAM* is recommended.

### Where your music goes

| Folder on the iPod | Shown as |
| --- | --- |
| `/Music` (or `/Musik`) | music |
| `/Podcasts/<podcast>/` | podcasts, one folder per podcast |
| `/Audiobooks/<audiobook>/` | audiobooks, one folder per audiobook |

After adding music, update the database (*Initialize Now*, or let Rockbox
update it automatically if you have switched that on).

## 4. Files you must not overwrite or delete

These files are **not** part of the package, so a merge (step 3.2) keeps
them. They are lost only if the whole `/.rockbox` folder is replaced or
deleted – so keep your backup until everything works.

| File or folder in `/.rockbox` | What it holds |
| --- | --- |
| `config.cfg` | **all your settings**, including the sound settings (volume, equaliser, bass and treble, balance, crossfade …), the language and the chosen theme |
| `sound*.cfg`, `config*.cfg` | sound settings and settings you saved yourself (*General Settings › Manage Settings*) |
| `eqs/` | your own equaliser presets |
| `themes/theme*.cfg` | theme settings you saved yourself |
| `fixed.cfg` | fixed settings, if you use them |
| `database_*.tcd` | the database (it is built again in step 3.7 anyway) |
| `tagnavi_custom.config` | your own database menus |
| `.resume.cfg`, `.playlist_control` | where playback resumes, the current playlist |
| `most-recent.bmark` | recent bookmarks (other bookmarks lie as `.bmark` files next to the music) |
| `shortcuts.txt` | your shortcuts |
| `recpresets/` | recording presets |
| `rocks/…` (data of plugins) | e.g. the Cover Flow cache and saved games; kept by the merge |

The package **replaces** on purpose: the firmware (`rockbox.ipod`,
`rockbox-info.txt`), `codecs/`, `rocks/` (the plugins themselves),
`langs/`, `codepages/`, the default fonts and themes, `viewers.config` and
`tagnavi.config`. `tagnavi.config` holds the database menus of this
firmware (with podcasts and audiobooks); put changes of your own into
`tagnavi_custom.config`, which is never replaced.

## 5. If something does not work

| Problem | What to do |
| --- | --- |
| The theme does not load, or looks broken | *Rockbox Info* must show **4.0 (dev build)**: the theme needs this firmware. Copy `.rockbox` again, and make sure it went to `/.rockbox` on the iPod (not into a second folder `/.rockbox/.rockbox`). |
| Podcasts or audiobooks appear as music, or their lists are empty | Build the database again (step 3.7); check the folders (section "Where your music goes"). |
| Settings are gone | `config.cfg` was replaced or deleted: copy it back from your backup. |
| Files starting with `._` on the iPod | made by macOS; harmless, Rockbox hides them. |

To go back to your previous installation, copy your backup of `.rockbox`
back onto the iPod.

## 6. Languages

The theme follows the language set on the iPod (*Settings › General
Settings › Language*). English, English (US), German and Spanish have all
texts of the theme; other languages show the theme's own texts in English.

## 7. License

- Rockbox and the changes of this firmware: GNU General Public License,
  version 2 or later. The source code is in the repository this package
  comes from.
- The Glossy Slate theme: GNU General Public License, version 3 or later
  (it builds on [adwaitapod](https://github.com/D0-0K/adwaitapod)).
- The fonts in `.rockbox/fonts/` (`*GlossySlate*`): SIL Open Font License
  1.1 (`GlossySlate-OFL.txt`), derived from Liberation Sans 2.

iPod is a trademark of Apple Inc. This project is not affiliated with or
endorsed by Apple.
