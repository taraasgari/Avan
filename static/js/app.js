(() => {
  "use strict";
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {
        // PWA failure must never block shopping.
      });
    });
  }
})();
