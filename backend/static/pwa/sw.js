/* Service worker TechParts AI — shell + manuais + Background Sync (T-P.5 / ADR-0006) */
const CACHE = "tp-shell-v2";
const MANUAL_CACHE = "tp-manuals-v1";
const OUTBOX = "tp-ticket-outbox-v1";
const PRECACHE = [
  "/",
  "/static/design-system/theme.css",
  "/static/vendor/bootstrap/bootstrap.min.css",
  "/static/js/htmx.min.js",
  "/static/js/alpine.min.js",
  "/chamados/",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE).catch(() => undefined))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => ![CACHE, MANUAL_CACHE, OUTBOX].includes(k))
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

function isManualRequest(url) {
  return (
    url.pathname.startsWith("/manuais/") ||
    url.pathname.startsWith("/media/manuals/") ||
    url.pathname.startsWith("/media/manuais/")
  );
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Background Sync outbox: enfileira POST de chamados offline
  if (req.method === "POST" && url.pathname.startsWith("/chamados/")) {
    event.respondWith(handleTicketPost(req));
    return;
  }

  if (req.method !== "GET") return;

  if (isManualRequest(url)) {
    event.respondWith(cacheFirst(MANUAL_CACHE, req));
    return;
  }

  event.respondWith(
    caches.match(req).then((cached) => {
      const network = fetch(req)
        .then((res) => {
          if (res && res.ok && req.url.startsWith(self.location.origin)) {
            const clone = res.clone();
            caches.open(CACHE).then((c) => c.put(req, clone));
          }
          return res;
        })
        .catch(() => cached || caches.match("/"));
      return cached || network;
    })
  );
});

async function cacheFirst(cacheName, req) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req);
  if (hit) return hit;
  try {
    const res = await fetch(req);
    if (res && res.ok) {
      cache.put(req, res.clone());
    }
    return res;
  } catch (err) {
    return (
      hit ||
      new Response("Manual indisponível offline.", {
        status: 503,
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      })
    );
  }
}

async function handleTicketPost(req) {
  try {
    return await fetch(req.clone());
  } catch (err) {
    const body = await req.clone().text();
    const entry = {
      url: req.url,
      body,
      headers: { "Content-Type": req.headers.get("Content-Type") || "application/x-www-form-urlencoded" },
      ts: Date.now(),
    };
    const cache = await caches.open(OUTBOX);
    await cache.put(
      new Request(`outbox://${entry.ts}`),
      new Response(JSON.stringify(entry), { headers: { "Content-Type": "application/json" } })
    );
    if (self.registration && self.registration.sync) {
      try {
        await self.registration.sync.register("tp-ticket-sync");
      } catch (_) {
        /* sync pode falhar sem HTTPS / permissão */
      }
    }
    return new Response(
      JSON.stringify({
        ok: false,
        queued: true,
        detail: "Chamado enfileirado para envio quando a rede voltar.",
      }),
      { status: 202, headers: { "Content-Type": "application/json" } }
    );
  }
}

self.addEventListener("sync", (event) => {
  if (event.tag === "tp-ticket-sync") {
    event.waitUntil(flushTicketOutbox());
  }
});

async function flushTicketOutbox() {
  const cache = await caches.open(OUTBOX);
  const keys = await cache.keys();
  for (const key of keys) {
    const res = await cache.match(key);
    if (!res) continue;
    const entry = await res.json();
    try {
      const posted = await fetch(entry.url, {
        method: "POST",
        headers: entry.headers,
        body: entry.body,
        credentials: "include",
      });
      if (posted.ok || posted.status < 500) {
        await cache.delete(key);
      }
    } catch (_) {
      /* mantém na fila */
    }
  }
}
