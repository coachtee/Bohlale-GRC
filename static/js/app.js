(function () {
  "use strict";

  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  // Mobile sidebar toggle
  var sidebar = qs("#sidebar");
  var backdrop = qs("#sidebar-backdrop");
  qsa("[data-toggle-sidebar]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      sidebar && sidebar.classList.toggle("open");
      backdrop && backdrop.classList.toggle("open");
    });
  });
  backdrop && backdrop.addEventListener("click", function () {
    sidebar.classList.remove("open");
    backdrop.classList.remove("open");
  });

  // Generic dropdown toggles (notifications, user menu)
  qsa("[data-dropdown-toggle]").forEach(function (btn) {
    var panelId = btn.getAttribute("data-dropdown-toggle");
    var panel = document.getElementById(panelId);
    if (!panel) return;
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      qsa(".dropdown-panel.open").forEach(function (p) {
        if (p !== panel) p.classList.remove("open");
      });
      panel.classList.toggle("open");
    });
  });
  document.addEventListener("click", function (e) {
    qsa(".dropdown-panel.open").forEach(function (p) {
      if (!p.contains(e.target)) p.classList.remove("open");
    });
  });

  // Light / dark theme toggle
  var THEME_KEY = "bohlale-theme";
  function applyTheme(theme) {
    if (theme) {
      document.documentElement.setAttribute("data-theme", theme);
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  }
  var savedTheme = localStorage.getItem(THEME_KEY);
  if (savedTheme) applyTheme(savedTheme);

  qsa("[data-theme-toggle]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var current = document.documentElement.getAttribute("data-theme");
      var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
      var effectiveDark = current ? current === "dark" : prefersDark;
      var next = effectiveDark ? "light" : "dark";
      applyTheme(next);
      localStorage.setItem(THEME_KEY, next);
    });
  });
})();
