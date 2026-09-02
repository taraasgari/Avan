(() => {
  "use strict";
  let deferredPrompt = null;
  window.addEventListener("beforeinstallprompt", event => {
    event.preventDefault();
    deferredPrompt = event;
    document.documentElement.dataset.pwaInstallable = "true";
  });
  document.addEventListener("click", async event => {
    const button = event.target.closest("[data-pwa-install]");
    if (!button || !deferredPrompt) return;
    deferredPrompt.prompt();
    try { await deferredPrompt.userChoice; } catch (_) {}
    deferredPrompt = null;
    document.documentElement.dataset.pwaInstallable = "false";
  });
  window.addEventListener("appinstalled", () => {
    deferredPrompt = null;
    document.documentElement.dataset.pwaInstallable = "false";
  });
})();
