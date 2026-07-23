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

  // Generic dropdown toggles (notifications, user menu). Keeps
  // aria-expanded in sync with visible state and supports Escape to
  // close + return focus to the trigger, for keyboard/screen-reader users.
  var dropdownTriggers = {};
  qsa("[data-dropdown-toggle]").forEach(function (btn) {
    var panelId = btn.getAttribute("data-dropdown-toggle");
    var panel = document.getElementById(panelId);
    if (!panel) return;
    btn.setAttribute("aria-haspopup", "true");
    btn.setAttribute("aria-expanded", "false");
    dropdownTriggers[panelId] = btn;
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      qsa(".dropdown-panel.open").forEach(function (p) {
        if (p !== panel) {
          p.classList.remove("open");
          var otherTrigger = dropdownTriggers[p.id];
          otherTrigger && otherTrigger.setAttribute("aria-expanded", "false");
        }
      });
      var nowOpen = panel.classList.toggle("open");
      btn.setAttribute("aria-expanded", nowOpen ? "true" : "false");
    });
  });
  function closeAllDropdowns() {
    qsa(".dropdown-panel.open").forEach(function (p) {
      p.classList.remove("open");
      var trigger = dropdownTriggers[p.id];
      trigger && trigger.setAttribute("aria-expanded", "false");
    });
  }
  document.addEventListener("click", function (e) {
    qsa(".dropdown-panel.open").forEach(function (p) {
      if (!p.contains(e.target)) {
        p.classList.remove("open");
        var trigger = dropdownTriggers[p.id];
        trigger && trigger.setAttribute("aria-expanded", "false");
      }
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      var openPanel = qs(".dropdown-panel.open");
      if (!openPanel) return;
      var trigger = dropdownTriggers[openPanel.id];
      closeAllDropdowns();
      trigger && trigger.focus();
    }
  });

  // Auto-submit a form when a marked field changes (CSP-friendly
  // replacement for inline onchange="this.form.submit()").
  qsa("[data-autosubmit]").forEach(function (field) {
    field.addEventListener("change", function () {
      field.form && field.form.submit();
    });
  });

  // Confirm before submitting a form (CSP-friendly replacement for
  // inline onsubmit="return confirm(...)").
  qsa("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.getAttribute("data-confirm"))) {
        e.preventDefault();
      }
    });
  });

  // Print the current page (CSP-friendly replacement for inline
  // onclick="window.print()").
  qsa("[data-print]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      window.print();
    });
  });

  // Immediate visual feedback for a link/button that triggers a
  // (possibly slow, e.g. AI-backed) full-page navigation, so a click
  // doesn't feel unresponsive while the next page loads. Progressive
  // enhancement only — the underlying navigation/submit is untouched.
  qsa("[data-loading-label]").forEach(function (el) {
    el.addEventListener("click", function () {
      el.setAttribute("aria-busy", "true");
      el.innerHTML =
        '<span class="bohlale-loader"><span></span><span></span><span></span><span></span></span> ' +
        el.getAttribute("data-loading-label");
    });
  });

  // Toggle a target element's visibility by id (CSP-friendly
  // replacement for a page-local inline <script> block).
  qsa("[data-toggle-target]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var target = document.getElementById(btn.getAttribute("data-toggle-target"));
      if (!target) return;
      target.style.display = target.style.display === "none" ? "table-row" : "none";
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
