# Brano originale: guida alle basi del formato .chs
#   intestazione completa, opzioni per brano ({row_spacing}: spazio fra le righe; {bar_width}, anche per una sola sezione), righe con e senza stanghette, durate, continuazioni,
#   stop, battuta vuota, accordi con basso, tonalità minore, {c: …} (riga stampata, come in ChordPro)
{format: v1}
{title: Formato base}
{subtitle: guida alle basi del .chs}
{composer: Modern Sheet .chs}
{tags: demo, guida}
{key: Am}
{time: 4/4}
{tempo: 88}
{capo: 2}
{bar_width: fit}
{row_spacing: wide}
{label_colors: by_type}
{bars_per_line: 4}

{start_of_intro: Intro}
{c: Solo pianoforte}
# Modalità implicita (nessuna |): ogni accordo dura una battuta, o la durata scritta in movimenti
[Am] [Am/G] [F:2] [E7:2] [Am]
{end_of_intro}

{start_of_verse: Strofa}
# Modalità esplicita: le stanghette delimitano le battute; gli accordi senza durata si dividono il resto;
# il testo prima del primo accordo di una battuta ("la") va con quell'accordo; [%] = nessun accordo nuovo
| la [Am]prima riga | [Dm7]con il testo | [G7]sopra le [C]sigle | [Fmaj7] |
| [Bm7b5:1.5] [E7:2.5] | [Am] [%] [Am/G] | [F] [/] | |
{end_of_verse}

{start_of_chorus: Ritornello}
# {bar_width} dentro una sezione vale solo per lei: il brano è "fit" (intestazione), il ritornello torna
# alla griglia, con le battute larghe uguali e le stanghette in colonna
{bar_width: uniform}
{text: Una battuta vuota (| |) continua l'accordo precedente e si vede come %.}
| [F] | [G] | [Em7] | [Am] |
| [Dm7] [G7] | [C/E] [F] | [Bm7b5] [E7sus4] [E7] | [Am] [/] ||
{end_of_chorus}
