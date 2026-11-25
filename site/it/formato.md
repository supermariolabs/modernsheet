---
title: Il formato .chs
slug: formato
nav: 4
other: format
description: Riferimento completo del formato .chs di Modern Sheet: intestazione, sezioni, accordi e durate, battute, ritornelli, volte, segni, testo, note scritte nel brano, MusicXML.
---

# Il formato .chs

Un brano è un file di testo UTF-8 con estensione `.chs`. Contiene **direttive** tra parentesi graffe (`{title: …}`), **accordi** tra parentesi quadre (`[Am7]`), **stanghette** (`|`) e il **testo** cantato. Le righe che iniziano con `#` sono commenti.

[TOC]

## Un esempio

```{ .chs .render }
{format: v1}
{title: Il mio brano}
{artist: Io}
{key: G}
{time: 4/4}
{tempo: 96}

{start_of_verse: Strofa}
| [G]Prima riga | [Em7]del testo | [C]e degli [D7]accordi | [G] |
{end_of_verse}

{start_of_chorus: Ritornello}
|: [C] | [D] | [Bm7] | [Em7] :|
{end_of_chorus}

{ref: Strofa}
```

## Intestazione

| Direttiva | Esempio | Note |
|---|---|---|
| `format` | `{format: v1}` | Versione del formato, come prima direttiva. Se manca vale v1. |
| `title`, `subtitle` | `{title: Amazing Grace}` | Titolo e sottotitolo. |
| `artist`, `composer` | `{artist: Traditional}` | Mostrati sotto il titolo. |
| `key` | `{key: F#m}` | La prima è la tonalità del brano; le successive sono **cambi di tonalità**. |
| `time` | `{time: 3/4}` | Il primo è il metro del brano; i successivi sono **cambi di metro**. |
| `tempo` | `{tempo: 96}` | BPM, mostrato come ♩ = 96. |
| `capo` | `{capo: 2}` | Capotasto. |
| `tags` | `{tags: jazz, ballad}` | Etichette per la libreria (ricerca con `#jazz`). |
| `bar_width` | `{bar_width: fit}` | `uniform` (battute uguali, la *Griglia* dell'app) o `fit` (*Riempi*) per questo brano; dentro una sezione vale solo per quella. |
| `tuning` | `{tuning: drop D}` | Accordatura per la tablatura: `standard`, `drop D`, `DADGAD`, `open G`, `open D`, `open E`, `half step down`, `bass`, `ukulele`… o le corde a vuoto (`D A D G B E`). |
| `tab_position` | `{tab_position: 5}` | Nella tablatura, la mano attorno al 5° tasto per le note che seguono (`auto` per tornare alla scelta automatica). |
| `notation` | `{notation: both}` | Battute notate: `staff` (pentagramma), `both` (pentagramma con tablatura per chitarra) o `tab` (solo tablatura, con il ritmo); anche dentro una sezione. |
| `row_spacing` | `{row_spacing: wide}` | Spazio fra le righe di questo brano: `compact`, `normal`, `wide`, `extra` o una percentuale (`120%`, fra 50% e 300%). |
| `bars_per_line` | `{bars_per_line: 6}` | Battute per riga (anche dentro una sezione). |
| `label_colors`, `section_colors` | `{section_colors: verse=#33cc66}` | Colori dei box delle sezioni. |
| `created`, `modified` | | Date scritte dall'app al salvataggio. |
| `comment` | `{comment: …}` | Commento, non stampato. |

## Sezioni

```
{start_of_verse: Strofa 1}
…
{end_of_verse}
```

Il tipo (`verse`, `chorus`, `bridge`, `intro`, `solo`, `outro`, `coda`…) è libero; l'etichetta dopo i due punti è quella mostrata. Ogni sezione comincia su una nuova riga.

**Richiami**: `{ref: Strofa}` ripete una sezione già scritta, `{ref: Ritornello x2 | più forte}` la ripete due volte con una nota. Se nel frattempo la tonalità è cambiata, il richiamo viene **trasposto automaticamente**.

## Accordi e durate

- `[Am7]` un accordo; `[C/E]` con il basso; la qualità è libera (`m7b5`, `7#9`, `sus4`, `6/9`…).
- `[C:2]` dura 2 movimenti (quarti); minimo mezzo movimento (`[G:1.5]`).
- In una battuta, gli accordi senza durata si dividono in parti uguali il tempo che resta.
- `[/]` è uno **stop**; `[%]` dice "nessun accordo nuovo".
- Una battuta senza accordi continua quello precedente e si vede come **%**.
- Il testo dopo un accordo è quello cantato su quell'accordo.

### Battute

- **Con le stanghette**: `| [C] [G] | [Am] |` – le battute sono delimitate da `|`.
- **Senza stanghette**: `[Gm7:2] [C7:2] [F]` – ogni accordo dura la sua durata, o una battuta intera.

### Segni dentro l'accordo

| Scrivi | Significato |
|---|---|
| `[(C)]` o `[C?]` | accordo **opzionale**, tra parentesi |
| `[<C]` / `[<<C]` | **anticipo** di un ottavo / di un sedicesimo |
| `[C~]` | **legatura** all'accordo seguente |
| `[C,,,]` | **barre ritmiche**, una per virgola |
| `[C fermata]` | **corona** |
| `[C diamond]` o `[C <>]` | **rombo**: accordo tenuto |
| `[A "1°"]` | **annotazione** sopra l'accordo; `[% "ripeti"]` su una battuta ripetuta |

Si combinano tra loro e con la durata: `[<(G7):2~ fermata]`.

## Stanghette, ritornelli e volte

| Scrivi | Significato |
|---|---|
| `\|\|` | doppia stanghetta |
| `\|: … :\|` | ritornello (2 volte) |
| `:\| x3` | ritornello ripetuto 3 volte |
| `{volta: 1}` … `{volta: 2}` | case di volta (anche `{volta: 1, 2}`) |
| `{volta_end}` / `{volta_end: hook}` | chiusura della volta, aperta o con gancio |
| `{br}` | a capo forzato |

```{ .chs .render }
|: [Gm7] [C7] | [Am7] [D7] |
{volta: 1} [Gm7] [C7] | [F7] [D7] :|
{volta: 2} [Gm7] [C7] | [F7] ||
```

La 2ª volta va a capo, allineata a destra sotto la 1ª.

## Cambi di tonalità e di metro

`{key: …}` e `{time: …}` possono stare su una riga propria o subito dopo una stanghetta:

```{ .chs .render bar_width=fit }
| [G7]ultimo giro || {key: Db} [Db]modulazione | [Gb] |
| [Gm7] | {time: 2/4} [C7] | {time: 4/4} [F7] |
```

Al cambio di tonalità compaiono la doppia stanghetta, la nuova armatura (con i bequadri di cortesia) e, sotto il pentagramma, il nome della nuova tonalità.

## Segni di navigazione

| Direttiva | Dove va | Resa |
|---|---|---|
| `{segno}` | inizio della battuta seguente | 𝄋 |
| `{coda}` | inizio della battuta seguente | ⊕ |
| `{to_coda}` | fine della battuta in cui è scritta | To Coda ⊕ |
| `{fine}` | fine della battuta | Fine, con doppia stanghetta |
| `{dc: al Fine}` | fine della battuta | D.C. al Fine |
| `{ds: al Coda}` | fine della battuta | D.S. al Coda |

```{ .chs .render }
{segno}
| [Am7] | [D7] {to_coda} | [G] | [G7] |
| [C] | [D7] {ds: al Coda} ||
```

## Righe di testo

`{text: Prima volta solo chitarra}` su una riga propria, dentro una sezione, stampa una riga di testo nello spartito in quel punto: prima della musica, fra due righe o in fondo alla sezione.

## Note da MusicXML

Le parti scritte (intro, riff, temi) si preparano in un editor di partiture (MuseScore, Dorico, Sibelius…), si esportano in **MusicXML** e si richiamano:

```
{start_of_intro: Intro}
{musicxml: intro.musicxml}
{end_of_intro}
```

`{musicxml: tema.musicxml | 3-6}` usa solo le battute dalla 3 alla 6. Il percorso è relativo alla cartella del brano. Note, accordi e testo del file vengono disegnati sul pentagramma, trasposti insieme al resto.

Nell'app i MusicXML citati si vedono in una scheda accanto al brano, in sola lettura; per modificarli conviene convertirli in note scritte nel `.chs` (sotto) con il pulsante **Converti in note nel brano**.

## Note scritte nel .chs

In alternativa al MusicXML, poche battute di note si possono scrivere **direttamente nel brano**, dentro una sezione:

```{ .chs .render bar_width=fit }
{start_of_intro: Intro}
{start_of_notes}
| [Gm7] G8 Bb D F [C7] A G E C | [Am7] C E G B [D7] F# E D16 C Bb A |
| [Gm7] G4. Bb8 [C7] E Db C Bb | [F7] A2- A4 R |
{end_of_notes}
{end_of_intro}
```

| Scrivi | Significa |
|---|---|
| `G` `Bb` `F#` | le note, come negli accordi; **l'alterazione si scrive sempre**, anche se è in armatura (in Fa il si bemolle è `Bb`); `Bn` = bequadro voluto |
| `8` `4` `2` `1` `16`, `4.` | la figura: croma, semiminima, minima, semibreve, semicroma; il punto. **Vale finché non cambia**: `G8 Bb D F` sono quattro crome |
| ottava | ogni nota va alla più vicina alla precedente; `'` la alza, `,` la abbassa; `C@5` fissa l'ottava (do centrale = `C4`; durata dopo una barra: `C@5/2`) |
| `R4` `R*` | pausa; pausa di battuta intera |
| `F2- F4` | legatura di valore |
| `3(F8 E D)` | terzina (in generale `5:4( … )`) |
| `<C E G>2` | più note sullo stesso gambo |
| `A4~3` | per la tablatura: la nota sulla 3ª corda (1 = la più acuta) |
| `[Gm7]` | l'accordo, subito prima della nota su cui cade |

Il testo cantato va su una riga `w:` sotto la riga di note, una sillaba per nota (`lu- ne- dì`; `_` salta una nota, `|` passa alla battuta dopo). Le travature si fanno da sole. Il risultato è lo stesso del MusicXML: si traspone, si impagina e si stampa allo stesso modo; l'esempio `note_nel_chs` è il blues con melodia scritto così.

## Versioni del formato

`{format: v1}` dichiara la versione. Le aggiunte arrivano nella versione corrente senza cambiare il significato dei file esistenti; se un giorno la sintassi cambiasse in modo incompatibile, l'app saprà ancora leggere i file v1 e offrirà di aggiornarli.

---

Per tutti i dettagli (regole di impaginazione, casi particolari) c'è la [specifica completa]({{repo}}/blob/main/SPEC.md) nel repository.
