
const CACHE = "avan-public-shell-v14";
const OFFLINE = "/offline/";

const SHELL = [
  "/",
  OFFLINE,
  "/static/css/base.css",
  "/static/css/shell.css",
  "/static/css/theme.css",
  "/static/js/app.js",
  "/static/pwa/manifest.webmanifest"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys =>
        Promise.all(
          keys
            .filter(key => key !== CACHE)
            .map(key => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;

  if (request.method !== "GET") return;

  const url = new URL(request.url);

  if (url.origin !== self.location.origin) return;

  // Never cache private or transactional pages.
  const networkOnly = [
    "/api/",
    "/admin/",
    "/owner/",
    "/checkout/",
    "/orders/",
    "/bag/",
    "/account/",
    "/size-passport/",
    "/outfits/",
    "/rewards/",
    "/report/"
  ];

  if (networkOnly.some(prefix => url.pathname.startsWith(prefix))) {
    return;
  }

  // Static files: network first, cache fallback.
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      fetch(request, { cache: "no-cache" })
        .then(response => {
          if (!response.ok) return response;

          return caches.open(CACHE).then(cache =>
            cache.put(request, response.clone()).then(() => response)
          );
        })
        .catch(() => caches.match(request))
    );

    return;
  }

  // Public HTML: network first, offline fallback.
  event.respondWith(
    fetch(request)
      .then(response => {
        if (response.ok && response.type === "basic") {
          // Clone immediately, before the browser starts consuming the body.
          const cacheCopy = response.clone();

          caches.open(CACHE)
            .then(cache => cache.put(request, cacheCopy))
            .catch(() => {});
        }

        return response;
      })
      .catch(() =>
        caches.match(request).then(hit => hit || caches.match(OFFLINE))
      )
  );
});
