# Esempio con zone notate: le battute dentro {musicxml: …} vengono lette da file MusicXML
# (note, accordi e testo) e scritte sul pentagramma; il resto del brano resta in sigle.
{format: v1}
{title: Blues del lunedì}
{subtitle: con intro e tema scritti}
{artist: Esempio .chs + MusicXML}
{tags: blues, jazz, musicxml}
{key: F}
{time: 4/4}
{tempo: 132}

{start_of_intro: Intro}
{musicxml: blues_intro_riff.musicxml}
{end_of_intro}

{start_of_verse: Strofa 1}
| [F7]Il lunedì mattina | [Bb7]no, | [F7]la sveglia | [Cm7]suona [F7]forte |
| [Bb7]esco di | [Bdim7]casa | [F7]con la testa | [Am7b5]ancora [D7b9]a letto |
| [Gm7]prendo il | [C7]tram | [F7:1.5]e mi [D7:2.5]metto | [Gm7]a can- [C7]tare |
{end_of_verse}

{start_of_chorus: Ritornello}
# tema scritto: melodia + accordi + testo dal file MusicXML
{musicxml: blues_tema.musicxml}
{end_of_chorus}

{start_of_verse: Strofa 2}
| [F7]la sera torno | [Bb7]stanco | [F7]ma con- | [Cm7]ten- [F7]to |
| [Bb7]suono il | [Bdim7]piano | [F7]e tutto | [Am7b5]si [D7b9]sistema |
| [Gm7]come | [C7]per | [F7]magia | [Gm7] [C7] |
{end_of_verse}

{ref: Ritornello | tutti insieme}

{start_of_solo: Shout chorus}
# MusicXML con terzine, ritornello e casse di volta 1. / 2.
{musicxml: blues_shout.musicxml}
{end_of_solo}

{start_of_bridge: Vamp}
# casse di volta scritte direttamente nel .chs
|: [Gm7] [C7] | [Am7] [D7] |
{volta: 1} [Gm7] [C7] | [F7] [D7] :|
{volta: 2} [Gm7] [C7] | [F7] ||
{end_of_bridge}

{start_of_outro: Coda}
# solo le ultime 2 battute del riff (misure 3-4), poi lo stop
{musicxml: blues_intro_riff.musicxml | 3-4}
| [F7#9:1] [/] |
{end_of_outro}
