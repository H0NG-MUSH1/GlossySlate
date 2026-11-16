# Settings without a tile of their own in the sidebar

As of 11 November 2026, firmware and theme on the iPod (Glossy Slate 1.0
with the changes of the fork). Worked out from the menu files of the
firmware, evaluated with the build switches of the iPod 6G, and from the
tile assignments of `glossyslate.sbs`. The names are the English menu texts
of Rockbox.

Until 17 November 2026 all entries listed here showed the substitute tile
with the gear in the sidebar. The skin assigns tiles by the text shown (`%LT`, through
`%Sx(...)`); entries with the same text therefore share a tile and appear
here only once (with "also under …").

**Already with a tile or preview of their own (24):** Sound Settings,
Volume, Equalizer, Playback Settings, Shuffle, Repeat, Album Art, General
Settings, Reset Settings, Database, Display, LCD Settings, Backlight,
Brightness, Bookmarking, Voice, Theme Settings, Scroll Bar, Second Line in
Player, Album Art Corners, Key Lock, Recording, Time & Date, Manage
Settings.

**Without a tile of their own: 224 entries.** Sub menus and functions are
included, because they show the sidebar as well.

**ID** (added 16 November 2026): every entry has a fixed ID, T001 to T224,
in the order of the tables. A tile made for an entry is named by its ID
(e.g. `T001.png` for "Volume Limit"), so that it can be matched to the menu
text without doubt. The IDs do not change; an entry added later gets the next
free number (T225 …), a removed one leaves its number unused.

**Tiles (17 November 2026):** every entry has a tile now, after the design
principle of RetailOS: one motif for related settings, and the entries of a
sub menu show the tile of the entry that opens it. The column **Tile** names
it: 49 new motifs (glyphs in `tools/sources/tiles/`, put into the tile font
by `tools/build_tile_glyphs.py`, U+E022 to U+E052) and 11 tiles that existed
already (`eq`, `shuffle`, `playlist`, `folder`, `database`, `timer`, `sun`,
`bookmark`, `voice`, `brush`, `scroll_right`). The skin assigns them by the
menu text in `setting_tiles()` of `tools/build_skin.py`; under the tile
stands the value of the entry (`%LV`).

¹ Its text changes with the state or contains brackets, so `%Sx(...)` cannot
name it: it gets the tile of its sub menu through the list title
(`SUBMENU_TILES` in `build_skin.py`).

The list below is the state of 11 November 2026 (firmware and theme); the
sidebar shows the gear only for entries that are not in it.


## Sound Settings

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T001 | `volume_limit` | Volume Limit | Upper limit the volume cannot be set above. |
| T002 | `bass` | Bass | Raises or lowers the low frequencies. |
| T003 | `bass` | Bass Cutoff | Frequency up to which the bass control works. |
| T004 | `treble` | Treble | Raises or lowers the high frequencies. |
| T005 | `treble` | Treble Cutoff | Frequency from which the treble control works. |
| T006 | `balance` | Balance | Distribution between the left and right channel; under Haas the weighting of the effect between the channels. (also under Sound Settings › Haas Stereo Widening) |
| T007 | `stereo` | Channel Configuration | Stereo, mono, swapped channels, karaoke or a custom stereo width. |
| T008 | `stereo_wide` | Stereo Width | Width of the stereo image in percent (with a custom channel configuration). |
| T009 | `headphones` | Crossfeed | Sub menu and switch: mixes the channels slightly, so that music in headphones sounds less "inside the head". |
| T010 | `dither` | Dithering | Noise shaping when converting to 16 bits, reduces distortion in quiet passages. |
| T011 | `stereo_wide` | Haas Stereo Widening | Sub menu and switch: widens the stereo image by delaying one channel slightly. |
| T012 | `bass` | Perceptual Bass Enhancement | Sub menu and switch: makes bass sound stronger on small earphones. |
| T013 | `treble` | Presence/Treble Attenuation | Softens sharp treble, so that long listening is less tiring. |
| T014 | `metronome` | Timestretch | Allows changing the tempo without changing the pitch. |
| T015 | `compressor` | Dynamic Range Compressor | Sub menu: evens out loud and quiet passages. |

