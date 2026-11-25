"""User interface languages (Italian, English).

Standard library only. The app calls `set_language()` from its settings and `tr(key, **values)`
for every text it shows; the catalog below holds one entry per text with all languages.
Engine messages (parser warnings) stay in English, as in the command line.
"""
from __future__ import annotations

LANGUAGES = {"it": "Italiano", "en": "English"}
DEFAULT = "it"
_current = DEFAULT


def set_language(lang: str) -> None:
    global _current
    _current = lang if lang in LANGUAGES else DEFAULT


def language() -> str:
    return _current


def tr(key: str, lang: str | None = None, **values) -> str:
    """Text for `key` in the current (or given) language, with {placeholders} filled in.
    An unknown key is returned as is, so a missing entry shows up instead of crashing."""
    entry = CATALOG.get(key)
    if entry is None:
        return key
    text = entry.get(lang or _current) or entry[DEFAULT]
    return text.format(**values) if values else text


def tr_count(n: int, key: str, lang: str | None = None) -> str:
    """'1 brano' / '3 brani': uses `key.one` or `key.many`."""
    return tr(f"{key}.{'one' if n == 1 else 'many'}", lang, n=n)


CATALOG: dict[str, dict[str, str]] = {
    # ---- general
    "cancel": {"it": "Annulla", "en": "Cancel"},
    "save": {"it": "Salva", "en": "Save"},
    "choose": {"it": "Scegli…", "en": "Choose…"},
    "library": {"it": "Libreria", "en": "Library"},
    "settings": {"it": "Impostazioni", "en": "Settings"},
    "songs.one": {"it": "{n} brano", "en": "{n} song"},
    "songs.many": {"it": "{n} brani", "en": "{n} songs"},
    "new_song": {"it": "Nuovo brano", "en": "New song"},
    "new_folder": {"it": "Nuova cartella", "en": "New folder"},

    # ---- library
    "lib.refresh": {"it": "Aggiorna", "en": "Refresh"},
    "lib.open_file": {"it": "Importa file .chs nella cartella aperta", "en": "Import a .chs file into the open folder"},
    "lib.imported_chs": {"it": "Importato: {name} in {folder}", "en": "Imported: {name} into {folder}"},
    "lib.imported_xml": {"it": " · copiati {n} MusicXML", "en": " · {n} MusicXML copied"},
    "lib.imported_missing": {"it": " · MusicXML non trovati: {names}", "en": " · MusicXML not found: {names}"},
    "lib.import_chs_failed": {"it": "Importazione non riuscita: {err}", "en": "Import failed: {err}"},
    "lib.csm_login_help": {"it": "Accedi al tuo account chordsheet.com per scegliere i brani da importare nella "
                                 "cartella aperta. La password serve solo per l'accesso e non viene salvata.",
                           "en": "Log in to your chordsheet.com account to choose the songs to import into the open "
                                 "folder. The password is only used to log in and is never stored."},
    "lib.csm_email": {"it": "Email", "en": "Email"},
    "lib.csm_password": {"it": "Password", "en": "Password"},
    "lib.csm_remember": {"it": "Ricorda l'email", "en": "Remember the email"},
    "lib.csm_txt": {"it": "Da file .txt…", "en": "From a .txt file…"},
    "lib.csm_login": {"it": "Accedi", "en": "Log in"},
    "lib.csm_connecting": {"it": "Accesso a chordsheet.com e lettura dei brani…",
                           "en": "Logging in to chordsheet.com and reading the songs…"},
    "lib.csm_wrong": {"it": "Email o password non corrette.", "en": "Wrong email or password."},
    "lib.csm_site_error": {"it": "chordsheet.com non risponde come previsto: {err}",
                           "en": "chordsheet.com did not answer as expected: {err}"},
    "lib.csm_none": {"it": "Nessun brano nel tuo account.", "en": "No songs in your account."},
    "lib.csm_pick_title": {"it": "I tuoi brani su chordsheet.com ({n}, già importati {done})",
                           "en": "Your songs on chordsheet.com ({n}, already imported {done})"},
    "lib.csm_already": {"it": "già importato", "en": "already imported"},
    "lib.csm_filter": {"it": "Filtra per titolo o artista", "en": "Filter by title or artist"},
    "lib.csm_all_new": {"it": "Tutti i nuovi", "en": "All new ones"},
    "lib.csm_none_sel": {"it": "Nessuno", "en": "None"},
    "lib.csm_import_n": {"it": "Importa ({n})", "en": "Import ({n})"},
    "lib.csm_importing": {"it": "Importo {i} di {n}: {title}", "en": "Importing {i} of {n}: {title}"},
    "lib.csm_stop": {"it": "Interrompi", "en": "Stop"},
    "lib.csm_done": {"it": "Importati {n} brani in {folder}", "en": "Imported {n} songs into {folder}"},
    "lib.csm_done_warn": {"it": " · {n} da controllare (#import_warn)", "en": " · {n} to check (#import_warn)"},
    "lib.csm_done_failed": {"it": " · {n} non letti", "en": " · {n} could not be read"},
    "lib.import": {"it": "Importa da chordsheet.com", "en": "Import from chordsheet.com"},
    "lib.search_hint": {"it": "Cerca titolo, artista, #tag, file · A* inizia · *xyz finisce · *testo* contiene · & e · | o",
                        "en": "Search title, artist, #tag, file · A* starts · *xyz ends · *text* contains · & and · | or"},
    "lib.search_help": {"it": "Ricerca in tutte le sottocartelle (maiuscole e accenti ignorati):\n"
                              "parole: tutte in titolo, artista, tag o nome del file\n"
                              "#jazz: brani con il tag jazz\n"
                              "A*: titoli che iniziano con A\n"
                              "*xyz: titoli che finiscono con xyz\n"
                              "*hey jude*: contiene «hey jude» (spazi compresi)\n"
                              "a & b: entrambe le condizioni · a | b: almeno una\n"
                              "es. A* & #jazz | B*",
                        "en": "Search in all subfolders (case and accents ignored):\n"
                              "words: all in the title, artist, tags or file name\n"
                              "#jazz: songs tagged jazz\n"
                              "A*: titles starting with A\n"
                              "*xyz: titles ending with xyz\n"
                              "*hey jude*: contains “hey jude” (spaces included)\n"
                              "a & b: both conditions · a | b: at least one\n"
                              "e.g. A* & #jazz | B*"},
    "lib.clear_search": {"it": "Cancella la ricerca", "en": "Clear search"},
    "lib.folder_actions": {"it": "Azioni sulla cartella", "en": "Folder actions"},
    "lib.rename": {"it": "Rinomina", "en": "Rename"},
    "lib.rename_title": {"it": "Rinomina «{name}»", "en": "Rename “{name}”"},
    "lib.rename_refs": {"it": "{n} brani di altre cartelle citano MusicXML di questa cartella: i loro riferimenti "
                              "verranno aggiornati.",
                        "en": "{n} songs in other folders cite MusicXML files of this folder: their references "
                              "will be updated."},
    "lib.rename_synced": {"it": "La cartella verrà rinominata anche sul remoto e sugli altri dispositivi "
                                "(i file passano dal cestino).",
                          "en": "The folder will be renamed on the remote and the other devices too "
                                "(the files go through the trash)."},
    "lib.rename_busy": {"it": "Sincronizzazione ancora in corso: riprova tra poco.",
                        "en": "Still syncing: try again in a moment."},
    "lib.rename_failed": {"it": "Rinomina non riuscita: {err}", "en": "Renaming failed: {err}"},
    "lib.rename_invalid": {"it": "Nome non valido o già usato da un'altra cartella.",
                           "en": "Invalid name, or already used by another folder."},
    "lib.renamed": {"it": "Rinominata: {old} → {new}", "en": "Renamed: {old} → {new}"},
    "lib.renamed_refs": {"it": " · aggiornati {n} brani", "en": " · {n} songs updated"},
    "lib.sort": {"it": "Ordina", "en": "Sort"},
    "lib.ascending": {"it": "Crescente", "en": "Ascending"},
    "lib.descending": {"it": "Decrescente", "en": "Descending"},
    "lib.view_list": {"it": "Vista a elenco", "en": "List view"},
    "lib.view_cards": {"it": "Vista a card", "en": "Card view"},
    "lib.choose_title": {"it": "Scegli la cartella con i tuoi brani .chs", "en": "Choose the folder with your .chs songs"},
    "lib.choose_help": {"it": "Le sottocartelle sono incluse. La cartella si cambia anche dalle Impostazioni.",
                        "en": "Subfolders are included. The folder can also be changed in Settings."},
    "lib.choose_button": {"it": "Scegli cartella", "en": "Choose folder"},
    "lib.results": {"it": "{n} risultati in {folder}", "en": "{n} results in {folder}"},
    "lib.no_songs": {"it": "Nessun brano trovato.", "en": "No songs found."},
    "lib.tag_tooltip": {"it": "Mostra i brani con #{tag}", "en": "Show the songs tagged #{tag}"},
    "lib.new_title": {"it": "Titolo", "en": "Title"},
    "lib.new_in": {"it": "In: {folder}", "en": "In: {folder}"},
    "lib.create": {"it": "Crea", "en": "Create"},
    "lib.create_failed": {"it": "Impossibile creare il file: {err}", "en": "Could not create the file: {err}"},
    "lib.folder_name": {"it": "Nome della cartella", "en": "Folder name"},
    "lib.folder_failed": {"it": "Impossibile creare la cartella: {err}", "en": "Could not create the folder: {err}"},
    "lib.up": {"it": "Cartella superiore", "en": "Parent folder"},
    "lib.home": {"it": "Cartella principale: {name}", "en": "Main folder: {name}"},
    "lib.empty_folder": {"it": "Cartella vuota: crea un brano o una sottocartella.",
                         "en": "Empty folder: create a song or a subfolder."},
    "sort.title": {"it": "Titolo", "en": "Title"},
    "sort.artist": {"it": "Artista", "en": "Artist"},
    "sort.key": {"it": "Tonalità", "en": "Key"},
    "sort.tempo": {"it": "BPM", "en": "BPM"},
    "sort.modified": {"it": "Ultima modifica", "en": "Last modified"},
    "sort.created": {"it": "Data di creazione", "en": "Date created"},
    "date.months": {"it": "gen feb mar apr mag giu lug ago set ott nov dic",
                    "en": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec"},
    "date.format": {"it": "{d} {month} {y}", "en": "{month} {d}, {y}"},
    "card.created": {"it": "Creato {date}", "en": "Created {date}"},
    "card.modified": {"it": "Modificato {date}", "en": "Modified {date}"},

    # ---- settings
    "set.folders": {"it": "Cartelle", "en": "Folders"},
    "set.library_folder": {"it": "Cartella dei brani", "en": "Songs folder"},
    "set.reset_examples": {"it": "Torna alla libreria predefinita (con gli esempi)",
                           "en": "Back to the default library (with the examples)"},
    "set.from_env": {"it": "{path} (da MODERNSHEET_LIBRARY)", "en": "{path} (from MODERNSHEET_LIBRARY)"},
    "set.examples": {"it": "Libreria predefinita, con gli esempi — {path}",
                     "en": "Default library, with the examples — {path}"},
    "set.pdf_folder": {"it": "Cartella per i PDF", "en": "PDF folder"},
    "set.no_pdf_folder": {"it": "Nessuna cartella predefinita", "en": "No default folder"},
    "set.pdf_ask": {"it": "Nessuna: si sceglie ogni volta", "en": "None: chosen every time"},
    "set.display": {"it": "Visualizzazione predefinita", "en": "Default display"},
    "set.display_help": {"it": "Vale per i brani aperti da ora in poi; nell'editor si può cambiare per il singolo brano.",
                         "en": "Applies to the songs opened from now on; the editor can change it for one song."},
    "set.theme": {"it": "Formato", "en": "Style"},
    "set.theme_help": {"it": "Real Book (scritto a mano) o Clean", "en": "Real Book (handwritten) or Clean"},
    "set.bar_width": {"it": "Larghezza delle battute", "en": "Bar width"},
    "set.bar_width_help": {"it": "Griglia: tutte uguali · Riempi: secondo il contenuto",
                           "en": "Grid: all equal · Fill: by content"},
    "set.row_spacing": {"it": "Spazio fra le righe", "en": "Row spacing"},
    "set.row_spacing_help": {"it": "Per tutti i brani; un brano può fissare il suo con {row_spacing}",
                             "en": "For every song; a song can set its own with {row_spacing}"},
    "set.notation": {"it": "Battute notate", "en": "Notated bars"},
    "set.notation_help": {"it": "Pentagramma, pentagramma con tablatura per chitarra, o solo tablatura",
                          "en": "Staff, staff with guitar tablature, or tablature only"},
    "set.chords": {"it": "Sigle degli accordi", "en": "Chord symbols"},
    "set.chords_help": {"it": "Standard (Cmaj7, Cm7b5) o jazz (CΔ7, Cø7)", "en": "Standard (Cmaj7, Cm7b5) or jazz (CΔ7, Cø7)"},
    "set.colors": {"it": "Colori per sezione", "en": "Colours by section"},
    "set.colors_help": {"it": "Un colore predefinito per ogni tipo di sezione (altrimenti tutti blu)",
                        "en": "A default colour for each kind of section (otherwise all blue)"},
    "set.general": {"it": "Generale", "en": "General"},
    "set.language": {"it": "Lingua", "en": "Language"},
    "set.language_help": {"it": "Lingua dell'interfaccia", "en": "Language of the interface"},
    "opt.grid": {"it": "Griglia", "en": "Grid"},
    "opt.fill": {"it": "Riempi", "en": "Fill"},
    "opt.notation.staff": {"it": "Pentagramma", "en": "Staff"},
    "opt.notation.both": {"it": "Entrambi", "en": "Both"},
    "opt.notation.tab": {"it": "Tablatura", "en": "Tab"},
    "opt.notation.staff_tip": {"it": "Le note sul pentagramma", "en": "Notes on the staff"},
    "opt.notation.both_tip": {"it": "Pentagramma con sotto la tablatura per chitarra",
                              "en": "Staff with the guitar tablature under it"},
    "opt.notation.tab_tip": {"it": "Solo tablatura per chitarra, con il ritmo",
                             "en": "Guitar tablature only, with the rhythm"},
    "opt.spacing.compact": {"it": "Compatta", "en": "Compact"},
    "opt.spacing.normal": {"it": "Normale", "en": "Normal"},
    "opt.spacing.wide": {"it": "Ampia", "en": "Wide"},
    "opt.spacing.extra": {"it": "Molto ampia", "en": "Extra wide"},
    "opt.standard": {"it": "Standard", "en": "Standard"},
    "opt.jazz": {"it": "Jazz", "en": "Jazz"},

    # ---- editor
    "ed.save": {"it": "Salva (⌘S / Ctrl+S)", "en": "Save (⌘S / Ctrl+S)"},
    "ed.undo": {"it": "Annulla l'ultima modifica (⌘Z / Ctrl+Z)", "en": "Undo the last change (⌘Z / Ctrl+Z)"},
    "ed.redo": {"it": "Ripristina (⌘⇧Z / Ctrl+Y)", "en": "Redo (⌘⇧Z / Ctrl+Y)"},
    "ed.save_as": {"it": "Salva con nome", "en": "Save as"},
    "ed.export_pdf": {"it": "Esporta PDF", "en": "Export PDF"},
    "ed.file_name": {"it": "Nome del file", "en": "File name"},
    "ed.other_place": {"it": "Altra posizione…", "en": "Other location…"},
    "ed.transpose": {"it": "Trasposizione", "en": "Transpose"},
    "ed.semitone_down": {"it": "−1 semitono", "en": "−1 semitone"},
    "ed.semitone_up": {"it": "+1 semitono", "en": "+1 semitone"},
    "ed.jazz": {"it": "Simboli jazz", "en": "Jazz symbols"},
    "ed.colors": {"it": "Colori per sezione", "en": "Colours by section"},
    "ed.upgrade": {"it": "Aggiorna al formato {v}", "en": "Upgrade to format {v}"},
    "ed.hide_editor": {"it": "Solo vista (chiudi l'editor)", "en": "View only (close the editor)"},
    "ed.show_editor": {"it": "Modifica", "en": "Edit"},
    "ed.fullscreen": {"it": "Schermo intero", "en": "Full screen"},
    "ed.exit_fullscreen": {"it": "Esci da schermo intero", "en": "Exit full screen"},
    "ed.exit_fullscreen_tip": {"it": "Esci da schermo intero (Esc)", "en": "Exit full screen (Esc)"},
    "ed.not_saved_tooltip": {"it": "Non salvato su file: usa \"Salva con nome\"",
                             "en": "Not saved to a file: use \"Save as\""},
    "ed.not_saved": {"it": "non salvato", "en": "not saved"},
    "ed.status": {"it": "{where} · {lines} righe · formato {version}", "en": "{where} · {lines} lines · format {version}"},
    "ed.unsaved": {"it": " · modifiche non salvate", "en": " · unsaved changes"},
    "ed.status_xml": {"it": "{where} · {lines} righe · MusicXML", "en": "{where} · {lines} lines · MusicXML"},
    "ed.format_undeclared": {"it": " (non indicato)", "en": " (not stated)"},
    "ed.format_newer": {"it": " ⚠ più recente di questa versione dell'app (fino a {v})",
                        "en": " ⚠ newer than this version of the app (up to {v})"},
    "ed.open_failed": {"it": "Impossibile aprire {name}: {err}", "en": "Could not open {name}: {err}"},
    "ed.engine_error": {"it": "⛔ Errore del motore (anteprima non aggiornata): {err}",
                        "en": "⛔ Engine error (preview not updated): {err}"},
    "ed.goto_line": {"it": "Vai alla riga", "en": "Go to line"},
    "ed.upgraded": {"it": "Sorgente aggiornato da {old} a {new}: salva per tenerlo",
                    "en": "Source upgraded from {old} to {new}: save to keep it"},
    "ed.newer_title": {"it": "Formato più recente", "en": "Newer format"},
    "ed.newer_text": {"it": "Questo brano usa il formato {v}, più recente di quello che questa versione dell'app conosce "
                            "({current}). Salvandolo da qui le parti che l'app non capisce potrebbero andare perse o "
                            "cambiare significato. Salvare comunque?",
                      "en": "This song uses format {v}, newer than the one this version of the app knows ({current}). "
                            "Saving it from here may lose or change the parts the app does not understand. "
                            "Save anyway?"},
    "ed.save_anyway": {"it": "Salva comunque", "en": "Save anyway"},
    "ed.save_failed": {"it": "Salvataggio non riuscito: {err}", "en": "Saving failed: {err}"},
    "ed.saved": {"it": "Salvato: {name}", "en": "Saved: {name}"},
    "ed.delete": {"it": "Elimina brano", "en": "Delete song"},
    "ed.delete_title": {"it": "Eliminare il brano?", "en": "Delete this song?"},
    "ed.delete_text": {"it": "«{title}»: verranno eliminati questi file:",
                       "en": "“{title}”: these files will be deleted:"},
    "ed.delete_kept": {"it": "Restano:", "en": "Kept:"},
    "ed.kept_shared": {"it": "{file}: usato anche da {songs}", "en": "{file}: also used by {songs}"},
    "ed.kept_outside": {"it": "{file}: fuori dalla libreria", "en": "{file}: outside the library"},
    "ed.kept_missing": {"it": "{file}: non trovato", "en": "{file}: not found"},
    "ed.delete_synced": {"it": "Spariranno anche dagli altri dispositivi; una copia resta nel cestino della "
                               "sincronizzazione (e, con Google Drive, nel cestino di Drive).",
                         "en": "They will disappear from your other devices too; a copy stays in the sync trash "
                               "(and, with Google Drive, in the Drive trash)."},
    "ed.delete_final": {"it": "L'operazione non si può annullare.", "en": "This cannot be undone."},
    "ed.delete_unsaved": {"it": "Le modifiche non salvate andranno perse.", "en": "Unsaved changes will be lost."},
    "ed.delete_confirm": {"it": "Elimina", "en": "Delete"},
    "ed.deleted": {"it": "Eliminato: {name}", "en": "Deleted: {name}"},
    "ed.delete_failed": {"it": "Eliminazione non riuscita: {err}", "en": "Deleting failed: {err}"},
    "ed.save_source": {"it": "Salva sorgente .chs", "en": "Save .chs source"},
    "ed.unsaved_title": {"it": "Modifiche non salvate", "en": "Unsaved changes"},
    "ed.unsaved_text": {"it": "Salvare le modifiche a \"{name}\"?", "en": "Save the changes to \"{name}\"?"},
    "ed.dont_save": {"it": "Non salvare", "en": "Don't save"},
    "ed.open_song": {"it": "Importa file .chs", "en": "Import a .chs file"},
    "ed.imported": {"it": "Importato: usa \"Salva con nome\" per tenere il sorgente convertito",
                    "en": "Imported: use \"Save as\" to keep the converted source"},
    "ed.pdf_saved": {"it": "PDF salvato: {name}", "en": "PDF saved: {name}"},

    # ---- directive completion (editor popup)
    "hint.format": {"it": "versione del formato .chs (prima direttiva)", "en": ".chs format version (first directive)"},
    "hint.title": {"it": "titolo del brano", "en": "song title"},
    "hint.subtitle": {"it": "sottotitolo", "en": "subtitle"},
    "hint.artist": {"it": "artista", "en": "artist"},
    "hint.composer": {"it": "compositore", "en": "composer"},
    "hint.key": {"it": "tonalità (la prima) o cambio di tonalità", "en": "key (the first one) or key change"},
    "hint.time": {"it": "metro (il primo) o cambio di tempo", "en": "time signature (the first one) or change"},
    "hint.tempo": {"it": "BPM", "en": "BPM"},
    "hint.capo": {"it": "capotasto", "en": "capo"},
    "hint.tags": {"it": "etichette separate da virgole (jazz, ballad…)", "en": "comma-separated tags (jazz, ballad…)"},
    "hint.section": {"it": "sezione {label}", "en": "{label} section"},
    "hint.end_section": {"it": "chiude la sezione aperta", "en": "closes the open section"},
    "hint.br": {"it": "a capo forzato", "en": "forced line break"},
    "hint.volta": {"it": "casa di volta (1., 2., …)", "en": "ending (1., 2., …)"},
    "hint.volta_end": {"it": "chiude la casa di volta", "en": "closes the ending"},
    "hint.ref": {"it": "richiama una sezione già scritta (x2, volta 2, = nuovo nome, | nota)",
                 "en": "repeats a section written earlier (x2, volta 2, = new label, | note)"},
    "hint.musicxml": {"it": "zona notata da un file MusicXML", "en": "notated bars from a MusicXML file"},
    "hint.start_of_notes": {"it": "note scritte qui: G8 Bb D F, R4, F2- F", "en": "notes written here: G8 Bb D F, R4, F2- F"},
    "hint.end_of_notes": {"it": "chiude il blocco di note", "en": "closes the notes block"},
    "hint.bars_per_line": {"it": "battute per riga", "en": "bars per line"},
    "hint.tuning": {"it": "accordatura della tablatura: drop D, DADGAD, open G, bass, ukulele…",
                    "en": "tablature tuning: drop D, DADGAD, open G, bass, ukulele…"},
    "hint.tab_position": {"it": "tablatura: la mano attorno a questo tasto (auto = automatica)",
                          "en": "tablature: the hand around this fret (auto = automatic)"},
    "hint.notation": {"it": "battute notate: staff, both (con tablatura) o tab; brano o sezione",
                      "en": "notated bars: staff, both (with tablature) or tab; song or section"},
    "hint.row_spacing": {"it": "spazio fra le righe: compact, normal, wide, extra o 120%",
                         "en": "space between rows: compact, normal, wide, extra or 120%"},
    "hint.bar_width": {"it": "uniform (griglia) o fit (riempi): brano, o sezione se scritto dentro",
                       "en": "uniform (grid) or fit (fill): song, or section if written inside one"},
    "hint.label_colors": {"it": "theme o by_type per questo brano", "en": "theme or by_type for this song"},
    "hint.section_colors": {"it": "colori dei box per tipo di sezione", "en": "box colours by section kind"},
    "hint.comment": {"it": "commento (non stampato)", "en": "comment (not printed)"},
    "hint.text": {"it": "riga di testo nello spartito (dentro una sezione)", "en": "text line on the sheet (inside a section)"},
    "hint.segno": {"it": "segno (inizio della battuta seguente)", "en": "segno (start of the next bar)"},
    "hint.coda": {"it": "coda: dove si salta (inizio della battuta seguente)", "en": "coda: where to jump (start of the next bar)"},
    "hint.to_coda": {"it": "To Coda (fine della battuta)", "en": "To Coda (end of the bar)"},
    "hint.fine": {"it": "Fine (fine della battuta)", "en": "Fine (end of the bar)"},
    "hint.dc": {"it": "D.C. … (fine della battuta), es. al Fine", "en": "D.C. … (end of the bar), e.g. al Fine"},
    "hint.ds": {"it": "D.S. … (fine della battuta), es. al Coda", "en": "D.S. … (end of the bar), e.g. al Coda"},

    # ---- MusicXML tabs (read only) and their conversion into notes
    "xml.read_only": {"it": "Sola lettura", "en": "Read only"},
    "xml.convert": {"it": "Converti in note nel brano", "en": "Convert to notes in the song"},
    "xml.convert_tip": {"it": "Scrive queste battute nel .chs come note ({start_of_notes}), al posto del riferimento",
                        "en": "Writes these bars into the .chs as notes ({start_of_notes}), in place of the reference"},
    "xml.convert_title": {"it": "Convertire {name} in note?", "en": "Convert {name} to notes?"},
    "xml.convert_text": {
        "it": "Le battute di {name} vengono scritte nel brano come note ({{start_of_notes}} … {{end_of_notes}}), "
              "al posto di ogni {{musicxml: {name}}}. Il riferimento resta nel brano come commento, per traccia, "
              "e il file MusicXML non viene toccato né cancellato. Il brano risulta modificato: "
              "controlla l'anteprima e salva (o esci senza salvare per annullare).",
        "en": "The bars of {name} are written into the song as notes ({{start_of_notes}} … {{end_of_notes}}), "
              "in place of every {{musicxml: {name}}}. The reference stays in the song as a comment, as a trace, "
              "and the MusicXML file is neither changed nor deleted. The song is then modified: "
              "check the preview and save (or leave without saving to undo)."},
    "xml.convert_ok": {"it": "Converti", "en": "Convert"},
    "xml.converted_note": {"it": "convertito in note qui sotto", "en": "converted to notes below"},
    "xml.converted": {"it": "{name} convertito in note ({n} riferimenti): le note sono identiche. Salva per tenerle.",
                      "en": "{name} converted to notes ({n} references): the notes are identical. Save to keep them."},
    "xml.converted_check": {
        "it": "{name} convertito in note ({n} riferimenti), ma qualcosa è cambiato: controlla l'anteprima e i warning prima di salvare.",
        "en": "{name} converted to notes ({n} references), but something changed: check the preview and the warnings before saving."},
    "xml.convert_failed": {"it": "Impossibile convertire {name}: {err}", "en": "Could not convert {name}: {err}"},

    # ---- editor tabs
    "tab.missing": {"it": "{name} (mancante)", "en": "{name} (missing)"},
    "tab.missing_text": {"it": "Il file {name} citato nel brano non esiste: le sue battute non si vedono. "
                               "Scrivile nel brano come note ({{start_of_notes}}).",
                         "en": "The file {name} referenced by the song does not exist: its bars are not shown. "
                               "Write them in the song as notes ({{start_of_notes}})."},
    "tab.compressed": {"it": "{name} è compresso (.mxl): non si può mostrare come testo, ma si può convertire in note.",
                       "en": "{name} is compressed (.mxl): it cannot be shown as text, but it can be converted to notes."},
    "tab.read_failed": {"it": "Impossibile leggere {name}: {err}", "en": "Could not read {name}: {err}"},
    "tab.new_tabs": {"it": "Nuove tab: {names}", "en": "New tabs: {names}"},

    # ---- library sync
    "sync.conflict": {"it": "conflitto {device} {when}", "en": "conflict {device} {when}"},
    "sync.this_device": {"it": "questo dispositivo", "en": "this device"},
    "sync.section": {"it": "Sincronizzazione", "en": "Sync"},
    "sync.folder": {"it": "Cartella sincronizzata", "en": "Synced folder"},
    "sync.folder_none": {"it": "Nessuna: la libreria non è sincronizzata",
                         "en": "None: the library is not synced"},
    "sync.folder_help": {"it": "Una cartella di iCloud Drive, Google Drive per desktop o Dropbox. L'app lavora su una "
                               "copia locale (funziona anche offline) e la allinea a questa cartella.",
                         "en": "A folder in iCloud Drive, Google Drive for desktop or Dropbox. The app works on a "
                               "local copy (also offline) and keeps it in step with this folder."},
    "sync.choose": {"it": "Scegli la cartella sincronizzata", "en": "Choose the synced folder"},
    "sync.stop": {"it": "Interrompi la sincronizzazione", "en": "Stop syncing"},
    "sync.now": {"it": "Sincronizza ora", "en": "Sync now"},
    "sync.local_copy": {"it": "Copia locale sincronizzata — {path}", "en": "Synced local copy — {path}"},
    "sync.merge_title": {"it": "Sincronizzare la libreria", "en": "Sync the library"},
    "sync.merge_text": {"it": "Aggiungere alla libreria sincronizzata anche i brani della libreria attuale ({name})? "
                              "I file che esistono già non vengono sovrascritti.",
                        "en": "Also add the songs of the current library ({name}) to the synced library? "
                              "Existing files are not overwritten."},
    "sync.merge_yes": {"it": "Sì, aggiungili", "en": "Yes, add them"},
    "sync.merge_no": {"it": "No, solo la cartella", "en": "No, just the folder"},
    "sync.never": {"it": "Mai sincronizzata", "en": "Never synced"},
    "sync.running": {"it": "Sincronizzazione in corso…", "en": "Syncing…"},
    "sync.last": {"it": "Ultima sincronizzazione: {when}", "en": "Last sync: {when}"},
    "sync.offline": {"it": "Cartella non raggiungibile: si lavora sulla copia locale", "en": "Folder not reachable: working on the local copy"},
    "sync.errors": {"it": "{n} file non sincronizzati: {first}", "en": "{n} files not synced: {first}"},
    "sync.conflicts": {"it": "{n} conflitti: trovi entrambe le versioni nella libreria ({first})",
                       "en": "{n} conflicts: both versions are in the library ({first})"},
    "sync.unavailable": {"it": "Sincronizzazione non disponibile: avvia l'app con «flet run»",
                         "en": "Sync not available: start the app with «flet run»"},
    "gd.title": {"it": "Google Drive", "en": "Google Drive"},
    "gd.help": {"it": "Sincronizza con una cartella del tuo Google Drive: funziona su tutti i dispositivi, anche iPad "
                      "e Android. L'app vede solo i file che crea lei. Un nome di cartella diverso è un'altra libreria.",
                "en": "Syncs with a folder in your Google Drive: works on every device, iPad and Android too. The app "
                      "only sees the files it creates. A different folder name is another library."},
    "gd.not_connected": {"it": "Non collegato", "en": "Not connected"},
    "gd.connected": {"it": "Collegato: {account}", "en": "Connected: {account}"},
    "gd.connect": {"it": "Collega l'account Google", "en": "Connect the Google account"},
    "gd.disconnect": {"it": "Scollega l'account Google", "en": "Disconnect the Google account"},
    "gd.no_client": {"it": "Manca la configurazione OAuth dell'app (google_client.json): vedi README, «Google Drive».",
                     "en": "The app's OAuth configuration is missing (google_client.json): see README, «Google Drive»."},
    "gd.code_title": {"it": "Collega Google Drive", "en": "Connect Google Drive"},
    "gd.code_text": {"it": "Su qualsiasi dispositivo apri {url} e inserisci questo codice:",
                     "en": "On any device open {url} and enter this code:"},
    "gd.open": {"it": "Apri la pagina", "en": "Open the page"},
    "gd.copy": {"it": "Copia il codice", "en": "Copy the code"},
    "gd.waiting": {"it": "In attesa della conferma…", "en": "Waiting for confirmation…"},
    "gd.denied": {"it": "Accesso negato.", "en": "Access denied."},
    "gd.expired": {"it": "Codice scaduto: riprova.", "en": "The code expired: try again."},
    "gd.failed": {"it": "Collegamento non riuscito: {err}", "en": "Connection failed: {err}"},
    "gd.auth_required": {"it": "Accesso a Google Drive scaduto o revocato: ricollega l'account nelle Impostazioni",
                         "en": "Google Drive access expired or revoked: connect the account again in Settings"},
    "gd.folder": {"it": "Cartella su Drive", "en": "Folder in Drive"},
    "gd.folder_help": {"it": "Nella radice del tuo Drive", "en": "In the root of your Drive"},
    "gd.folder_title": {"it": "Cambiare cartella su Drive", "en": "Change the Drive folder"},
    "gd.folder_text": {"it": "La libreria passerà alla cartella «{name}» del tuo Drive (creata se non esiste). "
                             "La libreria attuale resta nella cartella «{old}».",
                       "en": "The library will move to the «{name}» folder of your Drive (created if missing). "
                             "The current library stays in the «{old}» folder."},
    "gd.folder_ok": {"it": "Usa «{name}»", "en": "Use «{name}»"},
    "sync.remote_reset": {"it": "La cartella remota era vuota o nuova: i brani locali sono stati caricati di nuovo",
                          "en": "The remote folder was empty or new: the local songs were uploaded again"},
    "sync.folder_missing": {"it": "cartella non raggiungibile: {path}", "en": "folder not reachable: {path}"},

    # ---- default section labels (completion snippets, new song template)
    "section.intro": {"it": "Intro", "en": "Intro"},
    "section.verse": {"it": "Strofa", "en": "Verse"},
    "section.chorus": {"it": "Ritornello", "en": "Chorus"},
    "section.bridge": {"it": "Bridge", "en": "Bridge"},
    "section.solo": {"it": "Solo", "en": "Solo"},
    "section.instrumental": {"it": "Strumentale", "en": "Instrumental"},
    "section.outro": {"it": "Outro", "en": "Outro"},
    "section.coda": {"it": "Coda", "en": "Coda"},
}


def tr_date(when, lang: str | None = None) -> str:
    """A date in the UI language: "23 nov 2026" / "Nov 23, 2026"."""
    month = tr("date.months", lang).split()[when.month - 1]
    return tr("date.format", lang, d=when.day, month=month, y=when.year)


def tr_datetime(when, lang: str | None = None) -> str:
    """Date and time in the UI language: "23 nov 2026 13:05:12" / "Nov 23, 2026 13:05:12"."""
    return f"{tr_date(when, lang)} {when:%H:%M:%S}"
