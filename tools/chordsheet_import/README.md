# Importare da chordsheet.com (strumento a riga di comando)

Se usi [Chord Sheet Maker](https://www.chordsheet.com), puoi portare i tuoi brani in Modern Sheet: vengono **convertiti** nel formato `.chs`, con ritornelli, case di volta, segni, annotazioni e segni ritmici.

## Lo strumento di importazione

L'importazione si fa con un piccolo **programma a riga di comando**, separato dall'app: l'app non si collega a
chordsheet.com (le regole degli store sconsigliano di chiedere la password di un altro servizio). Serve
[Python](https://www.python.org) 3.10 o successivo e il codice di Modern Sheet:

```
git clone https://github.com/supermariolabs/modernsheet.git
cd modernsheet
pip install -r requirements.txt
```

## Dal tuo account

```
python chordsheet_cli.py account tua@email.it -o ~/Brani/chordsheet --list   # elenco dei brani
python chordsheet_cli.py account tua@email.it -o ~/Brani/chordsheet          # importa i brani nuovi
python chordsheet_cli.py account tua@email.it -o ~/Brani/chordsheet --match blues
```

1. La **password** si scrive nel terminale quando viene chiesta: serve solo per l'accesso e **non viene mai salvata**.
2. `--list` mostra **tutti i tuoi brani**; quelli già presenti nella cartella sono segnati con `*`. `--match` filtra per titolo o artista.
3. Senza `--list` i brani **nuovi** vengono letti uno alla volta e salvati nella cartella, senza sovrascrivere nulla (con `--again` anche quelli già importati).

Se la cartella è dentro la libreria dell'app, i brani compaiono dopo un aggiornamento della libreria e si sincronizzano come gli altri.

I brani che richiedono un controllo ricevono il tag **`import_warn`**: cercali nell'app con `#import_warn`. In testa a ogni file c'è il riferimento al brano originale e, se ci sono, le note di conversione.

> chordsheet.com non offre un'API: l'importazione legge le stesse pagine che vedi nel browser. Se il sito cambia, potrebbe servire un aggiornamento dello strumento.

## Da un file di testo

Salva in un file il testo del campo "Chords". In cima al file si possono aggiungere righe come `Title:`, `Artist:`, `Key:`, `BPM:`, `Time:`.

```
python chordsheet_cli.py convert --pdf brano.txt              # → brano.chs e brano.pdf
python chordsheet_cli.py convert *.txt -o convertiti/ --key G
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

Codice: `convert.py` (testo → `.chs`), `account.py` (accesso al sito), `cli.py` (riga di comando); specifica in [SPEC.md §9](../../SPEC.md).
