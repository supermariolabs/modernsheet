---
title: Download
slug: download
nav: 2
other: download
description: Download Modern Sheet for macOS, Windows, Linux and Android.
---

# Download

Modern Sheet for computers and Android, in the latest published version. The apps are free and open source (GPL-3.0 license).

<p class="latest" data-release hidden></p>

<div class="grid" markdown="1">
<div class="card" markdown="1"><span class="ico">🍎</span>
### macOS
Macs with Apple silicon or Intel.

<p class="build" data-asset="ModernSheet-macos.zip" hidden></p>

<a class="btn primary" data-asset-link="ModernSheet-macos.zip" href="{{repo}}/releases/latest/download/ModernSheet-macos.zip">Download for macOS</a>
</div>
<div class="card" markdown="1"><span class="ico">💻</span>
### Windows
Windows 10 and 11, 64-bit.

<p class="build" data-asset="ModernSheet-windows.zip" hidden></p>

<a class="btn primary" data-asset-link="ModernSheet-windows.zip" href="{{repo}}/releases/latest/download/ModernSheet-windows.zip">Download for Windows</a>
</div>
<div class="card" markdown="1"><span class="ico">🐧</span>
### Linux
x86_64, with GTK 3 (the most common desktop distributions).

<p class="build" data-asset="ModernSheet-linux.tar.gz" hidden></p>

<a class="btn primary" data-asset-link="ModernSheet-linux.tar.gz" href="{{repo}}/releases/latest/download/ModernSheet-linux.tar.gz">Download for Linux</a>
</div>
<div class="card" markdown="1"><span class="ico">🤖</span>
### Android
64-bit phones and tablets (APK). **Experimental**: not much tested yet.

<p class="build" data-asset="ModernSheet-android.apk" hidden></p>

<a class="btn primary" data-asset-link="ModernSheet-android.apk" href="https://drive.google.com/file/d/1vwZ0EVc03DHRL17h8emCMKTPHOiS09Ye/view?usp=sharing">Download for Android</a>
</div>
</div>

Every version, with its changes, is on the project's [Releases]({{repo}}/releases) page. The iPad and iPhone versions will come to the App Store.

## Installing and opening

The **macOS** app is signed and verified by Apple: it opens like any other app. The **Windows**, **Linux** and **Android** apps are not signed with a store certificate yet: on first start the system asks for a confirmation. This is normal for software distributed this way; all the code is public on [GitHub]({{repo}}).

### macOS

1. Open `ModernSheet-macos.zip`: **Modern Sheet.app** appears. Drag it to **Applications**.
2. Open it: on first start macOS only asks you to confirm that it is an app downloaded from the Internet.

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

### Android

1. Download the APK on the device: the button opens Google Drive, then tap **Download**.
2. Open the downloaded file. The first time, Android asks to allow *Install unknown apps* for the app you open it from (Drive, Files, Chrome…): allow it and go back.
3. If Play Protect warns that the app is unknown, choose **Install anyway**.

The APK is for 64-bit devices, which means nearly all recent ones. Updates install over the previous version, keeping the library. **If you installed the test APK from Google Drive** (up to 0.42), uninstall it once before installing this one: it is signed with a different key. With Google Drive sync your songs come back on first start.

## After installing

On first start the library holds the **examples** folder with the example songs. To get started there is the [app guide](/en/guide/); to write songs, the [.chs format](/en/format/).

<script src="/assets/releases.js" defer></script>
