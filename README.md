# Glossy Slate for Rockbox – iPod Classic 6G

Glossy Slate is a theme for the iPod Classic (6th generation) together with
the modified Rockbox firmware it is built for. The theme uses features that
only exist in this fork (new skin tags, list rendering, popups, database
categories), so the two belong together.

> **Only for the iPod Classic 6G running this fork.** The theme does not work
> with stock Rockbox, and the firmware is built and tested for the Rockbox
> target `ipod6g` only. Use at your own risk and keep a backup of your
> iPod's contents.

| Main menu | Now playing | Album list |
| --- | --- | --- |
| ![Main menu](GlossySlate/previews/main_menu_now_playing.png) | ![Now playing](GlossySlate/previews/now_playing.png) | ![Album list](GlossySlate/previews/album_list.png) |

| Settings | Lock screen | Quick menu |
| --- | --- | --- |
| ![Settings](GlossySlate/previews/settings_repeat.png) | ![Lock screen](GlossySlate/previews/lock_screen.png) | ![Quick menu](GlossySlate/previews/quick_menu.png) |

The pictures come from the skin simulator (`GlossySlate/tools/preview.py`)
with fictitious music; all previews are in `GlossySlate/previews/`.

## What is in this repository

| Path | Content |
| --- | --- |
| `GlossySlate/.rockbox/` | The theme: status bar skin, now playing skin, bitmaps, fonts, theme config |
| `GlossySlate/tools/` | The tools that generate the theme's skins, bitmaps and fonts, and the previews |
| `GlossySlate/DESIGN.md`, `ROCKBOX-CHANGES.md` | Design specification and what the theme needs from the firmware |
| `apps/`, `firmware/`, `lib/`, … | Rockbox with the changes of this fork |
| `docs/ipod6g-*.md` | Developer notes on every change of the fork |

The fork is based on Rockbox commit `41a3e60b9c`. All changes for the iPod
are guarded by `IPOD_6G` in the source.

## Features

### Theme

- Two-column menus: list on the left, a sidebar on the right with a symbol,
  the title and a count for the selected entry (albums, podcasts,
  audiobooks, playlists, bookmarks, recordings, shortcuts).
- Now playing screen with a tilted album cover, reflection and rounded
  corners, track number, title, artist, album and format.
- Lock screen with clock, quick menu for volume, brightness, shuffle and
  repeat, USB screens for "connected" and "ejected".
- Glossy selection bar, list arrows, values on the right of setting rows,
  an overlay scrollbar that fades out.
- Fonts "GlossySlate Sans", rendered from Liberation Sans 2.

### Firmware

- **Podcasts and audiobooks** as their own database categories, read from
  `/Podcasts` and `/Audiobooks` (one folder per podcast or audiobook). Music
  comes from `/Music` (or `/Musik`) only.
- **Heard status:** a blue dot marks podcast episodes and audiobook chapters
  not yet played for 15 seconds; "Mark as Unheard" resets a track or a
  whole podcast/audiobook (and its bookmark).
- **Automatic bookmarks** for podcasts and audiobooks: one per podcast or
  audiobook, written on stop and used when the bookmarked track is started
  again from the database.
- **Album list with covers** and a speaker icon at the playing track in all
  lists.
- **Cover Flow after the original iPod (RetailOS):** the first entry of the
  database opens Cover Flow (Rockpod's Cover Flow, in the colours of the
  theme and below its status bar, with smooth animations whose speed can be
  set). Selecting an album turns its cover to the left, and its back shows
  the album's tracks in the Glossy Slate style: album and artist in a blue
  header, up to seven titles with their length, the glossy selection bar,
  the fading scrollbar and the speaker at the playing track. The other
  covers stay visible around it; Menu turns the cover back. Albums without
  a picture show the theme's default cover.
- **Popups** drawn as glossy panels with shadows (messages, progress,
  yes/no with "Center button" / "Other button").
- **USB:** a second screen once the computer has ejected the drive.
- **Headset remote** with double and triple clicks (can be switched off).
- **Boot screen** over the whole display with the Rockbox logo; the version
  is written below it at start.
- Backlight fade-out, battery gauge that does not jump when the charger is
  plugged in or out and reads 100 % after a full charge, click-free
  switching of the sample rate, a fix for a file system race that could put
  the data of one file into another one.
- **Translatable theme:** every text the theme draws itself (counts in the
  sidebar, USB screens, lock screen date, quick menu …) comes from the
  language files. A new skin tag `%cD` writes dates in the words and order
  of the language ("Monday, 9 November", "Montag, 9. November",
  "lunes, 9 de noviembre").
- Languages: German, English, English (US) and Spanish carry the new texts;
  other languages show them in English.

## Installation

1. **Bootloader:** install the Rockbox bootloader for the iPod Classic as
   described in the Rockbox manual.
2. **Firmware:** build it (below) and unzip `rockbox.zip` into the root of
   the iPod.
3. **Theme:** copy the contents of `GlossySlate/.rockbox/` into the iPod's
   `/.rockbox/` folder. On the iPod choose *Settings › Theme Settings ›
   Browse Theme Files › glossyslate*.
4. **Music:** put music into `/Music`, podcasts into `/Podcasts/<podcast>/`
   and audiobooks into `/Audiobooks/<audiobook>/`, then build the database
   (*Settings › General Settings › Database › Initialize Now*). Loading the
   database into RAM is recommended.

The theme follows the language set on the iPod (*Settings › General
Settings › Language*).

## Building

The firmware is built like stock Rockbox, with the Rockbox ARM toolchain
(`tools/rockboxdev.sh`):

```sh
mkdir build && cd build
../tools/configure      # target: iPod Classic (ipod6g), build type: normal
make -j"$(nproc)"
make zip                # rockbox.zip
```

The theme's tools in `GlossySlate/tools/` need Python 3, Pillow, NumPy,
fontTools and Playwright with Chromium (the previews need only Pillow and
NumPy). Generated files are only changed through these tools;
`GlossySlate/DESIGN.md` (section 8.4) describes the order of the steps.

## Credits

This work would not have been possible without these projects:

- **[Rockbox](https://github.com/Rockbox/rockbox)** – the open source
  firmware this fork is built on, and everyone who has worked on it over the
  years.
- **[adwaitapod](https://github.com/D0-0K/adwaitapod)** by D0-0K – the
  Rockbox theme for the iPod Classic that Glossy Slate grew out of.
- **[Rockpod](https://github.com/nuxcodes/rockpod)** by nuxcodes – a Rockbox
  fork for the iPod Classic and Video that showed what a modern Rockbox on
  the iPod can be and was a reference for this fork; its Cover Flow is the
  base of the Cover Flow here.

The fonts are derived from Liberation Sans 2 (SIL Open Font License 1.1).

## License

- Rockbox and the changes of this fork: GNU General Public License,
  version 2 or later (`docs/COPYING`).
- The Glossy Slate theme (`GlossySlate/`): GNU General Public License,
  version 3 or later, as it builds on adwaitapod (GPL-3.0).
- The fonts in `GlossySlate/.rockbox/fonts/`: SIL Open Font License 1.1
  (`GlossySlate-OFL.txt`). "Liberation" is a reserved font name, so the
  fonts are called GlossySlate.

iPod is a trademark of Apple Inc. This project is not affiliated with or
endorsed by Apple.
