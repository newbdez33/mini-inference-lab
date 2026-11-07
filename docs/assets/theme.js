"use strict";

(() => {
  const storageKey = "mini-inference-theme";
  const requested = new URL(location.href).searchParams.get("theme");
  let saved;
  try {
    saved = localStorage.getItem(storageKey);
  } catch {
    // The theme control also works when browser storage is unavailable.
  }

  function applyTheme(theme) {
    const isDark = theme === "dark";
    document.documentElement.dataset.theme = theme;
    document.querySelector('meta[name="theme-color"]').content = isDark ? "#131b23" : "#f4f7f5";
    const button = document.querySelector(".theme-toggle");
    if (button) {
      button.setAttribute("aria-label", isDark ? "切换为浅色主题" : "切换为深色主题");
      button.querySelector("[data-theme-label]").textContent = isDark ? "浅色" : "深色";
      button.querySelector("[data-theme-icon]").textContent = isDark ? "☼" : "☾";
    }
    try {
      localStorage.setItem(storageKey, theme);
    } catch {
      // Keep the selected theme for the current page.
    }
  }

  const initial = [requested, saved].find(value => value === "dark" || value === "light") || "dark";
  applyTheme(initial);
  document.addEventListener("DOMContentLoaded", () => {
    applyTheme(document.documentElement.dataset.theme);
    document.querySelector(".theme-toggle")?.addEventListener("click", () => {
      const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      const url = new URL(location.href);
      url.searchParams.delete("theme");
      history.replaceState(null, "", url);
      applyTheme(theme);
    });
  });
})();
