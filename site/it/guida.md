---
title: Guida all'app
slug: guida
nav: 3
other: guide
description: Come installare e usare Modern Sheet: libreria, editor, PDF, sincronizzazione con Google Drive, importazione.
---

# Guida all'app

[TOC]

## Avviare Modern Sheet

Il modo più semplice è **scaricare l'app** per macOS, Windows o Linux dalla pagina [Download](/it/download/). In alternativa si avvia dai sorgenti, con **Python 3.10 o successivo**:

```
git clone {{repo}}.git
cd modernsheet
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flet run                                               # l'app desktop
```

Per creare un'app vera e propria si usa `flet build`:

| Comando | Risultato | Serve |
|---|---|---|
| `flet build macos` | app per Mac | Xcode completo e CocoaPods (`brew install cocoapods`) |
| `flet build windows` | app per Windows | Visual Studio con gli strumenti C++ |
| `flet build linux` | app per Linux | i pacchetti di sviluppo GTK |
| `flet build ipa` | iPad e iPhone | un Mac con Xcode e un account Apple Developer |
| `flet build apk` | Android | niente: Flet scarica l'Android SDK |

Per provare l'app su iPad o Android senza compilarla: installa l'app **Flet** dallo store, avvia `flet run --ios` (o `--android`) e inquadra il QR code.

Dalla riga di comando, senza app, si producono i PDF:

```
python modernsheet_cli.py brano.chs -o pdf/              # un PDF per brano
python modernsheet_cli.py *.chs --theme clean -t 3       # tema Clean, trasposto di 3 semitoni
python modernsheet_cli.py --check *.chs                  # solo controllo degli errori
```

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

- **Trasposizione** – / +: cambia sigle e armature; **Real Book** o **Clean**; **Griglia** (battute tutte uguali) o **Riempi**; **sigle jazz**; **colori per sezione**.
- **⛶ Schermo intero**: restano solo le pagine. Per uscire c'è il pulsante in alto a destra, oppure il tasto **Esc**.
- Le frecce, Pagina su/giù, lo spazio e le **pedaliere Bluetooth** girano le pagine.

La **matita** apre l'editor accanto allo spartito:

- **evidenziazione** della sintassi e **suggerimenti** delle direttive quando scrivi `{` (Invio o Tab per scegliere);
- l'anteprima si aggiorna mentre scrivi; i **warning** sono elencati sotto l'editor e toccandoli si va alla riga;
- una **scheda per ogni MusicXML** citato dal brano, modificabile come il sorgente;
- **Salva** (⌘S / Ctrl+S) diventa verde quando c'è qualcosa da salvare; **Salva con nome** crea una copia accanto al brano;
- **Esporta PDF**; il **cestino rosso** elimina il brano e i suoi MusicXML, dopo una conferma con l'elenco dei file.

L'app scrive da sola nel file le date `{created}` e `{modified}`.

## Sincronizzazione

La libreria è sempre **locale**: l'app funziona anche senza rete. In *Impostazioni › Sincronizzazione* puoi tenerla allineata con:

- **Google Drive**: *Collega*, poi inserisci il codice mostrato su google.com/device. L'app vede solo i file che crea lei (permesso `drive.file`), in una cartella "Modern Sheet" del tuo Drive (il nome si può cambiare).
- **una cartella**: per esempio dentro iCloud Drive, Dropbox o Google Drive per desktop, il cui programma la porta sugli altri computer.

La sincronizzazione parte all'avvio, dopo ogni salvataggio, ogni 5 minuti e con *Sincronizza ora*. Non si perde nulla: se lo stesso brano cambia su due dispositivi restano **entrambe le versioni**, e i file cancellati finiscono nel **cestino** (dell'app o di Drive). Collegando un secondo dispositivo, l'app scarica prima quello che c'è già e poi aggiunge solo i brani mancanti.

## Importare brani

- **Importa file .chs** (icona nella barra della libreria): copia un `.chs` nella cartella aperta, con i MusicXML che cita, senza sovrascrivere nulla.
- **Importa da chordsheet.com**: accedi al tuo account, scegli i brani da un elenco e vengono importati convertiti. Dettagli nella pagina [chordsheet.com](/it/chordsheet/).

## Impostazioni

Lingua (italiano o inglese), cartella dei brani, cartella per i PDF, opzioni di visualizzazione predefinite (tema, griglia, sigle, colori) e sincronizzazione. Le impostazioni restano salvate sul dispositivo.