## Sound Settings › Crossfeed

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T016 | `headphones` | Direct Gain | Crossfeed: level of the unchanged channel. |
| T017 | `headphones` | Cross Gain | Crossfeed: level of the opposite channel mixed in. |
| T018 | `headphones` | High-Frequency Attenuation | Crossfeed: damping of the treble in the mixed-in signal. |
| T019 | `headphones` | High-Frequency Cutoff | Crossfeed: frequency from which the treble is damped. |

## Sound Settings › Equalizer

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T020 | `eq` | Enable EQ | Switches the equaliser on or off. |
| T021 | `eq` | Graphical EQ | Equaliser with sliders for all bands. |
| T022 | `eq` | Precut | Lowers the level before the effect so that nothing clips. (also under Sound Settings › Perceptual Bass Enhancement; Playback Settings › Replaygain) |
| T023 | `eq` | Simple EQ Settings | Gain per band as a list. |
| T024 | `eq` | Advanced EQ Settings | Centre frequency, Q and gain per band. |
| T025 | `eq` | Save EQ Preset | Saves the current EQ setting as a file. |
| T026 | `eq` | Browse EQ Presets | Loads a saved EQ preset. |
| T027 | `eq` | Reset EQ | Resets all bands to neutral. |

## Sound Settings › Haas Stereo Widening

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T028 | `stereo_wide` | Upper Bypass Frequency | Haas: treble above this frequency stays untouched. |
| T029 | `stereo_wide` | Lower Bypass Frequency | Haas: bass below this frequency stays untouched. |
| T030 | `stereo_wide` | Process Side Channel Only | Haas: applies the effect to the stereo part only. |
| T031 | `stereo_wide` | Dry/Wet Mix | Haas: mix of the original and the effect. |

## Sound Settings › Dynamic Range Compressor

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T032 | `compressor` | Threshold | Compressor: level from which it compresses. |
| T033 | `compressor` | Makeup Gain | Compressor: gain after the compression. |
| T034 | `compressor` | Compression Ratio | Compressor: strength of the compression. |
| T035 | `compressor` | Knee | Compressor: soft or hard onset at the threshold. |
| T036 | `compressor` | Attack Time | Compressor: how fast it reacts to loud passages. |
| T037 | `compressor` | Release Time | Compressor: how fast it lets go again afterwards. |

## Playback Settings

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T038 | `shuffle` | Play Selected First | When shuffling, the selected track starts first. |
| T039 | `seek` | Fast-Forward/Rewind | Sub menu for fast forward and rewind. |
| T040 | `buffer` | Anti-Skip Buffer | How early the playback buffer is refilled (protection against dropouts). |
| T041 | `fade` | Fade on Stop/Pause | Fades out when stopping and in when resuming. |
| T042 | `single` | Single Mode | Stops after every track. |
| T043 | `party` | Party Mode | No stopping or skipping; new tracks are appended. |
| T044 | `crossfade` | Crossfade | Sub menu: a smooth transition between two tracks. |
| T045 | `soundcheck` | Replaygain | Sub menu: evens out tracks of different loudness. |
| T046 | `beep` | Track Skip Beep | A beep when changing to the next track. |
| T047 | `next_folder` | Auto-Change Directory | Plays the next folder after the last track of a folder. |
| T048 | `next_folder` | Constrain Auto-Change | Changes folders only within the starting folder. |
| T049 | `cd` | Cuesheet Support | Uses .cue files for track boundaries in long recordings. |
| T050 | `unplug` | Pause on Headphone Unplug | Sub menu and setting: pauses when the headphones are pulled. |
| T051 | `remote` | Headset Remote Control | Control through the buttons on the headphone cable (fork: double and triple clicks). |
| T052 | `skip` | Skip Length | What next/previous do: a whole track or a few seconds. |
| T053 | `skip` | Prevent Track Skipping | Next/previous do not change the track, only seek. |
| T054 | `rewind` | Rewind Across Tracks | Rewinding goes past the start of the track into the previous track. |
| T055 | `rewind` | Rewind Before Resume | Goes back a few seconds when resuming. |
| T056 | `rewind` | Rewind on Pause | Goes back a few seconds when pausing. |
| T057 | `tuning_fork` | Frequency | Output frequency of playback (44.1 / 48 kHz); under recording the sample rate of the recording. (also under Recording) |
| T058 | `log` | Logging | Writes played tracks to a log file (scrobbling). |

