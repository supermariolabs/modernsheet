---
title: Modern Sheet
slug:
nav: 1
other:
description: Write chords in a plain text file, get a Fake Book style lead sheet. Library, editor with live preview, PDF, Google Drive sync.
---

<div class="hero" markdown="1">
<div markdown="1">

# Fake Book style lead sheets, from a text file

<p class="lead">Write the chords in a simple format (<code>.chs</code>) and Modern Sheet lays them out like a Fake Book: staff, chord symbols, repeats, signs, lyrics. On screen and as PDF.</p>

<div class="cta">
<a class="btn primary" href="/en/download/">Download</a>
<a class="btn" href="/en/guide/">Guide</a>
<a class="btn" href="/en/format/">The .chs format</a>
<a class="btn" href="{{repo}}">GitHub</a>
</div>
<span class="tag">Free software (GPL-3.0) · macOS, Windows, Linux · iPad and Android in testing</span>

</div>
<img src="/assets/img/sheet-demo.png" alt="A song laid out by Modern Sheet in Fake Book style">
</div>

## What it does

<div class="grid" markdown="1">
<div class="card" markdown="1"><span class="ico">✍️</span>
### A readable text format
Chords in square brackets, bar lines, sections, lyrics. Write it with any editor; it reads well even without the app.
</div>
<div class="card" markdown="1"><span class="ico">🎼</span>
### Fake Book look
Handwritten Petaluma font, chord extensions in superscript, coloured section boxes, a uniform bar grid. Or the *Clean* theme.
</div>
<div class="card" markdown="1"><span class="ico">🔁</span>
### Repeats, endings and signs
Repeats with `x3`, 1st/2nd/3rd endings, Segno, Coda, D.C./D.S. al Fine, references to earlier sections with automatic transposition.
</div>
<div class="card" markdown="1"><span class="ico">🎵</span>
### Real notes where needed
Intros, riffs and heads written right in the song (`G8 Bb D F`) or imported from MusicXML, on the same page as the chord symbols. For guitar players also as **tablature**, worked out by the app.
</div>
<div class="card" markdown="1"><span class="ico">↕️</span>
### Transposition and jazz symbols
One click to transpose (key signatures included); standard or jazz chord symbols (Δ, –, ø, °), with letters or Italian names (Do, Re, Mi); rhythm marks, optional chords, annotations.
</div>
<div class="card" markdown="1"><span class="ico">🗂️</span>
### Song library
Cards with title, artist, key, time and tags, A–Z groups, sorting, search with `A*`, `*text*`, `&` and `|`, folders.
</div>
<div class="card" markdown="1"><span class="ico">🖥️</span>
### Editor with live preview
Syntax highlighting, directive suggestions, tabs for MusicXML files, a preview that follows your typing, full screen for the stage.
</div>
<div class="card" markdown="1"><span class="ico">☁️</span>
### Always with you, even offline
The library is local and syncs with Google Drive or a folder (iCloud, Dropbox…). No song gets lost: conflicts and deletions go through the trash.
</div>
<div class="card" markdown="1"><span class="ico">📤</span>
### Share and export
PDFs to print or send, songs with their MusicXML files in a `.zip`, a backup of the whole library in one file.
</div>
</div>

<div class="band two" markdown="1">
<div markdown="1">

### This is how you write…

```
{title: Blues del lunedì}
{subtitle: con intro e tema scritti}
{key: F}
{time: 4/4}
{tempo: 132}

{start_of_intro: Intro}
{musicxml: blues_intro_riff.musicxml}
{end_of_intro}

{start_of_verse: Strofa 1}
| [F7]Il lunedì mattina | [Bb7]no, | [F7]la sveglia | [Cm7]suona [F7]forte |
{end_of_verse}
```

</div>
<div markdown="1">

### …and this is how it reads

<img class="shot" src="/assets/img/sheet-blues-con-melodia.png" alt="The blues laid out, with the intro in notation from MusicXML">

</div>
</div>

## The app

<figure markdown="1">
<img class="shot" src="/assets/img/app-editor.jpg" alt="The Modern Sheet editor: source on the left, preview on the right">
<figcaption>The editor: highlighted source on the left, the sheet updated live on the right.</figcaption>
</figure>

<figure markdown="1">
<img class="shot" src="/assets/img/app-library.jpg" alt="The Modern Sheet library with song cards grouped by letter">
<figcaption>The library: song cards grouped by letter, search and sorting.</figcaption>
</figure>

<p class="tag">The screenshots show the Italian interface; the app is also available in English.</p>

## Project status

Modern Sheet is under active development. The apps for **macOS, Windows and Linux** can be [downloaded here](/en/download/) (not signed yet: the page explains how to open them); iPad and Android are in testing.

The code is on [GitHub]({{repo}}) under the **GPL-3.0** license. Reports and ideas are welcome in the *Issues*.
