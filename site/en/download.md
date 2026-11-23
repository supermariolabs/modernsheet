---
title: Download
slug: download
nav: 2
other: download
description: Download Modern Sheet for macOS, Windows and Linux.
---

# Download

Modern Sheet for computers, in the latest published version. The apps are free and open source (GPL-3.0 license).

<div class="grid" markdown="1">
<div class="card" markdown="1"><span class="ico">🍎</span>
### macOS
Macs with Apple silicon or Intel.

<a class="btn primary" href="{{repo}}/releases/latest/download/ModernSheet-macos.zip">Download for macOS</a>
</div>
<div class="card" markdown="1"><span class="ico">💻</span>
### Windows
Windows 10 and 11, 64-bit.

<a class="btn primary" href="{{repo}}/releases/latest/download/ModernSheet-windows.zip">Download for Windows</a>
</div>
<div class="card" markdown="1"><span class="ico">🐧</span>
### Linux
x86_64, with GTK 3 (the most common desktop distributions).

<a class="btn primary" href="{{repo}}/releases/latest/download/ModernSheet-linux.tar.gz">Download for Linux</a>
</div>
</div>

Every version, with its changes, is on the project's [Releases]({{repo}}/releases) page. iPad and Android are in testing: for now you can try them with the *Flet* app (see the [guide](/en/guide/)).

## Installing and opening

The apps are **not signed yet** with an Apple or Microsoft certificate: on first start the system asks for a confirmation. This is normal for software distributed this way; all the code is public on [GitHub]({{repo}}).

### macOS

1. Open `ModernSheet-macos.zip`: **Modern Sheet.app** appears. Drag it to **Applications**.
2. On first start macOS says the app cannot be opened because the developer cannot be verified. **Right-click › Open** the app, then **Open**. If there is no such button: *System Settings › Privacy & Security*, then **Open Anyway** at the bottom.
3. From the second start it opens normally.

Or, from the Terminal: `xattr -dr com.apple.quarantine "/Applications/Modern Sheet.app"`.

### Windows

1. Extract `ModernSheet-windows.zip` to a folder (for example *Documents\\Modern Sheet*): the app needs all the files in it.
2. Start the **.exe** file in the folder.
3. If *Windows protected your PC* appears, choose **More info › Run anyway**.

### Linux

```
mkdir -p ~/modernsheet && tar -xzf ModernSheet-linux.tar.gz -C ~/modernsheet
~/modernsheet/modernsheet
```

## After installing

On first start the library holds the **examples** folder with the example songs. To get started there is the [app guide](/en/guide/); to write songs, the [.chs format](/en/format/).
