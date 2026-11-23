---
title: chordsheet.com
slug: chordsheet
nav: 4
other: chordsheet
description: Come importare in Modern Sheet i chord sheet creati su chordsheet.com (Chord Sheet Maker), dal tuo account o da un file di testo.
---

# Importare da chordsheet.com

Se usi [Chord Sheet Maker](https://www.chordsheet.com), puoi portare i tuoi brani in Modern Sheet: vengono **convertiti** nel formato `.chs`, con ritornelli, case di volta, segni, annotazioni e segni ritmici.

## Dal tuo account

1. Nella libreria apri la cartella dove vuoi i brani e tocca **Importa da chordsheet.com**.
2. Inserisci **email e password** del tuo account chordsheet.com. Con *Ricorda l'email* l'app conserva l'email per la volta successiva; la **password non viene mai salvata**, serve solo per l'accesso.
3. Compare l'elenco di **tutti i tuoi brani**: scegli quelli da importare (c'è un filtro, *Tutti i nuovi* e *Nessuno*). Quelli già importati sono segnati.
4. **Importa**: i brani vengono letti uno alla volta e salvati nella cartella aperta, senza sovrascrivere nulla.

I brani che richiedono un controllo ricevono il tag **`import_warn`**: cercali con `#import_warn`. In testa a ogni file c'è il riferimento al brano originale e, se ci sono, le note di conversione.

> chordsheet.com non offre un'API: l'importazione legge le stesse pagine che vedi nel browser. Se il sito cambia, potrebbe servire un aggiornamento di Modern Sheet.

## Da un file di testo

Nella stessa finestra, **Da file .txt…** importa il testo del campo "Chords" salvato in un file. In cima al file si possono aggiungere righe come `Title:`, `Artist:`, `Key:`, `BPM:`, `Time:`. Dalla riga di comando:

```
python modernsheet_cli.py --from-chordsheet --pdf brano.txt
```

## Cosa viene convertito

| chordsheet.com | Modern Sheet |
|---|---|
| `A B C D`, `Dm7_G7` | battute, più accordi in una battuta |
| `*_B_*_*` | B sul secondo movimento |
| `( … )`, `\|: … :\|`, `x3` | ritornelli |
| `1.` `2.` `1.-3.+5.` | case di volta |
| `%`, `%%`, `%2` | ripetizione di battute |
| `= Titolo`, `: Titolo` | sezioni |
| `- testo`, `; testo` | righe di testo `{text}` |
| `$ o O fine D.C. … D.S. …` | segni di navigazione |
| `<C <<C C^ C,,, Cfermata C<>` | segni ritmici |
| `C?`, `[G_D+7]` | accordi opzionali |
| `A"1°"`, `Dm7 "II"` | annotazioni |
| `r1 r2 r4 r8`, `N.C.`, `3:4` | pause, N.C., cambi di metro |
| `X`, `P0`…`P9` | ignorati (rientri e colori) |

Su un archivio reale di 234 brani, 230 sono stati importati senza note; gli altri avevano errori nel sorgente originale o erano scritti in un altro formato.
