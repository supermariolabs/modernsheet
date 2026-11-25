// Download page: version and build time of each app, read from GitHub's releases when the page opens.
// <p data-release hidden>      → "Latest version: 0.45.0 · released on …"
// <p data-asset="NAME" hidden> → "Version 0.45.0 · built on … · 69 MB" for that file
// <a data-asset-link="NAME">   → its href becomes that file's download link (else it keeps its own)
// A build can fail for one platform while the others are published: each file is taken from the newest
// release that has it, so a platform whose build failed keeps the previous version (and says so).
// Everything from GitHub goes in as text (textContent / href of a GitHub URL), never as HTML.
(function () {
  var marks = document.querySelectorAll("[data-release],[data-asset],[data-asset-link]");
  if (!marks.length || !window.fetch) return;
  var it = (document.documentElement.lang || "").indexOf("it") === 0;
  function when(s) {
    try {
      return new Intl.DateTimeFormat(it ? "it-IT" : "en-GB", { dateStyle: "medium", timeStyle: "short" })
        .format(new Date(s));
    } catch (e) { return s; }
  }
  function mb(bytes) { return Math.round(bytes / 1048576) + " MB"; }
  function version(rel) { return String(rel.tag_name || "").replace(/^v/, ""); }
  function github(url) { return /^https:\/\/github\.com\//.test(url || ""); }
  fetch("https://api.github.com/repos/supermariolabs/modernsheet/releases?per_page=30",
        { headers: { Accept: "application/vnd.github+json" } })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function (list) {
      var releases = (list || []).filter(function (r) { return !r.draft && !r.prerelease; })
        .sort(function (a, b) { return String(b.published_at).localeCompare(String(a.published_at)); });
      if (!releases.length) return;
      var latest = releases[0];
      function newest(name) {               // the newest release that has this file, and the file
        for (var i = 0; i < releases.length; i++) {
          var assets = releases[i].assets || [];
          for (var j = 0; j < assets.length; j++) {
            if (assets[j].name === name) return { rel: releases[i], file: assets[j] };
          }
        }
        return null;
      }
      document.querySelectorAll("[data-release]").forEach(function (el) {
        el.textContent = "";
        el.appendChild(document.createTextNode(it ? "Ultima versione: " : "Latest version: "));
        var a = document.createElement("a");
        if (github(latest.html_url)) a.href = latest.html_url;
        var b = document.createElement("strong");
        b.textContent = version(latest);
        a.appendChild(b);
        el.appendChild(a);
        el.appendChild(document.createTextNode(" · " + (it ? "pubblicata il " : "released on ") + when(latest.published_at)));
        el.hidden = false;
      });
      document.querySelectorAll("[data-asset]").forEach(function (el) {
        var found = newest(el.getAttribute("data-asset"));
        if (!found) return;
        var text = (it ? "Versione " : "Version ") + version(found.rel) + " · " + (it ? "build del " : "built on ") +
          when(found.file.updated_at) + " · " + mb(found.file.size);
        if (found.rel !== latest) {
          text += it ? " (la build della " + version(latest) + " per questa piattaforma non è riuscita)"
                     : " (the " + version(latest) + " build for this platform did not succeed)";
        }
        el.textContent = text;
        el.hidden = false;
      });
      document.querySelectorAll("[data-asset-link]").forEach(function (el) {
        var found = newest(el.getAttribute("data-asset-link"));
        if (found && github(found.file.browser_download_url)) el.href = found.file.browser_download_url;
      });
    })
    .catch(function () { /* GitHub unreachable or no release: the page works without the details */ });
})();
