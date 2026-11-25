# Brano originale: ritornelli, case di volta e richiami
#   |: :| e :| x3, {volta: 1} {volta: 2} {volta: 3}, {volta: 1, 2}, {volta_end} e {volta_end: hook},
#   {ref: … x2 | nota}, {ref: … volta 2 = nome} (un giro dritto alla 2ª volta, con un altro nome),
#   {ref: … once} (senza ritornelli: ogni parte ripetuta una volta sola),
#   {br}, {bars_per_line} dentro una sezione
{format: v1}
{title: Ripetizioni e volte}
{subtitle: ritornelli, case di volta, richiami}
{artist: Modern Sheet .chs}
{tags: demo, guida}
{key: G}
{time: 4/4}
{tempo: 126}

{start_of_intro: Intro}
|: [G] | [C] | [D7] | [G] :| x3
{end_of_intro}

{start_of_verse: Strofa}
|: [G] | [Em7] | [Am7] | [D7] |
{volta: 1, 2} [G] | [C] :|
{volta: 3} [G] | [C] [D7] | [G] | {volta_end}
{end_of_verse}

{start_of_chorus: Ritornello}
{bars_per_line: 3}
|: [C] | [D] | [Bm7] |
{volta: 1} [Em7] | [Am7] | [D7] :|
{volta: 2} [Em7] | [A7] | [D7] | {volta_end: hook}
| [G] | {br} [C] | [G] ||
{end_of_chorus}

{ref: Strofa | tutti insieme}
{ref: Ritornello x2 | più forte}
{ref: Ritornello volta 2 = Ultimo ritornello | dritti alla 2ª volta}
{ref: Intro once = Chiusura | una volta sola}

{start_of_outro: Finale}
| [G] | [C] | [G] [D7] | [G] [/] |
{end_of_outro}
