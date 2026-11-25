---
title: Changelog
slug: changelog
nav: 6
other: changelog
description: La storia delle versioni di Modern Sheet pubblicate.
---

# Changelog

Le versioni di Modern Sheet pubblicate, dalla più recente. Le app da scaricare sono nella pagina
[Download](/it/download/); ogni versione con le app compilate ha la sua pagina di
[release su GitHub]({{repo}}/releases).

## 0.45.1 — 25 novembre 2026 {#v0.45.1}

[Release su GitHub]({{repo}}/releases/tag/v0.45.1) · app per macOS, Windows, Linux e Android

- Corretto: il richiamo di una sezione con il suo `{key}` all'inizio (per esempio un ritornello con
  `{key: A}` subito dopo `{start_of_chorus}`) veniva trasposto dell'intervallo sbagliato: richiamato in Si
  usciva in Re♭. Ora si traspone dalla tonalità delle sue battute.
- Download: se la build di una piattaforma non riesce, le altre vengono pubblicate comunque e per quella
  piattaforma la pagina [Download](/it/download/) offre la versione precedente, dicendolo.

## 0.45.0 — 25 novembre 2026 {#v0.45.0}

[Release su GitHub]({{repo}}/releases/tag/v0.45.0) · app per macOS, Windows, Linux e Android

- **Richiami con un altro nome**: `{ref: Strofa 1 = Strofa finale}` mostra la sezione richiamata con il nome
  scelto, con lo stesso colore dell'originale.
- **Richiami dritti a una volta**: `{ref: Ritornello volta 2}` suona il ritornello una volta sola, andando
  direttamente alla 2ª volta (senza ritornello né 1ª volta). Si combinano: `{ref: Ritornello volta 2 = Ultimo ritornello}`.
- Sito: la pagina del [formato .chs](/it/formato/) è stata completata (colori delle sezioni, tablatura,
  impaginazione, diagnostica) e ha uno spartito disegnato accanto a ogni esempio.

## 0.44.1 — 25 novembre 2026 {#v0.44.1}

[Release su GitHub]({{repo}}/releases/tag/v0.44.1) · app per macOS, Windows, Linux e Android

- Corretto: in un brano senza tonalità o metro nell'intestazione, un `{key}` o un `{time}` scritto dopo le
  prime battute diventava la tonalità (o il metro) dell'intero brano e il cambio non si vedeva. Ora è sempre
  un **cambio**, con doppia stanghetta, nuova armatura e nuovo metro; le schede della libreria leggono
  tonalità e metro solo dall'intestazione.
- Sito: accanto agli esempi del [formato .chs](/it/formato/) c'è lo **spartito disegnato** da Modern Sheet;
  nei blocchi di codice un'icona per **copiare** il testo.

## 0.44.0 — 24 novembre 2026 {#v0.44.0}

[Release su GitHub]({{repo}}/releases/tag/v0.44.0) · app per macOS, Windows, Linux e Android

Raccoglie le versioni 0.43 e 0.44.

**Editor**

- Quello che hai cambiato dall'ultimo salvataggio ha lo **sfondo verde** (più acceso sul testo scritto), che
  sparisce quando salvi.
- **Annulla** e **Ripristina** passo per passo, una parola alla volta: pulsanti ↶ ↷ in alto e
  ⌘Z / Ctrl+Z, ⌘⇧Z / Ctrl+Y.

**MusicXML**

- Le schede dei MusicXML citati da un brano sono ora **in sola lettura**: il file si vede già indentato e
  colorato. Il pulsante **Converti in note nel brano** scrive le sue battute nel `.chs` come note
  (`{start_of_notes}`), al posto del riferimento, che resta come commento; il file non viene toccato.
  Le note scritte nel brano sono molto più comode da modificare.
- Tolti di conseguenza la modifica dei MusicXML, *Indenta*, *Comprimi/Espandi* e *Crea il file MusicXML*.
  I brani che citano un MusicXML continuano a funzionare come prima.

**Sito**

- Questa pagina di changelog.

## 0.42.0 — 24 novembre 2026 {#v0.42.0}

