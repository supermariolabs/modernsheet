---
title: App guide
slug: guide
nav: 3
other: guida
description: How to install and use Modern Sheet: library, editor, PDF, Google Drive sync, import.
---

# App guide

[TOC]

## Running Modern Sheet

The simplest way is to **download the app** for macOS, Windows or Linux from the [Download](/en/download/) page. Otherwise it runs from source, with **Python 3.10 or later**:

```
git clone {{repo}}.git
cd modernsheet
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flet run                                               # the desktop app
```

To make a real app, use `flet build`:

| Command | Result | Needs |
|---|---|---|
| `flet build macos` | Mac app | full Xcode and CocoaPods (`brew install cocoapods`) |
| `flet build windows` | Windows app | Visual Studio with the C++ tools |
| `flet build linux` | Linux app | the GTK development packages |
| `flet build ipa` | iPad and iPhone | a Mac with Xcode and an Apple Developer account |
| `flet build apk` | Android | nothing: Flet downloads the Android SDK |

To try the app on iPad or Android without building it: install the **Flet** app from the store, run `flet run --ios` (or `--android`) and scan the QR code.

From the command line, without the app, you get PDF files:

```
python modernsheet_cli.py song.chs -o pdf/               # one PDF per song
python modernsheet_cli.py *.chs --theme clean -t 3       # Clean theme, 3 semitones up
python modernsheet_cli.py --check *.chs                  # check for errors only
```

## The library

On first start the library holds the **examples** folder with the example songs: a good way to see every feature. Your songs go next to it, in folders of your choice.

- **Cards** with title, artist, key, time, BPM, tags, file name and creation and modification dates. The icon on the right switches to the **list** view.
- **Sorting** by title, artist, key, BPM, last modified or date created. By title and artist the songs are **grouped by letter** (A, B, C…).
- **Folders**: *New folder* at the bottom right; the **⋮** menu of a folder **renames** it (references to MusicXML files are updated).
- **Songs with the same title**: the detail that tells them apart (modification date, creation date or file name) is in orange, and the most recent comes first.

### Search

Search looks through the whole library, subfolders included, ignoring case and accents.

| Type | Finds |
|---|---|
| `blues monday` | songs containing all the words (title, artist, tags, file name) |
| `#jazz` | songs tagged *jazz* |
| `A*` | titles **starting** with A |
| `*love` | titles **ending** with "love" |
| `*hey jude*` | songs **containing** "hey jude", spaces included |
| `A* & #jazz` | both conditions (**and**) |
| `A* \| B*` | at least one of them (**or**); `&` binds tighter than `\|` |

## Reading and editing a song

Tapping a card opens the song in **view mode**: just the sheet, with the options above it.

- **Transpose** – / +: changes chords and key signatures; **Real Book** or **Clean**; **Grid** (all bars equal) or **Fill** (a song or a section can set one in the source with `{bar_width}`); **jazz symbols**; **colours by section**.
- **Staff / Both / Tab**: for guitar players, the notated parts also as **tablature**, under the staff or in its place (with the rhythm under the numbers). The app chooses string and fret to stay in a comfortable position; with `{capo}` frets start from the capo. Where needed, correct it in the song: `{tab_position: 5}` (the hand around the 5th fret), `~3` after a note (that string), `{tuning: drop D}` (tuning, also bass and ukulele).
- **⛶ Full screen**: only the pages remain. To leave, use the button at the top right or the **Esc** key.
- Arrow keys, Page Up/Down, the space bar and **Bluetooth pedals** that send those keys turn the pages.

The **pencil** opens the editor next to the sheet:

- **syntax highlighting** and **suggestions** for directives when you type `{` (Enter or Tab to choose);
- what you changed since the last save has a **green background** (brighter on the text you wrote), which goes away when you save;
- **Undo** and **Redo** step by step (a word at a time) with the ↶ ↷ buttons at the top or with ⌘Z / Ctrl+Z and ⌘⇧Z / Ctrl+Y;
- the preview updates as you type; **warnings** are listed under the editor, and tapping one jumps to the line;
- a **tab for every MusicXML file** the song cites, **read only**: the file is shown indented and coloured, and the **Convert to notes in the song** button writes its bars into the `.chs` as notes (`{start_of_notes}`), in place of the reference, which stays as a comment for the record (the MusicXML file is not touched); check the preview and save;
- **Save** (⌘S / Ctrl+S) turns green when there is something to save; **Save as** makes a copy next to the song;
- **Export PDF**; the **red bin** deletes the song and its MusicXML files, after a confirmation listing the files.

The app writes the `{created}` and `{modified}` dates into the file by itself.

## Sync

The library is always **local**: the app works without a network. In *Settings › Sync* you can keep it in step with:

- **Google Drive**: *Connect*, then enter the code shown at google.com/device. The app only sees the files it creates (`drive.file` permission), in a "Modern Sheet" folder of your Drive (the name can be changed).
- **a folder**: for example inside iCloud Drive, Dropbox or Google Drive for desktop, whose client carries it to your other computers.

Sync runs at start, after every save, every 5 minutes and with *Sync now*. Nothing gets lost: if the same song changes on two devices **both versions** are kept, and deleted files go to the **trash** (the app's or Drive's). When a second device connects, the app first downloads what is already there and then adds only the missing songs.

## Importing songs

- **Import a .chs file** (icon in the library bar): copies a `.chs` into the open folder, with the MusicXML files it cites, never overwriting anything.
- **Import from chordsheet.com**: log in to your account, pick the songs from a list and they are imported converted. Details on the [chordsheet.com](/en/chordsheet/) page.

## Settings

Language (Italian or English), songs folder, PDF folder, default display options (theme, grid, row spacing, chord symbols, colours) and sync. A song can set its own row spacing with `{row_spacing}`. Settings are kept on the device.
