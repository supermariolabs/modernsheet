---
title: Download
slug: download
nav: 2
other: download
description: Scarica Modern Sheet per macOS, Windows, Linux e Android.
---

# Download

Modern Sheet per computer e Android, nell'ultima versione pubblicata. Le app sono gratuite e libere (licenza GPL-3.0).

<p class="latest" data-release hidden></p>

<div class="grid" markdown="1">
<div class="card" markdown="1"><span class="ico">🍎</span>
### macOS
Mac con chip Apple o Intel.

<p class="build" data-asset="ModernSheet-macos.zip" hidden></p>

<a class="btn primary" href="{{repo}}/releases/latest/download/ModernSheet-macos.zip">Scarica per macOS</a>
</div>
<div class="card" markdown="1"><span class="ico">💻</span>
### Windows
Windows 10 e 11, 64 bit.

<p class="build" data-asset="ModernSheet-windows.zip" hidden></p>

<a class="btn primary" href="{{repo}}/releases/latest/download/ModernSheet-windows.zip">Scarica per Windows</a>
</div>
<div class="card" markdown="1"><span class="ico">🐧</span>
### Linux
x86_64, con GTK 3 (le distribuzioni desktop più diffuse).

<p class="build" data-asset="ModernSheet-linux.tar.gz" hidden></p>

<a class="btn primary" href="{{repo}}/releases/latest/download/ModernSheet-linux.tar.gz">Scarica per Linux</a>
</div>
<div class="card" markdown="1"><span class="ico">🤖</span>
### Android
Telefoni e tablet a 64 bit (APK). **Sperimentale**: ancora poco provato.

<p class="build" data-asset="ModernSheet-android.apk" hidden></p>

<a class="btn primary" data-asset-link="ModernSheet-android.apk" href="https://drive.google.com/file/d/1vwZ0EVc03DHRL17h8emCMKTPHOiS09Ye/view?usp=sharing">Scarica per Android</a>
</div>
</div>

Tutte le versioni, con le novità, sono nella pagina [Releases]({{repo}}/releases) del progetto. L'app per iPad è in prova: per ora si prova con l'app *Flet* (vedi la [guida](/it/guida/)).

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

### Android

1. Scarica l'APK dal dispositivo: il pulsante apre Google Drive, da lì **Scarica**.
2. Apri il file scaricato. La prima volta Android chiede di consentire *Installa app sconosciute* all'app da cui lo apri (Drive, File, Chrome…): consenti e torna indietro.
3. Se Play Protect avvisa che l'app è sconosciuta, scegli **Installa comunque**.

L'APK è per i dispositivi a 64 bit, cioè quasi tutti quelli degli ultimi anni. Gli aggiornamenti si installano sopra la versione precedente, senza perdere la libreria. **Se avevi installato l'APK di prova da Google Drive** (fino alla 0.42), disinstallalo una volta prima di installare questo: è firmato con una chiave diversa. Con la sincronizzazione su Google Drive i brani tornano al primo avvio.

## Dopo l'installazione

Al primo avvio la libreria contiene la cartella **examples** con i brani di esempio. Per iniziare c'è la [guida all'app](/it/guida/); per scrivere i brani, il [formato .chs](/it/formato/).

<script src="/assets/releases.js" defer></script>