[Release su GitHub]({{repo}}/releases/tag/v0.42.0) · app per macOS, Windows, Linux e Android

Raccoglie le versioni da 0.37 a 0.42.

**Note scritte nel brano**

- Le battute con le note (intro, riff, temi) si possono scrivere **direttamente nel `.chs`**, in un blocco
  `{start_of_notes}` … `{end_of_notes}`, in alternativa al MusicXML: nomi delle note come gli accordi
  (`G`, `Bb`, `F#`), durate come figure (`8`, `4.`), ottava relativa con `'` e `,` o assoluta con `@N`,
  pause, legature, terzine, accordi verticali, sigle sopra la nota, testo su una riga `w:`.
  Vedi [Il formato .chs](/it/formato/).
- Travature automatiche, alterazioni ricalcolate rispetto all'armatura, trasposizione come per il MusicXML.

**Tablatura per chitarra**

- Le battute notate si possono mostrare come **pentagramma**, **pentagramma + tablatura** o **sola tablatura**
  con il ritmo sotto i numeri: `{notation: staff | both | tab}` per il brano o per una sezione, e un selettore
  sopra lo spartito nell'app.
- Corda e tasto calcolati per l'intero passaggio, per restare in una posizione comoda della mano; capotasto.
- Correzioni a mano: `{tab_position: N}` (mano attorno al tasto N), `~N` dopo una nota per sceglierne la corda,
  accordature `{tuning}` (drop D, DADGAD, open G, mezzo tono sotto, basso a 4 e 5 corde, ukulele, o le note
  delle corde), corda e tasto letti dal MusicXML.

**Impaginazione**

- `{bar_width: uniform | fit}` anche **per singola sezione**, sopra l'impostazione del brano e dell'app.
- *Riempi* (`fit`) va a capo solo quando le battute non ci stanno davvero e porta fino al margine le righe
  chiuse per mancanza di spazio.
- **Spazio fra le righe** regolabile, nelle impostazioni e per brano con `{row_spacing}` (compatto, normale,
  ampio, extra o una percentuale).

**App e sito**

- Nell'editor MusicXML: indentazione del file e righe comprimibili.
- **App Android** (APK sperimentale) compilata e firmata automaticamente insieme alle app desktop.
- Pagina Download con la versione e la data di ogni app, lette da GitHub.

## 0.36.1 — 23 novembre 2026 {#v0.36.1}

[Release su GitHub]({{repo}}/releases/tag/v0.36.1) · app per macOS, Windows e Linux

- Corretta la compilazione dell'app Linux, che nella 0.36.0 non era andata a buon fine.

## 0.36.0 — 23 novembre 2026 {#v0.36.0}

- **App desktop** per macOS, Windows e Linux compilate automaticamente su GitHub e scaricabili dalla
  pagina Download. Questa versione non ha prodotto le app (la build Linux si è fermata): sostituita dalla 0.36.1.

## 0.35.0 — 23 novembre 2026 {#v0.35.0}

Prima pubblicazione: codice su GitHub con licenza GPL-3.0, sito modernsheet.app in italiano e inglese,
test automatici. Comprende tutto il lavoro fatto fino a quel momento:

- **Formato `.chs`** versionato: sezioni, accordi con durata, battute esplicite o automatiche, ritornelli e
  case di volta, cambi di tempo e di tonalità, segno, coda, D.C., D.S., Fine, righe di testo, segni ritmici
  (anticipi, legature, barre, corona), accordi opzionali e annotazioni sugli accordi.
- **Lead sheet in stile Real Book**, in PDF e sullo schermo identici: griglia di battute allineate, sigle
  jazz opzionali, colori delle sezioni, trasposizione.
- **Zone notate da MusicXML**, con terzine, ritornelli e testo.
- **App** per computer e tablet: libreria di brani a card con ricerca e ordinamento, editor con
  evidenziazione, suggerimenti e anteprima dal vivo, modalità vista a schermo intero, esportazione PDF,
  interfaccia in italiano e inglese.
- **Sincronizzazione** della libreria con una cartella o con Google Drive, senza perdere dati nei conflitti.
- **Importazione** da chordsheet.com, da testo o direttamente dal proprio account.
