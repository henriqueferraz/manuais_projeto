(() => {
  const root = document.querySelector("[data-tp-hero-carousel]");
  if (!root) return;

  const slides = Array.from(root.querySelectorAll("[data-tp-hero-slide]"));
  if (slides.length < 2) return;

  const prevBtn = root.querySelector("[data-tp-hero-prev]");
  const nextBtn = root.querySelector("[data-tp-hero-next]");
  let index = slides.findIndex((s) => s.classList.contains("is-active"));
  if (index < 0) index = 0;
  let timer = null;
  const INTERVAL_MS = 5000;

  function show(i) {
    index = (i + slides.length) % slides.length;
    slides.forEach((slide, n) => {
      const active = n === index;
      slide.classList.toggle("is-active", active);
      slide.setAttribute("aria-hidden", active ? "false" : "true");
    });
  }

  function next() {
    show(index + 1);
  }

  function prev() {
    show(index - 1);
  }

  function start() {
    stop();
    timer = window.setInterval(next, INTERVAL_MS);
  }

  function stop() {
    if (timer) {
      window.clearInterval(timer);
      timer = null;
    }
  }

  if (prevBtn) prevBtn.addEventListener("click", () => { prev(); start(); });
  if (nextBtn) nextBtn.addEventListener("click", () => { next(); start(); });

  root.addEventListener("mouseenter", stop);
  root.addEventListener("mouseleave", start);
  root.addEventListener("focusin", stop);
  root.addEventListener("focusout", (ev) => {
    if (!root.contains(ev.relatedTarget)) start();
  });

  show(index);
  start();
})();
