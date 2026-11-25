# SPEC — Modern Sheet: formato `.chs` e motore di rendering

> Versione 0.44 — 24 novembre 2026 (0.44: nell'editor le **parti modificate** dall'ultimo salvataggio hanno lo sfondo verde (riga cambiata più chiara, testo scritto più acceso), che sparisce salvando; **Annulla / Ripristina** passo per passo (pulsanti e ⌘Z / ⌘⇧Z / Ctrl+Y), modulo `edits.py`; 0.43: nell'app i **MusicXML sono in sola lettura** (indentati e colorati) con il pulsante **Converti in note nel brano**, che scrive le battute nel `.chs` come `{start_of_notes}` e lascia il riferimento come commento; tolti modifica, completamento, *Indenta*, *Comprimi/Espandi* e *Crea il file MusicXML*; 0.42: tablatura, seconda fase: `{tab_position}`, corda di una nota `~N`, accordature `{tuning}` (anche basso e ukulele) con i nomi delle corde, corda e tasto dal MusicXML; esempio `riff_drop_d`; 0.41: **tablatura per chitarra** delle battute notate (§4.8b): pentagramma, pentagramma + tablatura o sola tablatura con il ritmo, diteggiatura calcolata, capotasto; globale, per brano e per sezione; esempio `riff_per_chitarra`; 0.40: spazio fra le righe regolabile, globale (impostazioni, `--row-spacing`) e per brano (`{row_spacing}`); 0.39.1: `fit` va a capo solo quando le battute non ci stanno davvero, le righe chiuse per mancanza di spazio arrivano al margine, nessuna battuta più stretta del necessario; 0.39: `{bar_width}` dentro una sezione vale solo per quella sezione, sopra l'impostazione del brano e dell'app; 0.38: **note scritte nel `.chs`** (§2.12b), blocco `{start_of_notes}` … `{end_of_notes}` in alternativa al MusicXML, con evidenziazione e completamento nell'editor ed esempio `note_nel_chs`; 0.37: nell'editor MusicXML barra con *Indenta* (rientra le righe o un elemento per riga) e *Comprimi/Espandi* degli elementi, battute comprese; 0.36.1: build Linux su GitHub Actions corretta (conflitto di libunwind con GStreamer sulle macchine Ubuntu 22.04); 0.36: app desktop per macOS, Windows e Linux compilate da GitHub Actions e scaricabili dalla pagina Download del sito; 0.35: pubblicazione su GitHub (licenza GPL-3.0, README, test automatici), sito modernsheet.app con documentazione in italiano e inglese, identificativo dell'app `app.modernsheet`; 0.34: importazione dal proprio account chordsheet.com con scelta multipla dei brani, email ricordata e password mai salvata; 0.33: "Importa file .chs" copia il brano e i suoi MusicXML nella libreria invece di aprirlo fuori; 0.32: pulsante Salva disattivato senza modifiche, verde quando c'è qualcosa da salvare; 0.31: rinomina delle cartelle della libreria (menu ⋮), con i riferimenti MusicXML aggiornati; la sincronizzazione toglie le cartelle che ha svuotato, anche su Google Drive; 0.30: libreria di una nuova installazione = cartella "Modern Sheet" con dentro solo `examples/`; l'unione con la libreria sincronizzata copia solo i file mancanti, dopo la prima sincronizzazione; 0.29: al cambio di tonalità la nuova tonalità è scritta per esteso sotto il pentagramma ("Key E♭"); 0.28: esempi che coprono tutto il formato (`formato_base`, `ripetizioni_e_volte`, `tempi_e_tonalita`); una volta successiva più lunga della 1ª ha il pentagramma intero; 0.27: ricerca con `A*` (inizia con), `*xyz` (finisce con), `*testo*` (contiene), `&` (e) e `|` (o); 0.26: libreria con i brani raggruppati per lettera (A–Z) ordinando per titolo o artista, cartelle in cima; 0.25: annotazioni sugli accordi `[A "1°"]`; importazione da chordsheet.com provata su 234 brani reali: annotazioni, `*` e `X` dentro `_`, finali attaccati `1.C`, `x4` staccato, rientri e palette ignorati; 0.24: segni ritmici (anticipi, legature, barre ritmiche, corona, rombo) e accordi opzionali dentro le parentesi dell'accordo (§2.4b), anche dall'importazione da chordsheet.com; 0.23: segni di navigazione `{segno}` `{coda}` `{to_coda}` `{fine}` `{dc}` `{ds}` e righe di testo `{text}` (§2.8b), anche dall'importazione da chordsheet.com; 0.22: i brani si aprono in modalità vista (matita per modificare); schermo intero con pulsante di uscita sempre visibile ed Esc; schede della libreria con il titolo in una fascia blu e altezza fissa (niente tagli su iPad); 0.21: eliminazione di un brano e dei suoi MusicXML dall'editor, con conferma ed elenco dei file; *Salva con nome* chiede il nome e salva accanto al brano, nella libreria; le schede mostrano il nome del file; direttive `{created}`/`{modified}` scritte dall'app al salvataggio, mostrate sempre nelle schede e usate per ordinare; brani con lo stesso titolo: il più recente prima, il dato che li distingue in arancione; `python src/main.py` usa la cartella dati di `flet run`; 0.20.1: nome, descrizione e icona di Modern Sheet nell'app Flet su iPad/Android (`src/assets/manifest.json`); 0.20: icona dell'app per tutte le piattaforme; 0.19: il progetto si chiama **Modern Sheet** (prima Chord Sheet): pacchetto `modernsheet`, `modernsheet_cli.py`, variabili `MODERNSHEET_*`, cartella Drive predefinita "Modern Sheet"; il formato resta `.chs`; 0.18: nome della cartella su Google Drive configurabile; remoto vuoto o ricreato mai trattato come cancellazione di tutto; 0.17: sincronizzazione con Google Drive, fase 2; 0.16: sincronizzazione della libreria local-first, fase 1: motore con conflitti senza perdita di dati e provider "cartella"; 0.15: editor a tab, una per ogni MusicXML citato dal brano, con evidenziazione e completamento; anteprima con il MusicXML non salvato; 0.14: libreria con *Nuova cartella*, percorso con tasto "su", cartelle vuote visibili; 0.13: interfaccia in italiano e inglese, lingua nelle impostazioni; 0.12: direttiva `{tags}`, libreria con vista a card, ricerca per artista e tag, ordinamento, indice dei brani; 0.11: versione del formato `{format: v1}` e parser per versione, conversione al formato corrente; 0.10: esempi come cartella dei brani predefinita, pagina Impostazioni, editor scuro con evidenziazione della sintassi e completamento delle direttive; 0.9: app con libreria di brani da una cartella con sottocartelle, editor del sorgente con anteprima dal vivo; 0.8.1: sigle e testo delle battute notate allineati su un'unica linea per riga; 0.8: colori personalizzati per sezione `{section_colors}`, testo dei box nero o bianco secondo il contrasto, brano demo; 0.7: importazione da Chord Sheet Maker / chordsheet.com; 0.6: motore a tre strati, prototipo app Flet; 0.5: terzine, ritornelli e casse di volta (MusicXML e .chs), 2ª volta allineata a destra sotto la 1ª; 0.2: battute affollate su più slot, dimensione accordi uniforme per battuta; 0.3: tema grafico "Real Book" predefinito, estensioni in apice, simboli jazz opzionali; 0.4: zone notate da MusicXML; 0.3.1: blu #0066CC come colore predefinito dei box di sezione, sigle standard come predefinite, accordi in grassetto, etichette di sezione in box pieni arrotondati, colori per tipo di sezione, titolo a sinistra, intestazione solo in prima pagina)
> Stato: **Fase 1 (motore + generatore PDF) implementata** in `src/modernsheet/`; **Fase 2: app Flet** in `src/main.py` con libreria, editor e impostazioni (§8).
> In caso di dubbio, il motore in `src/modernsheet/` è l'implementazione di riferimento: il comportamento descritto qui e quello dello script devono coincidere.

---

## 1. Visione

Un sistema personale (con possibile evoluzione a prodotto) per scrivere, gestire e suonare **chord sheet** di brani pop / rock / jazz.

- **Un solo file sorgente** per brano, in un formato testuale nuovo (`.chs`) che unisce:
  - il **testo con accordi in linea** di ChordPro;
  - la **struttura a battute** di Chord Sheet Maker (griglia, durate, ripetizioni).
- **Più viste** generate dallo stesso sorgente:
  - **Staff** (lead sheet su pentagramma, slash-notation semplificata) → implementata, output PDF;
  - **Classica** (testo con accordi sopra) → prevista per l'app.
- **Roadmap**
  - Fase 1 — motore Python (parser + renderer PDF) usabile da riga di comando e come libreria. ✅
  - Fase 2 — app per iPad, poi Android (e desktop) con lo **stesso motore Python** (Flet). 🚧 prototipo

Non è un requisito la compatibilità con ChordPro standard né con i suoi lettori.

---

## 2. Il formato `.chs`

### 2.1 Regole generali

| Regola | Dettaglio |
|---|---|
| Codifica | UTF-8, testo semplice. Estensione **`.chs`** (provvisoria). |
| Righe vuote | Ignorate. |
| Commenti | Riga che inizia con `#` → ignorata. |
| Direttive | `{nome}` oppure `{nome: valore}`. Possono stare su una riga propria o **dentro** una riga musicale. |
| Righe musicali | Contengono accordi `[...]`, testo, stanghette e direttive in linea. Devono stare dentro una sezione (altrimenti il parser apre una sezione senza titolo e segnala un warning). |
| Case | Nomi di direttive case-insensitive; nomi di accordi case-sensitive. |
| Versione del formato | `{format: v1}` come **prima direttiva** del file (§2.14). Senza, il file è in formato v1. |

### 2.2 Metadati (intestazione)

| Direttiva | Esempio | Note |
|---|---|---|
| `title` | `{title: Amazing Grace}` | Titolo (in grassetto, in alto a sinistra). |
| `subtitle` | `{subtitle: Jazz blues in F}` | Opzionale, in grigio sotto il titolo. |
| `artist` / `composer` | `{artist: Traditional}` | In grigio sotto il titolo, dopo il sottotitolo. |
| `key` | `{key: G}` / `{key: F#m}` | **La prima** `key` è la tonalità del brano; le successive sono **cambi di tonalità** (§2.8). |
| `time` | `{time: 3/4}` | **Il primo** `time` è il metro del brano; i successivi sono **cambi di tempo** (§2.8). Default `4/4`. |
| `tempo` | `{tempo: 80}` | BPM, mostrato come `♩ = 80`. |
| `capo` | `{capo: 2}` | Opzionale, mostrato in intestazione. |
| `bar_width` | `{bar_width: fit}` | Nell'intestazione sovrascrive la configurazione per questo brano; **dentro una sezione vale solo per quella** (come `bars_per_line`; §4.3). |
| `tuning` | `{tuning: drop D}` `{tuning: D A D G B E}` | Accordatura per la tablatura (§4.8b): `standard`, `drop D`, `double drop D`, `DADGAD`, `open G`, `open D`, `open E`, `half step down`, `bass`, `bass 5`, `ukulele`, oppure le corde a vuoto dalla più grave. Valore non valido → warning. |
| `tab_position` | `{tab_position: 5}` | Posizione della mano per la tablatura, per le note che seguono fino a fine sezione o al prossimo `{tab_position}` (`auto` = scelta automatica); anche dentro un blocco di note o una riga di battute. |
| `notation` | `{notation: both}` | Battute notate come pentagramma (`staff`), pentagramma con tablatura per chitarra (`both`) o sola tablatura (`tab`); nell'intestazione per il brano, **dentro una sezione solo per quella** (§4.8b). Valore non valido → warning. |
| `row_spacing` | `{row_spacing: wide}` `{row_spacing: 120%}` | Spazio fra le righe di questo brano: `compact` (75%), `normal`, `wide` (130%), `extra` (160%) o una percentuale fra 50% e 300% (anche `1.2`). Sovrascrive l'impostazione globale (§4.2). Valore non valido → warning. |
| `bars_per_line` | `{bars_per_line: 6}` | Vedi §2.10. |
| `tags` | `{tags: jazz, ballad, bossa nova}` | Etichette per organizzare i brani nella libreria dell'app (§8.2): separate da virgole, convertite in minuscolo, spazi interni ridotti a uno, doppioni e valori vuoti scartati. Più righe `{tags}` si sommano. Non stampate nel PDF. In `Song.tags`. |
| `created`, `modified` | `{created: 2026-11-20 11:47:00}` `{modified: 2026-11-23 10:24:59}` | Data e ora di **creazione** e di **ultimo salvataggio** (`AAAA-MM-GG HH:MM:SS`, ora locale; letti anche senza secondi, solo la data o con `T`). Le **scrive l'app**, non vanno scritte a mano: a ogni salvataggio con modifiche aggiorna `modified` e, se manca, aggiunge `created` (per un file che non l'aveva: la data di creazione del file su disco, se il sistema la conserva, altrimenti quella di modifica, la più vecchia delle due); *Salva con nome* crea un file nuovo, quindi `created` = adesso. Le righe esistenti si aggiornano al loro posto; quelle nuove vanno dopo le direttive d'intestazione in cima al file (mai prima di `{format}`), così la posizione del cursore non cambia. Non compaiono nella pagina; servono alla libreria (schede, ordinamento, §8.2). Un valore non valido dà un warning. Con la sincronizzazione restano giuste anche dopo il trasferimento su un altro dispositivo, a differenza delle date dei file. |

Tonalità ammesse: `C D E F G A B` con `#` o `b` opzionale, seguite da `m` per il minore (`Bb`, `Ebm`, `F#m`).

### 2.3 Sezioni

```
{start_of_<tipo>: Etichetta opzionale}
...righe musicali...
{end_of_<tipo>}
```

- `<tipo>` è **libero**: `intro`, `verse`, `chorus`, `bridge`, `solo`, `instrumental`, `outro`, `coda`…
- L'etichetta è ciò che viene mostrato (`{start_of_verse: Strofa 2}` → "Strofa 2"). Senza etichetta si mostra il tipo con iniziale maiuscola.
- Le sezioni **non si annidano**: aprire una sezione prima di chiudere la precedente genera un warning.
- Ogni sezione inizia su una nuova riga di pentagramma.

### 2.4 Accordi e durate

```
[Accordo]           durata implicita (§2.5)
[Accordo:durata]    durata esplicita in movimenti
```

- **Unità = movimento** (quarto / semiminima). Il numero di movimenti di una battuta è `num × 4 / den` (4/4 → 4, 3/4 → 3, 2/4 → 2, 6/8 → 3).
- Risoluzione minima: **mezzo movimento** (`[C:1.5]`, `[G:0.5]`). Durate non multiple di 0,5 vengono arrotondate con warning.
- Il **testo** che segue un accordo (fino al prossimo accordo o stanghetta) è la sillaba/parola cantata su quell'accordo.
- Il testo prima del primo accordo di una battuta viene agganciato al primo evento della battuta.

**Sintassi del nome accordo**

```
Accordo  := Radice Qualità? ( "/" Basso )?
Radice   := [A-G] ( "#" | "b" )?
Basso    := [A-G] ( "#" | "b" )?
Qualità  := testo libero: m, maj7, m7b5, 7b9, 7#9, sus4, dim7, add9, 6/9* …
```
\* Il parser riconosce radice e basso (necessari per la trasposizione); la qualità è conservata così com'è. Nel rendering `b` e `#` diventano `♭` e `♯` sulla radice, sul basso e davanti ai numeri (`Bbm7b5` → `B♭m7♭5`, `F7#9` → `F7♯9`).

**Simboli speciali al posto dell'accordo**

| Token | Significato | Rendering |
|---|---|---|
| `[/]` o `[/:d]` | **Stop**: l'accordo si interrompe; silenzio fino al prossimo accordo. Si comporta come un accordo per le durate. | `/` |
| `[%]` | Nessun nuovo accordo (continuazione esplicita). Raramente necessario: una battuta senza accordi è già una continuazione. | — |

### 2.4b Segni ritmici e accordi opzionali

Si scrivono **dentro le parentesi quadre** dell'accordo (aggiunte al formato v1): il nome dell'accordo resta separato, quindi trasposizione e durate funzionano come sempre. Si combinano liberamente: `[<(G7):2~ fermata]`.

