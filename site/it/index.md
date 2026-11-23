---
title: Modern Sheet
slug:
nav: 1
other:
description: Scrivi accordi in un file di testo, ottieni un lead sheet in stile Real Book. Libreria, editor con anteprima dal vivo, PDF, sincronizzazione con Google Drive.
---

<div class="hero" markdown="1">
<div markdown="1">

# Lead sheet in stile Real Book, da un file di testo

<p class="lead">Scrivi gli accordi in un formato semplice (<code>.chs</code>) e Modern Sheet li impagina come in un Real Book: pentagramma, sigle, ritornelli, segni, testo. Sullo schermo e in PDF.</p>

<div class="cta">
<a class="btn primary" href="/it/guida/">Inizia</a>
<a class="btn" href="/it/formato/">Il formato .chs</a>
<a class="btn" href="{{repo}}">GitHub</a>
</div>
<span class="tag">Software libero (GPL-3.0) · macOS, Windows, Linux · iPad e Android in prova</span>

</div>
<img src="/assets/img/sheet-demo.png" alt="Un brano impaginato da Modern Sheet in stile Real Book">
</div>

## Cosa fa

<div class="grid" markdown="1">
<div class="card" markdown="1"><span class="ico">✍️</span>
### Un formato di testo leggibile
Accordi tra parentesi quadre, stanghette, sezioni, testo cantato. Si scrive con qualunque editor e si legge anche senza l'app.
</div>
<div class="card" markdown="1"><span class="ico">🎼</span>
### Aspetto Real Book
Font Petaluma scritto a mano, sigle con estensioni in apice, box colorati per le sezioni, griglia uniforme delle battute. In alternativa il tema *Clean*.
</div>
<div class="card" markdown="1"><span class="ico">🔁</span>
### Ritornelli, volte e segni
Ritornelli con `x3`, case di volta 1/2/3, Segno, Coda, D.C./D.S. al Fine, richiami di sezioni già scritte con trasposizione automatica.
</div>
<div class="card" markdown="1"><span class="ico">🎵</span>
### Note vere dove servono
Intro, riff e temi scritti in un editor di partiture e importati da MusicXML, nella stessa pagina delle sigle.
</div>
<div class="card" markdown="1"><span class="ico">↕️</span>
### Trasposizione e sigle jazz
Un clic per trasporre (armature e sigle comprese); sigle standard o jazz (Δ, –, ø, °); segni ritmici, accordi opzionali, annotazioni.
</div>
<div class="card" markdown="1"><span class="ico">🗂️</span>
### Libreria di brani
Card con titolo, artista, tonalità, tempo e tag, gruppi A–Z, ordinamenti, ricerca con `A*`, `*testo*`, `&` e `|`, cartelle.
</div>
<div class="card" markdown="1"><span class="ico">🖥️</span>
### Editor con anteprima dal vivo
Evidenziazione della sintassi, suggerimenti delle direttive, schede per i MusicXML, anteprima aggiornata mentre scrivi, schermo intero per il palco.
</div>
<div class="card" markdown="1"><span class="ico">☁️</span>
### Sempre con te, anche offline
La libreria è locale e si sincronizza con Google Drive o con una cartella (iCloud, Dropbox…). Nessun brano si perde: conflitti e cancellazioni passano dal cestino.
</div>
<div class="card" markdown="1"><span class="ico">📥</span>
### Importa da chordsheet.com
Accedi al tuo account, scegli i brani e importali convertiti, con ritornelli, volte, segni e annotazioni.
</div>
</div>

<div class="band two" markdown="1">
<div markdown="1">

### Così si scrive…

```
{title: Blues del lunedì}
{subtitle: con intro e tema scritti}
{key: F}
{time: 4/4}
{tempo: 132}

{start_of_intro: Intro}
{musicxml: blues_intro_riff.musicxml}
{end_of_intro}

{start_of_verse: Strofa 1}
| [F7]Il lunedì mattina | [Bb7]no, | [F7]la sveglia | [Cm7]suona [F7]forte |
{end_of_verse}
```

</div>
<div markdown="1">

### …e così si legge

<img class="shot" src="/assets/img/sheet-blues-con-melodia.png" alt="Il blues impaginato, con l'intro in notazione da MusicXML">

</div>
</div>

## L'app

<figure markdown="1">
<img class="shot" src="/assets/img/app-editor.jpg" alt="L'editor di Modern Sheet: sorgente a sinistra, anteprima a destra">
<figcaption>L'editor: sorgente con evidenziazione a sinistra, spartito aggiornato dal vivo a destra.</figcaption>
</figure>

<figure markdown="1">
<img class="shot" src="/assets/img/app-library.jpg" alt="La libreria di Modern Sheet con le card dei brani raggruppate per lettera">
<figcaption>La libreria: card dei brani raggruppate per lettera, ricerca e ordinamenti.</figcaption>
</figure>

## Stato del progetto

Modern Sheet è in sviluppo attivo. L'app desktop (macOS, Windows, Linux) funziona e si avvia dai sorgenti; la compilazione per macOS è provata, iPad e Android sono in prova. Non ci sono ancora pacchetti pronti da scaricare: la [guida](/it/guida/) spiega come avviarla.

Il codice è su [GitHub]({{repo}}) con licenza **GPL-3.0**. Segnalazioni e idee sono benvenute nelle *Issues*.