## Playback Settings › Fast-Forward/Rewind

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T059 | `seek` | FF/RW Min Step | Step size at the start of seeking. |
| T060 | `seek` | FF/RW Accel | How fast seeking speeds up. |

## Playback Settings › Crossfade

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T061 | `crossfade` | Enable Crossfade | When to crossfade (off, only when shuffling, always …). |
| T062 | `crossfade` | Fade-In Delay | Crossfade: waiting time before the new track comes in. |
| T063 | `crossfade` | Fade-In Duration | Crossfade: duration of the fade in. |
| T064 | `crossfade` | Fade-Out Delay | Crossfade: waiting time before the old track gets quieter. |
| T065 | `crossfade` | Fade-Out Duration | Crossfade: duration of the fade out. |
| T066 | `crossfade` | Fade-Out Mode | Crossfade: whether the old track fades out or is mixed under the new one. |

## Playback Settings › Replaygain

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T067 | `soundcheck` | Replaygain Type | Replaygain by track, by album or depending on shuffle. |
| T068 | `soundcheck` | Prevent Clipping | Replaygain: lowers the level if the adjustment would clip. |

## Playback Settings › Pause on Headphone Unplug

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T069 | `unplug` | Disable resume on startup if phones unplugged | Resumes after unplugging only with the headphones plugged in. |

## General Settings

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T070 | `now_playing` | What's Playing Screen | Sub menu: hotkey and context menu of the now playing screen. |
| T071 | `playlist` | Playlists | Sub menu: behaviour of playlists. |
| T072 | `folder` | File View | Sub menu: behaviour of the file browser. |
| T073 | `ipod` | System | Sub menu: battery, disk, limits and hardware (the same text as the main menu entry "System"). |
| T074 | `power` | Startup/Shutdown | Sub menu: start, shutdown and sleep timer. |
| T075 | `resume` | Automatic Resume | Sub menu and switch: remembers the position in tracks (e.g. audiobooks). |
| T076 | `globe` | Language | Language of the user interface (choose a language file). |

## General Settings › What's Playing Screen

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T077 | `now_playing` ¹ | WPS Hotkey | Action of the hotkey on the now playing screen; the text shows the chosen action in brackets. |
| T078 | `now_playing` ¹ | Set Context Item 1 to 4 | Four entries of the context menu of the now playing screen; the text shows the number and action in brackets. |

## General Settings › Playlists

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T079 | `playlist` | Sort Playlists | Sort order of the playlists in the catalogue. |
| T080 | `playlist` | Playlist Viewer Settings | Sub menu: how the playlist is shown. |
| T081 | `playlist` | Recursively Insert Directories | Includes the subfolders when inserting a folder. |
| T082 | `playlist` | Current Playlist | Sub menu: behaviour of the current playlist. |

## General Settings › Playlists › Playlist Viewer Settings

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T083 | `playlist` | Show Icons | Icons in the playlist view (no effect in the fork, list icons are off). |
| T084 | `playlist` | Show Indices | Shows the number in front of every track of the playlist. |
| T085 | `playlist` | Track Display | The playlist shows file names or titles from the tags. |

## General Settings › Playlists › Current Playlist

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T086 | `playlist` | Warn When Erasing Dynamic Playlist | Asks before the current playlist is replaced. |
| T087 | `playlist` | Keep Current Track When Replacing Playlist | The playing track keeps playing when a new playlist is loaded. |
| T088 | `playlist` | Show Shuffled Adding Options | Shows "insert shuffled" in the context menu. |
| T089 | `playlist` | Show Queue Options | Shows "queue" in the context menu. |

## General Settings › File View

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T090 | `folder` | Sort Case Sensitive | Whether upper and lower case count when sorting. |
| T091 | `folder` | Sort Directories | Sorts folders alphabetically or by date. |
| T092 | `folder` | Sort Files | Sorts files alphabetically, by date or by type. |
| T093 | `folder` | Interpret numbers when sorting | "Track 2" before "Track 10" instead of purely alphabetically. |
| T094 | `folder` | Show Files | Which files the browser shows (all, supported, music only …). |
| T095 | `folder` | Show Filename Extensions | Shows extensions like ".mp3" in file names. |
| T096 | `folder` | Follow Playlist | The browser opens at the folder of the playing track. |
| T097 | `folder` | Show Path | Shows the folder path as the title of the browser. |
| T098 | `folder` | Always remember last folder | The browser opens in the folder visited last. |
| T099 | `folder` | Start File Browser at / | Resets the starting folder of the browser to the root. |
| T100 | `folder` ¹ | File Browser Hotkey | Action of the hotkey in the file browser; the text shows the chosen action. |

