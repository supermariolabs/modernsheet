---
title: Changelog
slug: changelog
nav: 6
other: changelog
description: The history of the released versions of Modern Sheet.
---

# Changelog

The released versions of Modern Sheet, newest first. The apps are on the
[Download](/en/download/) page; every version with built apps has its own
[release on GitHub]({{repo}}/releases).

## 0.45.0 — 25 November 2026 {#v0.45.0}

[Release on GitHub]({{repo}}/releases/tag/v0.45.0) · apps for macOS, Windows, Linux and Android

- **References under another name**: `{ref: Verse 1 = Last verse}` shows the referenced section with the
  chosen name, in the original's colour.
- **References straight to an ending**: `{ref: Chorus volta 2}` plays the chorus once, going straight to the
  2nd ending (no repeat, no 1st ending). They combine: `{ref: Chorus volta 2 = Last chorus}`.
- Website: the [.chs format](/en/format/) page is now complete (section colours, tablature, layout,
  diagnostics) and every example has its drawn sheet next to it.

## 0.44.1 — 25 November 2026 {#v0.44.1}

[Release on GitHub]({{repo}}/releases/tag/v0.44.1) · apps for macOS, Windows, Linux and Android

- Fixed: in a song without key or time in its header, a `{key}` or `{time}` written after the first bars
  became the key (or time) of the whole song and the change was not shown. It is now always a **change**,
  with a double bar line, new key signature and new time; library cards read key and time from the header only.
- Website: next to the examples of the [.chs format](/en/format/) is the **sheet drawn** by Modern Sheet;
  code blocks have an icon to **copy** the text.

## 0.44.0 — 24 November 2026 {#v0.44.0}

[Release on GitHub]({{repo}}/releases/tag/v0.44.0) · apps for macOS, Windows, Linux and Android

Gathers versions 0.43 and 0.44.

**Editor**

- What you changed since the last save has a **green background** (brighter on the text you wrote), which
  goes away when you save.
- Step-by-step **Undo** and **Redo**, a word at a time: ↶ ↷ buttons at the top and
  ⌘Z / Ctrl+Z, ⌘⇧Z / Ctrl+Y.

**MusicXML**

- The tabs of the MusicXML files a song cites are now **read only**: the file is shown indented and
  coloured. The **Convert to notes in the song** button writes its bars into the `.chs` as notes
  (`{start_of_notes}`), in place of the reference, which stays as a comment; the file is not touched.
  Notes written in the song are much easier to edit.
- Accordingly removed: editing MusicXML, *Indent*, *Collapse/Expand* and *Create the MusicXML file*.
  Songs that cite a MusicXML file keep working as before.

**Website**

- This changelog page.

## 0.42.0 — 24 November 2026 {#v0.42.0}

[Release on GitHub]({{repo}}/releases/tag/v0.42.0) · apps for macOS, Windows, Linux and Android

Gathers versions 0.37 to 0.42.

**Notes written in the song**

- Bars with notes (intros, riffs, heads) can be written **right in the `.chs`**, in a
  `{start_of_notes}` … `{end_of_notes}` block, as an alternative to MusicXML: note names like chords
  (`G`, `Bb`, `F#`), durations as figures (`8`, `4.`), relative octave with `'` and `,` or absolute with `@N`,
  rests, ties, tuplets, stacked notes, chord symbols over the note, lyrics on a `w:` line.
  See [The .chs format](/en/format/).
- Automatic beams, accidentals recomputed against the key signature, transposition as for MusicXML.

**Guitar tablature**

- Notated bars can be shown as **staff**, **staff + tablature** or **tablature only** with the rhythm under
  the numbers: `{notation: staff | both | tab}` for the song or a section, and a switch over the sheet in the app.
- String and fret worked out for the whole passage, to stay in a comfortable hand position; capo.
- Manual corrections: `{tab_position: N}` (hand around fret N), `~N` after a note to choose its string,
  `{tuning}` (drop D, DADGAD, open G, half step down, 4- and 5-string bass, ukulele, or the strings' notes),
  string and fret read from MusicXML.

**Layout**

- `{bar_width: uniform | fit}` also **for a single section**, over the song's and the app's setting.
- *Fit* wraps only when the bars really do not fit, and rows closed for lack of room reach the margin.
- Adjustable **space between rows**, in the settings and per song with `{row_spacing}` (compact, normal,
  wide, extra or a percentage).

**App and website**

- In the MusicXML editor: indenting the file and collapsible lines.
- **Android app** (experimental APK) built and signed automatically along with the desktop apps.
- Download page with the version and date of each app, read from GitHub.

## 0.36.1 — 23 November 2026 {#v0.36.1}

[Release on GitHub]({{repo}}/releases/tag/v0.36.1) · apps for macOS, Windows and Linux

- Fixed the build of the Linux app, which had failed in 0.36.0.

## 0.36.0 — 23 November 2026 {#v0.36.0}

- **Desktop apps** for macOS, Windows and Linux built automatically on GitHub and downloadable from the
  Download page. This version produced no apps (the Linux build stopped): replaced by 0.36.1.

## 0.35.0 — 23 November 2026 {#v0.35.0}

First release: code on GitHub under the GPL-3.0 license, the modernsheet.app website in Italian and English,
automated tests. It includes all the work done until then:

- **Versioned `.chs` format**: sections, chords with durations, explicit or automatic bars, repeats and
  endings, time and key changes, segno, coda, D.C., D.S., Fine, text lines, rhythm marks (pushes, ties,
  slashes, fermata), optional chords and chord annotations.
- **Real Book style lead sheets**, identical in PDF and on screen: a grid of aligned bars, optional jazz
  symbols, section colours, transposition.
- **Notated parts from MusicXML**, with tuplets, repeats and lyrics.
- **App** for computers and tablets: song library as cards with search and sorting, editor with
  highlighting, suggestions and live preview, full-screen view mode, PDF export, Italian and English interface.
- **Library sync** with a folder or Google Drive, losing nothing on conflicts.
- **Import** from chordsheet.com, from text or straight from your own account.
