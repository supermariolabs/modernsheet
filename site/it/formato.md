---
title: Il formato .chs
slug: formato
nav: 4
other: format
description: Riferimento completo del formato .chs di Modern Sheet: intestazione, sezioni e colori, accordi e durate, battute, ritornelli, volte, segni, testo, note scritte nel brano, tablatura per chitarra, MusicXML.
---

# Il formato .chs

Un brano è un file di testo UTF-8 con estensione `.chs`. Contiene **direttive** tra parentesi graffe (`{title: …}`), **accordi** tra parentesi quadre (`[Am7]`), **stanghette** (`|`) e il **testo** cantato. Accanto agli esempi c'è lo spartito che Modern Sheet disegna per quel codice.

[TOC]

## Regole generali

- Le righe che iniziano con `#` sono **commenti**; le righe vuote non contano.
- Una direttiva è `{nome}` oppure `{nome: valore}`: può stare su una riga propria o **dentro** una riga di musica. I nomi delle direttive non distinguono maiuscole e minuscole, quelli degli accordi sì.
- La musica sta **dentro una sezione** (`{start_of_…}` … `{end_of_…}`); fuori, l'app ne apre una senza titolo e lo segnala.
- Il file non si "rompe" mai: ciò che non si capisce diventa un **avviso** (warning) con il numero di riga, mostrato sotto l'editor, e il resto si disegna comunque (vedi [Diagnostica](#diagnostica)).

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

Le direttive in cima al file descrivono il brano. Quelle che regolano l'impaginazione (`bar_width`, `notation`, `bars_per_line`) valgono per tutto il brano, ma scritte **dentro una sezione** valgono solo per quella.

