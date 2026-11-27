---
title: Guida all'app
slug: guida
nav: 3
other: guide
description: Come installare e usare Modern Sheet: libreria, editor, PDF, sincronizzazione con Google Drive, importazione.
---

# Guida all'app

[TOC]

## Installare Modern Sheet

Scarica l'app per macOS, Windows, Linux o Android dalla pagina [Download](/it/download/), che spiega anche come aprirla la prima volta. Le versioni per iPad e iPhone arriveranno sull'App Store.

## La libreria

Al primo avvio la libreria contiene la cartella **examples** con i brani di esempio: sono un buon modo per vedere tutte le funzioni. I tuoi brani vanno accanto, in cartelle a piacere.

- **Card** con titolo, artista, tonalità, metro, BPM, tag, nome del file e date di creazione e modifica. Con l'icona a destra si passa alla vista a **elenco**.
- **Ordinamento** per titolo, artista, tonalità, BPM, ultima modifica o data di creazione. Per titolo e artista i brani sono **raggruppati per lettera** (A, B, C…).
- **Cartelle**: *Nuova cartella* in basso a destra; il menu **⋮** di una cartella permette di **rinominarla** (i riferimenti ai MusicXML vengono aggiornati).
- **Brani con lo stesso titolo**: il dato che li distingue (data di modifica, di creazione o nome del file) è in arancione, e il più recente viene prima.

### La ricerca

La ricerca guarda in tutta la libreria, sottocartelle comprese, senza distinguere maiuscole e accenti.

| Scrivi | Trova |
|---|---|
| `blues lunedì` | brani che contengono tutte le parole (titolo, artista, tag, nome del file) |
| `#jazz` | brani con il tag *jazz* |
| `A*` | titoli che **iniziano** con A |
| `*amore` | titoli che **finiscono** con "amore" |
| `*hey jude*` | brani che **contengono** "hey jude", spazi compresi |
| `A* & #jazz` | entrambe le condizioni (**e**) |
| `A* \| B*` | almeno una delle due (**o**); `&` lega più di `\|` |

## Leggere e modificare un brano

Toccando una card il brano si apre in **modalità vista**: solo lo spartito, con le opzioni in alto.

- **Trasposizione** – / +: cambia sigle e armature; **Fake Book** o **Clean**; **Griglia** (battute tutte uguali) o **Riempi** (un brano o una sezione possono fissarne una nel sorgente con `{bar_width}`); **sigle jazz**; **Do Re Mi** (accordi e tonalità con i nomi italiani; il sorgente resta con le lettere); **colori per sezione**.
- **Pentagramma / Entrambi / Tablatura**: per chi suona la chitarra, le parti in notazione anche in **tablatura**, sotto il pentagramma o al suo posto (con il ritmo sotto i numeri). Corda e tasto li sceglie l'app, per restare in una posizione comoda; con `{capo}` i tasti partono dal capotasto. Dove serve si corregge nel brano: `{tab_position: 5}` (la mano attorno al 5° tasto), `~3` dopo una nota (quella corda), `{tuning: drop D}` (accordatura, anche basso e ukulele).
- **⛶ Schermo intero**: restano solo le pagine. Per uscire c'è il pulsante in alto a destra, oppure il tasto **Esc**.
- Le frecce, Pagina su/giù, lo spazio e le **pedaliere Bluetooth** girano le pagine.

La **matita** apre l'editor accanto allo spartito:

- **evidenziazione** della sintassi e **suggerimenti** delle direttive quando scrivi `{` (Invio o Tab per scegliere);
- quello che hai cambiato dall'ultimo salvataggio ha lo **sfondo verde** (più acceso sul testo scritto), che sparisce quando salvi;
- **Annulla** e **Ripristina** passo per passo (una parola alla volta) con i pulsanti ↶ ↷ in alto o con ⌘Z / Ctrl+Z e ⌘⇧Z / Ctrl+Y;
- l'anteprima si aggiorna mentre scrivi; i **warning** sono elencati sotto l'editor e toccandoli si va alla riga;
- una **scheda per ogni MusicXML** citato dal brano, in **sola lettura**: il file si vede già indentato e colorato, e il pulsante **Converti in note nel brano** scrive le sue battute nel `.chs` come note (`{start_of_notes}`), al posto del riferimento, che resta come commento per traccia (il file MusicXML non viene toccato); controlla l'anteprima e salva;
- **Salva** (⌘S / Ctrl+S) diventa verde quando c'è qualcosa da salvare; **Salva con nome** crea una copia accanto al brano;
- **Esporta PDF**; su iPad, iPhone e Android **Condividi** manda il PDF o il sorgente `.chs` a Mail, File, AirDrop, WhatsApp…; *Brano con MusicXML (.zip)* esporta il brano insieme ai suoi MusicXML; il **cestino rosso** elimina il brano e i suoi MusicXML, dopo una conferma con l'elenco dei file.

L'app scrive da sola nel file le date `{created}` e `{modified}`.

## Sincronizzazione

La libreria è sempre **locale**: l'app funziona anche senza rete. In *Impostazioni › Sincronizzazione* puoi tenerla allineata con:

- **Google Drive**: *Collega*, poi inserisci il codice mostrato su google.com/device. L'app vede solo i file che crea lei, in una cartella "Modern Sheet" del tuo Drive (il nome si può cambiare).
- **una cartella**: per esempio dentro iCloud Drive, Dropbox o Google Drive per desktop, il cui programma la porta sugli altri computer.

La sincronizzazione parte all'avvio, dopo ogni salvataggio, ogni 5 minuti e con *Sincronizza ora*. Non si perde nulla: se lo stesso brano cambia su due dispositivi restano **entrambe le versioni**, e i file cancellati finiscono nel **cestino** (dell'app o di Drive). Collegando un secondo dispositivo, l'app scarica prima quello che c'è già e poi aggiunge solo i brani mancanti.

## Importare brani

- **Importa file .chs o .zip** (icona nella barra della libreria): copia un `.chs` nella cartella aperta, con i MusicXML che cita, senza sovrascrivere nulla. Uno **`.zip`** con un brano porta con sé anche i suoi MusicXML (utile su iPad e Android); uno `.zip` con più brani, per esempio una libreria esportata, finisce in una nuova cartella con il nome dell'archivio.
- **Esporta la libreria** (*Impostazioni › Cartelle*): tutti i brani e i MusicXML in un `.zip`, con le cartelle: un backup, o il modo per passare a un altro dispositivo.
- **Da chordsheet.com**: chi ha i brani su Chord Sheet Maker può convertirli con uno [strumento a riga di comando](https://github.com/supermariolabs/modernsheet/tree/main/tools/chordsheet_import) (richiede Python), poi aprirli nell'app come gli altri.

## Impostazioni

Lingua (italiano o inglese), cartella dei brani, cartella per i PDF, opzioni di visualizzazione predefinite (tema, griglia, spazio fra le righe, sigle, nomi delle note, colori) e sincronizzazione. Su **iPad, iPhone e Android** la libreria sta dentro l'app: su iPad e iPhone la trovi nell'app **File** in *Sul mio iPad › Modern Sheet* (puoi trascinarci dentro i brani; con Google Drive è la cartella *Modern Sheet (Google Drive · account)*); le cartelle non si scelgono e si sincronizza con Google Drive. Un brano può fissare il suo spazio fra le righe con `{row_spacing}`. Le impostazioni restano salvate sul dispositivo.
