# CLAUDE.md — Modern Sheet

Progetto personale di Mario: motore Python + app Flet per scrivere chord sheet nel formato `.chs` e
renderli come lead sheet in stile Fake Book (PDF e schermo). Possibile futuro prodotto.

## Fonte di verità

- **`SPEC.md`** descrive formato, regole di rendering, architettura e app. Il codice e la spec devono
  coincidere: ogni cambio di comportamento aggiorna **entrambi** (più esempi e test, vedi sotto).
- Se una richiesta è in conflitto con la spec, segnalalo prima di procedere.
- Lingua: spec, README e messaggi all'utente in **italiano**; nomi nel codice, docstring e commenti in **inglese**.
  L'interfaccia dell'app è in italiano e inglese: ogni testo nuovo va nel catalogo `src/modernsheet/i18n.py` con
  entrambe le lingue e si usa con `tr("chiave")` (mai stringhe fisse in `main.py`).

## Comandi

```
source .venv/bin/activate                                   # ambiente (pip install -r requirements.txt)
pytest                                                      # test di regressione (devono passare sempre)
python modernsheet_cli.py src/examples/demo.chs -o out/            # PDF di un brano
python modernsheet_cli.py src/examples/*.chs -o examples-pdf/      # rigenera i PDF di esempio
python modernsheet_cli.py --check src/examples/*.chs              # solo validazione
python chordsheet_cli.py convert --pdf examples-import/esempio_chordsheet_com.txt  # import chordsheet.com (fuori dall'app)
python chordsheet_cli.py account EMAIL -o cartella/ [--list]                      # brani di un account chordsheet.com
flet run                                                    # app desktop (Flet 1.x)
python tools/build_site.py                                  # sito modernsheet.app: site/ → docs/ (GitHub Pages)
```

Controllo visivo di un PDF (i test non vedono la grafica):
`pdftoppm -r 80 -png out/demo.pdf out/demo` e poi guarda le PNG.

## Architettura (tre strati, `src/modernsheet/`)

1. **Parser e modello** — `theory.py`, `model.py`, `musicxml.py`, `parser.py` → `formats/` (un parser per versione
   del formato, `formats/v1.py`): `.chs` (+ MusicXML) → `Song`. Solo libreria standard.
2. **Impaginazione** — `layout.py`, `fonts.py`, `display.py`: `Song` → `DisplayList` (pagine di operazioni
   `line`, `rect`, `circle`, `path`, `text` in punti PDF, origine in basso a sinistra).
   **Non deve importare reportlab né flet.** Il testo si misura con `fonts.py` (fontTools; larghezze in
   1/1000 em arrotondate come reportlab, così PDF e schermo coincidono).
3. **Backend** — `pdf.py` (reportlab), `flet_view.py` (canvas Flet), `svg.py`, con `screen.py` che converte
   in coordinate schermo per Flet e SVG. I backend **riproducono** la DisplayList, non decidono nulla
   di impaginazione.

Fuori dall'app (non entra in `flet build`): `chordsheet_cli.py` + `tools/chordsheet_import/` (`convert.py` testo di
chordsheet.com → `.chs`, `account.py` login al sito, elenco e sorgenti dei brani; nessuna API, si leggono le pagine; password
mai salvata; tolto dall'app nella 0.49 per le regole degli store, SPEC §8.6 e §9).

Altro: `library.py` (cartella di brani per
l'app), `settings.py` (impostazioni dell'app), `syntax.py` (evidenziazione e completamento del `.chs`), `edits.py` (sfondo delle parti modificate e annulla/ripristina dell'editor) / `xml_syntax.py` (evidenziazione e indentazione dei MusicXML, in sola lettura), `sync.py` / `gdrive.py` (sincronizzazione
local-first della libreria, cartella o Google Drive), `cli.py`,
`src/main.py` (app Flet: libreria + editor con anteprima + impostazioni),
font in `src/assets/fonts/` (condivisi da motore, PDF e app), esempi in `src/examples/` (copiati in `examples/`
nella libreria "Modern Sheet" di una nuova installazione).

## Regole di lavoro

- **Una modifica completa** = codice + `SPEC.md` (sezione giusta e riga "Versione" in cima) + esempio che la
  mostri + test in `tests/` (un file per area: `test_engine.py` motore e impaginazione, `test_notes.py`, `test_tab.py`,
  `test_library.py`, `test_editor.py`, `test_importers.py`, `test_formats.py`, `test_sync.py`; aiuti comuni in `helpers.py`) + PDF di esempio rigenerati in `examples-pdf/`. Se cambia qualcosa che
  l'utente vede, aggiorna anche la documentazione del sito (solo per gli utenti finali: i dettagli per sviluppatori vanno nel README o
  nel repository, SPEC §8.3c) (`site/it/` **e** `site/en/`) e rigenera `docs/` con
  `python tools/build_site.py`.
- Dopo ogni modifica grafica: rigenera i PDF coinvolti, **guardali** (PNG) e controlla anche le varianti
  `--theme clean`, `--bar-width fit` e una trasposizione (`-t 3`).
- Gli esempi devono leggersi **senza warning** (`--check`), è anche un test.
- Versione: aggiorna insieme `pyproject.toml`, `src/modernsheet/__init__.py` (`__version__`) e l'intestazione
  di `SPEC.md`.
