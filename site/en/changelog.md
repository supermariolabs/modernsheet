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

## 0.53.0 — 27 November 2026 {#v0.53.0}

[Release on GitHub]({{repo}}/releases/tag/v0.53.0) · apps for macOS, Windows, Linux and Android

Gathers versions 0.47 to 0.53, getting ready for 1.0 and the stores.

**.chs format, final for 1.0**

- `{comment}` and `{c}` are **printed**, as in ChordPro (like `{text}`); notes you don't want printed are
  written with `#`.
- `{bar_width}`, `{notation}` and `{bars_per_line}` written **between sections** hold from there on; inside a
  section, for that section only. Song directives (title, key…) after the first section give a warning.
- `:n` durations count notes of the time signature's **denominator**: quarters in 4/4, eighths in 6/8, halves in 2/2.
- An ending closes only with a sign (`:|`, the next ending, `{volta_end}`, the end of the section), never
  because a line of the file ends.
- Special characters are written as text with a **backslash**: `\|`, `\[spoken\]`, `{c: Chorus \{x2\}}`, `\#1`.
- Keywords in English, as in ChordPro (`{volta_end: hook}`; `chiusa` gives a warning).
- **Equivalent chord spellings** all look the same: `CMaj7` like `Cmaj7`, `F#-` like `F#m`, `Dø` like `Dm7b5`.
- The `.chs` extension is final.

**Sheet**

- **Do Re Mi**: chords and keys with Italian note names (a switch above the sheet and a default setting); the
  song is still written with letters.
- The handwritten theme is now called **Fake Book**.

**App**

- **Share**: on iPad, iPhone and Android the PDF or the source go to Mail, Files, AirDrop, WhatsApp…
- **.zip archives**: a song with its MusicXML files (*Song with MusicXML (.zip)*) and the **whole library**
  (*Settings › Export the library*), as a backup or to change device; *Import* also takes `.zip` files.
- On **iPad, iPhone and Android** the library lives inside the app (on iPad and iPhone visible in the **Files**
  app), syncs with Google Drive, and files come in and go out with Import and Share.
- Importing from chordsheet.com is no longer in the app: it is a separate tool, on GitHub.
- The **macOS** app is now signed and notarized by Apple: it opens without warnings.

**Website**

- Privacy policy completed, with the contact **privacy@modernsheet.app**.
- The website is for people who use the app; developer details are on GitHub.

## 0.46.1 — 25 November 2026 {#v0.46.1}

[Release on GitHub]({{repo}}/releases/tag/v0.46.1) · apps for macOS, Windows, Linux and Android

- Reference options are written with **`$`**: `{ref: Chorus $volta 2}`, `{ref: Verse $once}`,
  `{ref: Chorus x2 $short}`. Without `$` they are words of the section's name, so "First time 2" can be
  referenced by name; a reference written the old way gives a warning with the right line.
- A reference whose text is a section's name finds it even if the name holds `x2`, `=` or `|`.
- `:|` glued to a word (`I say:|`) is lyrics plus a bar line, no longer the end of a repeat.
- A line of text only, with no chords and no bar lines, now gives a warning instead of disappearing.

## 0.46.0 — 25 November 2026 {#v0.46.0}

[Release on GitHub]({{repo}}/releases/tag/v0.46.0) · apps for macOS, Windows, Linux and Android

- **References without repeats**: `{ref: Verse once}` plays the section once, dropping `|: :|` and the
  endings (the last one stays, or the one chosen with `volta N`).
- **Short references**: `{ref: Chorus x2 short}` prints just the section's box, without printing again the
  bars written further up; if the key has changed, the box says so.
- The words after the section's name (`x2`, `volta 2`, `once`, `short`) go in any order and combine with
  `= name` and `| note`. See [The .chs format](/en/format/#references).

## 0.45.1 — 25 November 2026 {#v0.45.1}

[Release on GitHub]({{repo}}/releases/tag/v0.45.1) · apps for macOS, Windows, Linux and Android

- Fixed: a reference to a section with its own `{key}` at the start (for example a chorus with `{key: A}`
  right after `{start_of_chorus}`) was transposed by the wrong interval: referenced in B it came out in D♭.
  It is now transposed from the key of its bars.
- Download: if the build for one platform fails, the others are published anyway and the
  [Download](/en/download/) page offers the previous version for that platform, saying so.

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