| Sintassi | Significato | Resa |
|---|---|---|
| `[(C)]` oppure `[C?]` | **accordo opzionale** | l'accordo tra parentesi tonde `(C)` |
| `[<C]` / `[<<C]` | **anticipo** di un ottavo / di un sedicesimo (l'accordo arriva prima del movimento) | `<` / `<<` piccoli davanti all'accordo |
| `[C~]` (o la parola `tie`) | **legatura** all'accordo seguente (tenuto, non ribattuto) | arco sopra le sigle fino all'accordo seguente; se questo è nella riga dopo, l'arco arriva in fondo alla riga e riparte all'inizio della successiva |
| `[C,]`, `[C,,,]` | **barre ritmiche** (colpi): una per virgola | barre oblique sul rigo, distribuite in parti uguali sulla durata dell'accordo (in 4/4, `[C,,,]` = un colpo per movimento) |
| `[C fermata]` | **corona** | corona sopra il rigo, centrata sull'accordo (sopra il testo, se la battuta ne ha) |
| `[C diamond]` o `[C <>]` | **rombo**: accordo tenuto, lasciar suonare | rombo vuoto subito dopo l'accordo |
| `[A "1°"]`, `[Dm7 "ad lib."]` | **annotazione**: testo breve sull'accordo (gradi, indicazioni, "1° giro"…) | testo piccolo sopra il rigo all'altezza dell'accordo; se la riga ha testo cantato, in una corsia sopra le parole (+10 pt); troncato con "…" prima dell'annotazione seguente; con la corona, la corona sta sopra |
| `[% "testo"]` | annotazione su una battuta **senza accordo nuovo** (ripetuta) | come sopra, sopra il segno `%` |

- Ordine dentro le parentesi: `<`/`<<`, poi il nome (eventualmente tra parentesi tonde), poi `:durata`, poi `~` e virgole (anche prima dei due punti o dentro le parentesi tonde: `[(D7~)]`), infine le parole `fermata`, `diamond`, `<>`, `tie` separate da spazi. L'annotazione tra virgolette può stare ovunque dopo il nome (`[Bm:2 "ad lib." fermata]`); gli spazi multipli al suo interno si riducono a uno; non può contenere `]`.
- I segni sono **notazione**: non cambiano le durate (un anticipo non sposta l'accordo nella griglia della battuta).
- Simboli musicali dal font Petaluma (SMuFL) in tutti i temi; lo spazio occupato da parentesi, anticipo e rombo conta nel calcolo della larghezza delle battute.
- Diagnostica: warning per una parola sconosciuta (`[C foo]`) e per più di due `<`.

Esempi: `src/examples/segni_ritmici.chs`, `src/examples/accordi_opzionali.chs` e `src/examples/annotazioni.chs`.

### 2.5 Battute: modalità esplicita

Una riga che contiene almeno una stanghetta è in **modalità esplicita**: le battute sono delimitate da `|`.

```
| [C]Prima riga del [Cmaj7]testo | [F]qui |
```

Regole di durata dentro una battuta delimitata:

1. Si sommano le durate esplicite.
2. I movimenti rimanenti si dividono **in parti uguali** tra gli accordi senza durata.
3. La quota è arrotondata per difetto al mezzo movimento; **l'ultimo** accordo senza durata prende il resto.
   - 4/4, `| [C] [G] |` → 2 + 2
   - 4/4, `| [C:3] [G] [D] |` → 3 + 0,5 + 0,5
   - 4/4, `| [C] [G] [D] |` → 1,5 + 1,5 + 1
   - 3/4, `| [G]hour [Em]I |` → 1,5 + 1,5
4. Se la somma delle durate esplicite **supera** la battuta → **errore** (warning, la battuta viene comunque disegnata).
5. Se tutte le durate sono esplicite e la somma è **inferiore**, l'ultimo evento si allunga fino a fine battuta.
6. Una battuta **senza accordi** (es. `| grace, how |` o `| |`) **prosegue l'accordo precedente** → rendering `%`.

Le battute vuote tra due stanghette contano (`| [G]see. | |` = 2 battute).

### 2.6 Battute: modalità implicita

Una riga **senza stanghette** è in modalità implicita:

- ogni accordo dura quanto indicato; **senza durata dura una battuta intera**;
- le battute si riempiono in ordine; un accordo che supera la stanghetta **prosegue** nella battuta successiva (rendering `%` se la battuta non ha altri accordi);
- se la riga termina con una battuta incompleta, l'ultimo evento viene allungato (warning).

```
[Gm7:2] [C7:2] [Am7:2] [D7:2] [F7:1] [/:3]
→ | Gm7 C7 | Am7 D7 | F7 / |
```

### 2.7 Stanghette e ripetizioni

| Token | Significato |
|---|---|
| `\|` | Stanghetta: chiude la battuta corrente. |
| `\|\|` | Doppia stanghetta alla fine della battuta corrente. |
| `\|:` | Inizio ritornello (repeat start) sulla battuta seguente. |
| `:\|` | Fine ritornello: il blocco si suona **2 volte**. |
| `:\| xN` | Fine ritornello: il blocco si suona **N volte** (es. `:\| x3`). |

```
|: [G] | [C] | [G] | [D7] :|            → ripetuto 2 volte
|: [Ab]A-men | [Db] :| x3               → ripetuto 3 volte
```

- Per N = 2 non si mostra alcuna indicazione (convenzione da spartito). Per N ≥ 3 si mostra **`xN` in grassetto** sopra la fine del ritornello.

**Casse di volta (1. / 2.)**

```
|: [Gm7] [C7] | [Am7] [D7] |
{volta: 1} [Gm7] [C7] | [F7] [D7] :|
{volta: 2} [Gm7] [C7] | [F7] ||
```

| Regola | Dettaglio |
|---|---|
| Apertura | `{volta: N}` (o `{volta: 1, 2}` → "1., 2.") prima della prima battuta della volta, in linea o su riga propria. |
| Chiusura | La volta termina: alla battuta con `:\|` (parentesi **chiusa**, con gancio verso il basso); all'apertura di un'altra volta; con `{volta_end}` (aperta) o `{volta_end: hook}` (chiusa); **a fine riga del sorgente** o a fine sezione (aperta). |
| Fine della 2ª volta | L'ultima volta (2ª, 3ª…) che non torna indietro chiude la struttura ripetuta: riceve **automaticamente la doppia stanghetta**. Dal MusicXML viene letto anche lo stile della stanghetta (`bar-style` light-light / light-heavy → doppia). |
| Allineamento | La 2ª volta (e le successive) **inizia sempre una riga nuova, allineata a destra**: finisce dove finisce la riga della 1ª volta, così le due volte stanno una sotto l'altra. A sinistra resta **spazio bianco** (nessun rigo al posto delle battute "mancanti"): la riga contiene **solo le battute** della volta, senza chiave né armatura, aperte da una stanghetta; dopo la volta si va a capo. Se è **più lunga** della 1ª, comincia sotto l'inizio della 1ª volta e prosegue oltre, con il pentagramma intero. |
| Resa | Linea orizzontale sopra il rigo con gancio iniziale e numero in grassetto; gancio finale solo se chiusa. Se la volta attraversa l'a capo continua sulla riga successiva senza ripetere il numero. Le righe con una volta ricevono 15 pt di spazio in più in alto. |
- Il testo mostrato è quello scritto (primo giro). Strofe multiple sotto lo stesso ritornello: vedi §8.

### 2.8 Cambi di tonalità e di tempo

`{key: …}` e `{time: …}` possono comparire **ovunque**: su riga propria (tra sezioni o dentro una sezione) o **in linea** subito dopo una stanghetta. Valgono dalla battuta successiva in poi.

```
| [G7]ultimo giro || {key: Db} [Db]modulazione | [Gb] |
| [Gm7]come | {time: 2/4} [C7]per | {time: 4/4} [F7]magia |
```

- **Cambio di tonalità**: doppia stanghetta automatica prima della battuta che cambia; nuova armatura con **bequadri di cortesia** quando si perdono alterazioni (es. G → Ab: ♮ sul Fa, poi 4 bemolle). Da quel punto ogni riga riparte con la nuova armatura. Sotto il pentagramma, all'altezza della nuova armatura, compare anche la **nuova tonalità per esteso** ("Key E♭", "Key F♯m", nello stesso stile dell'intestazione: font delle note del tema, 9 pt, grigio), sia quando il cambio è a metà riga sia quando apre una riga (anche nei richiami trasposti); nelle righe successive c'è solo l'armatura.
- **Cambio di tempo**: il nuovo metro compare nella battuta in cui cambia; tutte le regole di durata usano il nuovo numero di movimenti.

### 2.8b Segni di navigazione (Segno, Coda, D.C./D.S., Fine) e righe di testo

Aggiunte al formato v1 (compatibili: i file v1 esistenti non cambiano significato).

| Direttiva | Dove va | Resa |
|---|---|---|
| `{segno}` | all'**inizio** della battuta **seguente** | segno 𝄋 (SMuFL, Petaluma in tutti i temi) sopra il rigo, a sinistra |
| `{coda}` | all'**inizio** della battuta **seguente** (dove si salta) | segno di coda ⊕ sopra il rigo, a sinistra |
| `{to_coda}` | alla **fine** della battuta in cui è scritta | "To Coda ⊕" sopra il rigo, allineato a destra; il testo si può cambiare: `{to_coda: al ⊕}` |
| `{fine}` | alla **fine** della battuta | "Fine" a destra; la battuta riceve la **doppia stanghetta** |
| `{dc}`, `{dc: al Fine}`, `{dc: al Coda}` | alla **fine** della battuta | "D.C." seguito dal valore così come è scritto |
| `{ds}`, `{ds: al Coda}`, `{ds: al Fine}` | alla **fine** della battuta | "D.S." seguito dal valore |

- **Quale battuta**: i segni d'inizio (`segno`, `coda`) valgono per la battuta che segue, come `{volta}`. Quelli di fine valgono per la battuta **in cui sono scritti** (`| [D7] {to_coda} |`); scritti subito dopo una stanghetta, su riga propria o in fondo alla riga, per la **battuta precedente** (`| [D7] | {ds: al Coda}`). Nelle righe senza stanghette contano la posizione fra gli accordi: dopo un accordo → fine della battuta in cui quell'accordo finisce; prima di un accordo → inizio della battuta in cui comincia.
- **Resa**: i segni d'inizio stanno a sinistra della battuta (dopo il segno di ritornello), le indicazioni di fine allineate a destra sulla stanghetta (a sinistra dell'eventuale `x3` del ritornello), in grassetto nel font delle etichette del tema. Più indicazioni sulla stessa battuta si affiancano. **Altezza**: se la riga non ha testo cantato, case di volta né battute notate, i segni stanno **appena sopra il rigo**, nello spazio che altrimenti occuperebbe il testo (la riga cresce di soli 4 pt); altrimenti hanno una **corsia** propria di 21 pt sopra testo e case di volta.
- **Richiami** (`{ref}`): le copie non ripetono segni né righe di testo, che restano nella sezione originale.
- **Diagnostica**: warning per un segno di fine prima di qualsiasi battuta, per un `{segno}`/`{coda}` a fine sezione (nessuna battuta lo segue).
- Il brano **non viene "srotolato"**: i segni sono indicazioni per chi suona, come sulla carta.

