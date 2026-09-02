(() => {
    "use strict";
    const open = document.querySelector("[data-owner-menu-open]");
    const close = document.querySelector("[data-owner-menu-close]");
    const setOpen = (value) => document.body.classList.toggle("owner-menu-open", value);
    open?.addEventListener("click", () => setOpen(true));
    close?.addEventListener("click", () => setOpen(false));
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") setOpen(false);
    });
})();
