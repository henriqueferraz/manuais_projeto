(() => {
  if (!("serviceWorker" in navigator)) return;
  const url = document.body && document.body.dataset.swUrl;
  if (!url) return;
  navigator.serviceWorker.register(url).catch(function () {});
})();
