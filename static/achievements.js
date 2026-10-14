(function (global) {
  "use strict";
  if (global.CodeQuestAchievements) return;

  var script = document.currentScript;
  var PENDING_URL = script && script.getAttribute("data-pending-url");

  var ENTER_MS = 450;     // animação de descida
  var DISPLAY_MS = 5000;  // tempo na tela
  var LEAVE_MS = 450;     // animação de saída
  var GAP_MS = 250;       // intervalo entre conquistas
  var MAX_QUEUE = 12;

  var CSS =
    ".cq-ach-host{position:fixed;top:max(12px,env(safe-area-inset-top));left:50%;transform:translateX(-50%);" +
    "z-index:2147483000;width:min(380px,calc(100vw - 24px));display:flex;flex-direction:column;gap:8px;pointer-events:none}" +
    ".cq-ach{pointer-events:none;display:flex;align-items:center;gap:12px;padding:10px 16px 10px 10px;" +
    "background:#1c1c1f;border:2px solid #55555e;border-radius:4px;color:#fff;text-align:left;" +
    "box-shadow:0 0 0 2px #0b0b0d,0 10px 24px rgba(0,0,0,.45);" +
    "font-family:'Segoe UI',system-ui,-apple-system,sans-serif;line-height:1.3;" +
    "opacity:0;transform:translateY(-140%);" +
    "transition:transform " + ENTER_MS + "ms cubic-bezier(.22,1,.36,1),opacity .35s ease}" +
    ".cq-ach.cq-in{opacity:1;transform:translateY(0)}" +
    ".cq-ach.cq-out{opacity:0;transform:translateY(-60%);transition:transform " + LEAVE_MS + "ms ease-in,opacity .35s ease}" +
    ".cq-ach-icon{flex:0 0 46px;height:46px;display:flex;align-items:center;justify-content:center;font-size:26px;" +
    "background:#2d2d33;border:2px solid #7a7a86;border-radius:3px;box-shadow:inset 0 0 0 2px #1a1a1d}" +
    ".cq-ach-text{min-width:0}" +
    ".cq-ach-kicker{display:block;font-size:11px;font-weight:800;letter-spacing:.6px;text-transform:uppercase;color:#ffe14d}" +
    ".cq-ach-name{display:block;font-size:16px;font-weight:800;color:#fff}" +
    ".cq-ach-desc{display:block;margin-top:2px;font-size:12px;color:#c9c9d1}" +
    "@media (prefers-reduced-motion:reduce){.cq-ach,.cq-ach.cq-out{transition:opacity .2s linear;transform:none}}";

  var queue = [];
  var seen = Object.create(null);
  var active = false;
  var host = null;

  function noop() {}

  function whenBodyReady(fn) {
    if (document.body) return fn();
    document.addEventListener("DOMContentLoaded", fn, { once: true });
  }

  function ensureHost() {
    if (host && host.isConnected) return host;
    if (!document.getElementById("cq-ach-style")) {
      var st = document.createElement("style");
      st.id = "cq-ach-style";
      st.textContent = CSS;
      document.head.appendChild(st);
    }
    host = document.createElement("div");
    host.className = "cq-ach-host";
    host.setAttribute("role", "status");
    host.setAttribute("aria-live", "polite");
    document.body.appendChild(host);
    return host;
  }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text) node.textContent = text; // textContent: nome/descrição nunca viram HTML
    return node;
  }

  function build(badge) {
    var card = el("div", "cq-ach");
    card.appendChild(el("div", "cq-ach-icon", badge.icon || "🏆"));
    var text = el("div", "cq-ach-text");
    text.appendChild(el("span", "cq-ach-kicker", "Conquista desbloqueada!"));
    text.appendChild(el("span", "cq-ach-name", badge.name));
    if (badge.description) text.appendChild(el("span", "cq-ach-desc", badge.description));
    card.appendChild(text);
    return card;
  }

  function next() {
    if (active || !queue.length) return;
    if (document.hidden) {
      document.addEventListener("visibilitychange", next, { once: true });
      return;
    }
    active = true;
    var card = build(queue.shift());
    ensureHost().appendChild(card);

    // dois frames: garante que a transição de entrada seja animada
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { card.classList.add("cq-in"); });
    });

    setTimeout(function () {
      card.classList.remove("cq-in");
      card.classList.add("cq-out");
      setTimeout(function () {
        if (card.parentNode) card.parentNode.removeChild(card);
        active = false;
        setTimeout(next, GAP_MS);
      }, LEAVE_MS);
    }, ENTER_MS + DISPLAY_MS);
  }

  function show(badges) {
    if (!badges) return;
    if (!Array.isArray(badges)) badges = [badges];
    badges.forEach(function (b) {
      if (!b || !b.name) return;
      var key = b.code || b.name;
      if (seen[key] || queue.length >= MAX_QUEUE) return;
      seen[key] = true;
      queue.push(b);
    });
    whenBodyReady(next);
  }

  /* ---- 1) fetch(): qualquer JSON com new_badges vira toast ---- */
  function inspect(res) {
    try {
      if (!res || !res.ok || res.type === "opaque") return;
      if (res.url && new URL(res.url, location.href).origin !== location.origin) return;
      var ct = (res.headers && res.headers.get("content-type")) || "";
      if (ct.indexOf("json") === -1) return;
      res.clone().json().then(function (data) {
        if (data && Array.isArray(data.new_badges) && data.new_badges.length) show(data.new_badges);
      }).catch(noop);
    } catch (e) { /* nunca atrapalhar a página */ }
  }

  var originalFetch = global.fetch;
  if (typeof originalFetch === "function") {
    global.fetch = function () {
      var promise = originalFetch.apply(this, arguments);
      try { promise.then(inspect, noop); } catch (e) { /* ignora */ }
      return promise;
    };
  }

  /* ---- 2) conquistas pendentes (ganhas em outra requisição/página) ---- */
  function loadPending() {
    if (!PENDING_URL || typeof originalFetch !== "function") return;
    originalFetch(PENDING_URL, {
      credentials: "same-origin",
      cache: "no-store",
      headers: { Accept: "application/json" }
    })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) { if (data && data.badges) show(data.badges); })
      .catch(noop);
  }

  global.CodeQuestAchievements = { show: show };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadPending, { once: true });
  } else {
    loadPending();
  }
  // voltar pelo histórico (bfcache) não recarrega a página
  global.addEventListener("pageshow", function (ev) { if (ev.persisted) loadPending(); });
})(window);