- Commit piccoli, uno per funzionalità, messaggio in italiano.
- **Mai pubblicare `main`** (la cronologia di sviluppo resta locale): su GitHub va solo il ramo `github`, creato da
  `tools/publish_github.sh` (un commit per pubblicazione con i file di `main`, più l'etichetta `v<versione>`) e spinto con
  `git push origin github:main v<versione>`: l'etichetta fa compilare le app desktop (`.github/workflows/release.yml`).
- A ogni pubblicazione aggiorna il **changelog** del sito (`site/it/changelog.md` e `site/en/changelog.md`): una voce per la
  versione pubblicata, che riassume tutte le versioni locali dalla pubblicazione precedente.

## Cose da sapere (decisioni già prese)

- Formato versionato: `{format: v1}` prima direttiva (assente = v1). Una modifica **distruttiva** della sintassi
  = nuovo `formats/vN.py` + `UPGRADES[N-1]` + `CURRENT = N`; le aggiunte restano nella versione corrente.
  Un parser già superato da un formato successivo non si modifica più (SPEC §2.14).

- Tema predefinito `realbook`: font Petaluma / Petaluma Script (SIL OFL, convertiti in TTF). Accordi in
  grassetto simulato (contorno ripassato), estensioni in apice, pentagramma e simboli in grigio,
  accordi e testo quasi neri.
- Box delle sezioni: colore pieno arrotondato, default `#0066CC`; `{section_colors: …}` per colori
  personalizzati; testo del box bianco o quasi nero in base al contrasto.
- Griglia `uniform` (default): tutte le battute larghe uguali, calcolate sulla riga più lunga; una battuta
  affollata occupa 2+ slot invece di rimpicciolire sotto `chord_fit_size`. Nessuna sovrapposizione.
- Durate in movimenti (quarti), minimo mezzo movimento; divisione in parti uguali per gli accordi senza
  durata; battuta senza accordi = continuazione (`%`); `[/]` = stop.
- `|:` non crea mai una battuta vuota prima di sé; una volta (`{volta: N}`) si chiude a `:|`, a
  `{volta_end}` o a fine riga del sorgente; la 2ª volta va a capo, allineata a destra sotto la 1ª, solo
  battute (niente chiave/armatura); l'ultima volta chiude con doppia stanghetta.
- Battute notate (MusicXML o note scritte nel `.chs`, `{start_of_notes}`, SPEC §2.12b, modulo `notes.py`): sigle sopra il rigo e testo sotto, **una sola linea per riga**. Note scritte: alterazioni sempre esplicite, durate come figure (mantenute), ottava relativa con `@N` facoltativa.
  Nell'app i MusicXML non si modificano più (dalla 0.43): tab in sola lettura e pulsante che li converte in note nel `.chs`
  (`library.convert_musicxml`, riferimento lasciato come commento).
- Tablatura (SPEC §4.8b, `tab.py`): `{notation: staff|both|tab}` (opzione, brano, sezione); diteggiatura per programmazione dinamica,
  nota scritta = notazione per chitarra (corde a vuoto Mi3…Mi5 scritti), capotasto; default `staff` (i brani esistenti non cambiano).
  Correzioni: `{tab_position: N}`, `~N` (corda) sulle note, `{tuning}` (anche basso/ukulele), corda/tasto dal MusicXML.
- Intestazione solo in prima pagina, titolo a sinistra.
- Icona: disegno `MS icon.jpeg` → `python tools/make_icons.py` → `src/assets/icon*.png` e `src/assets/icons/` (+ `icon_background` in
  `pyproject.toml`); non modificare a mano le PNG generate (SPEC §8.3). `src/assets/manifest.json` dà nome e icona
  all'anteprima nell'app Flet del dispositivo (`flet run --ios`).
- Esempi: solo brani originali o di pubblico dominio (niente testi protetti da copyright).

## Stato e prossimi passi

- App Flet (libreria da cartella con vista a card, ricerca/ordinamento e indice dei brani + editor scuro a tab (.chs + MusicXML citati in sola lettura, convertibili in note) con evidenziazione/completamento e anteprima dal vivo + impostazioni)
  funzionante su desktop; **mai provata su
  iPad/Android**: da verificare accesso alla cartella dei brani, posizione verticale dei testi, pedaliera Bluetooth, MusicXML dei file importati sul dispositivo (arrivano senza la loro cartella: non si possono copiare).
- Sincronizzazione (SPEC §8.3b): fase 1 (motore local-first + provider cartella) e fase 2 (Google Drive, `gdrive.py`,
  device flow + `drive.file`) fatte e provate con un vero account Google (credenziali in `src/google_client.json`,
  fuori da git; app Google pubblicata senza logo, il logo richiede la verifica del brand). Poi eventualmente iCloud nativo.
- Pubblicazione negli store (App Store, Google Play, Mac con Developer ID): piano e rischi di rifiuto in SPEC §8.6;
  primo passo la libreria interna all'app su mobile.
- `flet build macos` provato e funzionante (servono Xcode completo e CocoaPods). Identificativo app `app.modernsheet`.
- Pubblicazione: licenza GPL-3.0, sito https://modernsheet.app (GitHub Pages da `docs/`, sorgenti in `site/`,
  italiano e inglese), test su GitHub Actions. Repository https://github.com/supermariolabs/modernsheet.
- Segni di navigazione (`{segno}` `{coda}` `{to_coda}` `{fine}` `{dc}` `{ds}`) e righe `{text}`: SPEC §2.8b.
- Segni ritmici e accordi opzionali dentro le parentesi dell'accordo (`[<(C)~,, fermata]`): SPEC §2.4b.
- Annotazioni sugli accordi `[A "1°"]` (SPEC §2.4b). Importazione da chordsheet.com provata su 234 brani reali
  dell'utente: 230 puliti (gli altri 4 hanno problemi nel sorgente originale).
- Candidati: salto pagina, pause puntate (`r2.`); vista classica (testo + accordi sopra);
  richiami compatti e mappa del brano; setlist; anacrusi; casse di volta e repeat più complessi; strofe
  multiple sotto un ritornello. Elenco completo in `SPEC.md` §10.
