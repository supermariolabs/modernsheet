---
title: Privacy
slug: privacy
other: privacy
description: Privacy policy of Modern Sheet and the modernsheet.app website.
---

# Privacy policy

*Last updated: 26 November 2026*

Modern Sheet is an application that runs on your device. **We have no servers**, we collect no personal data, and we use no advertising, analytics or tracking.

## Data on your device

Songs, settings, the library index and the local copy of a synced library stay on your device, in the app's data folder (on iPad and iPhone the library is in the app's folder that you see in the **Files** app). None of this data is sent to us.

The app does not ask for access to the camera, microphone, location, contacts or photos. It uses the network only if you connect Google Drive.

## Files you share or export

When you use *Share*, *Export PDF*, *Save as* or *Export the library*, the file goes **only where you choose** (another app, a folder, a message), through the operating system's dialogs. When you import a file, the app reads only the one you picked.

## Google Drive (optional)

If you connect Google Drive to sync your library:

- the app asks Google only for the **`drive.file`** permission: it can see and change **only the files it creates** (the library folder and the songs in it), not the rest of your Drive;
- you sign in with the code entered at google.com/device; the **access token** is stored only on your device, in the app's data folder, and is deleted with *Disconnect*;
- songs travel directly between your device and your Google Drive, with no intermediary;
- the app reads your email address only to show which account is connected and to keep the libraries of different accounts apart on the device.

The use of information received from Google APIs adheres to the [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy), including the *Limited Use* requirements. You can revoke access at any time from your [Google Account security page](https://myaccount.google.com/permissions).

## chordsheet.com (optional)

The app **does not connect to chordsheet.com**. The [command-line tool](https://github.com/supermariolabs/modernsheet/tree/main/tools/chordsheet_import) that imports songs runs on your computer: the email and password are sent **only to chordsheet.com** to log in and the **password is never stored**.

## The modernsheet.app website

The website is hosted by GitHub Pages and uses no cookies or analytics. The Download page asks GitHub (api.github.com) for the details of the latest published version, to show its number and date. GitHub may record technical data about visits (for example the IP address) to run and protect the service: see [GitHub's privacy statement](https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement).

## Deleting data

Uninstalling the app deletes all its data from the device. *Disconnect* in *Settings › Sync* deletes the Google token; the songs on Google Drive remain yours and you manage them from your Drive. Having no servers, we keep nothing to delete.

## Children

The app is not directed at children and collects no data from anyone, children included.

## Changes

If this policy changes, the new version is published on this page with its update date.

## Contact

For questions about this policy or your data, write to **[privacy@modernsheet.app](mailto:privacy@modernsheet.app)**, or open an issue in the [project repository]({{repo}}/issues).
