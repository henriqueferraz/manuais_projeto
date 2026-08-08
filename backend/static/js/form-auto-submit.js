(() => {
  document.addEventListener("change", (event) => {
    const el = event.target;
    if (!(el instanceof Element) || !el.matches("[data-auto-submit]")) return;
    const form = el.form || el.closest("form");
    if (!form) return;
    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
    } else {
      form.submit();
    }
  });
})();
