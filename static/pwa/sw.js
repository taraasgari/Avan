const CACHE = "avan-shell-v1";
const SHELL = ["/", "/static/css/base.css", "/static/js/app.js", "/static/pwa/manifest.webmanifest"];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // API, checkout, cart and account data must remain network-authoritative.
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/admin/")) return;

  event.respondWith(
    fetch(request)
      .then(response => {
        const copy = response.clone();
        caches.open(CACHE).then(cache => cache.put(request, copy));
        return response;
      })
      .catch(() => caches.match(request).then(hit => hit || caches.match("/")))
  );
});
