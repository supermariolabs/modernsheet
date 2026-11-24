// Download page: version and build time of the latest GitHub release, read when the page opens.
// <p data-release hidden>   → "Latest version: 0.42.0 · released on …"
// <p data-asset="NAME" hidden> → "Version 0.42.0 · built on … · 69 MB" for that file of the release
// <a data-asset-link="NAME"> → its href becomes the release file, if the release has it (else it keeps its own)
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
  fetch("https://api.github.com/repos/supermariolabs/modernsheet/releases/latest",
        { headers: { Accept: "application/vnd.github+json" } })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function (rel) {
      var version = String(rel.tag_name || "").replace(/^v/, "");
      var files = {};
      (rel.assets || []).forEach(function (a) { files[a.name] = a; });
      document.querySelectorAll("[data-release]").forEach(function (el) {
        el.textContent = "";
        el.appendChild(document.createTextNode(it ? "Ultima versione: " : "Latest version: "));
        var a = document.createElement("a");
        if (/^https:\/\/github\.com\//.test(rel.html_url || "")) a.href = rel.html_url;
        var b = document.createElement("strong");
        b.textContent = version;
        a.appendChild(b);
        el.appendChild(a);
        el.appendChild(document.createTextNode(" · " + (it ? "pubblicata il " : "released on ") + when(rel.published_at)));
        el.hidden = false;
      });
      document.querySelectorAll("[data-asset]").forEach(function (el) {
        var f = files[el.getAttribute("data-asset")];
        if (!f) return;
        el.textContent = (it ? "Versione " : "Version ") + version + " · " + (it ? "build del " : "built on ") +
          when(f.updated_at) + " · " + mb(f.size);
        el.hidden = false;
      });
      document.querySelectorAll("[data-asset-link]").forEach(function (el) {
        var f = files[el.getAttribute("data-asset-link")];
        if (f && /^https:\/\/github\.com\//.test(f.browser_download_url || "")) el.href = f.browser_download_url;
      });
    })
    .catch(function () { /* GitHub unreachable or no release: the page works without the details */ });
})();
