# Esempio con le note scritte nel .chs (SPEC §2.12b): lo stesso brano di blues_con_melodia.chs,
# con le zone notate dentro {start_of_notes} … {end_of_notes} invece che in file MusicXML.
# Note come gli accordi (G, Bb, F#), durate come figure (8 = croma, 4. = semiminima puntata),
# ottava relativa alla nota precedente (' e , per spostarla, @5 per fissarla), R = pausa, - = legatura,
# 3( … ) = terzina; il testo cantato sulla riga w: sotto, una sillaba per nota.
{format: v1}
{title: Blues del lunedì}
{subtitle: con le note scritte nel .chs}
{artist: Esempio .chs, note nel sorgente}
{tags: blues, jazz, note}
{key: F}
{time: 4/4}
{tempo: 132}

{start_of_intro: Intro}
{start_of_notes}
| [Gm7] G8 Bb D F [C7] A G E C | [Am7] A C E G [D7] F# E D16 C Bb A | [Gm7] G4. Bb8 [C7] E Db C Bb | [F7] A2- A4 R |
{end_of_notes}
{end_of_intro}

{start_of_verse: Strofa 1}
| [F7]Il lunedì mattina | [Bb7]no, | [F7]la sveglia | [Cm7]suona [F7]forte |
| [Bb7]esco di | [Bdim7]casa | [F7]con la testa | [Am7b5]ancora [D7b9]a letto |
| [Gm7]prendo il | [C7]tram | [F7:1.5]e mi [D7:2.5]metto | [Gm7]a can- [C7]tare |
{end_of_verse}

{start_of_chorus: Ritornello}
# tema scritto: melodia + accordi + testo (una sillaba per nota; "-" = la parola continua)
{start_of_notes}
| [Bb7] D2 Ab | [F7] C4 A F A | [Gm7] Bb8 D F4 [C7] E4. R8 | [F7] F1 |
w: Blues, blues | del lu- ne- dì | pas- sa pre- sto
{end_of_notes}
{end_of_chorus}

{start_of_verse: Strofa 2}
| [F7]la sera torno | [Bb7]stanco | [F7]ma con- | [Cm7]ten- [F7]to |
| [Bb7]suono il | [Bdim7]piano | [F7]e tutto | [Am7b5]si [D7b9]sistema |
| [Gm7]come | [C7]per | [F7]magia | [Gm7] [C7] |
{end_of_verse}

{ref: Ritornello | tutti insieme}

{start_of_solo: Shout chorus}
# terzine, ritornello e casse di volta 1. / 2. anche dentro le note; F, = fa all'ottava sotto
{start_of_notes}
|: [F7] 3( A8 C D ) F4 3( E8 D C ) A4 | [Bb7] D2 3( F,4 Ab Bb ) | {volta: 1} [Gm7] G8 Bb D F [C7] E2 :| {volta: 2} [F7] F R |
{end_of_notes}
{end_of_solo}

{start_of_bridge: Vamp}
# casse di volta scritte direttamente nel .chs
|: [Gm7] [C7] | [Am7] [D7] |
{volta: 1} [Gm7] [C7] | [F7] [D7] :|
{volta: 2} [Gm7] [C7] | [F7] ||
{end_of_bridge}

{start_of_outro: Coda}
# le ultime 2 battute del riff, poi lo stop
{start_of_notes}
| [Gm7] G4. Bb8 [C7] E Db C Bb | [F7] A2- A4 R |
{end_of_notes}
| [F7#9:1] [/] |
{end_of_outro}
