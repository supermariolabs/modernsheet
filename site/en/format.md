---
title: The .chs format
slug: format
nav: 3
other: formato
description: Complete reference of the Modern Sheet .chs format: header, sections, chords and durations, bars, repeats, endings, signs, text, MusicXML.
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
| `bar_width` | `{bar_width: fit}` | `uniform` (equal bars) or `fit` for this song. |
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

## Format versions

`{format: v1}` declares the version. Additions arrive in the current version without changing the meaning of existing files; should the syntax ever change incompatibly, the app will still read v1 files and offer to upgrade them.

---

All the details (layout rules, special cases) are in the [full specification]({{repo}}/blob/main/SPEC.md) in the repository (in Italian).
