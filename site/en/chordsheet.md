---
title: chordsheet.com
slug: chordsheet
nav: 4
other: chordsheet
description: How to import into Modern Sheet the chord sheets made on chordsheet.com (Chord Sheet Maker), from your account or a text file.
---

# Importing from chordsheet.com

If you use [Chord Sheet Maker](https://www.chordsheet.com), you can bring your songs into Modern Sheet: they are **converted** to the `.chs` format, with repeats, endings, signs, annotations and rhythm marks.

## From your account

1. In the library, open the folder where you want the songs and tap **Import from chordsheet.com**.
2. Enter the **email and password** of your chordsheet.com account. With *Remember the email* the app keeps the email for next time; the **password is never stored**, it is only used to log in.
3. A list of **all your songs** appears: pick the ones to import (there is a filter, *All new ones* and *None*). Songs already imported are marked.
4. **Import**: the songs are read one at a time and saved in the open folder, never overwriting anything.

Songs that need a check get the **`import_warn`** tag: find them with `#import_warn`. Each file starts with a reference to the original song and, if any, the conversion notes.

> chordsheet.com has no API: the import reads the same pages you see in the browser. If the site changes, Modern Sheet may need an update.

## From a text file

In the same window, **From a .txt file…** imports the text of the "Chords" field saved in a file. Lines like `Title:`, `Artist:`, `Key:`, `BPM:`, `Time:` can be added at the top. From the command line:

```
python modernsheet_cli.py --from-chordsheet --pdf song.txt
```

## What is converted

| chordsheet.com | Modern Sheet |
|---|---|
| `A B C D`, `Dm7_G7` | bars, several chords in a bar |
| `*_B_*_*` | B on the second beat |
| `( … )`, `\|: … :\|`, `x3` | repeats |
| `1.` `2.` `1.-3.+5.` | endings |
| `%`, `%%`, `%2` | repeated bars |
| `= Title`, `: Title` | sections |
| `- text`, `; text` | `{text}` lines |
| `$ o O fine D.C. … D.S. …` | navigation signs |
| `<C <<C C^ C,,, Cfermata C<>` | rhythm marks |
| `C?`, `[G_D+7]` | optional chords |
| `A"1°"`, `Dm7 "II"` | annotations |
| `r1 r2 r4 r8`, `N.C.`, `3:4` | rests, N.C., time changes |
| `X`, `P0`…`P9` | ignored (indents and colours) |

On a real archive of 234 songs, 230 were imported without notes; the others had errors in the original source or were written in another format.
