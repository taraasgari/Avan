const CACHE = "avan-shell-v5";
const SHELL = [
  "/",
  "/static/css/base.css",
  "/static/css/shell.css",
  "/static/js/app.js",
  "/static/pwa/manifest.webmanifest"
];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Private/transactional routes must always remain network-authoritative.
  const networkOnly = ["/api/", "/admin/", "/checkout/", "/orders/", "/bag/", "/account/", "/size-passport/", "/outfits/"];
  if (networkOnly.some(prefix => url.pathname.startsWith(prefix))) return;

  // Static assets: cache first, refresh in background.
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(request).then(hit => {
        const network = fetch(request).then(response => {
          if (response.ok) caches.open(CACHE).then(cache => cache.put(request, response.clone()));
          return response;
        }).catch(() => hit);
        return hit || network;
      })
    );
    return;
  }

  // Public pages: network first, cached fallback.
  event.respondWith(
    fetch(request)
      .then(response => {
        if (response.ok) caches.open(CACHE).then(cache => cache.put(request, response.clone()));
        return response;
      })
      .catch(() => caches.match(request).then(hit => hit || caches.match("/")))
  );
});
