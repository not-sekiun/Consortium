// Auto-initialize asciinema players.
//
// Any element on a page that carries a `data-asciinema-cast` attribute is
// turned into an asciinema player, so individual docs pages never need an
// inline <script>. A page only writes a single element, for example:
//
//   <div
//     data-asciinema-cast="asciinema/disconnected_interpreter_demo.cast"
//     data-cols="100" data-rows="30" data-theme="gruvbox-dark"
//   ></div>
//
// Options map to asciinema-player create() options via data-* attributes:
//   data-cols, data-rows, data-theme, data-autoplay, data-loop, data-speed,
//   data-idle-time-limit, data-poster.

(function () {
  // Capture the site base once, from this script's own absolute URL. Doing it
  // at load time (when document.currentScript is available) keeps it correct
  // across instant navigations, where the script tag itself may not persist.
  var scriptSrc = (document.currentScript && document.currentScript.src) || "";
  var BASE = scriptSrc.replace(/javascripts\/asciinema-init\.js.*$/, "") || "/";

  function buildOptions(el) {
    var d = el.dataset;
    var opts = {
      cols: Number(d.cols) || 100,
      rows: Number(d.rows) || 30,
      theme: d.theme || "gruvbox-dark",
    };
    // Only forward optional settings when the author actually set them.
    if (d.autoplay) opts.autoPlay = d.autoplay === "true";
    if (d.loop) opts.loop = d.loop === "true";
    if (d.speed) opts.speed = Number(d.speed);
    if (d.idleTimeLimit) opts.idleTimeLimit = Number(d.idleTimeLimit);
    if (d.poster) opts.poster = d.poster;
    return opts;
  }

  function createPlayers() {
    if (typeof AsciinemaPlayer === "undefined") {
      return;
    }
    var targets = document.querySelectorAll("[data-asciinema-cast]");
    targets.forEach(function (el) {
      // Guard against double-initialization (document$ can emit more than
      // once for the same, still-mounted element).
      if (el.dataset.asciinemaReady) {
        return;
      }
      el.dataset.asciinemaReady = "true";
      AsciinemaPlayer.create(BASE + el.dataset.asciinemaCast, el, buildOptions(el));
    });
  }

  // Prefer Zensical's document$ observable: it emits on the initial load AND
  // after every instant navigation (navigation.instant), so players are
  // created on soft page swaps too. Fall back to DOMContentLoaded when the
  // observable is not present (instant navigation disabled or bundle absent).
  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(createPlayers);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", createPlayers);
  } else {
    createPlayers();
  }
})();