## General Settings › Database

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T101 | `database` | Load to RAM | Keeps the database in memory, so the music list opens faster. |
| T102 | `database` | Auto Update | Updates the database automatically at start. |
| T103 | `database` | Initialize Now | Builds the database completely anew. |
| T104 | `database` | Update Now | Adds new and removes deleted files in the database. |
| T105 | `database` | Gather Runtime Data | Counts plays and play time per track (for top lists). |
| T106 | `database` | Export Modifications | Saves the runtime data to a file. |
| T107 | `database` | Import Modifications | Loads saved runtime data back. |
| T108 | `database` | Select directories to scan | Folders the database reads. |

## General Settings › Display › LCD Settings

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T109 | `timer` ¹ | Backlight (While Plugged In) | How long the display stays lit while the charger is plugged in. |
| T110 | `timer` | Backlight on Lock | Whether the light comes on while the key lock is on. |
| T111 | `timer` | Caption Backlight | Switches the light on briefly when a new track starts. |
| T112 | `timer` | First Buttonpress Enables Backlight Only | The first press with a dark display only wakes the light. |
| T113 | `timer` | Backlight Exemptions | Sub menu: buttons that do not switch the light on. |
| T114 | `timer` ¹ | Sleep (After Backlight Off) | Switches the display off completely after the light. |
| T115 | `sun` | Composite Video Output | TV output through the dock (off, PAL, NTSC). |

## General Settings › Display › LCD Settings › Backlight Exemptions

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T116 | `timer` | Enabled | Switches the backlight exemptions on or off. |
| T117 | `timer` | Settings | Choice of the buttons for the backlight exemptions (the same text as the main menu entry "Settings"). |

## General Settings › Display

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T118 | `sun` | Scrolling | Sub menu: scrolling text and list behaviour. |
| T119 | `meter` | Peak Meter | Sub menu: level meter in recording and skins. (also under Recording) |
| T120 | `sun` | Default Codepage | Character set for tags and files without Unicode. |

## General Settings › Display › Scrolling

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T121 | `sun` | Scroll Speed Setting Example | Speed of the scrolling text; the row shows the effect. |
| T122 | `sun` | Scroll Start Delay | Waiting time before a scrolling text starts. |
| T123 | `sun` | Scroll Step Size Setting Example Text | Pixels per scrolling step; the row shows the effect. |
| T124 | `sun` | Bidirectional Scroll Limit | Up to which length text scrolls back and forth instead of round. |
| T125 | `sun` | Screen Scrolls Out of View | Lets scrolling text run out over the edge. |
| T126 | `sun` | Disable main menu scrolling | No scrolling text in the main menu. |
| T127 | `sun` | Screen Scroll Step Size | Step size when moving long rows sideways. |
| T128 | `sun` | Paged Scrolling | Lists jump page by page instead of row by row. |
| T129 | `sun` | List Wraparound | Jumps from the end of the list back to the start. |
| T130 | `sun` | List Order | Order of the lists (normal or reversed). |

## General Settings › Display › Peak Meter

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T131 | `meter` | Peak Release | Level meter: how fast the bar falls back. (also under Recording › Peak Meter) |
| T132 | `meter` | Peak Hold Time | Level meter: how long the peak stays. (also under Recording › Peak Meter) |
| T133 | `meter` | Clip Hold Time | Level meter: how long the clip mark stays. (also under Recording › Peak Meter) |
| T134 | `meter` | Clip Counter | Counts clipping while recording. (also under Recording › Peak Meter) |
| T135 | `meter` | Scale | Level meter in dB or linear. (also under Recording › Peak Meter) |
| T136 | `meter` | Minimum of Range | Lower limit of the level meter. (also under Recording › Peak Meter) |
| T137 | `meter` | Maximum of Range | Upper limit of the level meter. (also under Recording › Peak Meter) |