**Righe di testo** `{text: …}` (su riga propria, **dentro una sezione**): una riga di testo libero nello spartito, nel punto in cui è scritta (indicazioni d'esecuzione, note per i musicisti). Prima della prima battuta → sotto il titolo della sezione; fra due righe musicali → la riga seguente comincia dopo il testo (a capo forzato); dopo l'ultima battuta → in fondo alla sezione. Testo a tutta larghezza, a capo automatico, nel font delle note del tema (10,5 pt); resta sulla stessa pagina della riga che lo segue. Fuori da una sezione → warning, ignorata. Non si traspone. Diversa da `{comment}` e dalle righe `#`, che non vengono stampate.

Esempi: `src/examples/segno_e_coda.chs` (D.S. al Coda, solo sigle: segni bassi), `src/examples/segni_con_testo.chs` (D.S. al Coda con testo cantato: segni sopra il testo) e `src/examples/da_capo_al_fine.chs` (D.C. al Fine).

### 2.9 Richiami (`ref`)

```
{ref: Etichetta}
{ref: Etichetta x2}
{ref: Etichetta | nota}
{ref: chorus x2 | tutti insieme}
```

- Ripete una sezione **già definita più sopra** (non si può richiamare una sezione futura → warning).
- Ricerca: prima per **etichetta** (case-insensitive), poi per **tipo** (prima sezione di quel tipo).
- `xN` ripete la sezione N volte di seguito; l'intestazione mostra `×N`.
- Il testo dopo `|` è una **nota** mostrata accanto all'intestazione, in corsivo grigio, preceduta da "reprise".
- **Trasposizione automatica**: se la tonalità corrente è diversa da quella in cui la sezione è stata scritta, il richiamo viene trasposto (es. ultima strofa un semitono sopra con una sola riga).
- La sezione richiamata conserva ritornelli, doppie stanghette e cambi di tempo interni; un eventuale cambio di tonalità/tempo pendente si applica alla sua prima battuta.
- Nel PDF il richiamo è sempre **espanso** (tutte le battute). Nell'app sarà commutabile espanso/compatto (§7).

### 2.10 Impaginazione dal sorgente

| Direttiva | Effetto |
|---|---|
| `{bars_per_line: N}` **dentro** una sezione | N battute per riga solo per quella sezione. |
| `{bars_per_line: N}` **fuori** da sezioni | N battute per riga da quel punto in poi. |
| `{bars_per_line}` (senza valore) | Torna al valore di configurazione. |
| `{br}` in linea | La battuta in cui compare **inizia una nuova riga**; il conteggio riparte. |

Gli a capo del file sorgente **non** determinano gli a capo del rendering: conta solo il numero di battute per riga (configurazione → direttive → `{br}`).

### 2.11 Diagnostica

Il parser non si ferma mai: produce sempre un risultato e una lista di **warning** con numero di riga. Casi segnalati:

- battuta più lunga del metro;
- durata non valida o non multipla di 0,5;
- accordo non riconosciuto;
- direttiva sconosciuta; `end_of_` senza `start_of_` corrispondente; sezione non chiusa;
- `ref` a sezione inesistente o successiva;
- tonalità o metro non validi;
- musica fuori da una sezione; battuta incompleta in modalità implicita.

### 2.12 Zone notate (MusicXML)

In alcuni punti, tipicamente intro, riff, parti strumentali o il tema, il pentagramma può contenere **note vere** invece delle sole sigle. Ci sono due modi, che si possono usare anche nello stesso brano: scriverle in un qualsiasi editor di partiture (MuseScore, Sibelius, Finale, Dorico…), esportarle in **MusicXML** e richiamarle dal sorgente (questa sezione), oppure **scriverle direttamente nel `.chs`** con una notazione testuale (§2.12b).

```
{start_of_intro: Intro}
{musicxml: blues_intro_riff.musicxml}            ← tutte le misure del file
{end_of_intro}

{start_of_outro: Coda}
{musicxml: blues_intro_riff.musicxml | 3-4}      ← solo le misure 3–4
| [F7#9:1] [/] |                                 ← si può proseguire con battute normali
{end_of_outro}
```

| Regola | Dettaglio |
|---|---|
| Sintassi | `{musicxml: percorso}` oppure `{musicxml: percorso \| N-M}` (intervallo di misure, anche una sola: `\| 5`). Su riga propria, dentro una sezione. |
| Percorso | Relativo alla cartella del file `.chs`. Formati: `.musicxml` / `.xml` (non compresso) e `.mxl` (compresso). |
| Cosa viene letto | **Prima parte** (`part`), **voce 1**: note, pause (anche di misura intera), accordi verticali, punti, legature di valore, travature (`beam` 1 e 2), **gruppi irregolari/terzine** (`time-modification` + `tuplet`), **ritornelli** (`barline/repeat` forward/backward, con `times`), **casse di volta** (`barline/ending` start/stop/discontinue), **sigle** (`harmony`, tradotte nella sintassi `.chs`, es. `dominant` → `7`, `half-diminished` → `m7b5`, gradi alterati → `b9`, `#11`), **testo** (`lyric` 1, con trattino per le sillabe spezzate). |
| Cosa viene ignorato | Altre parti e voci, abbellimenti, dinamiche, articolazioni, segni D.S./Coda, chiavi diverse da quella di violino (vedi §10). |
| Integrazione | Ogni misura del file diventa **una battuta** del brano: partecipa alla griglia, a `bars_per_line`, ai `{ref}` e alla trasposizione come le altre. Le sigle del file diventano gli accordi della battuta. |
| Metro | Se il metro del MusicXML è diverso da quello corrente, diventa un cambio di tempo (§2.8). |
| Tonalità | La tonalità resta quella del `.chs` (`{key}`); se l'armatura del file è diversa viene segnalato un warning. Le alterazioni vengono **ricalcolate** rispetto all'armatura del brano. |
| Trasposizione | Le note vengono trasposte come gli accordi e scritte con l'ortografia della tonalità di arrivo (es. in Mi♭: F♯ → E♮, A♭ → G♭). |
| Diagnostica | File mancante o non valido, misura di durata diversa dal metro, armatura diversa → warning con numero di riga. |

Nell'app i file MusicXML si **vedono** in una tab accanto al brano ma **non si modificano** (dalla 0.43): per cambiare quelle battute si convertono in note scritte nel `.chs` (§2.12b, *Conversione di un brano*) con il pulsante *Converti in note nel brano* (§8.2). Il riferimento `{musicxml: …}` resta comunque valido: i brani esistenti non cambiano.

### 2.12b Note scritte nel `.chs`

> Dalla versione 0.38 (modulo `notes.py`, esempio `examples/note_nel_chs.chs`). È un'**alternativa** al MusicXML (§2.12), che resta: si possono usare tutte e due, anche nello stesso brano.

**Perché.** Le zone notate sono di solito poche battute (intro, riff, un tema) dentro un brano fatto soprattutto di griglia di accordi, e si scrivono al computer **copiandole da uno spartito**. Con il MusicXML servono un editor di partiture e un secondo file per ogni zona, e una battuta occupa decine di righe di XML. Qui le note si scrivono **nel `.chs`, come le battute di accordi**, con l'anteprima dal vivo accanto per controllare.

**Esempio** (un riff di sei battute in 4/4; nell'ultima riga `@` fissa l'ottava: il do acuto, poi il si bemolle sotto il rigo, e le note seguenti ripartono da lì):

```
{start_of_intro: Intro}
{start_of_notes}
| [Gm7] G8 Bb D F [C7] A G E C | [Am7] C E G B [D7] C# A 3(F E D) |
| [Gm7] D4. C8 [C7] E Eb D C | [F7] F2- F4 R4 |
| [F7] C@5/4 A F D | [Bb7] Bb@3/8 D F Ab C Bb Ab F |
{end_of_notes}
{end_of_intro}
```

Con il testo cantato (una riga `w:` sotto la riga di note):

```
{start_of_notes}
| [F7] D2 Ab | [Bb7] C4 A F A |
w: Blues, blues del lu- ne- dì
{end_of_notes}
```

#### Blocco

| Regola | Dettaglio |
|---|---|
| Delimitatori | `{start_of_notes}` … `{end_of_notes}`, su righe proprie, **dentro una sezione** (come `{musicxml}`). Stessa convenzione dei blocchi di ChordPro (`start_of_abc`). |
| Righe | Dentro il blocco ogni riga che inizia con una stanghetta è una **riga di battute** con le stesse stanghette e ripetizioni della modalità esplicita (§2.5, §2.7: `|` `||` `|:` `:|` `:| xN`, `{volta: N}`). Le righe `w:` sono il testo (vedi sotto); righe vuote e commenti `#` come altrove; `{time}` e `{key}` su riga propria cambiano metro e tonalità come in §2.8. |
| Battute | Ogni battuta del blocco diventa **una battuta notata** del brano, esattamente come una misura MusicXML (§2.12, *Integrazione*): partecipa alla griglia, a `bars_per_line`, ai `{ref}` e alla trasposizione. Una battuta con soli accordi e nessuna nota è una battuta normale a sigle. |
| Accordi | `[Gm7]` come nel resto del `.chs` (§2.4, anche con segni ritmici e annotazioni, §2.4b), **subito prima della nota** su cui cade: la sigla si mette sopra quella nota. Durate `:n` qui non servono e danno un warning. Per un cambio d'accordo durante una nota tenuta si spezza la nota con una legatura: `G2- [C7] G2`. |

#### Note

| Elemento | Sintassi | Esempi |
|---|---|---|
| Nome | Lettera `A`–`G` come negli accordi (anche minuscola). | `G` `c` |
| Alterazione | `#` diesis, `b` bemolle, `##` / `bb` doppie, `n` bequadro esplicito. **Si scrive sempre l'altezza reale**, anche quando è nell'armatura: in Fa maggiore il si bemolle è `Bb`. | `Bb` `F#` `Bn` |
| Ottava | **Relativa**: ogni nota va all'ottava più vicina alla nota precedente (entro una quarta, contando i nomi delle note e non le alterazioni). `'` sale di un'ottava rispetto a quella scelta, `,` scende (ripetibili: `''`). La prima nota del blocco, se non ha `@`, è la più vicina al **Si centrale** del rigo (B4): fra il Fa sotto il rigo e il Mi sopra. In un accordo verticale conta la prima nota. | `C'` `G,` |
| Ottava assoluta | **Facoltativa**: `@` e il numero d'ottava, con il do centrale = `C4` (notazione scientifica; l'ottava cambia al do: `B@3` è il si appena sotto `C@4`). Vale su qualsiasi nota, anche la prima del blocco; le note seguenti tornano relative a partire da quella. Non si combina con `'` o `,` sulla stessa nota (warning). Si usa `@` e non un numero attaccato perché il numero dopo la nota è la durata (`G4` = sol da un quarto). | `C@5` `Bb@3` `F#@4` |
| Durata | **Figura**: `1` semibreve, `2` minima, `4` semiminima, `8` croma, `16` semicroma, `32` biscroma; `.` o `..` per il punto. **Si scrive solo quando cambia**: una nota senza durata ha quella della nota precedente (all'inizio del blocco `4`). | `G8 Bb D F` = quattro crome; `D4.` |
| Pausa | `R` più la durata; `R*` = pausa di battuta intera (in qualunque metro). | `R4` `R8.` `R*` |
| Legatura di valore | `-` subito dopo la nota la lega alla seguente (stessa altezza, anche nella battuta dopo e oltre l'a capo). | `F2- F4` |
| Corda (tablatura) | `~N` in fondo alla nota la suona sulla corda N (numerazione della chitarra: 1 = la più acuta); nei gruppi `< >` dopo ogni nota. Solo per la tablatura (§4.8b). | `A4~3` `<C~5 E~4 G~3>2` |
| Accordo verticale | Note fra `< >`, durata dopo la parentesi. | `<C E G>2` |
| Gruppo irregolare | `3( … )` terzina (3 nel tempo di 2); in generale `N:M( … )`, N note nel tempo di M. Dentro, le figure sono quelle scritte. | `3(F8 E D)` `5:4(C16 D E F G)` |
| Travature | Automatiche, per movimento (semiminima puntata nei tempi composti, 6/8 9/8 12/8); in 4/4 quattro crome semplici sulla stessa mezza battuta si uniscono, come le scrive un editor di partiture. Pause e note da un quarto in su interrompono la travatura. (È l'unica differenza visibile con gli esempi MusicXML, che uniscono le crome a coppie.) | |

Ordine degli elementi di una nota: nome, alterazione, ottava (`'` `,` oppure `@N`), durata, punto, legatura, corda (`F#'8.-~2`). **Dopo `@N` la durata si separa con `/`**, perché il numero d'ottava e quello della durata non si confondano: `C@5/2-` è il do acuto, minima, legato; senza `@` la durata segue direttamente: `C2-`.

Separatori: spazi fra le note (gli accordi `[…]` possono stare attaccati alla nota: `[C7]A`).

#### Testo cantato (`w:`)

- Una riga `w:` subito dopo una riga di note ne contiene il testo: **una sillaba per nota**, separate da spazi; una sillaba che finisce con `-` continua nella seguente (`lu- ne- dì`, disegnate con il trattino come nel MusicXML).
- Le sillabe vanno alle note in ordine, **saltando pause e note legate** alla precedente; `_` salta una nota (la sillaba precedente si prolunga, melisma); `|` nella riga `w:` riallinea alla battuta seguente (le note rimaste senza sillaba restano senza).
- Il testo si disegna sotto il pentagramma come quello delle battute MusicXML (§4.8).

#### Resa, tonalità, trasposizione

- Il risultato è lo **stesso modello delle battute MusicXML** (`Notation` con le `Note`, §3): impaginazione, PDF e schermo non cambiano (§4.8). Le alterazioni mostrate sono **ricalcolate per battuta rispetto all'armatura** (`♯ ♭ ♮` solo quando servono): scrivere `Bb` in Fa non disegna nessun bemolle, scrivere `B` (o `Bn`) disegna il bequadro.
- **Trasposizione**: le note si traspongono come quelle MusicXML, con l'ortografia della tonalità di arrivo (§5).

#### Diagnostica (warning con numero di riga)

- Battuta di durata diversa dal metro ("measure 2: 3.5 beats in 4/4").
- **Nota scritta senza alterazione che l'armatura altera** (in Fa: `B` invece di `Bb`): warning, perché copiando da uno spartito è l'errore più facile; se il bequadro è voluto si scrive `Bn` e il warning sparisce.
- Elemento non riconosciuto, legatura fra note di altezza diversa, gruppo irregolare non chiuso, sillabe in più rispetto alle note, blocco non chiuso o fuori da una sezione, durata `:n` su un accordo dentro il blocco.

#### App e strumenti

- **Editor**: evidenziazione di note, durate, pause, legature e righe `w:`; `{start_of_notes}` fra i suggerimenti, con il blocco vuoto da completare.
- **Convertitore**: `notes.to_notes_text(misure, tonalità)` scrive il blocco `{start_of_notes}` di misure MusicXML (note, accordi, pause, legature, terzine, ritornelli, volte, testo, corda `~N`; `@N` solo dove un salto lo richiede); rileggendolo si riottengono le stesse note (test). Così è stato scritto `note_nel_chs.chs` da `blues_con_melodia.chs`.
- **Conversione di un brano** (`library.convert_musicxml(sorgente, file, cartella, nota)`, pulsante *Converti in note nel brano* nell'app, §8.2): ogni riga `{musicxml: file}` / `{musicxml: file | N-M}` del sorgente diventa un blocco `{start_of_notes}` nella tonalità in vigore in quel punto (ultimo `{key}` prima della riga), preceduto da `{time: n/d}` dove il file cambia tempo (un blocco per tratto con lo stesso tempo). La riga del riferimento **resta sopra il blocco come commento** (`# {musicxml: file}  (convertito in note qui sotto)`), per traccia; le righe già commentate non si toccano e il file MusicXML non viene modificato né cancellato. Dopo la conversione il brano viene riletto e confrontato con l'originale (note, accordi, tempi, ritornelli e volte battuta per battuta): il risultato dice se è identico. Si perdono solo i dati che le note scritte non hanno: il tasto imposto della tablatura (resta la corda) e le travature del file (ricalcolate, §2.12b *Travature*). Da fare: un comando della riga di comando; eventuale esportazione inversa verso MusicXML.
- Esempio `src/examples/note_nel_chs.chs`: lo stesso brano di `blues_con_melodia.chs` con le zone notate scritte nel `.chs`; i test controllano che le note siano identiche a quelle lette dai MusicXML.

#### Compatibilità

- È un'**aggiunta** al formato `v1` (§2.14): i brani esistenti, con o senza MusicXML, non cambiano significato e non serve convertirli.
- Un brano che usa il blocco, aperto con una versione dell'app precedente alla 0.38 (verificato): gli **accordi e la griglia si leggono**, ma ogni blocco diventa una **sezione in più chiamata "Notes"** (quella che lo contiene resta vuota), le note compaiono come testo cantato sotto le battute e ci sono dei warning (sezione non chiusa). Il file non si rovina; aggiornando l'app si vede giusto. Con la libreria sincronizzata conviene aggiornare tutti i dispositivi prima di usarlo.

#### Scelte

Durate come figure; ottava relativa (prima nota vicina al Si centrale) con l'ottava assoluta `@N` facoltativa e la durata dopo `/`; alterazioni sempre scritte, anche quelle in armatura, con `n` per il bequadro esplicito; blocco `{start_of_notes}` … `{end_of_notes}`; testo su riga `w:`; `R*` per la pausa di battuta intera; travature automatiche; MusicXML che resta come alternativa.

### 2.13 Esempio completo

Vedi `examples/amazing_grace.chs` (3/4, modulazione G → Ab, ritornello, `ref` trasposto, stop) e `examples/blues_del_lunedi.chs` (4/4 jazz, modalità implicita, mezzi movimenti, cambio di tempo, `x3`, `{br}`, testo troncato).

### 2.14 Versione del formato e compatibilità

```
# commenti e righe vuote possono precedere la direttiva
{format: v1}
{title: …}
```

| Regola | Dettaglio |
|---|---|
| Sintassi | `{format: vN}` (`N` intero ≥ 1; si accetta anche il solo numero, `{format: 1}`, e la `v` maiuscola). Si scrive `vN`. |
| Posizione | **Prima direttiva** del file: prima possono esserci solo commenti e righe vuote. Più avanti vale comunque, con un warning. |
| Assente | Il file è in formato **v1** (tutti i file scritti prima della versione 0.11). |
| Valore non valido | Warning, il file si legge come v1. |
| Versione corrente | **v1**. Esempi, modello di "Nuovo brano" e importazione da chordsheet.com scrivono `{format: v1}`. |

**Quando cambia il numero.** Solo con una modifica **distruttiva**: una sintassi esistente cambia significato o viene tolta. Le **aggiunte** (una nuova direttiva, un nuovo simbolo prima non valido) restano nella stessa versione: un programma più vecchio le segnala come direttiva sconosciuta e disegna il resto.

**Un parser per versione.** Ogni formato ha il proprio parser (`formats/v1.py`, `formats/v2.py`, …), congelato quando esce il formato successivo; tutti producono lo stesso modello `Song`, quindi impaginazione e backend non dipendono dal formato. Il registro `formats/__init__.py` (`CURRENT`, `PARSERS`) legge `{format}` e passa il testo al parser giusto; `Song.format` riporta la versione dichiarata.

**File più recenti del programma** (es. `{format: v3}` con un programma che arriva a v2): warning in prima posizione ("format v3 is newer than this version…") e lettura **al meglio** con il parser più recente disponibile. L'app chiede conferma prima di salvarli, perché le parti non capite potrebbero perdersi.

**Conversione.** `UPGRADES[n]` riscrive un sorgente dal formato n al formato n+1; `upgrade()` li applica in catena fino a `CURRENT` e aggiorna (o aggiunge) `{format}`. I file più recenti del programma non vengono mai toccati. Riga di comando: `--format-info` (formato di ogni file) e `--upgrade` (riscrive i file nel formato corrente). App: pulsante *Aggiorna al formato vN* sotto l'editor, visibile se il file è in un formato precedente o non dichiara il formato. Con la sola v1 la catena è vuota e la conversione aggiunge soltanto `{format: v1}`; il meccanismo è provato nei test con un finto formato v2.

```
{title: Amazing Grace}
{key: G}
{time: 3/4}
{tempo: 80}

{start_of_intro: Intro}
|: [G] | [C] | [G] | [D7] :|
{end_of_intro}

{start_of_verse: Strofa 1}
| [G]A-ma-zing | grace, how | [C]sweet the | [G]sound, that |
...
{end_of_verse}

{key: Ab}
{ref: Strofa 1 | ultima strofa, un semitono sopra}

{start_of_outro: Finale}
|: [Ab]A-men | [Db] :| x3
| [Ab:1] [/] |
{end_of_outro}
```

---

## 3. Modello dati

```
Song
 ├─ meta: {title, subtitle, artist, key, time, tempo, capo, bar_width}
 ├─ sections: [Section]
 └─ warnings: [str]

Section
 ├─ kind, label, key (tonalità in cui è scritta)
 ├─ bars: [Bar]
 ├─ bars_per_line: int | null
 ├─ is_ref, times, note        (per i richiami)

Bar
 ├─ notation: Notation | null  (zona notata da MusicXML: lista di Note)
 ├─ num, den                   (metro; beats = num*4/den)
 ├─ key                        (tonalità corrente)
 ├─ events: [Event]
 ├─ time_change, key_change, prev_key
 ├─ double_after, break_before
 ├─ repeat_start, repeat_end (0 = nessuno, N = volte)
 └─ volta ("1." | "1., 2." | null), volta_end ("hook" | "open" | null)

Note (solo battute notate)
 ├─ step, alter, octave        (step null = pausa)
 ├─ start, dur, type, dots     (in quarti)
 ├─ chord (nota sovrapposta), tie_start, tie_stop
 ├─ tuplet (actual, normal) | null, tuplet_start, tuplet_stop
 ├─ beams {1: begin|continue|end|…, 2: …}
 └─ lyric

Event
 ├─ chord: str | null | "/"    (null = continuazione)
 ├─ start, dur                 (in movimenti, risolti)
 └─ lyric: str
```

I richiami sono **espansi nel modello** (le battute sono copiate e trasposte); `is_ref`/`times`/`note` servono solo alla presentazione.

---

## 4. Rendering "staff" (PDF) — specifica visiva

Obiettivo: un lead sheet leggibile sul leggio, con **accordi in primo piano** e tutto il resto in secondo piano.

### 4.0 Temi grafici

Il layout (§4.1–4.6) è lo stesso per tutti i temi; cambiano font, colori e alcuni dettagli tipografici.

| | **`realbook`** *(default)* | `clean` |
|---|---|---|
| Ispirazione | Real Book manoscritto | Lead sheet tipografico pulito |
| Testo, titolo, accordi, etichette | **Petaluma Script** (scrittura a mano) | DejaVu Sans / Bold |
| Simboli musicali (chiave, alterazioni, metro, `%`, ♩) | **Petaluma** (font SMuFL a mano) | FreeSerif (Unicode) + DejaVu Bold |
| Titolo | A sinistra, 26 pt in grassetto | A sinistra, bold 20 pt |
| Etichette di sezione | **Box pieno arrotondato** blu `#0066CC`, testo **bianco in grassetto** | Box pieno arrotondato blu `#0066CC`, testo bianco in grassetto |
| Accordi | 17 pt **in grassetto** (contorno del glifo ripassato: Petaluma Script non ha un peso bold); **estensioni in apice** (§4.7) | Bold 13,5 pt, tutto sulla linea |
| `%` | Simbolo di ripetizione battuta SMuFL (`repeat1Bar`) | `%` bold |
| Pentagramma | Linee grigie 0,75 pt, simboli grigio scuro, stanghette 1,2 pt | Linee grigio chiaro 0,6 pt |

In entrambi i temi accordi e testo sono quasi neri, mentre pentagramma, chiave, armatura e metro restano **in grigio** per far risaltare gli accordi.

### 4.1 Pagina

- Formato A4 (opzione Letter), margini 42 pt, impaginazione automatica su più pagine.
- **Intestazione — solo nella prima pagina.** Le pagine successive contengono solo lo spartito e il piè di pagina.
  - sinistra: **titolo allineato a sinistra** (grassetto, dimensione secondo il tema); sotto, in grigio, `sottotitolo - artista`;
  - destra, riga 1: `Key G` (le alterazioni come ♯/♭);
  - destra, riga 2: `3/4 · ♩ = 80` (+ `Capo N` se presente);
  - linea sottile grigia sotto l'intestazione.
- **Piè di pagina**: `Titolo — p. N`, centrato, grigio.
- Una sezione non inizia in fondo alla pagina se non c'è spazio per l'intestazione **e** almeno una riga.

### 4.2 Riga (dall'alto in basso)

1. **Testo** — piccolo (8,6 pt, grigio scuro), appena sopra il pentagramma, allineato all'inizio dell'evento.
2. **Pentagramma** — 5 linee **grigio chiaro**, con:
   - **chiave di violino** a inizio riga (grigio);
   - **armatura** della tonalità corrente su **ogni** riga (grigio);
   - **metro** solo sulla prima riga del brano e dove cambia (grigio, bold);
   - stanghette in grigio medio.
3. **Accordi** — **neri, centrati verticalmente sul pentagramma** (dimensione secondo il tema, §4.0), su un fondino bianco che interrompe le linee del rigo; allineati a sinistra all'inizio del loro movimento.

**Spazio fra le righe** (`row_spacing`): l'altezza di una riga è quella del contenuto più lo spazio libero sotto il pentagramma (≈ 19,6 pt al normale); `row_spacing` moltiplica quello spazio libero: `compact` 0,75, `normal` 1, `wide` 1,3, `extra` 1,6, o una percentuale fra 50% e 300%. Lo spazio che serve a note, testo sotto le battute notate, volte e segni si aggiunge sempre per intero, quindi anche al minimo nulla si sovrappone. Globale: impostazione dell'app / `--row-spacing`; per brano: `{row_spacing}` nell'intestazione, che vince. Non cambia lo spazio prima dei titoli di sezione.

Colori di riferimento (tema `clean`): accordi/testo quasi nero `#0F0F0F`, simboli del rigo `#8C8C8C`, linee del rigo `#B8B8B8`, box delle etichette di sezione `#0066CC`. Tema `realbook`: simboli del rigo `#6B6B6B`, linee `#9E9E9E`. Box delle etichette in entrambi i temi: `#0066CC`.

### 4.3 Battute e larghezze

Parametro **`bar_width`**:

| Valore | Comportamento |
|---|---|
| `uniform` *(default)* | **Tutte le battute hanno la stessa larghezza**, calcolata sulla riga con il maggior numero di battute del brano (o sul `bars_per_line` più alto). Le righe con meno battute lasciano spazio vuoto a destra. Anche lo spazio di testata (chiave + armatura + metro) è uniforme → **le stanghette sono allineate in colonna** su tutto il brano. |
| `fit` | Ogni riga **piena** occupa tutta la larghezza: quella con `bars_per_line` battute e quella che va a capo perché la battuta seguente non ci sta. Dentro la riga la larghezza è proporzionale ai movimenti (una battuta in 4/4 è più larga di una in 3/4), ma nessuna battuta scende sotto lo spazio che le serve: le battute affollate tengono il loro, le altre si dividono il resto. Si va a capo solo quando lo spazio **necessario** delle battute non entra nella riga. L'ultima riga di una sezione e quelle interrotte da `{br}` o da una volta tengono la larghezza di una riga piena e lasciano spazio a destra. |

**Tre livelli**, vince il più specifico:

1. **globale**: l'opzione dell'app (*Impostazioni*, o *Griglia*/*Riempi* nella barra sopra lo spartito) o `--bar-width` della riga di comando;
2. **brano**: `{bar_width: …}` nell'intestazione;
3. **sezione**: `{bar_width: …}` dentro una sezione (anche dopo il suo testo `{text}`), solo per quella sezione; un `{ref}` la mantiene. Valore diverso da `uniform`/`fit` → warning.

Le sezioni `uniform` condividono **la stessa griglia** (larghezza di battuta e spazio di testata calcolati solo su di loro), quindi restano allineate in colonna fra loro anche con sezioni `fit` in mezzo.

Regole comuni:

- **Una sola dimensione di carattere per battuta**: tutti gli accordi di una battuta usano la stessa dimensione, la più grande (max 13,5 pt) a cui ognuno entra nel proprio spazio (dal suo movimento al prossimo accordo o alla stanghetta), con un minimo di 9 pt. Mai accordi di dimensioni diverse affiancati.
- **Battuta affollata** (es. 4 accordi, uno per movimento): se gli accordi non entrano a **11 pt** (`chord_fit_size`):
  - `uniform`: la battuta occupa **2 (o più) slot** della griglia, cioè il doppio della larghezza standard. La griglia resta allineata in colonna e la riga va a capo prima se gli slot superano `bars_per_line`.
  - `fit`: la battuta prende lo spazio che le serve togliendolo alle altre della riga; la riga va a capo prima solo se la somma degli spazi necessari supera la pagina (prima della 0.39.1 bastava una battuta affollata per mandare a capo l'ultima, soprattutto nel tema `clean`).
- Gli accordi **non si sovrappongono mai**: quando lo spazio manca la battuta cresce, non si comprime.
- **Testo troppo lungo** per il proprio spazio (fino al prossimo evento o alla stanghetta): viene **troncato con "…"**.

### 4.4 Simboli dentro la battuta

| Situazione | Rendering |
|---|---|
| Inizio di un accordo | Sigla dell'accordo al suo movimento. |
| Accordo che prosegue nei movimenti successivi | Rigo vuoto (nessuna barra di movimento). |
| Battuta senza accordi (continuazione) | **`%`** grande, centrato nella battuta. |
| Stop `[/]` | **`/`** nero al movimento in cui inizia lo stop. |
| Cambio di tonalità a metà riga | Doppia stanghetta + bequadri di cortesia + nuova armatura all'inizio della battuta. |
| Cambio di tempo a metà riga | Nuovo metro all'inizio della battuta. |

### 4.5 Stanghette

| Caso | Disegno |
|---|---|
| Normale | Linea sottile. |
| `\|\|` o prima di un cambio di tonalità | Doppia linea sottile. |
| Fine brano | Sottile + spessa. |
| `\|:` | Spessa + sottile + due puntini (negli spazi 2 e 3), a inizio battuta. |
| `:\|` | Due puntini + sottile + spessa, a fine battuta; con N ≥ 3 → **`xN`** bold sopra. |
| Casse di volta | Parentesi sopra il rigo (§2.7), valgono sia per il `.chs` sia per il MusicXML. |

### 4.6 Intestazioni di sezione

Etichetta a sinistra in un **box a colore pieno con angoli arrotondati** (raggio 4 pt, margine interno 7 pt) e **testo bianco in grassetto**, per farla risaltare a colpo d'occhio sul leggio. Colore del box: parametro `label_colors` (vedi sotto). Per i richiami: `Etichetta  xN` nel box + "reprise - nota" in grigio accanto. Anche l'indicazione `xN` dei ritornelli è in grassetto.

**Colore dei box (`label_colors`)**

| Valore | Effetto |
|---|---|
| `theme` *(default)* | **Blu `#0066CC`** per tutti i box (default di entrambi i temi; contrasto con il bianco 5,6:1). |
| `#RRGGBB` | Un colore fisso per tutti i box (es. `#1F3A5F` blu notte, `#8B1E3F` bordeaux, `#0F5C5C` verde petrolio). |
| `by_type` | **Un colore per tipo di sezione**, per riconoscere la forma del brano a colpo d'occhio (tabella seguente). |

| Gruppo | Tipi di sezione (anche in italiano) | Colore |
|---|---|---|
| Strofa | `verse`, `strofa` | Blu notte `#1F3A5F` |
| Ritornello | `chorus`, `ritornello`, `refrain` | Bordeaux `#8B1E3F` |
| Bridge | `bridge`, `inciso`, `prechorus` | Verde petrolio `#0F5C5C` |
| Strumentale | `instrumental`, `solo`, `assolo`, `interlude`, `interludio` | Ocra scuro `#8A5300` |
| Cornice | `intro`, `outro`, `coda`, `ending`, `finale` e tipi non riconosciuti | Antracite `#3A3A42` |

**Colori personalizzati**: `{section_colors: intro=#3366ff, verse=#33cc66, chorus=#ff9900, bridge=#ff33cc}` nel file. Le chiavi possono essere l'etichetta di una sezione (`Ritornello`), il suo tipo (`chorus`, `solo`…) o il gruppo della tabella (`verse`, `chorus`, `bridge`, `instrumental`, `frame`); vale la prima che corrisponde, nell'ordine etichetta → tipo → gruppo. Le sezioni non elencate usano `label_colors`.

**Colore del testo nei box**: bianco, salvo sui colori chiari (es. `#ff9900`, `#33cc66`) dove il bianco avrebbe un contrasto inferiore a 3:1: lì il testo diventa quasi nero, per restare leggibile.

I colori della tabella `by_type` garantiscono un contrasto ≥ 4,5:1 con il testo bianco. I richiami (`ref`) usano il colore della sezione richiamata. Impostabile da CLI (`--label-colors`) o nel file (`{label_colors: by_type}`).

### 4.7 Grafica delle sigle (tema `realbook`)

Come nei Real Book, la sigla ha una gerarchia visiva:

| Parte | Rendering | Esempio |
|---|---|---|
| Lettera della radice | Dimensione piena, sulla linea | **C** |
| Alterazione della radice | 72 %, rialzata | B♭ |
| `m` del minore (o `-` in modalità jazz) | Sulla linea (80 % / 100 %) | Am, A- |
| Resto della qualità (7, maj7, 7♭9, sus4, 13…) | **Apice**: 62 %, rialzato | C + maj7 in apice, D + 7♭9 in apice |
| Basso `/X` | 85 %, sulla linea | Em7/D (7 in apice) |

Le alterazioni dentro la qualità (`b9`, `#11`) diventano ♭ e ♯.

**Sigle standard (default, `chord_symbols = text`)**: la sigla è resa come scritta, con la sola sostituzione tipografica di `b`/`#` con ♭/♯ (es. `C7b5` → C + 7♭5 in apice, `Bbmaj7` → B♭ + maj7 in apice).

**Simboli jazz** (solo su richiesta, opzione `chord_symbols = jazz`):

| Scritto | Reso |
|---|---|
| `maj7`, `ma7`, `M7` | Δ7 |
| `m7`, `min7`, `m` | -7, - |
| `m7b5` | ø7 |
| `dim`, `dim7` | °, °7 |

La sostituzione riguarda solo la grafica: il file sorgente non cambia.

---

### 4.8 Battute notate (zone MusicXML)

Nelle battute notate il pentagramma ospita le note, quindi la disposizione verticale cambia:

| Elemento | Posizione / resa |
|---|---|
| Sigle | **Sopra il pentagramma**, alla posizione orizzontale del loro movimento, nello stesso stile delle altre (grassetto, apici). **Tutte le sigle di una riga stanno sulla stessa linea**: la linea è sopra la nota (o gambo, travatura, cifra di terzina) più alta dell'intera riga, mai più bassa di 10 pt sopra il rigo. |
| Note | Nere, glifi Petaluma (scritti a mano): teste piene/vuote, gambi (in su sotto la terza linea, in giù sopra), code di croma/semicroma, **travature** dritte con pendenza limitata e gambo minimo di 2,75 spazi, seconda travatura per le semicrome. |
| Alterazioni | Ricalcolate per battuta rispetto all'armatura: si mostra ♯ ♭ ♮ solo quando servono; valgono fino a fine battuta. |
| Terzine e gruppi irregolari | Cifra (glifo SMuFL a mano) centrata sul gruppo, dal lato dei gambi: sopra/sotto la travatura se il gruppo è tutto sotto una sola travatura, altrimenti con **parentesi quadra** interrotta dalla cifra (es. terzina di semiminime). La spaziatura usa le durate reali. |
| Altri segni | Punti di valore, tagli addizionali (in grigio come il rigo), pause, pausa di misura centrata, **legature di valore** (anche tra battute; se attraversano l'a capo, l'arco arriva a fine riga e riparte dalla nota successiva). |
| Testo | **Sotto il pentagramma**, centrato sulla nota (convenzione dei lead sheet con melodia); come le sigle, **una sola linea per riga**, sotto la nota più grave dell'intera riga. |
| Spaziatura | Una colonna per ogni attacco di nota o di sigla, larghezza crescente con la durata (∝ durata^0,6) più spazio per alterazioni e punti. |
| Larghezza battuta | Calcolata dal contenuto: in modalità `uniform` una battuta fitta occupa **più slot** della griglia (come le battute con molti accordi, §4.3). |
| Altezza riga | Le righe con battute notate si allungano solo quanto serve: spazio sopra per le sigle e le note acute, sotto per il testo e le note gravi. |

Le battute notate e quelle a sole sigle possono stare sulla stessa riga.

### 4.8b Tablatura per chitarra

Per chi suona la chitarra e non legge il pentagramma, le battute notate (MusicXML o note scritte nel `.chs`) si possono mostrare in tre modi, opzione **`notation`**:

| Valore | Resa | Ritmo |
|---|---|---|
| `staff` *(default)* | il pentagramma, come sempre | sul pentagramma |
| `both` | il pentagramma e, sotto (dopo il testo cantato), la **tablatura**: sei linee (1ª corda in alto), "TAB" a inizio riga, il numero del tasto sulla corda, **nella stessa colonna della nota** | sul pentagramma; nella tablatura solo i numeri |
| `tab` | la tablatura **al posto del pentagramma** nelle battute notate (le battute di sole sigle della stessa riga restano sul pentagramma); "TAB" e metro al posto di chiave e armatura | **sotto i numeri**: gambi (più corti per le minime, nessuno per le semibrevi), travature piatte (doppie per le semicrome), codette, punti, pause sulle linee, cifra dei gruppi irregolari; il testo cantato sotto il ritmo |

Tre livelli come per `bar_width`: opzione globale (*Impostazioni › Battute notate*, selettore **Pentagramma / Entrambi / Tablatura** sopra lo spartito, `--notation`), `{notation}` nell'intestazione del brano, `{notation}` dentro una sezione (anche con `{ref}`). Il ritmo non si scrive mai a parte: viene dalle note.

**Diteggiatura** (`tab.py`): ogni nota si può suonare in più punti; corda e tasto si scelgono per tutto il passaggio insieme (righe di battute notate consecutive di una sezione), come **cammino di costo minimo** (programmazione dinamica): costano i tasti tastati (una corda a vuoto non impegna un dito), i tasti alti (oltre il 7°), gli spostamenti della mano fra una nota e l'altra (molto oltre 4 tasti), i cambi di corda; le note sullo stesso gambo vanno su corde diverse entro un'apertura di 4 tasti. Una nota legata alla precedente ne ripete corda e tasto, scritta fra parentesi `(3)`. Esempi tarati nei test: la scala di Do dal do centrale in prima posizione, gli accordi aperti di Do e Sol.

- **Ottava**: la nota scritta è letta come notazione per chitarra (la chitarra suona un'ottava sotto): corde a vuoto Mi3 La3 Re4 Sol4 Si4 Mi5 scritti, accordatura standard, fino al 20° tasto. Una nota fuori portata si sposta di ottave, con un warning ("out of the guitar's range"); note sullo stesso gambo impossibili insieme (due sulla stessa corda) → warning.
- **Capotasto**: con `{capo: N}` i tasti si contano dal capotasto (0 = capotasto).
- **Trasposizione**: la tablatura si calcola dopo la trasposizione.
- **Correzioni manuali** (dalla 0.42), dove la scelta automatica non è quella voluta:
  - `{tab_position: N}`: la mano attorno al tasto N (da N−1 a N+4) per le note che seguono, fino a fine sezione o al prossimo `{tab_position}` (`auto` per tornare alla scelta automatica); vale per le note scritte nel `.chs` e per le zone MusicXML che seguono. Fuori dalla finestra si paga molto, una corda a vuoto da una posizione alta un po';
  - `~N` su una nota: quella corda (1 = la più acuta); se la nota non sta su quella corda, warning e scelta automatica.
- **Accordature** (`{tuning}`): con nome (`standard`, `drop D`, `double drop D`, `DADGAD`, `open G`, `open D`, `open E`, `half step down`, `bass` e `bass 5` scritti un'ottava sopra come la chitarra, `ukulele` G C E A rientrante) o con le corde a vuoto dalla più grave (`D A D G B E`, `DADGBE`, con `#`/`b`: ogni corda più acuta della precedente, la prima vicino al Mi grave). La tablatura ha tante linee quante corde; con un'accordatura diversa dalla standard, a inizio riga i **nomi delle corde a vuoto** (in bemolli se l'accordatura ha Mi♭, La♭ o Si♭) al posto di "TAB".
- **MusicXML**: corda e tasto delle parti per chitarra (`notations/technical/string` e `fret`, come li esporta MuseScore) si usano così come sono; un tasto che non corrisponde alla nota viene ignorato (resta la corda). La conversione in note `.chs` li riporta come `~N`.

---

## 5. Trasposizione

- Si traspone di **N semitoni** l'intero brano: tonalità di intestazione, ogni cambio di tonalità, ogni accordo (radice e basso). Le modulazioni mantengono il loro intervallo.
- **Ortografia** delle note decisa dalla tonalità di arrivo: tonalità con bemolli → nomi bemolle (`Bb`, `Eb`…); con diesis → nomi diesis; Do/La minore → `C Db D Eb E F F# G Ab A Bb B`.
- Scelta della tonalità enarmonica: quella con meno alterazioni (a parità, i bemolli: `Gb` invece di `F#`).
- La qualità dell'accordo non viene modificata (`m7b5`, `7#9`…).
- Se la trasposizione è 0, gli accordi restano **esattamente** come scritti.

---

## 6. Configurazione

Ordine di precedenza (vince l'ultimo): **default → configurazione (CLI / impostazioni app) → direttive nel file → `{br}` puntuale**.

| Parametro | Default | CLI | Direttiva file |
|---|---|---|---|
| Battute per riga | `4` | `--bars-per-line N` | `{bars_per_line: N}` |
| Larghezza battute | `uniform` | `--bar-width uniform\|fit` | `{bar_width: fit}` (anche per sezione) |
| Spazio fra le righe | `normal` | `--row-spacing compact\|normal\|wide\|extra\|N%` | `{row_spacing: wide}` |
| Battute notate | `staff` | `--notation staff\|both\|tab` | `{notation: both}` (anche per sezione) |
| Trasposizione | `0` | `-t / --transpose N` | — |
| Formato carta | `A4` | `--paper A4\|Letter` | — |
| Tema grafico | `realbook` | `--theme realbook\|clean` | — |
| Simboli accordi | `text` | `--chord-symbols text\|jazz` | — |
| Colore box sezioni | `theme` | `--label-colors theme\|by_type\|#RRGGBB` | `{label_colors: by_type}` |

Parametri di stile: spazio del rigo 5,6 pt e altezza riga 62 pt (classe `Style`); dimensioni dei caratteri per tema (classe `Theme`): `realbook` accordi 17 pt, `chord_fit_size` 13, minimo 11, testo 9,5 pt; `clean` accordi 13,5 pt, `chord_fit_size` 11, minimo 9, testo 8,6 pt. `chord_fit_size` è la soglia sotto la quale una battuta occupa più slot invece di rimpicciolire ancora; tra due accordi resta sempre almeno ~7 pt di spazio.

---

## 7. Architettura del motore (tre strati) e strumento a riga di comando

Un **unico motore Python** serve la riga di comando, il PDF e l'app (desktop, iPad, Android). È diviso in tre strati; ogni strato dipende solo da quelli sopra:

| Strato | Moduli (`src/modernsheet/`) | Cosa fa | Dipendenze |
|---|---|---|---|
| **1. Parser e modello** | `theory.py`, `model.py`, `musicxml.py`, `parser.py` (ingresso), `formats/` (registro delle versioni e un parser per versione, §2.14) | `.chs` (+ MusicXML) → `Song` | solo libreria standard |
| **2. Impaginazione** | `layout.py`, `fonts.py`, `display.py` | `Song` → `DisplayList`: pagine di operazioni di disegno (linee, rettangoli, cerchi, tracciati, testi) in punti PDF | `fontTools` (metriche dei font) |
| **3. Backend** | `pdf.py` (reportlab), `flet_view.py` (canvas Flet), `svg.py` (anteprime), `screen.py` (conversione in coordinate schermo, condivisa da Flet e SVG) | riproducono la `DisplayList` senza prendere decisioni di impaginazione | reportlab / flet |

Regole che tengono insieme gli strati:

- L'impaginazione **misura il testo con le stesse metriche** (`fonts.py`, larghezze in 1/1000 em arrotondate come reportlab) usate da tutti i backend: schermo e PDF mostrano esattamente la stessa pagina.
- La `DisplayList` è l'unico contratto tra impaginazione e backend (formato documentato in `display.py`). Un nuovo backend (es. nativo Swift/Kotlin, web) deve solo saper disegnare quelle cinque operazioni.
- Sullo schermo ogni testo è posizionato come riquadro alto 1 em (`height = 1.0`) e la linea di base cade a `ascent / (ascent − descent)` del font (metriche `hhea`, o `OS/2 typo` se il font lo richiede).
- I font stanno in `src/assets/fonts/` e sono gli stessi file per motore, PDF e app.
- `library.py` (solo libreria standard, fuori dai tre strati) serve all'app: scansione di una cartella di brani con sottocartelle, ricerca, nomi dei file per i brani nuovi, numero di riga dei warning (§8.2). Allo stesso modo `settings.py` (impostazioni dell'app, JSON), `i18n.py` (testi dell'interfaccia in italiano e inglese) e `syntax.py` (evidenziazione e completamento nell'editor).

**Requisiti**: Python ≥ 3.10, `reportlab`, `fonttools` (più `flet` per l'app). Font inclusi: **Petaluma** e **Petaluma Script** di Steinberg (SIL Open Font License, convertiti da OTF a TTF) per il tema `realbook`; FreeSerif e DejaVu Sans per il tema `clean` e come ripiego per i caratteri mancanti. Il renderer sceglie il font carattere per carattere: se un simbolo non è nel font del tema (es. ♩, Δ, °) usa il glifo SMuFL di Petaluma o, in ultima istanza, DejaVu.

```
python modernsheet_cli.py song.chs                       # → song.pdf   (oppure: cd src && python -m modernsheet …)
python modernsheet_cli.py a.chs b.chs -o out/            # più file in una cartella
python modernsheet_cli.py song.chs -t -2                 # un tono sotto
python modernsheet_cli.py song.chs --bar-width fit --bars-per-line 6
python modernsheet_cli.py song.chs --chord-symbols jazz  # CΔ7, C-7, Cø7, C°7
python modernsheet_cli.py song.chs --theme clean         # stile tipografico pulito
python modernsheet_cli.py song.chs --check               # solo validazione (exit 1 se ci sono warning)
python modernsheet_cli.py *.chs --format-info            # versione del formato di ogni file (§2.14)
python modernsheet_cli.py *.chs --upgrade                # riscrive i file nel formato corrente
```

Uso come libreria:

```python
from modernsheet import parse, layout, render_pdf
song = parse(open("song.chs").read(), transpose=2, base_dir=".")   # base_dir: dove cercare i MusicXML
dl = layout(song, theme="realbook", bar_width="uniform")            # DisplayList
render_pdf(song, "song.pdf")                                        # oppure modernsheet.pdf.write_pdf(dl, …)
```

**Test di regressione** (`tests/`, `pytest`; un file per area: `test_engine.py` motore e impaginazione, `test_notes.py`, `test_tab.py`, `test_library.py`, `test_editor.py`, `test_importers.py`, `test_formats.py`, `test_sync.py`, con gli aiuti comuni in `helpers.py`): tutti gli esempi si leggono senza warning, si impaginano e producono PDF in tre combinazioni di opzioni, le operazioni a schermo restano nella pagina, le forme Flet si costruiscono, la trasposizione di un'ottava è un'identità, la libreria trova i brani nelle sottocartelle (saltando quelli nascosti, tenendo le cartelle vuote), i nomi delle nuove cartelle sono puliti e senza conflitti, la ricerca ignora maiuscole e accenti, il modello di brano nuovo si legge senza warning; versioni del formato: lettura di `{format}` (posizione, valori non validi), file più recenti letti con warning, conversione, e un finto formato v2 distruttivo registrato nel test per provare che i file v1 mantengono il loro significato e che `upgrade()` li converte; tag normalizzati; indice della libreria (rilegge solo i file cambiati, toglie quelli spariti, si ricostruisce se rovinato); ricerca per artista e `#tag`; ordinamenti con i dati mancanti in fondo; date `{created}`/`{modified}` (lettura, valori non validi, scrittura al loro posto o dopo l'intestazione mai prima di `{format}`, *Salva con nome* = creato adesso, ordinamento con i dati mancanti in fondo, indice); importazione da un account chordsheet.com contro un finto sito (login con token, credenziali sbagliate, elenco delle schede, sorgenti, fogli vuoti, `import_warn`, brani già importati, la password solo nel corpo del POST); importazione di un `.chs` nella libreria (nome libero, MusicXML copiati accanto e riferimenti riscritti, riuso dei file identici, riferimenti mancanti senza cartella); rinomina delle cartelle (nome pulito, nome già usato, cartella principale, sole maiuscole, riferimenti MusicXML riscritti) e cartelle svuotate tolte dalla sincronizzazione su entrambi i lati (cartella e Google Drive; `.DS_Store` ignorato, file non sincronizzati e PDF su Drive le tengono); libreria di una nuova installazione (solo `examples/`, creata una volta) e unione che copia solo i file mancanti senza doppioni; nome della nuova tonalità sotto il pentagramma ai cambi (a metà riga e a inizio riga, nessuno senza cambi); volta successiva più lunga della 1ª (pentagramma fino all'ultima battuta); ricerca con `A*`, `*xyz`, `*testo*`, `&`, `|` (precedenza, accenti, caratteri iniziali, compatibilità con parole e `#tag`); gruppi A–Z della libreria (iniziale con accenti e caratteri speciali, gruppo "#" in fondo, verso decrescente, per artista); annotazioni sugli accordi (lettura, disegno sopra l'accordo o sopra il testo, `[% "…"]`) e correzioni dell'importatore trovate sui brani reali (annotazioni attaccate e staccate, `*` sui movimenti, rientri, `x4` staccato, finali attaccati, palette); segni ritmici e accordi opzionali (lettura di tutte le forme, trasposizione, warning, disegno in entrambi i temi, legatura che continua sulla riga seguente, importazione da chordsheet.com); segni di navigazione (battuta giusta nelle righe con e senza stanghette, Fine con doppia stanghetta, warning, richiami senza segni) e righe di testo (prima, fra e dopo le righe), disegnati in entrambi i temi, appena sopra il rigo nelle righe senza testo e in una corsia propria altrimenti; importazione da chordsheet.com di `$ o O fine D.C. D.S.` e `- testo`; eliminazione di un brano (`.chs` più i MusicXML citati, tranne quelli condivisi con altri brani, fuori dalla libreria o mancanti; cestino della sincronizzazione senza sovrascritture; propagata agli altri dispositivi). Editor: parti modificate (righe e caratteri, righe cancellate, divisione dei pezzi colorati senza perdite), annulla/ripristina (una parola per passo, a capo, pausa, cancellazioni consecutive, modifica nuova che cancella i ripristini, annulla del campo di testo riconosciuto). Tab dell'editor: citazioni MusicXML di un brano, anteprima con il testo di un MusicXML passato al parser, evidenziazione XML; conversione dei MusicXML in note (tutti gli esempi: note identiche, citazioni commentate e non più lette, nessun warning; intervallo di misure, cambio di tempo, rientro, citazioni già commentate lasciate stare, file mancante); tablatura, seconda fase (posizione della mano, corda imposta e impossibile, accordi con corde imposte, drop D, nomi delle corde, basso a 4 linee, accordature scritte e non valide, corda e tasto dal MusicXML e nella conversione); tablatura (scala in prima posizione, accordi aperti, legature, pause, capotasto, note fuori portata e impossibili insieme con warning, tre modalità disegnate, livelli opzione/brano/sezione, pentagramma invariato, altezza delle righe, esempio senza warning); spazio fra le righe (nomi e percentuali, valori non validi, brano che vince sull'opzione, pagine in più con più spazio, impostazioni); righe `fit` (a capo solo se serve, righe chiuse per mancanza di spazio fino al margine, mai una battuta più stretta del necessario); larghezza delle battute per sezione (sezione che vince su brano e app, griglia condivisa dalle sezioni `uniform`, `{ref}`, valore non valido); note scritte nel `.chs` (altezze, ottave relative e `@N`, figure mantenute, punto, legature, terzine, accordi verticali, pause e `R*`, accordi sulla nota, battute di soli accordi, ritornelli e volte, testo `w:` con `_` e `|`, warning: armatura, durata della battuta, `@N` senza `/`, legature, blocco non chiuso; trasposizione; travature per movimento, mezza battuta in 4/4, tempi composti; conversione dai MusicXML di esempio e ritorno identico; esempio identico a quello MusicXML; evidenziazione e completamento); indentazione XML (contenuto identico, stabile, un elemento per riga, errore con la riga). Sincronizzazione con un remoto in memoria e due "dispositivi": file nuovi nei due sensi, modifiche, lavoro offline recuperato senza coda, cancellazioni nel cestino, segnaposto iCloud mai trattati come cancellazioni, conflitti con entrambe le versioni conservate, modifica che vince su cancellazione, file occupati rimandati, provider cartella. Google Drive contro un finto server Drive: device flow (attesa, conferma), token privato e rinnovato dopo un 401, cartella dell'app riusata dal secondo dispositivo, sottocartelle, conflitti, cestino di Drive, offline, accesso revocato, lettura della configurazione OAuth, cartella rinominata sul sito (ricreata, file ricaricati, niente nel cestino), nome di cartella diverso = libreria diversa; remoto svuotato non trattato come cancellazione. Al passaggio a tre strati i PDF sono stati confrontati pixel per pixel con quelli della versione monolitica: identici nel tema `realbook`, differenze di antialiasing trascurabili nel tema `clean`.

---

## 8. Fase 2 — App (Flet: iPad, Android, desktop)

### 8.1 Scelta tecnologica

**Flet** (Python + Flutter, v1.x): un solo codice Python per iPad, Android, macOS, Windows e Linux, che usa direttamente il motore (§7). L'interfaccia è disegnata da Flutter; la pagina è disegnata sul `Canvas` di Flet a partire dalla `DisplayList`. Alternative valutate: BeeWare/Toga (UI nativa, meno ricca), riscrittura del motore in Dart (app più leggera, ma due motori da tenere allineati), motore su server (escluso: sul palco serve funzionare offline).

### 8.2 App (`src/main.py`)

L'app ha tre schermate: libreria, editor e impostazioni.

**Libreria.** Mostra la **cartella dei brani** scelta nelle impostazioni (in sviluppo si può forzare con la variabile d'ambiente `MODERNSHEET_LIBRARY`). **Predefinita** (installazione nuova): una cartella **"Modern Sheet"** nei dati dell'app (`FLET_APP_STORAGE_DATA/Modern Sheet`), creata al primo avvio, che contiene **solo la sottocartella `examples/`** con una copia degli esempi inclusi (`src/examples/`, modificabili); i brani e le cartelle dell'utente vanno accanto. Senza cartella dati (casi eccezionali) si usano direttamente gli esempi inclusi. Gli esempi aggiunti nelle versioni successive non vengono copiati nelle librerie già create. **Unione con una libreria sincronizzata** (*Unisci* quando si attiva la sincronizzazione): prima si sincronizza, così arriva quello che il remoto ha già (per esempio la sua `examples/`); poi si copiano dalla libreria precedente **solo i file che mancano**, allo stesso percorso (`library.merge_into`). Così un secondo dispositivo collegato allo stesso Drive non duplica gli esempi né lascia file sparsi nella radice, e un esempio aggiornato nella nuova versione dell'app non crea copie "in conflitto". Se la cartella scelta non esiste più si torna a quella predefinita. La schermata mostra il contenuto di una cartella alla volta: prima le sottocartelle (con il numero di brani che contengono, sottocartelle comprese), poi i brani, ordinati per nome senza distinguere maiuscole e minuscole. Sotto la ricerca c'è il **percorso** (*breadcrumb*): un tasto **⬆** che apre la cartella superiore (disattivato nella cartella principale), poi 🏠 cartella principale › sottocartella › …; ogni parte tranne l'ultima (in grassetto, la cartella aperta) apre quella cartella. Durante una ricerca al suo posto compare "N risultati in …".

- Sono brani i file `.chs` (estensione senza distinzione di maiuscole). File e cartelle nascosti (che iniziano con `.`) sono ignorati. Le cartelle senza brani si vedono (una cartella appena creata è vuota); aprendone una compare "Cartella vuota: crea un brano o una sottocartella."
- **Due viste**, scelte con un pulsante e ricordate tra un avvio e l'altro:
  - **card** (predefinita): righe di schede larghe al più 300 px (tante colonne quante ne stanno, che si dividono la larghezza; ricalcolate quando la finestra smette di cambiare dimensione) e **alte tutte uguali** (236 px, così su iPad niente viene tagliato in basso). Ogni brano mostra il **titolo** in una **fascia blu** (`#0066CC`, lo stesso blu dei box di sezione) con testo bianco, fino a due righe, poi su una riga ciascuno l'**artista** (`artist`, altrimenti `composer`), **tonalità · tempo · ♩ = BPM** (solo i campi presenti; la tonalità con ♭/♯) e i **tag** come etichette `#tag` (quelli che non stanno si scorrono di lato). In fondo, in piccolo, il **nome del file** (quello su cui agiscono *Salva con nome* ed *Elimina*; distingue le copie con lo stesso titolo; durante una ricerca preceduto dalla cartella: "Google Drive › Jazz › file.chs") e sotto, una per riga, **sempre** le due **date**: "Creato 20 nov 2026" (solo la data) e "Modificato 23 nov 2026 10:24:59" (data e ora); per i brani mai salvati dall'app, senza `{created}`/`{modified}`, vengono dal file su disco (creazione, se il sistema la conserva, e modifica). Nella vista a elenco le stesse informazioni stanno nella riga sotto il titolo. **Brani con lo stesso titolo** fra quelli mostrati: il dato che li distingue è in **arancione** e in grassetto, cioè la data di modifica se è diversa per tutti, altrimenti la data di creazione, altrimenti il nome del file. Le cartelle sono schede color ambra con il numero di brani.
  - **elenco**: una riga per brano con titolo, poi artista · tonalità · tempo · BPM · nome del file, e i primi tag a destra.
- I dati delle schede vengono dalle direttive del file: il primo `title` (altrimenti il nome del file con `_` → spazio), `artist`/`composer`, la prima `key`, il primo `time`, `tempo`, tutti i `tags`.
- **Ricerca**: cerca sempre in **tutta la cartella dei brani** (quella delle impostazioni) e in tutte le sue sottocartelle, qualunque sia la cartella aperta, senza distinguere maiuscole, minuscole e accenti; un brano corrisponde se soddisfa **tutte** le parole: una parola normale deve comparire nel titolo, nell'artista, nei tag o nel percorso relativo (cartelle comprese); `#parola` deve essere **uno dei tag** (uguale, non contenuto). **Condizioni avanzate** (caratteri jolly): `A*` = il **titolo inizia** con "A"; `*xyz` = il **titolo finisce** con "xyz" (in entrambi i casi si ignorano i caratteri iniziali e finali che non sono lettere o cifre, come per i gruppi A–Z: `o*` trova "(Out here) on my own", `*ancora` trova "Ancora!"); `*testo*` = **contiene** "testo" (titolo, artista, tag o percorso, spazi compresi: `*hey jude*`); `&` = **e** (AND), `|` = **o** (OR), con `&` che lega più di `|`: `A* & #jazz | B*` = (inizia con A e ha il tag jazz) oppure inizia con B. Dentro una condizione normale gli spazi valgono ancora come AND. Il suggerimento nel campo riassume la sintassi, il tooltip la spiega per esteso. I risultati si aggiornano dopo una breve pausa nella digitazione (0,12 s) e si ridisegnano **solo i risultati**: barra di ricerca e percorso restano gli stessi controlli, così il campo non perde il focus. Le righe di card si ricostruiscono al ridimensionamento solo se cambiano colonne o larghezza delle card, non per i cambi di sola altezza (la tastiera a schermo di iPad/Android), che altrimenti chiuderebbero la tastiera a ogni tasto. Funzioni `library.parse_query` e `library.search`. Toccando un tag su una scheda si cercano i brani con quel tag. I risultati mostrano la cartella. Con del testo nel campo compare una **×** a destra, dentro il campo: la cancella e toglie il filtro.
- **Ordinamento** (menu accanto alla ricerca, verso crescente/decrescente, ricordati): titolo, artista, tonalità (Do, Do♯/Re♭ … Si; maggiore prima del minore), BPM, **ultima modifica** (`{modified}`, altrimenti la data del file), **data di creazione** (`{created}`, altrimenti la data di creazione del file). I brani senza quel dato vanno sempre in fondo; a parità, ordine per titolo e, fra brani con lo **stesso titolo**, prima il più recente (creato o salvato più di recente), in qualunque ordinamento e verso. Le cartelle restano in ordine alfabetico, prima dei brani.
- **Gruppi A–Z**: ordinando per **titolo** o per **artista**, i brani sono divisi per iniziale di quel campo, con un'intestazione a tutta larghezza ("A ────") prima di ogni gruppo, in card e in elenco. L'iniziale è la prima lettera A–Z del testo, senza distinguere maiuscole e accenti ("(Out here) on my own" → O, "È la luna" → E, "50 special" → S); senza lettere (o senza artista) → gruppo "#", sempre in fondo. In verso decrescente i gruppi vanno da Z ad A. Con gli altri ordinamenti (tonalità, BPM, date) niente gruppi. Le **cartelle** stanno sempre in cima, prima dei gruppi, in schede più basse (112 px). Funzioni `library.index_letter` e `library.group_by_letter`.
- **Indice**: per non rileggere tutti i file a ogni apertura, i dati delle schede sono salvati in un file JSON nella cartella dati dell'app (`FLET_APP_STORAGE_DATA/index/<hash del percorso della libreria>.json`, uno per cartella dei brani; non nella cartella dei brani, così non nascono conflitti se è sincronizzata tra dispositivi e funziona anche in sola lettura). Per ogni `.chs` (percorso relativo) contiene data di modifica e dimensione del file e i dati letti. A ogni lettura della libreria si controllano solo data e dimensione: si rileggono i file nuovi o cambiati, si tolgono quelli spariti, e l'indice si riscrive solo se è cambiato (scrittura atomica). Un indice mancante, rovinato o di una versione precedente (`INDEX_VERSION`) si ricostruisce; è solo una cache. La libreria si rilegge tornando dall'editor (quindi dopo un salvataggio) e con *Aggiorna*.
- **Nuovo brano**: chiede il titolo e crea `Titolo.chs` nella cartella aperta (nella cartella dei brani durante una ricerca) con un modello minimo (titolo, tonalità, tempo, una strofa di 4 battute); dal titolo si tolgono i caratteri non ammessi nei nomi dei file e, se il file esiste già, si aggiunge ` 2`, ` 3`, … Il brano si apre subito nell'editor.
- **Nuova cartella**: chiede il nome e crea una sottocartella della cartella aperta (della cartella principale durante una ricerca), poi la apre. Dal nome si tolgono i caratteri non ammessi e il punto iniziale (le cartelle nascoste non si vedrebbero); se esiste già un file o una cartella con quel nome si aggiunge ` 2`, ` 3`, … Nome vuoto: "Nuova cartella".
- **Importa file .chs** (icona nella barra in alto della libreria): sceglie un `.chs` e lo **copia nella libreria**, nella cartella aperta (nella principale durante una ricerca), poi lo apre dalla copia; l'originale non viene più toccato. Non sovrascrive mai: il brano prende un nome libero ("Nome 2.chs"…). I **MusicXML citati** vengono copiati **accanto al brano** e i riferimenti riscritti con il nome della copia (così `../comuni/riff.musicxml` diventa `riff.musicxml` e nulla finisce fuori dalla libreria); un MusicXML già presente con lo stesso nome e contenuto viene riusato, con contenuto diverso la copia prende un nome libero ("riff 2.musicxml"). Su iPad, Android e web il file arriva **senza la sua cartella**: i MusicXML citati non si possono copiare, i riferimenti restano come scritti e il messaggio li elenca. Con la libreria sincronizzata l'importazione parte subito verso il remoto. Funzione `library.import_song`. (Prima della 0.33 il pulsante *apriva* il file dov'era, fuori dalla libreria.)
- **Rinomina cartella**: menu **⋮** sulla scheda o sulla riga di ogni cartella → *Rinomina*. Il nome si pulisce come per *Nuova cartella*; sono rifiutati un nome vuoto e un nome già usato da un'altra cartella accanto (un cambio di sole maiuscole, `jazz` → `Jazz`, passa da un nome temporaneo, per i dischi che non distinguono le maiuscole). La cartella principale della libreria non si rinomina (il nome della cartella su Drive è un'impostazione). Il dialogo dice quanti brani contiene, avvisa se brani di **altre** cartelle citano MusicXML di questa (i loro riferimenti `{musicxml: …}` vengono **riscritti** con il nuovo percorso; quelli dei brani interni, relativi, restano validi) e, con la libreria sincronizzata, che la rinomina arriverà anche sul remoto e sugli altri dispositivi. La rinomina aspetta la fine di una sincronizzazione in corso e nessuna ne parte finché non è finita. Funzioni `library.rename_folder` e `library.outside_refs`.
- I pulsanti **Nuova cartella** e **Nuovo brano** stanno in basso a destra, uno accanto all'altro.
- La libreria si rilegge tornando dall'editor e con il pulsante *Aggiorna*.
- Restano disponibili l'apertura di un singolo `.chs` fuori dalla libreria e l'importazione da chordsheet.com (§9). Non c'è più un menu degli esempi: sono la libreria predefinita.

**Impostazioni** (icona ingranaggio nella libreria; salvate nelle preferenze dell'app, modulo `settings.py`):

| Voce | Valori | Default |
|---|---|---|
| Lingua | Italiano / English (`language` `it` / `en`): lingua dell'interfaccia | Italiano |
| Cartella dei brani | una cartella scelta con il selettore; pulsante per tornare agli esempi inclusi | esempi inclusi |
| Cartella per i PDF | cartella da cui parte il dialogo *Esporta PDF*; si può togliere | nessuna (decide il dialogo) |
| Formato | Real Book / Clean (`theme`) | Real Book |
| Larghezza delle battute | Griglia / Riempi (`bar_width` `uniform` / `fit`) | Griglia |
| Spazio fra le righe | Compatta / Normale / Ampia / Molto ampia (`row_spacing` `compact` / `normal` / `wide` / `extra`); un brano con `{row_spacing}` usa il suo | Normale |
| Battute notate | Pentagramma / Entrambi / Tablatura (`notation` `staff` / `both` / `tab`, §4.8b); anche nella barra sopra lo spartito, per il brano aperto | Pentagramma |
| Sigle degli accordi | Standard / Jazz (`chord_symbols` `text` / `jazz`) | Standard |
| Colori per sezione | sì / no (`label_colors` `by_type` / `theme`) | no |

**Lingua.** L'interfaccia è in **italiano** (predefinito) o **inglese**, scelta in *Impostazioni › Generale › Lingua* e salvata nelle preferenze (`language`); un valore sconosciuto torna all'italiano. Tutti i testi dell'app (menu, pulsanti, suggerimenti, dialoghi, messaggi, descrizioni del completamento) stanno nel catalogo `i18n.py`, una voce per testo con tutte le lingue (`tr(chiave, **valori)`, `tr_count` per singolare/plurale); i test controllano che ogni voce abbia tutte le lingue con gli stessi segnaposto e che ogni chiave usata dall'app esista. Cambiando lingua le schermate vengono ricostruite (dalle Impostazioni, quindi senza documenti aperti) e la lingua passa anche ai controlli di Flutter (`locale_configuration`). Seguono la lingua anche le etichette proposte per le sezioni nel completamento (`{start_of_verse: Strofa}` / `Verse`) e nel modello di "Nuovo brano". **Restano in inglese** i warning del parser (come nella riga di comando); restano in italiano le note di conversione dell'importazione da chordsheet.com e il contenuto degli esempi.

Le quattro opzioni di visualizzazione sono i **valori iniziali** di ogni brano aperto; nell'editor si cambiano per il singolo brano (senza salvarle). Le direttive nel file restano prioritarie (§6). Valori sconosciuti nelle preferenze tornano al default.

**Editor.** Aprendo un brano, a sinistra c'è il **sorgente** e a destra l'**anteprima** con le opzioni di visualizzazione.

- **Tab**: sopra l'editor una tab per il `.chs` (la prima, sempre presente) e **una per ogni file MusicXML citato** dal brano (`{musicxml: file}` su riga propria, in ordine di prima citazione, senza doppioni; percorsi relativi alla cartella del `.chs`, quindi solo per brani salvati su file; una citazione commentata con `#` non conta). Ogni tab mostra il nome del file; cambiando tab si ritrova la posizione di scorrimento.
  - Le tab si aggiornano **all'apertura, a ogni salvataggio e dopo una conversione**: un `{musicxml: …}` aggiunto al sorgente fa comparire la sua tab al salvataggio successivo (se è il primo MusicXML del brano la tab si apre subito); una citazione tolta fa sparire la tab.
  - **I MusicXML sono in sola lettura** (dalla 0.43). Scriverli a mano era scomodo e le zone notate si scrivono meglio nel `.chs` (§2.12b): la tab serve a **vedere** il file e a **convertirlo**. Il testo è mostrato **già indentato**, un elemento per riga con gli elementi di solo testo su una riga (`<step>C</step>`; `xml_syntax.format_xml`, che cambia solo lo spazio fra gli elementi; un file non ben formato si mostra com'è), con l'evidenziazione della sintassi; il file su disco non viene mai riscritto. Si può selezionare e copiare.
  - Sopra il testo una barra con *Sola lettura* e il pulsante **Converti in note nel brano**: dopo una conferma (che spiega cosa succede) scrive le battute del file nel `.chs` come blocchi `{start_of_notes}` al posto di ogni sua citazione, lasciando la citazione come commento per traccia (`library.convert_musicxml`, §2.12b); poi torna alla tab del `.chs` con il cursore sul commento, la tab del MusicXML sparisce (non è più citato) e un messaggio dice quante citazioni sono state convertite e se le note sono **identiche** a prima o se qualcosa è cambiato (da controllare nell'anteprima). Il brano risulta modificato: si salva, oppure si esce senza salvare per annullare. Il file MusicXML resta dov'era.
  - **File citato che non esiste**: tab "nome (mancante)" con un avviso (le sue battute non si vedono; scriverle come note nel brano). Non si crea più un MusicXML dall'app.
  - File compresso `.mxl`: non si mostra come testo, ma si può convertire; file illeggibile: la tab spiega il motivo.
  - **Salva** (⌘S / Ctrl+S) salva il `.chs`. (Fino alla 0.42 le tab MusicXML erano modificabili, con completamento, *Indenta*, *Comprimi/Espandi*, *Crea il file MusicXML* e anteprima dal testo non salvato: tutto tolto. Il motore accetta ancora `parse(…, files={percorso: testo})`.)
  - Toccando un warning si torna alla tab del `.chs` (i numeri di riga sono del sorgente); così anche *Aggiorna al formato*.
- Nelle tab MusicXML **evidenziazione** (modulo `xml_syntax.py`, stessi colori dell'editor): dichiarazioni `<?xml …?>`/`<!DOCTYPE …>` e commenti in grigio, nomi degli elementi in azzurro, attributi in viola, valori in arancio, entità (`&amp;`) in blu, `<` `>` `/` in grigio.

- Il sorgente è su **sfondo scuro con testo chiaro**, a spaziatura fissa (DejaVu Sans Mono incluso nell'app, così le metriche sono uguali su tutti i dispositivi), senza correzione automatica né virgolette tipografiche.
- **Evidenziazione della sintassi** (modulo `syntax.py`, solo libreria standard): commenti `#` in grigio corsivo; graffe in grigio; nomi delle direttive in viola, quelli di sezione (`start_of_…`, `end_of_…`) in azzurro, valori in arancio; accordi `[…]` in giallo con la durata `:n` in verde; stanghette e ripetizioni (`|`, `||`, `|:`, `:| xN`) in blu; il testo cantato in chiaro. Una `{` o `[` non ancora chiusa si colora fino a fine riga. Tecnica: un campo di testo con il testo trasparente sopra una copia colorata con lo stesso font e le stesse metriche; i due scorrono insieme. Dentro `{start_of_notes}` … `{end_of_notes}` (§2.12b) le note in verde acqua, durate in verde, pause in grigio, legature, terzine e stanghette in blu, `w:` in viola con il testo in chiaro; fra i suggerimenti `start_of_notes` (anche dentro una sezione) e, nel blocco aperto, prima `end_of_notes`.
- **Completamento delle direttive**: digitando `{` compare un elenco delle direttive vicino al cursore, filtrato dalle lettere scritte dopo la graffa (prima quelle che iniziano con le lettere, poi quelle che le contengono), con una breve descrizione. Dentro una sezione aperta il primo suggerimento è il suo `end_of_…` e le aperture di sezione spariscono. **Invio** o **Tab** inseriscono il suggerimento evidenziato, **↑/↓** lo cambiano, **Esc** chiude, un tocco ne sceglie uno. Il testo inserito chiude la graffa e seleziona il valore da scrivere (`{time: 4/4}` con `4/4` selezionato); `start_of_X` inserisce anche `{end_of_X}` due righe sotto, con l'etichetta selezionata. Se il nome è già seguito da `:` o `}` si completa solo il nome.

- **Parti modificate** (modulo `edits.py`, `changes` e `mark`): quello che è diverso dal testo **all'apertura o all'ultimo salvataggio** ha uno sfondo verde: verde scuro sulla parte non toccata di una riga cambiata, verde più acceso sui caratteri scritti o sostituiti (righe nuove comprese). Il confronto è per righe (`difflib`) e, dentro le righe cambiate, per caratteri; le righe solo cancellate non si possono mostrare (si recuperano con *Annulla*). Lo sfondo **sparisce al salvataggio** (anche *Salva con nome*), compresi i `{created}`/`{modified}` scritti dall'app; un brano nuovo o importato parte senza sfondo dal testo con cui si apre. Vale anche per le modifiche fatte dall'app (completamento, *Converti in note*, *Aggiorna al formato*). Tecnica: lo sfondo è sugli stessi pezzi colorati dell'evidenziazione, sotto il campo di testo trasparente.
- **Annulla / Ripristina** passo per passo (`edits.History`), con i pulsanti ↶ ↷ nella barra in alto (visibili con l'editor aperto, disattivati quando non c'è nulla da annullare o ripristinare) e da tastiera **⌘Z / Ctrl+Z** e **⌘⇧Z / Ctrl+⇧Z / Ctrl+Y**. Un passo è **una parola** scritta (lo spazio che segue una parola ne apre un altro), una serie di cancellazioni consecutive, un a capo, oppure una modifica dell'app (completamento, conversione, aggiornamento del formato); una pausa di più di 1 s o uno spostamento del cursore cominciano un passo nuovo. Annullare riporta il testo e il cursore dove la modifica era cominciata; una modifica nuova dopo un annullamento cancella i passi da ripristinare. Fino a 500 passi per brano, finché resta aperto; dopo il salvataggio si può ancora annullare (il testo torna diverso dal salvato e riprende lo sfondo). Il campo di testo ha anche un suo annulla interno (nella versione web ⌘Z arriva solo a lui): una modifica che riporta esattamente il testo di prima dell'ultimo passo è riconosciuta come quell'annullamento (`History.observe`), così le due cronologie non si contraddicono; quando il tasto arriva all'app, vale il suo annulla e quello del campo viene scartato. Una nuova versione arrivata dalla sincronizzazione azzera la cronologia.
- L'anteprima si ridisegna **dal vivo**, 0,35 s dopo l'ultima modifica; parser e impaginazione girano fuori dal thread dell'interfaccia. Se il motore va in errore su un sorgente a metà, resta l'ultima anteprima valida con il messaggio d'errore sopra.
- I **warning** del parser compaiono sotto l'editor; toccandone uno si seleziona la riga corrispondente.
- Il titolo in alto è quello del brano, preceduto da `●` se ci sono **modifiche non salvate**; sotto l'editor: percorso del file, numero di righe, stato.
- **Salva** (anche ⌘S / Ctrl+S) riscrive il file. Il pulsante è **disattivato** finché non c'è nulla da salvare e si **attiva diventando verde** (icona piena) appena si modifica il brano (lo stesso stato del "●" davanti al titolo); senza modifiche anche ⌘S non fa nulla. Un brano senza file (importato, nuovo) ha già qualcosa da salvare; **Salva con nome** ne crea uno nuovo. Per un brano della libreria (o un brano nuovo) chiede solo il **nome del file** in un dialogo dell'app e salva nella **stessa cartella** del brano (o nella cartella aperta, indicata sotto il nome come nel percorso della libreria: "In: Google Drive › Jazz"; lo stesso in *Nuovo brano* e *Nuova cartella*, mai il nome tecnico della copia locale, `library`), senza mai sovrascrivere (`library.new_song_path`: "Nome 2.chs"…): il nuovo file è subito nella libreria e i MusicXML citati con percorsi relativi restano validi. Il pulsante *Altra posizione…* apre il dialogo di sistema per salvare altrove; è l'unica via per i brani aperti da fuori la libreria. Motivo: con la libreria sincronizzata la cartella dei brani è la copia locale nei dati dell'app, che il dialogo di sistema (macOS) non apre in modo affidabile: il file finiva in un'altra cartella e non compariva nella libreria. Esempi e brani importati non hanno un file: *Salva* chiede dove salvarli.
- **Elimina brano** (cestino **rosso**, ultimo pulsante della barra; solo per i brani che hanno un file) elimina il `.chs` **e i MusicXML che cita** (letti dal brano salvato). Prima chiede conferma con un dialogo che mostra l'**elenco** dei file che verranno eliminati (percorsi relativi alla cartella del brano) e, sotto *Restano:*, i MusicXML citati che non vengono toccati, con il motivo: usati anche da un altro brano della libreria (elencato), fuori dalla libreria, non trovati. Seguono cosa succede dopo (vedi sotto) e l'avviso se ci sono modifiche non salvate; il pulsante *Elimina* è rosso. Con la libreria **sincronizzata** i file vanno nel cestino della sincronizzazione (`…/trash/AAAA-MM-GG/<percorso>`, come i file cancellati dalla sincronizzazione, senza sovrascrivere) e la sincronizzazione che parte subito dopo porta la cancellazione al remoto (cestino di Drive o cancellazione nella cartella) e da lì agli altri dispositivi (nei loro cestini); altrimenti i file sono cancellati definitivamente. Poi si torna alla libreria. Eccezione: eliminare gli **ultimi** file sincronizzati lascia il remoto vuoto, che per sicurezza non è una cancellazione (vedi *Remoto vuoto o ricreato*, §8.3b): gli altri dispositivi li ricaricano. Funzioni `library.delete_plan` (cosa si elimina e cosa resta) e `library.delete_song`.
- Tornando alla libreria, aprendo un altro brano o chiudendo la finestra (desktop) con modifiche non salvate, l'app chiede *Salva / Non salvare / Annulla*.
- **Vista e modifica.** Un brano si apre in modalità **vista**: solo lo spartito a tutta larghezza, con la barra delle opzioni (trasposizione, tema, griglia, sigle, colori). Nella barra in alto, dopo lo **schermo intero**, la **matita** apre l'editor accanto all'anteprima (modalità **modifica**); la stessa icona, diventata "lettura", lo richiude. *Nuovo brano* e l'importazione da chordsheet.com aprono direttamente in modifica; un clic su un warning apre l'editor alla riga giusta.
- **Schermo intero** (icona ⛶ nella barra in alto; uso sul palco): restano solo le pagine, senza barra in alto, opzioni ed editor; su desktop anche la finestra va a schermo intero. Per uscire c'è sempre il pulsante **"Esci da schermo intero"** in alto a destra, e il tasto **Esc**; tornare alla libreria o aprire l'editor da un warning esce comunque. Frecce, Pagina su/giù, spazio e pedaliera continuano a girare le pagine.
- Con il cursore nell'editor frecce e spazio servono al testo; il cambio pagina da tastiera e pedaliera funziona quando l'editor non ha il fuoco.

| Funzione | Stato |
|---|---|
| Libreria da una cartella con sottocartelle: navigazione, ricerca, nuovo brano | ✅ |
| Vista a card (titolo, artista, tonalità, tempo, BPM, tag), ricerca per artista e `#tag`, ordinamento, indice dei brani | ✅ |
| Editor del sorgente con anteprima dal vivo, salvataggio, avviso per modifiche non salvate | ✅ |
| Visualizzazione delle pagine a tutta larghezza, scorrimento verticale | ✅ |
| Esempi inclusi come cartella dei brani predefinita, apertura di un `.chs` dal dispositivo | ✅ |
| Impostazioni: cartella dei brani, cartella dei PDF, formato, griglia/riempi, sigle, colori per sezione | ✅ |
| Editor scuro con evidenziazione della sintassi e completamento delle direttive dopo `{` | ✅ |
| Trasposizione −/+ dal vivo | ✅ |
| Tema Real Book / Clean, griglia `uniform` / `fit`, simboli jazz, colori per sezione | ✅ |
| Avvisi del parser mostrati sopra lo spartito | ✅ |
| Cambio pagina da tastiera e **pedaliera Bluetooth** (Pagina giù/su, frecce, spazio) | ✅ (da provare con la pedaliera reale) |
| Esportazione PDF identica allo schermo | ✅ |
| Vista classica, richiami compatti, mappa del brano, setlist, autoscroll, tema scuro dell'intera app; nell'editor: completamento dei valori (tonalità, sezioni per `ref`), annulla/ripeti oltre a quello del campo di testo, rinomina/sposta/elimina brani | ⏳ prossimi passi |

### 8.3 Avvio e compilazione

```
pip install "flet[all]" reportlab fonttools       # oppure: uv sync
flet run                                          # app desktop, dalla cartella del progetto
python src/main.py                                # idem (es. debugger di VS Code): stessa cartella dati di flet run
flet run --ios | --android                        # anteprima sul dispositivo con l'app "Flet" dagli store
flet build ipa                                    # iPad/iPhone: serve un Mac con Xcode e un account Apple Developer
flet build apk | aab                              # Android: Flet scarica Flutter e l'Android SDK al primo build
flet build macos | windows | linux                # desktop
```

**Cartella dati in sviluppo.** `flet run` passa all'app la cartella dei dati (`FLET_APP_STORAGE_DATA` = `.flet/storage/data` nel progetto, fuori da git), dove stanno indice, copia locale sincronizzata e stato della sincronizzazione. Avviando `src/main.py` direttamente con Python la variabile mancherebbe: la sincronizzazione resterebbe spenta senza avvisi e la libreria sarebbe `src/examples`. Per questo, se manca ed è avviata dai sorgenti, l'app usa la stessa cartella di `flet run`.

`flet build macos` (provato) richiede Xcode completo e CocoaPods (`brew install cocoapods`); il `flutter` scaricato da Flet non serve nel PATH.

Configurazione in `pyproject.toml` (`[tool.flet]`): identificativo dell'app **`app.modernsheet`** (`org` e `bundle_id`, dal dominio modernsheet.app; fino alla 0.34 era il segnaposto `com.example.modernsheet`, quindi un'app compilata con la versione precedente usa una nuova cartella dati: impostazioni e copia locale della libreria si ricreano, i brani tornano dalla sincronizzazione). Gli asset (`src/assets/fonts`, `src/examples`) vengono inclusi nel pacchetto.

**Icona dell'app.** Disegno originale: `MS icon.jpeg` (1024×1024, chiave di violino e libro aperto con la griglia di un accordo, su un riquadro crema arrotondato). `python tools/make_icons.py` ne ricava in `src/assets/`:

| File | Uso (`flet build`) |
|---|---|
| `icon.png` | il logo su fondo **trasparente**: Flet lo adatta a ogni piattaforma; con `icon_background = "#F6F1E6"` (crema, `[tool.flet]`) diventa l'icona adattiva **Android** (logo nella zona sicura su fondo crema) e quella **macOS** (riquadro arrotondato Apple crema con ombra) |
| `icon_ios.png` | **iOS**: quadrato crema a tutto campo, opaco (l'App Store non accetta trasparenza), logo nelle proporzioni del disegno; gli angoli li arrotonda iOS |
| `icon_windows.png`, `icon_linux.png`, `icon_web.png` | **Windows, Linux, web**: il riquadro crema arrotondato del disegno (senza l'ombra), angoli trasparenti, usato così com'è |
| `icons/*.png` | anteprima con `flet run --ios \| --android`: icona nell'app *Flet* del dispositivo (vedi sotto) |
| `favicon.png`, `icon.ico` | scheda del browser (`flet run --web`); icona della finestra con `flet run` su **Windows** (su macOS, in sviluppo, il Dock mostra l'icona del client Flet: l'icona vera compare nell'app compilata) |

Cambiando il disegno: sostituire `MS icon.jpeg` e rilanciare lo script (se il logo si sposta, aggiornare `ART_BOX` e `CREAM` nello script e `icon_background`).

**Nome nell'anteprima su dispositivo.** Con `flet run --ios | --android` l'app è servita come pagina web e l'app *Flet* dello store mostra nome, descrizione e icona presi dal `manifest.json` della pagina. Flet usa `src/assets/manifest.json` al posto del suo (che direbbe "Flet"): nome *Modern Sheet*, descrizione, colori crema/blu. Le icone sono in `src/assets/icons/` con gli stessi nomi di quelle di Flet (`apple-touch-icon-192.png`, `icon-192/512.png`, `icon-maskable-192/512.png`), così le sostituiscono anche dove la pagina le cita direttamente: sono il quadrato crema **opaco** di `icon_ios.png` (gli angoli trasparenti sul dispositivo apparirebbero scuri), generate da `make_icons.py`. Il `<title>` della pagina resta "Flet": `flet run` non permette di cambiarlo, e copiare l'`index.html` di Flet negli asset si romperebbe al primo aggiornamento di Flet. Il manifest è scritto a mano.

### 8.3b Sincronizzazione della libreria (local-first)

Obiettivo: la stessa libreria su tutti i dispositivi, **funzionante anche senza rete**. L'app legge e scrive **sempre una cartella locale** (la "cache"); un motore di sincronizzazione la allinea a una copia remota quando questa è raggiungibile. Modulo `sync.py` (solo libreria standard).

**Nome precedente.** Fino alla 0.18 il progetto si chiamava *Chord Sheet*. Per compatibilità: le impostazioni salvate sotto la vecchia chiave (`chordsheet.settings`) vengono lette se manca quella nuova; le variabili `CHORDSHEET_LIBRARY`, `CHORDSHEET_GOOGLE_CLIENT_ID/SECRET` valgono ancora se mancano le `MODERNSHEET_*`; la cartella Drive "Chord Sheet" (predefinita fino alla 0.18) resta una scelta valida e mantiene la sua copia locale (`gdrive:<e-mail>`), mentre la nuova predefinita è "Modern Sheet".

**Fasi.** 1 (fatta): motore + provider **cartella** (una cartella esterna, tipicamente dentro iCloud Drive, Google Drive per desktop o Dropbox, il cui client porta i file sugli altri computer). 2 (fatta): provider **Google Drive** via API (funziona anche su iPad e Android), modulo `gdrive.py`. 3, se serve: **iCloud** nativo su iPad/iPhone (estensione Flutter, `flet build`).

**Google Drive** (`gdrive.py`, solo libreria standard: `urllib`):
- **Accesso** con il *device flow* OAuth 2.0 (client "TV e dispositivi con input limitato" del progetto Google Cloud dell'utente; configurazione nel README): *Impostazioni › Sincronizzazione › Google Drive › Collega* mostra un codice (con *Apri la pagina* e *Copia il codice*); su qualsiasi dispositivo si apre google.com/device e lo si inserisce; l'app attende la conferma (interrogazioni ogni 5 s, più rade se Google lo chiede) e poi chiede l'account (e-mail) per chiamare la libreria. Funziona uguale su macOS, Windows, Linux, iPad e Android, senza redirect né SDK nativi. *Scollega* cancella il token e ferma la sincronizzazione.
- **Ambito `drive.file`**: l'app vede solo i file creati da lei. Non richiede la verifica di sicurezza di Google; i file aggiunti a mano dal sito di Drive non sono visibili all'app.
- **Credenziali dell'app**: variabili `MODERNSHEET_GOOGLE_CLIENT_ID` / `MODERNSHEET_GOOGLE_CLIENT_SECRET`, oppure `src/google_client.json` (fuori da git, incluso nei pacchetti) o `google_client.json` nella cartella dati dell'app; formato `{"client_id", "client_secret"}` o quello scaricato da Google (`{"installed": {…}}`). Senza configurazione la voce Google Drive lo dice e non si può collegare.
- **Il client secret non è un segreto** (scelta consapevole): il device flow di Google lo richiede, quindi viaggia **dentro ogni app compilata** (desktop, APK) e chi la scarica può estrarlo; per le app installate Google stessa lo considera non riservato. Tenerlo fuori da git serve solo a non legarlo al codice sorgente. Chi lo estrae può presentarsi a Google come "Modern Sheet" e consumare la quota del progetto, ma **non può accedere ai dati di nessuno**: ogni utente deve accedere e dare il consenso, il permesso `drive.file` vede solo i file creati dall'app e il token resta sul dispositivo. Se ne vedi un abuso (Google Cloud Console › API e servizi › metriche), si rigenera il secret e si pubblica una nuova versione. Alternative valutate e scartate: accesso nativo Android/iOS senza secret (codice nativo, non disponibile in Flet, e solo per mobile), server che custodisce il secret (servizio da mantenere, utilizzabile da chiunque al posto del secret), client Google di ogni utente (troppo complicato).
- **Token**: il refresh token sta in `FLET_APP_STORAGE_DATA/google/token.json`, leggibile solo dall'utente (permessi 600); l'access token si rinnova da solo (anche su una risposta 401). Se l'accesso è revocato o scaduto la sincronizzazione si ferma con "Accesso a Google Drive scaduto o revocato: ricollega l'account" (non viene scambiato per assenza di rete).
- **Cartella su Drive**: *Impostazioni › Sincronizzazione › Google Drive › Cartella su Drive* (predefinita **Modern Sheet**; si conferma con Invio o uscendo dal campo; spazi in eccesso e `/` tolti, vuoto = predefinita). È una cartella della radice del Drive; **un nome diverso è un'altra libreria**, con la sua copia locale (`gdrive:<e-mail>:<cartella>`; con il nome predefinito la chiave resta `gdrive:<e-mail>` delle versioni precedenti). Cambiandola mentre l'account è collegato l'app chiede conferma e poi, come al collegamento, se aggiungere i brani della libreria attuale; la vecchia cartella resta com'è, su Drive e in locale. Gli altri dispositivi devono usare lo stesso nome per condividere la libreria.
- **Nel Drive**: la cartella scelta nella radice (creata se manca, ritrovata dagli altri dispositivi), con le sottocartelle della libreria (create quando serve). Revisione di un file = il suo **MD5** su Drive. Prima di sovrascrivere o cancellare si controlla che l'MD5 sia ancora quello atteso (altrimenti si rimanda). Le **cancellazioni** spostano il file nel **cestino di Drive**. Due file con lo stesso percorso: vale il più recente.
- La copia locale è per account (`sync/<hash di "gdrive:e-mail">/library`); nel percorso della libreria la cartella principale si chiama "Google Drive".
- **Verificato** con un vero account Google (progetto Google Cloud pubblicato, senza logo) nell'app macOS compilata con `flet build macos`; i test usano un finto server Drive.

**Impostazioni › Sincronizzazione › Cartella sincronizzata.** Scegliendo una cartella:
- la libreria diventa la **copia locale** nella cartella dati dell'app (`FLET_APP_STORAGE_DATA/sync/<hash del remoto>/library`, una per cartella remota, così cambiare remoto non mescola i file); nel percorso della libreria la cartella principale ha il nome della cartella sincronizzata; *Cartella dei brani* non si può cambiare finché la sincronizzazione è attiva;
- se la libreria attuale contiene brani l'app chiede se **aggiungerli** alla libreria sincronizzata (i file già presenti non vengono sovrascritti) o usare solo la cartella;
- *Interrompi la sincronizzazione* torna alla cartella dei brani precedente; la copia locale resta e viene riusata se si riseleziona la stessa cartella.
- Serve la cartella dati dell'app (`flet run` o app compilata); `MODERNSHEET_LIBRARY` disattiva la sincronizzazione.

**Cosa si sincronizza.** I file `.chs`, `.musicxml`, `.xml`, `.mxl` della libreria, sottocartelle comprese; non i file e le cartelle nascosti né altri tipi di file. Le cartelle vuote compaiono sugli altri dispositivi solo quando contengono un brano.

**Algoritmo** (per file, confronto a tre vie): contenuto locale attuale (hash SHA-1, ricalcolato solo se data o dimensione cambiano), revisione remota attuale, e stato dell'**ultima sincronizzazione riuscita** (manifesto JSON accanto alla copia locale: hash e revisione remota per file, ora dell'ultima sincronizzazione).

| Locale | Remoto | Azione |
|---|---|---|
| cambiato | invariato | carica (o cancella sul remoto se cancellato in locale) |
| invariato | cambiato | scarica (o sposta nel **cestino** locale se cancellato sul remoto) |
| cambiato | cambiato, contenuto diverso | **conflitto**: la versione remota prende il nome, quella locale diventa `Titolo (conflitto <dispositivo> AAAA-MM-GG HH-MM).chs` e viene caricata come file nuovo: nessuna modifica si perde |
| cambiato | cambiato, stesso contenuto | nessuna copia, si aggiorna solo il manifesto |
| modificato | cancellato (o viceversa) | **vince la modifica**: il file torna |
| nuovo | nuovo | come un conflitto (o nulla se identici) |

- **Remoto vuoto o ricreato**: se il remoto risulta vuoto, o la sua cartella è stata appena creata (es. rinominata o cancellata dal sito di Drive, e quindi ricreata dall'app), mentre l'ultima sincronizzazione conosceva dei file, **non** è una cancellazione di tutto: si riparte come con un remoto nuovo e i file locali vengono caricati di nuovo (messaggio "La cartella remota era vuota o nuova…"). Conseguenza voluta: cancellare **tutti** i brani su un dispositivo non si propaga agli altri (al primo giro li ricaricano).
- Se si chiede una sincronizzazione mentre ne è in corso un'altra (es. salvataggio durante la sincronizzazione automatica) viene eseguita subito dopo, non persa.
- **Offline**: se il remoto non è raggiungibile (per il provider cartella: la cartella non esiste, es. disco scollegato) non cambia nulla e l'indicatore lo segnala; il lavoro fatto nel frattempo non ha bisogno di una coda: alla sincronizzazione successiva risulta semplicemente "cambiato rispetto all'ultima volta".
- Le cancellazioni arrivate dal remoto spostano i file nel **cestino** (`…/trash/AAAA-MM-GG/…`), mai cancellati del tutto.
- **Cartelle svuotate**: la sincronizzazione lavora file per file, quindi una cartella rinominata (o svuotata) su un dispositivo arriva come "file cancellati + file nuovi". A fine giro le cartelle **rimaste vuote per colpa delle cancellazioni di questo giro** vengono tolte, dalla più profonda: in locale quelle svuotate da cancellazioni remote, sul remoto quelle svuotate da cancellazioni locali (cartella: `rmdir`; Google Drive: nel cestino di Drive, solo se Drive conferma che non contiene **nulla**, nemmeno file che l'app non sincronizza, come un PDF messo a mano). "Vuota" = nessun file a parte un `.DS_Store` del Finder; un segnaposto iCloud o un altro file la tiene. Le cartelle vuote create apposta (*Nuova cartella*) non vengono toccate. Se un altro dispositivo modifica offline un brano della cartella rinominata, al ritorno vince la modifica: il brano ricompare nella vecchia cartella (nessuna perdita). Rinominare una cartella grande costa una cancellazione e un caricamento per file (lo spostamento nativo di Drive è un'ottimizzazione possibile).
- Un caricamento che trova il remoto cambiato nel frattempo (revisione diversa da quella attesa) si rimanda alla sincronizzazione successiva, che lo tratta come conflitto se serve.
- Il provider cartella usa come revisione data di modifica e dimensione del file remoto.
- **File iCloud tolti dal disco**: su macOS meno recenti iCloud sostituisce un file "ottimizzato" con un segnaposto nascosto `.Titolo.chs.icloud`. Il provider cartella lo elenca come file **presente ma non disponibile** (mai come cancellato) e ne chiede il download (`brctl download`); finché non è leggibile il file resta com'è: se in locale non è cambiato si considera invariato, altrimenti si rimanda (nessuna copia scaricata, nessun caricamento sopra una versione che non si può leggere).

**Quando si sincronizza.** All'avvio, tornando alla libreria, dopo ogni salvataggio, ogni 5 minuti mentre l'app è aperta, e con **Sincronizza ora** (Impostazioni, o l'icona della nuvola nella barra della libreria). Si sincronizza in background. I file aperti nell'editor **con modifiche non salvate** non vengono toccati (li tratta la sincronizzazione dopo il salvataggio, eventualmente come conflitto); quelli aperti senza modifiche si ricaricano se ne arriva una versione nuova.

**Stato.** Icona nella barra della libreria (☁ fatto, nuvola sbarrata = non raggiungibile, avviso = conflitti o errori; il suggerimento dice l'ora dell'ultima sincronizzazione) e riga nelle Impostazioni. I conflitti vengono anche annunciati con un messaggio; le copie di conflitto si vedono e si cercano nella libreria come gli altri brani.

**Usare una cartella cloud senza sincronizzazione dell'app** (solo desktop): si può anche scegliere direttamente come *Cartella dei brani* una cartella di iCloud Drive / Google Drive per desktop. Funziona, ma offline dipende dal client del cloud: iCloud con "Ottimizza spazio Mac" può togliere i file dal disco, Google Drive in modalità "streaming" li scarica solo all'apertura (va scelto "rendi disponibile offline" / "mirroring"). Con la sincronizzazione dell'app la copia locale c'è sempre.

### 8.3c Sito, documentazione e pubblicazione

- **Repository GitHub**: licenza **GPL-3.0-or-later** (`LICENSE`, `pyproject.toml`); il `README.md` è la home del repository (funzioni, immagini, avvio rapido, struttura, sviluppo, configurazione di Google Drive). Fuori da git: `src/google_client.json`, `.flet/` (dati dell'app in sviluppo, compresa la copia della libreria sincronizzata), `out/`, `build/`.
- **Pubblicazione**: la cronologia di sviluppo (ramo locale `main`) non viene pubblicata. `tools/publish_github.sh [messaggio]` crea sul ramo locale `github` **un solo commit** con i file attuali di `main` (padre: la pubblicazione precedente; niente se non è cambiato nulla; rifiuta se ci sono modifiche non committate); poi `git push origin github:main`. Su GitHub si vede quindi una cronologia di versioni pubblicate.
- **App desktop scaricabili**: un'etichetta `v<versione>` (creata da `tools/publish_github.sh` sul commit pubblicato) fa partire `.github/workflows/release.yml`, che su macchine GitHub esegue `flet build` per **macOS** (universale arm64 + x86_64), **Windows** e **Linux** e allega a una *Release* `ModernSheet-macos.zip`, `ModernSheet-windows.zip`, `ModernSheet-linux.tar.gz` (nomi fissi: il sito usa i link `releases/latest/download/…`). La pagina Download mostra **versione e data** dell'ultima Release e, in ogni scheda, versione, data di caricamento e dimensione del suo file: le legge all'apertura da `api.github.com/repos/…/releases/latest` (`docs/assets/releases.js`, testo inserito come testo, mai come HTML); se GitHub non risponde quelle righe non compaiono. Il pulsante Android punta all'APK della Release quando c'è, altrimenti al link di riserva. Le app **non sono firmate**: la pagina Download spiega come aprirle (macOS: *clic destro › Apri*; Windows: SmartScreen *Esegui comunque*). Il client OAuth di Google arriva dal secret `GOOGLE_CLIENT_JSON`; senza, le app funzionano ma senza Google Drive. Il secret di GitHub tiene il file fuori dal repository, ma il client finisce comunque dentro le app pubblicate (vedi §8.3b: non è un segreto vero). Si può avviare anche a mano dalla scheda *Actions* (solo artefatti, senza Release).
- **APK Android** (sperimentale): compilato da `release.yml` in un job separato (`flet build apk --split-per-abi`, si pubblica la versione arm64 come `ModernSheet-android.apk`) e firmato con la **chiave di rilascio** del progetto, così ogni versione si installa sopra la precedente. La chiave (`.jks`, PKCS12, alias `modernsheet`) la crea e la conserva l'autore, fuori dal repository; arriva alla pipeline dai secret `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS` (le password passano per variabili d'ambiente, mai sulla riga di comando). Senza secret il job viene saltato; un suo errore non blocca la Release delle app desktop. Fino alla 0.42 l'APK era compilato a mano con la chiave di debug di un Mac e caricato su Google Drive: chi l'ha installato deve disinstallarlo una volta (firma diversa).
- **Test automatici**: `.github/workflows/tests.yml` esegue `--check` sugli esempi e `pytest` a ogni push e pull request, con Python 3.10 (il minimo) e 3.13.
- **Sito** `https://modernsheet.app` su **GitHub Pages** (sorgente: ramo `main`, cartella `docs/`; dominio in `docs/CNAME`). È HTML statico generato da `python tools/build_site.py` a partire da `site/`: un modello comune (`site/template.html`) e pagine Markdown in **italiano** (`site/it/`) e **inglese** (`site/en/`), con intestazione `title`, `slug`, `nav`, `other` (la pagina corrispondente nell'altra lingua) e `description`. Pagine: home, download, guida all'app, il formato `.chs`, importazione da chordsheet.com, **changelog** (le versioni pubblicate, dalla più recente, con il link alla Release di GitHub e un'ancora `#v<versione>` per ognuna; le versioni solo locali non compaiono: una pubblicazione che ne raccoglie più d'una le riassume insieme), privacy. La radice `/` porta a `/it/` o `/en/` secondo la lingua del browser; il generatore scrive anche `404.html`, `sitemap.xml`, `robots.txt` e `.nojekyll` (niente Jekyll). Stile in `docs/assets/style.css` (tema chiaro e scuro automatico, menu a scomparsa sotto i 1100 px, voci mai a capo, nessuna risorsa esterna); nei blocchi di codice un'**icona di copia** in basso a destra, dentro il riquadro (`docs/assets/copy.js`: copia il testo esatto negli appunti, con ripiego per i browser senza Clipboard API; per un istante diventa una spunta verde; etichetta "Copia"/"Copy" come suggerimento e per i lettori di schermo; sempre visibile sugli schermi touch); immagini in `docs/assets/img/` (spartiti dagli esempi, schermate dell'app con i soli brani di esempio).
- La pagina **privacy** descrive i dati trattati (tutto sul dispositivo; Google Drive con `drive.file`; password di chordsheet.com mai salvata) ed è quella da indicare nel *Branding* della schermata di consenso Google insieme alla home.
- Repository: `https://github.com/supermariolabs/modernsheet` (`REPO` in `tools/build_site.py`, link nel README); autore dei commit pubblicati con l'indirizzo *noreply* di GitHub.

### 8.4 Limiti noti e cose da verificare sul dispositivo

- **Provato su desktop (macOS), non ancora su iPad/Android**: libreria, editor e anteprima sono stati verificati in una finestra reale (schermate catturate dall'app); su tablet e telefono vanno controllati il comportamento grafico di Flutter e la tastiera a schermo nell'editor.
- **Editor con evidenziazione**: il testo colorato sta sotto un campo trasparente; i due devono avere font, interlinea e spaziatura identici (`letter_spacing` 0, perché il tema Material ne aggiunge 0,5 ai campi di testo) e il campo disegna le righe 4 px più in alto (`HIGHLIGHT_SHIFT`, misurato su macOS): da ricontrollare su iPad/Android. La posizione del popup di completamento è calcolata simulando l'a capo tra le parole con il font a spaziatura fissa (`syntax.caret_row_col`), con una colonna di margine: al più il popup finisce una riga più in basso, mai sopra la riga del cursore. Con la tastiera a schermo Tab e frecce possono mancare: resta il tocco sul suggerimento.
- **Posizione verticale dei testi**: calcolata dalle metriche del font (§7); se su un dispositivo un font risultasse spostato di qualche pixel, si corregge in `screen.py` con un fattore per font.
- **Cartella dei brani su mobile**: su desktop la cartella scelta si legge e si scrive direttamente. Su iPad il percorso restituito dal selettore è valido solo finché l'app ha l'accesso alla cartella (*security-scoped*), su Android servono i permessi di archiviazione: da verificare; in alternativa, usare la cartella documenti dell'app (visibile in *File* / condivisione file).
- **MusicXML su mobile**: un `.chs` aperto dal selettore di file del telefono/tablet arriva da solo, senza la sua cartella, quindi i `{musicxml: …}` non si trovano. Soluzioni previste: importare una cartella o un archivio `.zip` del brano, oppure incorporare il MusicXML nel `.chs`.
- **Dimensione dell'app**: il runtime di Flutter + Python aggiunge decine di MB rispetto a un'app nativa.
- **Prestazioni**: impaginazione e disegno di un brano di 3 pagine in ~0,2 s su desktop; da misurare sui dispositivi.

### 8.5 Requisiti dell'app (da dettagliare)

- **Formato**: `.chs` come unico formato di salvataggio.
- **Viste**: *staff* (questa spec) e *classica* (testo con accordi sopra, durate ignorate, testo mai troncato), commutabili con un tocco.
- **Richiami**: modalità **espansa** (come nel PDF) o **compatta** (solo intestazione "▶ Ritornello ×2" + nota).
- **Mappa del brano** generata da sezioni e richiami (es. `Intro – Strofa 1 – Ritornello ×2 – …`) mostrata in alto e usata per saltare tra le sezioni.
- **Validazione nell'editor**: i warning di §2.11 mostrati accanto alla riga.
- Da definire: libreria/setlist, sincronizzazione, autoscroll, modalità palco/tema scuro, import (ChordPro, testo, PDF).

---

## 9. Importazione da Chord Sheet Maker (chordsheet.com)

Converte il testo del campo **"Chords"** di chordsheet.com in un sorgente `.chs` (`src/modernsheet/importers/chordsheet_com.py`). Chord Sheet Maker tiene titolo, artista, tonalità, BPM e metro in campi separati del modulo: si possono scrivere come **righe d'intestazione** in cima al file (`Title:`, `Artist:`, `Key:`, `BPM:`, `Time:` — anche in italiano: `Titolo`, `Artista`, `Tonalità`, `Tempo`, `Metro`) oppure passare da riga di comando.

```
python modernsheet_cli.py --from-chordsheet brano.txt                 # → brano.chs
python modernsheet_cli.py --from-chordsheet --pdf brano.txt           # → brano.chs + brano.pdf
python modernsheet_cli.py --from-chordsheet *.txt -o convertiti/ --key G --time 3/4
```

**Dal proprio account** (app, pulsante **"Importa da chordsheet.com"** nella libreria; modulo `importers/chordsheet_account.py`, solo libreria standard, quindi anche su iPad e Android):

1. **Accesso**: email (precompilata se ricordata) e password; casella **"Ricorda l'email"** (salvata nelle impostazioni, `csm_email`). La **password non viene mai salvata**: serve solo per il login e si chiede ogni volta; i cookie della sessione restano in memoria. Il login è quello del sito (modulo Symfony: `_username`, `_password`, `_csrf_token` letto dalla pagina `/login`); credenziali sbagliate → messaggio, sito irraggiungibile o cambiato → messaggio con il motivo.
2. **Scelta**: finestra con **tutti i brani dell'account** (titolo — artista, dalla pagina "My Chord Sheets"), casella per ciascuno, filtro per titolo o artista, **"Tutti i nuovi"** / **"Nessuno"**, contatore sul pulsante **Importa (N)**, cartella di destinazione indicata. I brani **già importati** (riconosciuti dal commento `# chordsheet.com: /song/<id>/…` dei file della libreria) sono segnati "già importato" e non selezionati da "Tutti i nuovi".
3. **Importazione** nella **cartella aperta** (nella principale durante una ricerca): i sorgenti si leggono **uno alla volta** dalla pagina "view source" (`/song/source/<id>`), con una pausa di 0,25 s tra l'uno e l'altro per non pesare sul sito; ognuno è convertito come qui sotto e scritto senza sovrascrivere ("Titolo 2.chs"…), con il commento `# chordsheet.com: /song/<id>/<slug>` e il tag **`import_warn`** se la conversione lascia note o warning (o il foglio è vuoto). Finestra di avanzamento con **Interrompi** (si ferma tra un brano e l'altro); alla fine un riepilogo (importati, da controllare, non letti) e la sincronizzazione.

chordsheet.com **non ha un'API**: l'importazione legge le stesse pagine di un browser e va adattata se il sito cambia. Provata (lettura e conversione) su 241 brani di un account reale: 230 puliti, 11 con `import_warn` (7 fogli vuoti, 2 scritti in ChordPro, 2 con errori nel sorgente originale).

**Da file** (pulsante **"Da file .txt…"** nella stessa finestra): il testo del campo "Chords" in un file `.txt`, convertito e aperto nell'editor; **"Salva"** per tenere il sorgente convertito. Le note di conversione compaiono sopra lo spartito e in testa al file `.chs` come commenti.

| chordsheet.com | `.chs` |
|---|---|
| `A B C D` (una battuta per accordo) | `\| [A] \| [B] \| [C] \| [D] \|` |
| `Dm7_G7` (più accordi nella battuta) | `\| [Dm7] [G7] \|` (divisione in parti uguali, §2.5) |
| `\|\|` | `\|\|` |
| `(A B)`, `\|:A B:\|`, `(A B)x3`, `(A B)3x` | `\|: … :\|`, `:\| x3` |
| `(A B 1. C D 2. E F)`, `1.-3.+5.` | casse di volta `{volta: 1}` … `:\|` `{volta: 2}` … (§2.7) |
| `%` | battuta vuota (= `%`); se la battuta precedente aveva più accordi, viene **copiata** |
| `%%`, `%N` | copia delle 2 / N battute precedenti |
| `*` (accordo da decidere) | battuta vuota (segnalato) |
| `r1`, `r2`, `r4` | stop `[/]`, `[/:2]`, `[/:1]` (frazione della battuta) |
| `N.C.` | `[/]` |
| `3:4` in linea | `{time: 3/4}` |
| `= Titolo` | nuova sezione + doppia stanghetta prima |
| `: Titolo`, `<= A`, `+ Titolo` | nuova sezione (tipo dedotto dal nome: Intro, Verse/Strofa, Chorus/Ritornello, Bridge/Inciso, Solo, Outro/Coda…; altrimenti `part`) |
| `- testo`, `; testo` | righe di testo `{text: …}` (§2.8b; spazi multipli ridotti a uno) |
| `<- …`, `>- …`, `# commento` | commenti `#` nel `.chs` |
| Righe del sorgente | `{br}` all'inizio di ogni riga: le righe originali restano righe; `{bars_per_line}` = lunghezza di riga più frequente |
| `X` (rientro) | ignorato: le 2ª volte si allineano da sole (§2.7) |
| Numeri Nashville (`1 4 5 6m b7 5/7`) | accordi nella tonalità indicata (serve `Key`) |
| `$` (o `§`), `O` | `{segno}`, `{coda}` sulla battuta seguente (§2.8b) |
| `o`, `fine`, `D.C. …`, `D.S. …` | `{to_coda}`, `{fine}`, `{dc: …}`, `{ds: …}` sulla battuta precedente (`al coda` → `al Coda`) |
| `<C`, `<<C`, `C,,`, `C^` o `^` da solo, `Cfermata`, `Cdiamond`/`C<>` | `[<C]`, `[<<C]`, `[C,,]`, `[C~]` (il `^` da solo lega l'ultimo accordo), `[C fermata]`, `[C diamond]` (§2.4b) |
| `C?`, `[G_D+7]` (parentesi quadre attorno a uno o più accordi) | accordi opzionali `[(C)]` (§2.4b) |
| `A"1°"`, `Dm7 "a II-V-I"`, `%"ripeti"` (testo tra virgolette dopo un accordo o un `%`, anche con spazi) | annotazioni `[A "1°"]`, `[% "ripeti"]` (§2.4b) |
| `*` o `X` **dentro** `_` (`*_B_*_*`: B sul 2° movimento) | `[%]`: movimento libero, l'accordo precedente continua |
| `1.C`, `2.%)` (numero della volta attaccato all'accordo) | come `1. C`, `2. %)` |
| `( … ) x4` (numero di ripetizioni staccato) | `:| x4` |
| `X` (rientro, anche a metà o in fondo alla riga), `P0`…`P9` (palette colori) | ignorati |

Testi (lyrics) di chordsheet.com: stanno in una pagina separata del sito e non vengono importati.

---

## 10. Questioni aperte

1. **Strofe multiple dentro un ritornello** (`|: … :|` con testo diverso a ogni giro): righe di testo sovrapposte come negli spartiti? Oggi si mostra solo il testo scritto.
2. **Rilevamento automatico delle ripetizioni** (battute identiche senza testo → `|: :|`): da valutare come opzione.
3. **Bequadri di cortesia a fine riga precedente** (convenzione tipografica) invece che a inizio riga: ridurrebbe lo spazio di testata in modalità `uniform`.
4. **Metri composti** (6/8, 12/8): oggi l'unità è il quarto (6/8 = 3 movimenti); valutare il conteggio in ottavi o in movimenti puntati.
5. **D.S. / Coda / Fine**: disponibili da v0.23 come indicazioni (§2.8b); da valutare uno "srotolamento" del brano (lista delle battute nell'ordine in cui si suonano) per la riproduzione o la pedaliera.
6. **Anacrusi** (battuta in levare): non ancora prevista.
7. **MusicXML avanzato**: più voci, chiave di basso/altre chiavi, abbellimenti, dinamiche e articolazioni (oggi ignorati); testo **sopra** le note invece che sotto, per uniformità con le battute a sole sigle.
8. **Nome definitivo** del formato e dell'estensione (`.chs` provvisoria).
9. **Lingua delle etichette** generate (oggi inglese: "Key", "reprise", "p."): fissa o localizzabile.
10. **Token di Google Drive nel portachiavi di sistema** (valutato il 24 novembre 2026). Oggi il token di accesso (refresh token) è in `<dati dell'app>/google/token.json`, leggibile solo dall'utente (§8.3b). Il pacchetto ufficiale **`flet-secure-storage`** (classe `SecureStorage`, metodi asincroni `set`/`get`/`remove`, basato su `flutter_secure_storage`) lo terrebbe nel portachiavi: Keystore su Android, Keychain su iOS e macOS, Gestione credenziali su Windows, libsecret su Linux. Guadagno reale **solo su desktop** (oggi un programma dello stesso utente può leggere il file); su Android e iPad la cartella dell'app è già isolata. Da fare, se si fa: portachiavi dove funziona e **ripiego sul file** dove no (Linux senza portachiavi attivo, web), migrazione del token esistente, accesso al token in `gdrive.py` reso iniettabile (oggi sincrono e senza Flet, il portachiavi è asincrono e passa dall'app). **Rischio principale da provare prima**: su macOS `flutter_secure_storage` potrebbe richiedere l'entitlement *keychain-sharing*, legato alla firma, e le app scaricabili non sono firmate (§8.3c). Non riguarda il *client secret*, che resta nell'app per scelta (§8.3b): cifrarlo, per esempio con `flet.security.encrypt`, richiederebbe di mettere anche la chiave nell'app, quindi non lo proteggerebbe.
11. **Modifica dei brani con un agente AI** (valutato il 24 novembre 2026). Un server MCP **dentro l'app** non conviene: i brani sono già file di testo che un agente sul computer (Claude Code, Claude Desktop con accesso ai file) legge e modifica direttamente; funzionerebbe solo ad app aperta, su iPad/Android richiederebbe una porta di rete aperta da proteggere, e andrebbe in conflitto con le modifiche non salvate nell'editor. (Il server MCP di Flet, `flet mcp` / `flet-mcp`, non c'entra: serve agli assistenti di programmazione per consultare le API di Flet, non a pilotare un'app.) Quello che manca a un agente è la **verifica del risultato**. Da fare, se si fa:
    - **server MCP separato** `modernsheet-mcp` (stdio, avviato da Claude Desktop/Claude Code sul computer) che usa lo stesso motore: elenco e ricerca dei brani della libreria (`library.py`), lettura e scrittura di un `.chs`, **validazione** (warning come `--check`), **anteprima di una pagina in PNG** perché l'agente veda lo spartito, trasposizione, conversione dei MusicXML in note (`library.convert_musicxml`);
    - nell'app, **ricaricare un brano cambiato da fuori** (oggi solo per le modifiche arrivate dalla sincronizzazione): controllo del file su disco quando l'app torna in primo piano; brano senza modifiche non salvate → ricaricato, altrimenti un avviso. Utile anche a chi modifica i `.chs` con altri editor.

---

## 11. File di riferimento

| File | Contenuto |
|---|---|
| `src/modernsheet/` | Motore di riferimento a tre strati (§7). |
| `modernsheet_cli.py` | Riga di comando. |
| `src/main.py` | App Flet (§8). |
| `src/modernsheet/library.py` | Libreria di brani per l'app: scansione delle cartelle con indice, ricerca, ordinamento, brani nuovi (§8.2). |
| `src/modernsheet/gdrive.py` | Provider Google Drive per la sincronizzazione: accesso con device flow, API Drive v3 (§8.3b). |
| `MS icon.jpeg`, `tools/make_icons.py`, `src/assets/icon*.png` | Icona dell'app: disegno originale e script che genera le icone per `flet build` (§8.3). |
| `src/modernsheet/sync.py` | Sincronizzazione local-first della libreria: motore, manifesto, provider cartella (§8.3b). |
| `src/modernsheet/tab.py` | Tablatura per chitarra (§4.8b): scelta di corda e tasto (programmazione dinamica), capotasto, ottave. |
| `src/examples/riff_per_chitarra.chs` | Riff originale per chitarra: `{notation: both}`, una sezione in quinta posizione (`{tab_position: 5}`, `~3`), una in sola tablatura. |
| `src/examples/riff_drop_d.chs` | Riff originale in Drop D (`{tuning: drop D}`), con i nomi delle corde nella tablatura. |
| `src/modernsheet/notes.py` | Note scritte nel `.chs` (§2.12b): lettura dei blocchi `{start_of_notes}`, testo `w:`, travature, conversione da MusicXML. |
| `src/examples/note_nel_chs.chs` | Il blues con melodia con le zone notate scritte nel `.chs` invece che in MusicXML. |
| `src/modernsheet/edits.py` | Parti modificate dall'ultimo salvataggio e annulla/ripristina dell'editor (§8.2). |
| `src/modernsheet/xml_syntax.py` | Evidenziazione e indentazione dei MusicXML nelle tab dell'editor, in sola lettura (§8.2). |
| `src/modernsheet/i18n.py` | Testi dell'interfaccia in italiano e inglese (§8.2, *Lingua*). |
| `src/modernsheet/settings.py`, `src/modernsheet/syntax.py` | Impostazioni dell'app; evidenziazione della sintassi e completamento delle direttive nell'editor (§8.2). |
| `src/examples/` | Brani di esempio: anche la cartella dei brani predefinita dell'app (§8.2). |
| `pyproject.toml` | Dipendenze e configurazione `flet build`. |
| `tests/test_*.py`, `tests/helpers.py` | Test di regressione, un file per area (§7). |
| `src/examples/demo.chs` + `demo_intro.musicxml` | **Brano demo** del tool (PDF: `examples-pdf/demo.pdf`): intro in notazione da MusicXML (terzina, punto, taglio addizionale), ritornelli con volte 1./2., `x3`, cambio di tonalità e di tempo, `%`, stop, ripresa con `{ref}`, colori personalizzati, 4 battute per riga. |
| `examples-pdf/` | PDF generati dagli esempi. |
| `src/modernsheet/importers/` | Importatori da altri formati (oggi: chordsheet.com, §9). |
| `examples-import/` | Esempio di testo chordsheet.com con il `.chs` e il PDF risultanti. |
| `src/examples/amazing_grace.chs` / `.pdf` | 3/4, ritornello, `%`, divisione in parti uguali, modulazione G → Ab con `ref` trasposto, 4/4 a metà, stop, `x3`. |
| `src/examples/blues_del_lunedi.chs` / `.pdf` | Jazz blues in F: modalità implicita, mezzi movimenti, accordi jazz (`m7b5`, `7b9`, `7#9`, `dim7`), cambio di tempo 2/4, `\|\|`, `{br}`, testo troncato. |
| `src/examples/quattro_accordi.chs` | Test di leggibilità: 4 accordi per battuta (triadi, settime, sigle jazz lunghe, con testo, misto). |
| `src/examples/blues_con_melodia.chs` / `.pdf` | Il blues con **zone notate**: intro (riff con crome, semicrome, alterazioni, punto, legatura di valore, pausa), tema del ritornello con testo, *shout chorus* con terzine e casse di volta da MusicXML, *vamp* con casse di volta scritte nel `.chs`, coda con un estratto di misure (`\| 3-4`). |
| `src/examples/blues_intro_riff.musicxml`, `blues_tema.musicxml`, `blues_shout.musicxml` | I file MusicXML richiamati dall'esempio (lo *shout chorus* contiene terzine di crome e di semiminime, ritornello e casse di volta 1./2.). |
| `src/examples/formato_base.chs` | Guida alle basi: intestazione completa (`subtitle`, `composer`, `capo`, `tags`), `bar_width: fit` (e `uniform` solo per il ritornello), `row_spacing: wide`, `label_colors: by_type`, `bars_per_line`, `{comment}`, modalità implicita ed esplicita, durate (anche mezzi movimenti), testo prima del primo accordo, `[%]`, stop, battuta vuota, accordi con basso, tonalità minore. |
| `src/examples/ripetizioni_e_volte.chs` | Ritornelli `\|: :\|` e `:\| x3`, volte `{volta: 1, 2}` / 3ª volta più lunga della 1ª, `{volta_end}` e `{volta_end: hook}`, `{bars_per_line}` in una sezione, `{br}`, `{ref: … \| nota}` e `{ref: … x2 \| nota}`. |
| `src/examples/tempi_e_tonalita.chs` | 3/4, 6/8 e 2/4, cambi di metro in linea, modulazioni con bequadri di cortesia, tonalità con diesis e bemolle, richiamo trasposto automaticamente. |
| `src/examples/segno_e_coda.chs`, `segni_con_testo.chs`, `da_capo_al_fine.chs` | Segni di navigazione e righe `{text}` (§2.8b). |
| `src/examples/segni_ritmici.chs`, `accordi_opzionali.chs`, `annotazioni.chs` | Segni ritmici, accordi opzionali e annotazioni (§2.4b). |
| `examples-pdf/blues_del_lunedi_jazz.pdf` | Lo stesso blues con `--chord-symbols jazz`. |
| `src/assets/fonts/` | Petaluma, Petaluma Script, FreeSerif, DejaVu Sans (+ licenze). |
