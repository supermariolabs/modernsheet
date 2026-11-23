# Importato da Chord Sheet Maker (chordsheet.com)
{format: v1}
{title: Esempio da Chord Sheet Maker}
{artist: Brano di prova}
{key: G}
{tempo: 96}
{time: 4/4}
# testo copiato dal campo "Chords" di chordsheet.com
#
# Note di conversione:
#  - D.C./D.S./Coda/Fine/Segno non esistono ancora nel formato .chs: riportati come commenti.
#  - '*' (accordo da decidere) → battuta vuota.
#  - Segni ritmici non supportati, rimossi: anticipi (<) ×1.
#  - Segni ritmici non supportati, rimossi: colpi (,) ×1.
#  - Segni ritmici non supportati, rimossi: legature (^) ×1.

{start_of_intro: Intro}
|: [G] | [D/F#] | [Em7] | [Cmaj7] :| x3
{end_of_intro}

{start_of_verse: Verse}
# Segno
| [G] | | [Am7] [D7] | [G] |
{br} | [Em7] | | [C] [D] | |
# secondo giro più piano
{br} |: [G] | [Bm7] | [C] | [D] :|
{end_of_verse}

{start_of_chorus: Chorus}
# To Coda
|: [C] | [D] | [Bm7] | [Em7] | {volta: 1} [Am7] | [D7] :| {volta: 2} [Am7] [D7] | [G] || {volta_end}
{end_of_chorus}

{start_of_bridge: Bridge}
| {time: 3/4} [Em7] | [Bm7] | [C] | [Bm7] | [C] |
# D.S. al coda
{br} | {time: 4/4} [Am7] [D] | [G] | [/:2] [D] ||
{end_of_bridge}

{start_of_coda: Coda}
# Coda · Fine
| [C] | [Cm6] | [G] |
{end_of_coda}
