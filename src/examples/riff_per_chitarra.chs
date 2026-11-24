# Esempio originale per chitarristi: le battute notate si vedono come pentagramma, pentagramma + tablatura
# o solo tablatura ({notation: staff | both | tab}, per il brano o per una sezione; nell'app anche con il
# selettore sopra lo spartito). Corda e tasto li sceglie l'app, per restare in una posizione comoda;
# il ritmo viene dalle note (in "tab" è disegnato sotto i numeri). Con {tab_position: N} e ~N
# (corda di una nota) si corregge la diteggiatura dove serve.
{format: v1}
{title: Riff per chitarra}
{subtitle: tablatura calcolata dalle note}
{artist: Esempio .chs}
{tags: chitarra, tablatura, demo}
{key: G}
{time: 4/4}
{tempo: 96}
{notation: both}

{start_of_intro: Riff}
{start_of_notes}
| [G] G@3/8 B D G [D] F# D A4 | [Em] E@3/8 G B E [C] E G C4 |
| [G] <G@3 B D G>4 D'8 G B4 [D] A8 F# | [G] G2- G4 R4 |
{end_of_notes}
{end_of_intro}

{start_of_instrumental: In quinta posizione}
# lo stesso riff un'ottava sopra: {tab_position: 5} tiene la mano attorno al 5° tasto,
# ~3 dopo una nota sceglie la corda (numerazione della chitarra: 1 = Mi cantino)
{tab_position: 5}
{start_of_notes}
| [G] G@4/8 B D G [D] F# D A4~3 | [Em] E@4/8 G B E [C] E G C4 |
{end_of_notes}
{end_of_instrumental}

{start_of_verse: Strofa}
| [G] | [D] | [Em] | [C] |
| [G] | [D] | [C] [D] | [G] |
{end_of_verse}

{start_of_outro: Finale}
# solo tablatura, con il ritmo sotto i numeri
{notation: tab}
{start_of_notes}
| [C] C@4/8 E G E [D] D F# A F# | [G] <G@3 B D G>1 ||
{end_of_notes}
{end_of_outro}