## General Settings › System

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T138 | `ipod` | Battery | Sub menu: battery and charging. |
| T139 | `ipod` | Disk | Sub menu: storage (hardly relevant on an iPod with an SSD). |
| T140 | `ipod` | Limits | Sub menu: upper limits for lists and fonts. |
| T141 | `ipod` | Volume Adjustment Mode | Volume steps in dB or evenly spread. |
| T142 | `ipod` | Number of Volume Steps | Number of steps in the even mode. |
| T143 | `ipod` | Use Shortcuts Menu Instead of Quick Screen | The quick screen button opens the shortcuts instead. |
| T144 | `ipod` | Use Morse Code Input | Text input in Morse code instead of the on-screen keyboard. |
| T145 | `ipod` | Car Adapter Mode | Sub menu and switch: playback follows the power supply in the car. |
| T146 | `ipod` | Serial Bitrate | Speed of the serial dock interface (accessories). |
| T147 | `ipod` | Accessory Power Supply | Powers accessories on the dock. |
| T148 | `ipod` | Line Out | Switches the line output on the dock on or off. |
| T149 | `ipod` | Keyclick | Sub menu: click sounds on button presses. |
| T150 | `ipod` | USB | Sub menu: behaviour on the computer. |

## General Settings › System › Battery

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T151 | `ipod` | Battery Capacity | Capacity of the built-in battery for the runtime estimate. |
| T152 | `ipod` | Charge During USB Connection | Whether and when to charge over USB. |

## General Settings › System › Disk

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T153 | `ipod` | Disk Spindown | When the disk switches off after the last access. |
| T154 | `ipod` | Directory Cache | Keeps the folder structure in memory (faster browser). |

## General Settings › System › Limits

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T155 | `ipod` | Max Entries in File Browser | Maximum number of entries per folder in the browser. |
| T156 | `ipod` | Max Playlist Size | Maximum number of tracks in a playlist. |
| T157 | `ipod` | Glyphs To Cache | How many font characters are kept in memory. |

## General Settings › System › Car Adapter Mode

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T158 | `ipod` | Delay Before Resume | Car adapter: waiting time before playback resumes. |

## General Settings › System › Keyclick

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T159 | `ipod` | Headphone Keyclick | A click in the headphones when pressing a button or turning the wheel. |
| T160 | `ipod` | Speaker Keyclick | A click through the built-in speaker. |
| T161 | `ipod` | Keyclick Repeats | Repeats the click while a button is held. |

## General Settings › System › USB

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T162 | `ipod` | USB HID | The iPod also registers as a keyboard/remote control on the computer. |
| T163 | `ipod` | USB Keypad Mode | Which key assignment applies in HID mode (multimedia, presentation …). |
| T164 | `ipod` | USB-DAC | The iPod plays sound from the computer as a USB sound card. |
| T165 | `ipod` | USB Mode | Mass storage, charge only, or ask when plugged in. |

## General Settings › Startup/Shutdown

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T166 | `power` | Show Shutdown Message | Shows a message when switching off. |
| T167 | `power` | Start Screen | The screen Rockbox starts with (main menu, now playing …). |
| T168 | `power` | Idle Poweroff | Switches off after a while without use and playback. |
| T169 | `power` ¹ | Start Sleep Timer / Cancel Sleep Timer | Starts the sleep timer or cancels it; the text changes with the state. |
| T170 | `power` | Default Sleep Timer Duration | Duration the sleep timer starts with. |
| T171 | `power` | Start Sleep Timer on Boot | Starts the sleep timer at every start. |
| T172 | `power` | Restart Sleep Timer on Keypress | Every button press restarts the sleep timer. |
| T173 | `power` | Clear settings when hold switch is on during startup | Resets all settings when hold is on at start. |

## General Settings › Bookmarking

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T174 | `bookmark` | Bookmark on Stop | Creates a bookmark automatically when stopping. |
| T175 | `bookmark` | Update on Stop | Updates an existing bookmark when stopping. |
| T176 | `bookmark` | Load Last Bookmark | Loads the last bookmark of a file when it is opened. |
| T177 | `bookmark` | Maintain a List of Recent Bookmarks? | Keeps the list "Recent Bookmarks" in the main menu. |

## General Settings › Automatic Resume

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T178 | `resume` | Automatic Track Change Only | Resumes also when the track changes by itself. |

