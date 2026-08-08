(() => {
  document.addEventListener(
    "submit",
    (ev) => {
      const form = ev.target;
      if (!(form instanceof HTMLFormElement) || !form.hasAttribute("data-confirm")) return;
      const msg = form.getAttribute("data-confirm") || "Confirmar?";
      if (!window.confirm(msg)) {
        ev.preventDefault();
      }
    },
    true
  );
})();