| Direttiva | Esempio | Note |
|---|---|---|
| `format` | `{format: v1}` | Versione del formato, come prima direttiva. Se manca vale v1. |
| `title`, `subtitle` | `{title: Amazing Grace}` | Titolo (in alto a sinistra) e sottotitolo. |
| `artist`, `composer` | `{artist: Traditional}` | Mostrati sotto il titolo. |
| `key` | `{key: F#m}` | Tonalità: `C D E F G A B`, con `#` o `b`, e `m` per il minore (`Bb`, `Ebm`). Prima della musica è la tonalità del brano (senza: Do); dopo le prime battute è un **cambio di tonalità**. |
| `time` | `{time: 3/4}` | Metro. Prima della musica è quello del brano (senza: 4/4); dopo le prime battute è un **cambio di metro**. |
| `tempo` | `{tempo: 96}` | BPM, mostrato come ♩ = 96. |
| `capo` | `{capo: 2}` | Capotasto: mostrato in intestazione; nella [tablatura](#tablatura-per-chitarra) i tasti si contano dal capotasto. |
| `tags` | `{tags: jazz, ballad}` | Etichette per la libreria (ricerca con `#jazz`); più righe si sommano. Non stampate. |
| `bar_width` | `{bar_width: fit}` | `uniform` (battute uguali, la *Griglia* dell'app) o `fit` (*Riempi*). Vedi [Impaginazione](#impaginazione). |
| `bars_per_line` | `{bars_per_line: 6}` | Battute per riga. Vedi [Impaginazione](#impaginazione). |
| `row_spacing` | `{row_spacing: wide}` | Spazio fra le righe: `compact`, `normal`, `wide`, `extra` o una percentuale fra 50% e 300% (`120%`). |
| `label_colors`, `section_colors` | `{label_colors: by_type}` | Colori dei box delle sezioni. Vedi [Colori delle sezioni](#colori-delle-sezioni). |
| `notation`, `tuning`, `tab_position` | `{notation: both}` | Pentagramma e/o tablatura per le battute con le note. Vedi [Tablatura](#tablatura-per-chitarra). |
| `created`, `modified` | | Date di creazione e di ultimo salvataggio: le scrive l'app, non serve toccarle. |
| `comment` (o `c`) | `{comment: …}` | Commento, non stampato. |

## Sezioni

```
{start_of_verse: Strofa 1}
| [C] | [F] |
{end_of_verse}
```

- Il tipo dopo `start_of_` è **libero** (`verse`, `chorus`, `bridge`, `intro`, `solo`, `outro`, `coda`…, anche in italiano: `strofa`, `ritornello`, `inciso`…); conta per i [colori per tipo](#colori-delle-sezioni).
- L'etichetta dopo i due punti è quella mostrata nel box; senza etichetta si mostra il tipo (`Verse`).
- Ogni sezione comincia su una nuova riga; le sezioni non si annidano (aprirne una prima di chiudere la precedente dà un avviso).

### Richiami

| Scrivi | Significato |
|---|---|
| `{ref: Strofa}` | ripete qui una sezione **già scritta più sopra** |
| `{ref: Ritornello x2}` | la ripete due volte (nel box: `x2`) |
| `{ref: chorus \| tutti insieme}` | con una nota accanto al box ("reprise – tutti insieme") |

La sezione si cerca prima per etichetta (senza badare alle maiuscole), poi per tipo. Il richiamo conserva ritornelli, volte e cambi di metro della sezione e il suo colore; i segni di navigazione e le righe `{text}` restano solo nell'originale. Se nel frattempo la tonalità è cambiata, il richiamo viene **trasposto automaticamente** nella nuova tonalità.

## Colori delle sezioni

Il nome di ogni sezione sta in un **box colorato**, per riconoscere la forma del brano a colpo d'occhio sul leggio. Il colore si sceglie così:

| Direttiva | Effetto |
|---|---|
| `{label_colors: theme}` | il blu di Modern Sheet per tutti i box (predefinito) |
| `{label_colors: #8B1E3F}` | un colore a scelta per tutti i box |
| `{label_colors: by_type}` | un colore per tipo di sezione (tabella sotto) |
| `{section_colors: intro=#3366ff, chorus=#ff9900}` | colori a scelta per singole sezioni; le altre seguono `label_colors` |

Con `by_type`:

| Tipi di sezione | Colore |
|---|---|
| `verse`, `strofa` | blu notte |
| `chorus`, `ritornello`, `refrain` | bordeaux |
| `bridge`, `inciso`, `prechorus` | verde petrolio |
| `instrumental`, `solo`, `assolo`, `interlude`, `interludio` | ocra |
| `intro`, `outro`, `coda`, `ending`, `finale` e gli altri | antracite |

In `section_colors` la chiave può essere l'**etichetta** di una sezione (`Ritornello`), il suo **tipo** (`chorus`) o uno dei gruppi della tabella (`verse`, `chorus`, `bridge`, `instrumental`, `frame`); vale la prima che corrisponde, in quest'ordine. I colori si scrivono come `#RRGGBB`; uno scritto male viene ignorato. Il testo del box è bianco, o quasi nero sui colori chiari, per restare leggibile. Se il brano non ha `label_colors`, l'interruttore *Colori per sezione* dell'app equivale a `by_type`.

```{ .chs .render }
{label_colors: by_type}
{section_colors: Assolo di sax=#ff9900}

{start_of_verse: Strofa}
| [C] | [Am] | [F] | [G7] |
{end_of_verse}

{start_of_chorus: Ritornello}
| [F] | [G] | [C] | [C] |
{end_of_chorus}

{start_of_solo: Assolo di sax}
| [Dm7] | [G7] | [C] | [C] |
{end_of_solo}
```

## Accordi e durate

- `[Am7]` un accordo: radice (`A`–`G` con `#` o `b`), qualità libera (`m`, `maj7`, `m7b5`, `7#9`, `sus4`, `dim7`, `6/9`…) e basso facoltativo dopo `/` (`[C/E]`). Nello spartito `b` e `#` diventano ♭ e ♯.
- `[C:2]` dura 2 **movimenti** (quarti); la durata minima è mezzo movimento (`[G:1.5]`, `[D:0.5]`).
- In una battuta, gli accordi senza durata si dividono il tempo che resta in parti uguali, arrotondate al mezzo movimento; l'ultimo prende il resto. In 4/4: `| [C] [G] |` = 2 + 2; `| [C] [G] [D] |` = 1,5 + 1,5 + 1; `| [C:3] [G] [D] |` = 3 + 0,5 + 0,5.
- `[/]` è uno **stop** (silenzio fino all'accordo seguente; anche con durata: `[/:2]`); `[%]` dice esplicitamente "nessun accordo nuovo".
- Una battuta **senza accordi** (`| |` o solo testo) continua l'accordo precedente e si vede come **%**.
- Il **testo** dopo un accordo è quello cantato su quell'accordo; il testo prima del primo accordo di una battuta va con il primo accordo.

### Battute

- **Con le stanghette**: `| [C] [G] | [Am] |`. Le battute vuote contano (`| [G] | |` sono due battute). Se le durate scritte superano la battuta c'è un avviso; se sono tutte scritte e non la riempiono, l'ultimo accordo si allunga.
- **Senza stanghette**: `[Gm7:2] [C7:2] [Am7:2] [D7:2] [F]` – ogni accordo dura la sua durata, o una battuta intera se non ce l'ha; le battute si riempiono in ordine e un accordo che supera la stanghetta prosegue nella battuta dopo (**%**).

### Segni dentro l'accordo

| Scrivi | Significato |
|---|---|
| `[(C)]` o `[C?]` | accordo **opzionale**, tra parentesi |
| `[<C]` / `[<<C]` | **anticipo** di un ottavo / di un sedicesimo |
| `[C~]` | **legatura** all'accordo seguente (anche sulla riga dopo) |
| `[C,,,]` | **barre ritmiche**, una per virgola, distribuite sulla durata |
| `[C fermata]` | **corona** |
| `[C diamond]` o `[C <>]` | **rombo**: accordo tenuto, lasciar suonare |
| `[A "1°"]` | **annotazione** sopra l'accordo; `[% "ripeti"]` su una battuta ripetuta |

Si combinano tra loro e con la durata, in quest'ordine: anticipo, nome (eventualmente tra parentesi), `:durata`, `~` e virgole, poi le parole: `[<(G7):2~ fermata]`. Sono solo notazione: non spostano l'accordo nel tempo.

```{ .chs .render }
| [C,,,] | [<F~] [F] | [(G7)] [A "1°"] | [C diamond] [/] |
| [Dm7:3] [G7:1 fermata] | [C] | [% "ripeti"] | [C] |
```

## Stanghette, ritornelli e volte

| Scrivi | Significato |
|---|---|
| `\|\|` | doppia stanghetta |
| `\|: … :\|` | ritornello (2 volte, senza scritte) |
| `:\| x3` | ritornello ripetuto 3 volte (`x3` sopra la fine) |
| `{volta: 1}` … `{volta: 2}` | case di volta (anche `{volta: 1, 2}`) |
| `{volta_end}` / `{volta_end: hook}` | chiusura della volta, aperta o con gancio |

```{ .chs .render }
|: [Gm7] [C7] | [Am7] [D7] |
{volta: 1} [Gm7] [C7] | [F7] [D7] :|
{volta: 2} [Gm7] [C7] | [F7] ||
```

Una volta si chiude da sola al `:|` (con il gancio), all'apertura della volta seguente, con `{volta_end}` o **a fine riga del file**. La 2ª volta va a capo, allineata a destra sotto la 1ª, e l'ultima volta riceve la doppia stanghetta.

## Cambi di tonalità e di metro

`{key: …}` e `{time: …}` possono stare su una riga propria o subito dopo una stanghetta, e valgono dalla battuta seguente:

```{ .chs .render bar_width=fit }
| [G7]ultimo giro || {key: Db} [Db]modulazione | [Gb] |
| [Gm7] | {time: 2/4} [C7] | {time: 4/4} [F7] |
```

Al cambio di tonalità compaiono la doppia stanghetta, la nuova armatura (con i bequadri di cortesia) e, sotto il pentagramma, il nome della nuova tonalità; al cambio di metro, il nuovo metro. Dopo le prime battute sono sempre cambi, anche se il brano non ha tonalità e metro nell'intestazione.

## Impaginazione

Gli a capo del file **non** decidono gli a capo dello spartito: contano le battute per riga.

| Scrivi | Effetto |
|---|---|
| `{bars_per_line: 6}` dentro una sezione | 6 battute per riga in quella sezione |
| `{bars_per_line: 6}` fuori dalle sezioni | 6 battute per riga da lì in avanti |
| `{bars_per_line}` (senza valore) | torna al valore delle impostazioni (4) |
| `{br}` in una riga di battute | la battuta in cui compare comincia una nuova riga |
| `{bar_width: uniform}` | **Griglia**: battute tutte larghe uguali e allineate in colonna anche fra sezioni diverse; una battuta affollata occupa due posti invece di rimpicciolire le sigle |
| `{bar_width: fit}` | **Riempi**: ogni battuta larga quanto le serve (in proporzione ai movimenti); si va a capo solo quando le battute non ci stanno |
| `{row_spacing: wide}` | più spazio fra le righe (`compact`, `normal`, `wide`, `extra`, o `50%`–`300%`) |

`bar_width` e `bars_per_line` scritti nell'intestazione valgono per il brano, dentro una sezione solo per quella; nell'app le impostazioni e la barra sopra lo spartito danno il valore predefinito.

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

Scritti su una riga propria, `{to_coda}`, `{fine}`, `{dc}` e `{ds}` vanno alla fine dell'ultima battuta scritta.

## Righe di testo

`{text: Prima volta solo chitarra}` su una riga propria, dentro una sezione, stampa una riga di testo nello spartito in quel punto: prima della musica, fra due righe (la riga seguente va a capo) o in fondo alla sezione.

```{ .chs .render }
{start_of_verse: Strofa}
{text: Prima volta solo chitarra}
| [Em] | [C] | [G] | [D] |
{text: Seconda volta tutti}
| [Em] | [C] | [D] | [D] |
{end_of_verse}
```

## Note scritte nel .chs

Le parti con le note (intro, riff, temi) si scrivono **direttamente nel brano**, in un blocco dentro una sezione:

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
| `G` `Bb` `F#` `C##` `Ebb` | le note, come negli accordi (anche minuscole); **l'alterazione si scrive sempre**, anche se è in armatura (in Fa il si bemolle è `Bb`); `Bn` = bequadro voluto |
| `1` `2` `4` `8` `16` `32` | la figura: semibreve, minima, semiminima, croma, semicroma, biscroma; `.` o `..` per il punto. **Vale finché non cambia**: `G8 Bb D F` sono quattro crome (all'inizio del blocco: `4`) |
| ottava | ogni nota va alla più vicina alla precedente (entro una quarta); `'` la alza di un'ottava, `,` la abbassa (`''` due). La prima nota del blocco va vicino al si centrale del rigo |
| `C@5` | ottava fissa: do centrale = `C4`; le note dopo tornano relative da lì. Dopo `@N` la durata va dopo una barra: `C@5/2` |
| `R4` `R8.` `R*` | pausa; `R*` = pausa di battuta intera, in qualunque metro |
| `F2- F4` | legatura di valore (anche alla battuta dopo e oltre l'a capo) |
| `3(F8 E D)` | terzina; in generale `N:M( … )` = N note nel tempo di M (`5:4(C16 D E F G)`) |
| `<C E G>2` | più note sullo stesso gambo, la durata dopo `>` |
| `A4~3` | solo per la tablatura: la nota sulla 3ª corda (1 = la più acuta); in `< >` dopo ogni nota |
| `[Gm7]` | l'accordo, subito prima della nota su cui cade (senza durata). Per cambiare accordo su una nota tenuta: `G2- [C7] G2` |

Ordine dentro una nota: nome, alterazione, ottava, durata, punto, legatura, corda (`F#'8.-~2`). Le note si separano con spazi.

- Le righe del blocco cominciano con una stanghetta e accettano tutto quello delle battute normali: `||`, `|: … :|`, `:| x3`, `{volta: 1}`, i segni di navigazione; `{key}` e `{time}` su riga propria cambiano tonalità e metro. Una battuta con soli accordi è una battuta normale.
- **Testo cantato**: una riga `w:` sotto la riga di note, una sillaba per nota (`w: Blues, blues del lu- ne- dì`). Una sillaba che finisce con `-` continua nella seguente; le pause e le note legate si saltano da sole; `_` salta una nota (la sillaba prima si prolunga); `|` passa alla battuta dopo.
- Le travature si fanno da sole (per movimento; in 4/4 quattro crome sulla stessa metà di battuta stanno sotto una sola travatura). Le alterazioni nello spartito sono ricalcolate rispetto all'armatura: `Bb` in Fa non disegna nessun bemolle.
- Avvisi utili quando si copia da uno spartito: battuta più lunga o più corta del metro, nota senza alterazione che l'armatura altererebbe (in Fa: `B` invece di `Bb`), legatura fra note diverse, gruppo irregolare non chiuso, sillabe in più.

Nell'app un riferimento `{musicxml: …}` si può convertire in note scritte così con un pulsante (vedi [Note da MusicXML](#note-da-musicxml)).

## Tablatura per chitarra

Le battute con le note (scritte nel `.chs` o da MusicXML) si possono mostrare in tre modi, con la direttiva `notation`:

| Scrivi | Resa |
|---|---|
| `{notation: staff}` | solo pentagramma (predefinito) |
| `{notation: both}` | pentagramma e, sotto, la **tablatura**: il numero del tasto sulla corda, nella stessa colonna della nota |
| `{notation: tab}` | solo tablatura, al posto del pentagramma, con il **ritmo** disegnato sotto i numeri (gambi, travature, punti, pause) |

Nell'intestazione vale per il brano, dentro una sezione solo per quella; nell'app c'è anche un selettore sopra lo spartito (*Pentagramma / Entrambi / Tablatura*), che vince su tutto. Il ritmo non si scrive a parte: viene dalle note.

```{ .chs .render bar_width=fit }
{key: G}
{notation: both}
{start_of_intro: Riff}
{start_of_notes}
| [G] G@3/8 B D G [D] F# D A4 | [Em] E@3/8 G B E [C] E G C4 |
{end_of_notes}
{end_of_intro}
```

```{ .chs .render bar_width=fit }
{key: G}
{start_of_outro: Finale}
{notation: tab}
{start_of_notes}
| [C] C@4/8 E G E [D] D F# A F# | [G] <G@3 B D G>1 ||
{end_of_notes}
{end_of_outro}
```

- **Corda e tasto** li sceglie l'app, per tutto il passaggio insieme: resta in una posizione comoda della mano, preferisce le corde a vuoto e i tasti bassi, evita i salti; le note sullo stesso gambo vanno su corde diverse a portata di mano. Una nota legata ripete il tasto tra parentesi: `(3)`.
- **Ottava**: le note sono lette come si scrivono per chitarra, che suona un'ottava sotto lo scritto: le corde a vuoto sono Mi3 La3 Re4 Sol4 Si4 Mi5 scritti (il Mi grave è `E@3`). Una nota fuori portata si sposta di ottava, con un avviso.
- **Capotasto**: con `{capo: 2}` i tasti si contano dal capotasto (0 = capotasto).
- **Correzioni a mano**, dove la scelta automatica non è quella voluta:
  - `{tab_position: 5}` tiene la mano attorno al 5° tasto (dal 4° al 9°) per le note che seguono, fino a fine sezione o al prossimo `{tab_position}`; `{tab_position: auto}` torna alla scelta automatica;
  - `~N` dopo una nota la mette sulla corda N (`A4~3`; 1 = la più acuta); se la nota non sta su quella corda, avviso e scelta automatica.
- **Accordature** con `{tuning: …}`: `standard`, `drop D`, `double drop D`, `DADGAD`, `open G`, `open D`, `open E`, `half step down`, `bass` (4 corde), `bass 5`, `ukulele`; oppure le corde a vuoto dalla più grave, `{tuning: D A D G B E}` (anche `DADGBE`). La tablatura ha tante linee quante corde e, con un'accordatura diversa dalla standard, mostra a inizio riga i nomi delle corde al posto di "TAB".
- Dai **MusicXML** delle parti per chitarra (per esempio esportati da MuseScore) si usano corda e tasto scritti nel file.

## Note da MusicXML

In alternativa alle note scritte nel brano, una parte preparata in un editor di partiture (MuseScore, Dorico, Sibelius…) ed esportata in **MusicXML** si richiama così:

```
{start_of_intro: Intro}
{musicxml: intro.musicxml}
{end_of_intro}
```

- `{musicxml: tema.musicxml | 3-6}` usa solo le misure dalla 3 alla 6 (`| 5`: solo la 5). Il percorso è relativo alla cartella del brano; vanno bene `.musicxml`, `.xml` e `.mxl` (compresso).
- Si legge la **prima parte**, voce 1: note, pause, accordi, punti, legature, travature, terzine e gruppi irregolari, ritornelli, case di volta, sigle (tradotte negli accordi del `.chs`) e testo. Si ignorano le altre parti e voci, abbellimenti, dinamiche, articolazioni e chiavi diverse da quella di violino.
- Ogni misura diventa una battuta del brano, trasposta e impaginata come le altre. Se il metro del file è diverso diventa un cambio di metro; la tonalità resta quella del brano (un'armatura diversa dà un avviso).
- Nell'app i MusicXML citati si vedono in una scheda accanto al brano, in sola lettura. Il pulsante **Converti in note nel brano** li trasforma in un blocco `{start_of_notes}`, molto più comodo da modificare, e lascia il riferimento come commento.

## Diagnostica

L'app non si ferma mai su un errore: mostra lo spartito con quello che riesce a leggere e, sotto l'editor, gli **avvisi** con il numero di riga (toccandoli si va alla riga). I casi segnalati:

- battuta più lunga del metro; durata non valida o non multipla di mezzo movimento;
- accordo non riconosciuto; direttiva sconosciuta o con un valore non valido (tonalità, metro, accordatura, `bar_width`, `notation`, `row_spacing`…);
- sezione non chiusa, `end_of_` senza `start_of_`, musica fuori da una sezione, battuta incompleta senza stanghette;
- `{ref}` a una sezione che non esiste o che viene dopo;
- nelle note scritte e nei MusicXML: i casi elencati nelle loro sezioni.

## Versioni del formato

`{format: v1}` dichiara la versione. Le aggiunte arrivano nella versione corrente senza cambiare il significato dei file esistenti; se un giorno la sintassi cambiasse in modo incompatibile, l'app saprà ancora leggere i file v1 e offrirà di aggiornarli.

---

Per tutti i dettagli (regole di impaginazione, casi particolari) c'è la [specifica completa]({{repo}}/blob/main/SPEC.md) nel repository.