## General Settings › Voice

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T179 | `voice` | Voice Menus | Voice: announce menus. |
| T180 | `voice` | Voice Directories | Voice: announce folder names. |
| T181 | `voice` | Use Directory .talk Clips | Voice: use prepared voice files for folders. |
| T182 | `voice` | Voice Filenames | Voice: announce file names. |
| T183 | `voice` | Use File .talk Clips | Voice: use prepared voice files for files. |
| T184 | `voice` | Say File Type | Voice: announce the file type as well. |
| T185 | `voice` | Announce Battery Level | Voice: announce the battery level when it drops. |
| T186 | `voice` | Voice Prompt Volume | Volume of the announcements relative to the music. |

## Theme Settings

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T187 | `brush` | Browse Theme Files | List of the themes to load. |
| T188 | `font` | Font | Choose the font of the user interface. |
| T189 | `now_playing` | While Playing Screen | Choose the skin of the now playing screen. |
| T190 | `rec_screen` | Recording Screen | Choose the skin of the recording screen. |
| T191 | `base_skin` | Base Skin | Choose the skin for the status bar and menus. |
| T192 | `backdrop` | Clear Backdrop | Removes a backdrop picture of the menus. |
| T193 | `scroll_right` | Status-/Scrollbar | Sub menu: status bar, scroll bar, second line, album art corners, key lock. |
| T194 | `line_selector` | Line Selector Type | Look of the selected row (bar, gloss bar, colour …). |
| T195 | `line_separator` | Line Separator | Line between the list rows (thickness). |
| T196 | `palette` | Colours | Sub menu: colours of the user interface. |

## Theme Settings › Status-/Scrollbar

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T197 | `scroll_right` | Scroll Bar Width | Width of the scroll bar in pixels. |

## Theme Settings › Colours

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T198 | `palette` | Line Selector Colours | Sub menu: colours of the selection bar. |
| T199 | `palette` | Line Separator Colour | Colour of the line between the rows. |
| T200 | `palette` | Background Colour | Background colour of the lists. |
| T201 | `palette` | Foreground Colour | Text colour of the lists. |
| T202 | `palette` | Reset Colours | Resets all colours to the default. |

## Theme Settings › Colours › Line Selector Colours

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T203 | `palette` | Primary Colour | Selection bar: top colour of the gradient. |
| T204 | `palette` | Secondary Colour | Selection bar: bottom colour of the gradient. |
| T205 | `palette` | Text Colour | Text colour on the selection bar. |

## Settings (top level)

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T206 | `main_menu` | Main Menu | Shows, hides and orders the entries of the main menu. |

## Manage Settings

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T207 | `cfg_file` | Browse .cfg Files | Loads a saved configuration; under recording a recording preset. (also under Recording) |
| T208 | `cfg_save` | Save .cfg File | Saves all settings as a file; under recording the recording preset. (also under Recording) |
| T209 | `cfg_save` | Save Sound Settings | Saves only the sound settings as a file. |
| T210 | `cfg_save` | Save Theme Settings | Saves only the theme settings as a file. |

## Recording

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T211 | `audio_file` | Format | File format of the recording (WAV, MP3, FLAC …). |
| T212 | `audio_file` | Encoder Settings | Quality or bitrate of the chosen format. |
| T213 | `plug` | Source | Recording source (microphone, line in). |
| T214 | `stereo` | Channels | Recording in stereo or mono. |
| T215 | `stereo` | Mono mode | How stereo becomes mono (mix, left only, right only). |
| T216 | `scissors` | File Split Options | Sub menu: splits long recordings into several files. |
| T217 | `prerecord` | Prerecord Time | Seconds recorded before the start as well. |
| T218 | `rec_folder` | Clear Recording Directory | Saves recordings in the default folder again. |
| T219 | `clip_light` | Clipping Light | Flashes the display when clipping. |
| T220 | `trigger` | Trigger | Starts and stops the recording automatically by level. |

## Recording › File Split Options

| ID | Tile | Setting | Description |
| --- | --- | --- | --- |
| T221 | `scissors` | Split Measure | Splits by time or by file size. |
| T222 | `scissors` | What to do when Splitting | Starts a new file or stops the recording. |
| T223 | `scissors` | Split Time | Length after which to split. |
| T224 | `scissors` | Split Filesize | File size after which to split. |
