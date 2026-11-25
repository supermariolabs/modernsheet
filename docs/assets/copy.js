// Code snippets: a "Copy" button in the top-right corner of every <pre> block of the documentation.
// The button sits on a wrapper, not inside the <pre>, so it stays put when a long line scrolls sideways.
// Copies the snippet's text exactly (no trailing newline); without the Clipboard API (old browsers,
// pages not on https) it falls back to a hidden textarea and execCommand("copy").
(function () {
  var it = (document.documentElement.lang || "").indexOf("it") === 0;
  var T = it ? { copy: "Copia", done: "Copiato", fail: "Non copiato" }
             : { copy: "Copy", done: "Copied", fail: "Not copied" };
  var ICON_COPY = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"/>' +
                  '<path d="M5 15V6a2 2 0 0 1 2-2h9"/></svg>';
  var ICON_DONE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';

  function fallback(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok ? Promise.resolve() : Promise.reject();
  }

  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(function () { return fallback(text); });
    }
    return fallback(text);
  }

  function show(btn, label, icon) {
    btn.innerHTML = icon + "<span>" + label + "</span>";
    btn.setAttribute("aria-label", label);
  }

  document.querySelectorAll("main pre").forEach(function (pre) {
    if (pre.parentNode.classList && pre.parentNode.classList.contains("code-box")) return;
    var box = document.createElement("div");
    box.className = "code-box";
    pre.parentNode.insertBefore(box, pre);
    box.appendChild(pre);
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy-btn";
    show(btn, T.copy, ICON_COPY);
    var timer = null;
    btn.addEventListener("click", function () {
      var text = (pre.querySelector("code") || pre).textContent.replace(/\n$/, "");
      copy(text).then(function () {
        show(btn, T.done, ICON_DONE);
        btn.classList.add("copied");
      }, function () {
        show(btn, T.fail, ICON_COPY);
      }).then(function () {
        clearTimeout(timer);
        timer = setTimeout(function () { show(btn, T.copy, ICON_COPY); btn.classList.remove("copied"); }, 1800);
      });
    });
    box.appendChild(btn);
  });
})();
