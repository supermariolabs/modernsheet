---
title: The .chs format
slug: format
nav: 4
other: formato
description: Complete reference of Modern Sheet's .chs format: header, sections and colours, chords and durations, bars, repeats, endings, signs, lyrics, notes written in the song, guitar tablature, MusicXML.
---

# The .chs format

A song is a UTF-8 text file with the `.chs` extension. It holds **directives** in braces (`{title: …}`), **chords** in square brackets (`[Am7]`), **bar lines** (`|`) and the **lyrics**. Next to the examples is the sheet Modern Sheet draws for that code.

[TOC]

## General rules

- Lines starting with `#` are **comments**; blank lines do not count.
- A directive is `{name}` or `{name: value}`: on a line of its own or **inside** a line of music. Directive names ignore case, chord names do not.
- Music goes **inside a section** (`{start_of_…}` … `{end_of_…}`); outside one, the app opens an untitled section and says so.
- A file never "breaks": what cannot be understood becomes a **warning** with its line number, shown under the editor, and the rest is drawn anyway (see [Diagnostics](#diagnostics)).

## An example

```{ .chs .render }
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

The directives at the top of the file describe the song. Those that drive the layout (`bar_width`, `notation`, `bars_per_line`) apply to the whole song, but written **inside a section** they apply to that section only.

| Directive | Example | Notes |
|---|---|---|
| `format` | `{format: v1}` | Format version, as the first directive. Without it: v1. |
| `title`, `subtitle` | `{title: Amazing Grace}` | Title (top left) and subtitle. |
| `artist`, `composer` | `{artist: Traditional}` | Shown under the title. |
| `key` | `{key: F#m}` | Key: `C D E F G A B`, with `#` or `b`, and `m` for minor (`Bb`, `Ebm`). Before the music it is the song's key (none: C); after the first bars it is a **key change**. |
| `time` | `{time: 3/4}` | Time signature. Before the music it is the song's (none: 4/4); after the first bars it is a **time change**. |
| `tempo` | `{tempo: 96}` | BPM, shown as ♩ = 96. |
| `capo` | `{capo: 2}` | Capo: shown in the header; in the [tablature](#guitar-tablature) frets count from the capo. |
| `tags` | `{tags: jazz, ballad}` | Labels for the library (search with `#jazz`); several lines add up. Not printed. |
| `bar_width` | `{bar_width: fit}` | `uniform` (equal bars, the app's *Grid*) or `fit`. See [Layout](#layout). |
| `bars_per_line` | `{bars_per_line: 6}` | Bars per row. See [Layout](#layout). |
| `row_spacing` | `{row_spacing: wide}` | Space between rows: `compact`, `normal`, `wide`, `extra` or a percentage between 50% and 300% (`120%`). |
| `label_colors`, `section_colors` | `{label_colors: by_type}` | Colours of the section boxes. See [Section colours](#section-colours). |
| `notation`, `tuning`, `tab_position` | `{notation: both}` | Staff and/or tablature for bars with notes. See [Tablature](#guitar-tablature). |
| `created`, `modified` | | Creation and last-save dates: written by the app, no need to touch them. |
| `comment` (or `c`) | `{comment: …}` | Comment, not printed. |

## Sections

```
{start_of_verse: Verse 1}
| [C] | [F] |
{end_of_verse}
```

- The kind after `start_of_` is **free** (`verse`, `chorus`, `bridge`, `intro`, `solo`, `outro`, `coda`…, Italian names too: `strofa`, `ritornello`, `inciso`…); it matters for the [colours by kind](#section-colours).
- The label after the colon is what the box shows; without a label, the kind (`Verse`).
- Every section starts on a new row; sections do not nest (opening one before closing the previous one gives a warning).

### References

| Write | Meaning |
|---|---|
| `{ref: Verse}` | repeats here a section **written further up** |
| `{ref: Chorus x2}` | repeats it twice (in the box: `x2`) |
| `{ref: chorus \| all together}` | with a note next to the box ("reprise – all together") |

The section is looked up by label first (ignoring case), then by kind. The reference keeps the section's repeats, endings, time changes and colour; navigation signs and `{text}` lines stay with the original only. If the key has changed in the meantime, the reference is **transposed automatically** into the new key.

## Section colours

Each section name sits in a **coloured box**, to see the form of the song at a glance on the music stand. The colour is chosen like this:

| Directive | Effect |
|---|---|
| `{label_colors: theme}` | Modern Sheet's blue for every box (default) |
| `{label_colors: #8B1E3F}` | one colour of your choice for every box |
| `{label_colors: by_type}` | one colour per kind of section (table below) |
| `{section_colors: intro=#3366ff, chorus=#ff9900}` | colours of your choice for single sections; the others follow `label_colors` |

With `by_type`:

| Kinds of section | Colour |
|---|---|
| `verse`, `strofa` | midnight blue |
| `chorus`, `ritornello`, `refrain` | burgundy |
| `bridge`, `inciso`, `prechorus` | teal |
| `instrumental`, `solo`, `assolo`, `interlude`, `interludio` | ochre |
| `intro`, `outro`, `coda`, `ending`, `finale` and the others | anthracite |

In `section_colors` a key can be a section's **label** (`Chorus`), its **kind** (`chorus`) or one of the table's groups (`verse`, `chorus`, `bridge`, `instrumental`, `frame`); the first that matches wins, in that order. Colours are written as `#RRGGBB`; a wrong one is ignored. The box text is white, or near black on light colours, to stay readable. If the song has no `label_colors`, the app's *Colours by section* switch is the same as `by_type`.

```{ .chs .render }
{label_colors: by_type}
{section_colors: Sax solo=#ff9900}

{start_of_verse: Verse}
| [C] | [Am] | [F] | [G7] |
{end_of_verse}

{start_of_chorus: Chorus}
| [F] | [G] | [C] | [C] |
{end_of_chorus}

{start_of_solo: Sax solo}
| [Dm7] | [G7] | [C] | [C] |
{end_of_solo}
```

## Chords and durations

- `[Am7]` a chord: root (`A`–`G` with `#` or `b`), free quality (`m`, `maj7`, `m7b5`, `7#9`, `sus4`, `dim7`, `6/9`…) and an optional bass after `/` (`[C/E]`). On the sheet `b` and `#` become ♭ and ♯.
- `[C:2]` lasts 2 **beats** (quarter notes); the shortest is half a beat (`[G:1.5]`, `[D:0.5]`).
- In a bar, chords without a duration share the remaining time equally, rounded to half beats; the last one takes the rest. In 4/4: `| [C] [G] |` = 2 + 2; `| [C] [G] [D] |` = 1.5 + 1.5 + 1; `| [C:3] [G] [D] |` = 3 + 0.5 + 0.5.
- `[/]` is a **stop** (silence until the next chord; also with a duration: `[/:2]`); `[%]` says explicitly "no new chord".
- A bar **without chords** (`| |` or lyrics only) carries the previous chord on and shows as **%**.
- The **lyrics** after a chord are sung on that chord; lyrics before the first chord of a bar go with that first chord.

### Bars

- **With bar lines**: `| [C] [G] | [Am] |`. Empty bars count (`| [G] | |` is two bars). If written durations exceed the bar there is a warning; if they are all written and do not fill it, the last chord is lengthened.
- **Without bar lines**: `[Gm7:2] [C7:2] [Am7:2] [D7:2] [F]` – each chord lasts its duration, or a whole bar without one; bars fill in order, and a chord crossing the bar line carries on into the next bar (**%**).

### Marks inside the chord

| Write | Meaning |
|---|---|
| `[(C)]` or `[C?]` | **optional** chord, in parentheses |
| `[<C]` / `[<<C]` | **push**, an eighth / a sixteenth early |
| `[C~]` | **tie** to the next chord (also onto the next row) |
| `[C,,,]` | **rhythm slashes**, one per comma, spread over the duration |
| `[C fermata]` | **fermata** |
| `[C diamond]` or `[C <>]` | **diamond**: held chord, let ring |
| `[A "1st"]` | **annotation** above the chord; `[% "repeat"]` on a repeated bar |

They combine with each other and with the duration, in this order: push, name (optionally in parentheses), `:duration`, `~` and commas, then the words: `[<(G7):2~ fermata]`. They are notation only: they do not move the chord in time.

```{ .chs .render }
| [C,,,] | [<F~] [F] | [(G7)] [A "1st"] | [C diamond] [/] |
| [Dm7:3] [G7:1 fermata] | [C] | [% "repeat"] | [C] |
```

## Bar lines, repeats and endings

| Write | Meaning |
|---|---|
| `\|\|` | double bar line |
| `\|: … :\|` | repeat (twice, nothing written) |
| `:\| x3` | played 3 times (`x3` above the end) |
| `{volta: 1}` … `{volta: 2}` | endings (also `{volta: 1, 2}`) |
| `{volta_end}` / `{volta_end: hook}` | end of the ending, open or with a hook |

```{ .chs .render }
|: [Gm7] [C7] | [Am7] [D7] |
{volta: 1} [Gm7] [C7] | [F7] [D7] :|
{volta: 2} [Gm7] [C7] | [F7] ||
```

An ending closes by itself at the `:|` (with the hook), when the next ending opens, with `{volta_end}` or **at the end of the file's line**. The 2nd ending starts a new row, right-aligned under the 1st, and the last ending gets the double bar line.

## Key and time changes

`{key: …}` and `{time: …}` go on a line of their own or right after a bar line, and apply from the next bar:

```{ .chs .render bar_width=fit }
| [G7]last time round || {key: Db} [Db]modulation | [Gb] |
| [Gm7] | {time: 2/4} [C7] | {time: 4/4} [F7] |
```

A key change brings a double bar line, the new key signature (with courtesy naturals) and, under the staff, the name of the new key; a time change, the new time signature. After the first bars they are always changes, even if the song has no key or time in its header.

## Layout

Line breaks in the file **do not** decide the rows of the sheet: bars per row do.

| Write | Effect |
|---|---|
| `{bars_per_line: 6}` inside a section | 6 bars per row in that section |
| `{bars_per_line: 6}` outside sections | 6 bars per row from there on |
| `{bars_per_line}` (no value) | back to the settings' value (4) |
| `{br}` in a row of bars | the bar it is in starts a new row |
| `{bar_width: uniform}` | **Grid**: all bars equally wide and aligned in columns, even across sections; a crowded bar takes two places instead of shrinking the chords |
| `{bar_width: fit}` | **Fit**: each bar as wide as it needs (in proportion to its beats); a row wraps only when the bars do not fit |
| `{row_spacing: wide}` | more space between rows (`compact`, `normal`, `wide`, `extra`, or `50%`–`300%`) |

`bar_width` and `bars_per_line` in the header apply to the song, inside a section to that section only; in the app, the settings and the bar above the sheet give the default.

## Navigation signs

| Directive | Where it goes | Shown as |
|---|---|---|
| `{segno}` | start of the next bar | 𝄋 |
| `{coda}` | start of the next bar | ⊕ |
| `{to_coda}` | end of the bar it is written in | To Coda ⊕ |
| `{fine}` | end of the bar | Fine, with a double bar line |
| `{dc: al Fine}` | end of the bar | D.C. al Fine |
| `{ds: al Coda}` | end of the bar | D.S. al Coda |

```{ .chs .render }
{segno}
| [Am7] | [D7] {to_coda} | [G] | [G7] |
| [C] | [D7] {ds: al Coda} ||
```

On a line of their own, `{to_coda}`, `{fine}`, `{dc}` and `{ds}` go at the end of the last bar written.

## Text lines

`{text: First time guitar only}` on a line of its own, inside a section, prints a line of text in the sheet at that point: before the music, between two rows (the next row starts on a new line) or at the end of the section.

```{ .chs .render }
{start_of_verse: Verse}
{text: First time guitar only}
| [Em] | [C] | [G] | [D] |
{text: Second time everybody}
| [Em] | [C] | [D] | [D] |
{end_of_verse}
```

## Notes written in the .chs

Parts with notes (intros, riffs, heads) are written **right in the song**, in a block inside a section:

```{ .chs .render bar_width=fit }
{start_of_intro: Intro}
{start_of_notes}
| [Gm7] G8 Bb D F [C7] A G E C | [Am7] C E G B [D7] F# E D16 C Bb A |
| [Gm7] G4. Bb8 [C7] E Db C Bb | [F7] A2- A4 R |
{end_of_notes}
{end_of_intro}
```

| Write | Meaning |
|---|---|
| `G` `Bb` `F#` `C##` `Ebb` | notes, as in chords (lower case too); **the accidental is always written**, even when it is in the key signature (in F, B flat is `Bb`); `Bn` = intended natural |
| `1` `2` `4` `8` `16` `32` | the note value: whole, half, quarter, eighth, sixteenth, thirty-second; `.` or `..` for dots. **It stays until it changes**: `G8 Bb D F` are four eighths (at the start of the block: `4`) |
| octave | each note goes to the one nearest the previous note (within a fourth); `'` raises it an octave, `,` lowers it (`''` two). The block's first note goes near the staff's middle B |
| `C@5` | fixed octave: middle C = `C4`; the following notes are relative again from there. After `@N` the duration goes after a slash: `C@5/2` |
| `R4` `R8.` `R*` | rest; `R*` = whole-bar rest, in any time signature |
| `F2- F4` | tie (also into the next bar and across a line break) |
| `3(F8 E D)` | triplet; in general `N:M( … )` = N notes in the time of M (`5:4(C16 D E F G)`) |
| `<C E G>2` | several notes on one stem, the duration after `>` |
| `A4~3` | for the tablature only: the note on the 3rd string (1 = the highest); in `< >` after each note |
| `[Gm7]` | the chord, right before the note it falls on (no duration). To change chord over a held note: `G2- [C7] G2` |

Order inside a note: name, accidental, octave, duration, dot, tie, string (`F#'8.-~2`). Notes are separated by spaces.

- The block's rows start with a bar line and accept everything ordinary bars do: `||`, `|: … :|`, `:| x3`, `{volta: 1}`, navigation signs; `{key}` and `{time}` on a line of their own change key and time. A bar with chords only is an ordinary bar.
- **Lyrics**: a `w:` line under the row of notes, one syllable per note (`w: Blues, blues on Mon- day`). A syllable ending with `-` continues into the next; rests and tied notes are skipped by themselves; `_` skips a note (the previous syllable is held); `|` jumps to the next bar.
- Beams are automatic (per beat; in 4/4 four eighths in the same half bar share one beam). Accidentals on the sheet are recomputed against the key signature: `Bb` in F draws no flat.
- Useful warnings when copying from a score: a bar longer or shorter than the time signature, a note without an accidental that the key signature would alter (in F: `B` instead of `Bb`), a tie between different notes, an unclosed tuplet, extra syllables.

In the app a `{musicxml: …}` reference can be turned into notes written like this with one button (see [Notes from MusicXML](#notes-from-musicxml)).

## Guitar tablature

Bars with notes (written in the `.chs` or from MusicXML) can be shown in three ways, with the `notation` directive:

| Write | Result |
|---|---|
| `{notation: staff}` | staff only (default) |
| `{notation: both}` | the staff and, under it, the **tablature**: the fret number on its string, in the same column as the note |
| `{notation: tab}` | tablature only, instead of the staff, with the **rhythm** drawn under the numbers (stems, beams, dots, rests) |

In the header it applies to the song, inside a section to that section only; the app also has a switch above the sheet (*Staff / Both / Tablature*), which wins over everything. The rhythm is never written separately: it comes from the notes.

```{ .chs .render bar_width=fit }
{key: G}
{notation: both}
{start_of_intro: Riff}
{start_of_notes}
| [G] G@3/8 B D G [D] F# D A4 | [Em] E@3/8 G B E [C] E G C4 |
{end_of_notes}
{end_of_intro}
```

```{ .chs .render bar_width=fit }
{key: G}
{start_of_outro: Ending}
{notation: tab}
{start_of_notes}
| [C] C@4/8 E G E [D] D F# A F# | [G] <G@3 B D G>1 ||
{end_of_notes}
{end_of_outro}
```

- **String and fret** are chosen by the app, for the whole passage at once: it stays in a comfortable hand position, prefers open strings and low frets, avoids jumps; notes on one stem go on different strings within reach. A tied note repeats its fret in parentheses: `(3)`.
- **Octave**: notes are read as written for guitar, which sounds an octave below the written note: the open strings are written E3 A3 D4 G4 B4 E5 (the low E is `E@3`). A note out of range moves by octaves, with a warning.
- **Capo**: with `{capo: 2}` frets count from the capo (0 = the capo).
- **Manual corrections**, where the automatic choice is not the one you want:
  - `{tab_position: 5}` keeps the hand around the 5th fret (4th to 9th) for the notes that follow, until the end of the section or the next `{tab_position}`; `{tab_position: auto}` goes back to the automatic choice;
  - `~N` after a note puts it on string N (`A4~3`; 1 = the highest); if the note does not fit on that string, a warning and the automatic choice.
- **Tunings** with `{tuning: …}`: `standard`, `drop D`, `double drop D`, `DADGAD`, `open G`, `open D`, `open E`, `half step down`, `bass` (4 strings), `bass 5`, `ukulele`; or the open strings from the lowest, `{tuning: D A D G B E}` (also `DADGBE`). The tablature has as many lines as strings and, with a tuning other than standard, shows the string names at the start of the row instead of "TAB".
- From **MusicXML** guitar parts (exported by MuseScore, for example) the string and fret written in the file are used.

## Notes from MusicXML

Instead of notes written in the song, a part prepared in a notation editor (MuseScore, Dorico, Sibelius…) and exported as **MusicXML** is referenced like this:

```
{start_of_intro: Intro}
{musicxml: intro.musicxml}
{end_of_intro}
```

- `{musicxml: head.musicxml | 3-6}` uses measures 3 to 6 only (`| 5`: only 5). The path is relative to the song's folder; `.musicxml`, `.xml` and `.mxl` (compressed) are all fine.
- The **first part**, voice 1, is read: notes, rests, chords, dots, ties, beams, triplets and tuplets, repeats, endings, chord symbols (turned into `.chs` chords) and lyrics. Other parts and voices, grace notes, dynamics, articulations and clefs other than treble are ignored.
- Each measure becomes a bar of the song, transposed and laid out like the others. A different time signature in the file becomes a time change; the key stays the song's (a different key signature gives a warning).
- In the app the MusicXML files a song cites are shown in a tab next to it, read only. The **Convert to notes in the song** button turns them into a `{start_of_notes}` block, much easier to edit, and keeps the reference as a comment.

## Diagnostics

The app never stops on an error: it shows the sheet with what it can read and, under the editor, the **warnings** with their line number (tapping one jumps to the line). What is reported:

- a bar longer than its time signature; an invalid duration, or one that is not a multiple of half a beat;
- an unrecognised chord; an unknown directive, or one with an invalid value (key, time, tuning, `bar_width`, `notation`, `row_spacing`…);
- a section not closed, `end_of_` without `start_of_`, music outside a section, an incomplete bar without bar lines;
- a `{ref}` to a section that does not exist or comes later;
- in written notes and MusicXML: the cases listed in their sections.

## Format versions

`{format: v1}` declares the version. Additions land in the current version without changing the meaning of existing files; should the syntax ever change incompatibly, the app will still read v1 files and offer to upgrade them.

---

For every detail (layout rules, special cases) see the [full specification]({{repo}}/blob/main/SPEC.md) in the repository (in Italian).
