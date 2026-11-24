---
title: The .chs format
slug: format
nav: 4
other: formato
description: Complete reference of the Modern Sheet .chs format: header, sections, chords and durations, bars, repeats, endings, signs, text, notes written in the song, MusicXML.
---

# The .chs format

A song is a UTF-8 text file with the `.chs` extension. It holds **directives** in braces (`{title: …}`), **chords** in square brackets (`[Am7]`), **bar lines** (`|`) and the **lyrics**. Lines starting with `#` are comments.

[TOC]

## An example

```
{format: v1}
{title: My song}
{artist: Me}
{key: G}
{time: 4/4}
{tempo: 96}

{start_of_verse: Verse}
| [G]First line | [Em7]of the lyrics | [C]and the [D7]chords | [G] |
{end_of_verse}

{start_of_chorus: Chorus}
|: [C] | [D] | [Bm7] | [Em7] :|
{end_of_chorus}

{ref: Verse}
```

## Header

| Directive | Example | Notes |
|---|---|---|
| `format` | `{format: v1}` | Format version, as the first directive. Missing means v1. |
| `title`, `subtitle` | `{title: Amazing Grace}` | Title and subtitle. |
| `artist`, `composer` | `{artist: Traditional}` | Shown under the title. |
| `key` | `{key: F#m}` | The first is the song's key; later ones are **key changes**. |
| `time` | `{time: 3/4}` | The first is the song's time; later ones are **time changes**. |
| `tempo` | `{tempo: 96}` | BPM, shown as ♩ = 96. |
| `capo` | `{capo: 2}` | Capo. |
| `tags` | `{tags: jazz, ballad}` | Labels for the library (search with `#jazz`). |
| `bar_width` | `{bar_width: fit}` | `uniform` (equal bars, the app's *Grid*) or `fit` (*Fill*) for this song; inside a section, for that section only. |
| `tuning` | `{tuning: drop D}` | Tuning for the tablature: `standard`, `drop D`, `DADGAD`, `open G`, `open D`, `open E`, `half step down`, `bass`, `ukulele`… or the open strings (`D A D G B E`). |
| `tab_position` | `{tab_position: 5}` | In the tablature, the hand around the 5th fret for the notes that follow (`auto` goes back to the automatic choice). |
| `notation` | `{notation: both}` | Notated bars: `staff`, `both` (staff with guitar tablature) or `tab` (tablature only, with the rhythm); also inside a section. |
| `row_spacing` | `{row_spacing: wide}` | Space between rows for this song: `compact`, `normal`, `wide`, `extra` or a percentage (`120%`, between 50% and 300%). |
| `bars_per_line` | `{bars_per_line: 6}` | Bars per line (also inside a section). |
| `label_colors`, `section_colors` | `{section_colors: verse=#33cc66}` | Colours of the section boxes. |
| `created`, `modified` | | Dates written by the app when saving. |
| `comment` | `{comment: …}` | A comment, not printed. |

## Sections

```
{start_of_verse: Verse 1}
…
{end_of_verse}
```

The kind (`verse`, `chorus`, `bridge`, `intro`, `solo`, `outro`, `coda`…) is free; the label after the colon is what is shown. Every section starts on a new line.

**References**: `{ref: Verse}` repeats a section written earlier, `{ref: Chorus x2 | louder}` repeats it twice with a note. If the key changed in the meantime, the reference is **transposed automatically**.

## Chords and durations

- `[Am7]` a chord; `[C/E]` with a bass note; the quality is free (`m7b5`, `7#9`, `sus4`, `6/9`…).
- `[C:2]` lasts 2 beats (quarter notes); half a beat at least (`[G:1.5]`).
- In a bar, chords without a duration share the remaining time equally.
- `[/]` is a **stop**; `[%]` means "no new chord".
- A bar without chords continues the previous one and is shown as **%**.
- The text after a chord is what is sung on it.

### Bars

- **With bar lines**: `| [C] [G] | [Am] |` – bars are delimited by `|`.
- **Without bar lines**: `[Gm7:2] [C7:2] [F]` – each chord lasts its duration, or a whole bar.

### Marks inside the chord

| Write | Meaning |
|---|---|
| `[(C)]` or `[C?]` | **optional** chord, in parentheses |
| `[<C]` / `[<<C]` | **push**: an eighth / a sixteenth early |
| `[C~]` | **tie** to the next chord |
| `[C,,,]` | **rhythm slashes**, one per comma |
| `[C fermata]` | **fermata** |
| `[C diamond]` or `[C <>]` | **diamond**: held chord |
| `[A "1st"]` | **annotation** over the chord; `[% "again"]` on a repeated bar |

They combine with each other and with the duration: `[<(G7):2~ fermata]`.

## Bar lines, repeats and endings

| Write | Meaning |
|---|---|
| `\|\|` | double bar line |
| `\|: … :\|` | repeat (twice) |
| `:\| x3` | repeat played 3 times |
| `{volta: 1}` … `{volta: 2}` | endings (also `{volta: 1, 2}`) |
| `{volta_end}` / `{volta_end: hook}` | close the ending, open or with a hook |
| `{br}` | forced line break |

```
|: [Gm7] [C7] | [Am7] [D7] |
{volta: 1} [Gm7] [C7] | [F7] [D7] :|
{volta: 2} [Gm7] [C7] | [F7] ||
```

The 2nd ending starts a new line, right-aligned under the 1st.

## Key and time changes

`{key: …}` and `{time: …}` go on a line of their own or right after a bar line:

```
| [G7]last time round || {key: Db} [Db]modulation | [Gb] |
| [Gm7] | {time: 2/4} [C7] | {time: 4/4} [F7] |
```

A key change brings a double bar line, the new key signature (with courtesy naturals) and, under the staff, the name of the new key.

## Navigation signs

| Directive | Where | Shown as |
|---|---|---|
| `{segno}` | start of the next bar | 𝄋 |
| `{coda}` | start of the next bar | ⊕ |
| `{to_coda}` | end of the bar it is written in | To Coda ⊕ |
| `{fine}` | end of the bar | Fine, with a double bar line |
| `{dc: al Fine}` | end of the bar | D.C. al Fine |
| `{ds: al Coda}` | end of the bar | D.S. al Coda |

```
{segno}
| [Am7] | [D7] {to_coda} | [G] | [G7] |
| [C] | [D7] {ds: al Coda} ||
```

## Text lines

`{text: First time guitar only}` on a line of its own, inside a section, prints a line of text in the sheet at that point: before the music, between two lines or at the end of the section.

## Notes from MusicXML

Written parts (intros, riffs, heads) are prepared in a notation editor (MuseScore, Dorico, Sibelius…), exported as **MusicXML** and referenced:

```
{start_of_intro: Intro}
{musicxml: intro.musicxml}
{end_of_intro}
```

`{musicxml: head.musicxml | 3-6}` uses bars 3 to 6 only. The path is relative to the song's folder. Notes, chords and lyrics from the file are drawn on the staff, transposed along with the rest.

In the app, cited MusicXML files are shown in a tab next to the song, read only; to change them, convert them into notes written in the `.chs` (below) with the **Convert to notes in the song** button.

## Notes written in the .chs

Instead of MusicXML, a few bars of notes can be written **right in the song**, inside a section:

```
{start_of_intro: Intro}
{start_of_notes}
| [Gm7] G8 Bb D F [C7] A G E C | [Am7] C E G B [D7] F# E D16 C Bb A |
| [Gm7] G4. Bb8 [C7] E Db C Bb | [F7] A2- A4 R |
{end_of_notes}
{end_of_intro}
```

| Write | Means |
|---|---|
| `G` `Bb` `F#` | the notes, as in chords; **the accidental is always written**, also when it is in the key signature (in F the B flat is `Bb`); `Bn` = a natural you mean |
| `8` `4` `2` `1` `16`, `4.` | the note value: eighth, quarter, half, whole, sixteenth; the dot. **It stays until it changes**: `G8 Bb D F` are four eighths |
| octave | each note goes to the nearest one from the previous note; `'` raises it, `,` lowers it; `C@5` sets the octave (middle C = `C4`; duration after a slash: `C@5/2`) |
| `R4` `R*` | rest; whole-bar rest |
| `F2- F4` | tie |
| `3(F8 E D)` | triplet (in general `5:4( … )`) |
| `<C E G>2` | several notes on one stem |
| `A4~3` | for the tablature: the note on the 3rd string (1 = the highest) |
| `[Gm7]` | the chord, right before the note it falls on |

Lyrics go on a `w:` line under the row of notes, one syllable per note (`lu- ne- dì`; `_` skips a note, `|` moves to the next bar). Beams are added automatically. The result is the same as with MusicXML: it transposes, lays out and prints the same way; the `note_nel_chs` example is the blues with melody written like this.

## Format versions

`{format: v1}` declares the version. Additions arrive in the current version without changing the meaning of existing files; should the syntax ever change incompatibly, the app will still read v1 files and offer to upgrade them.

---

All the details (layout rules, special cases) are in the [full specification]({{repo}}/blob/main/SPEC.md) in the repository (in Italian).
