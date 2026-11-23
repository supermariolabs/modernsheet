---
title: Download
slug: download
nav: 2
other: download
description: Scarica Modern Sheet per macOS, Windows e Linux.
---

# Download

Modern Sheet per computer, nell'ultima versione pubblicata. Le app sono gratuite e libere (licenza GPL-3.0).

<div class="grid" markdown="1">
<div class="card" markdown="1"><span class="ico">🍎</span>
### macOS
Mac con chip Apple o Intel.

<a class="btn primary" href="{{repo}}/releases/latest/download/ModernSheet-macos.zip">Scarica per macOS</a>
</div>
<div class="card" markdown="1"><span class="ico">💻</span>
### Windows
Windows 10 e 11, 64 bit.

<a class="btn primary" href="{{repo}}/releases/latest/download/ModernSheet-windows.zip">Scarica per Windows</a>
</div>
<div class="card" markdown="1"><span class="ico">🐧</span>
### Linux
x86_64, con GTK 3 (le distribuzioni desktop più diffuse).

<a class="btn primary" href="{{repo}}/releases/latest/download/ModernSheet-linux.tar.gz">Scarica per Linux</a>
</div>
</div>

Tutte le versioni, con le novità, sono nella pagina [Releases]({{repo}}/releases) del progetto. iPad e Android sono in prova: per ora si provano con l'app *Flet* (vedi la [guida](/it/guida/)).

## Installare e aprire

Le app **non sono ancora firmate** con un certificato Apple o Microsoft: al primo avvio il sistema chiede una conferma. È normale per il software distribuito così; il codice è tutto pubblico su [GitHub]({{repo}}).

### macOS

1. Apri `ModernSheet-macos.zip`: compare **Modern Sheet.app**. Trascinala in **Applicazioni**.
2. Al primo avvio macOS dice che l'app non può essere aperta perché lo sviluppatore non è verificato. Fai **clic destro › Apri** sull'app, poi **Apri**. Se il pulsante non c'è: *Impostazioni di Sistema › Privacy e sicurezza*, in fondo **Apri comunque**.
3. Dal secondo avvio si apre normalmente.

In alternativa, dal Terminale: `xattr -dr com.apple.quarantine "/Applications/Modern Sheet.app"`.

### Windows

1. Estrai `ModernSheet-windows.zip` in una cartella (per esempio *Documenti\\Modern Sheet*): l'app ha bisogno di tutti i file che contiene.
2. Avvia il file **.exe** della cartella.
3. Se compare *Windows ha protetto il PC*, scegli **Ulteriori informazioni › Esegui comunque**.

### Linux

```
mkdir -p ~/modernsheet && tar -xzf ModernSheet-linux.tar.gz -C ~/modernsheet
~/modernsheet/modernsheet
```

## Dopo l'installazione

Al primo avvio la libreria contiene la cartella **examples** con i brani di esempio. Per iniziare c'è la [guida all'app](/it/guida/); per scrivere i brani, il [formato .chs](/it/formato/).
