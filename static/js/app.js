(() => {
    "use strict";

    // PWA failure is never allowed to block shopping.
    if ("serviceWorker" in navigator) {
        window.addEventListener("load", () => {
            navigator.serviceWorker.register("/sw.js", {scope: "/"}).catch(() => {});
        });
    }

    const search = document.querySelector("[data-search-overlay]");
    const searchInput = document.querySelector("[data-search-input]");
    const menu = document.querySelector("[data-mobile-menu]");

    const lock = () => { document.body.style.overflow = "hidden"; };
    const unlock = () => { document.body.style.overflow = ""; };

    const openSearch = () => {
        search?.classList.add("is-open");
        search?.setAttribute("aria-hidden", "false");
        lock();
        window.setTimeout(() => searchInput?.focus(), 120);
    };
    const closeSearch = () => {
        search?.classList.remove("is-open");
        search?.setAttribute("aria-hidden", "true");
        unlock();
    };
    const openMenu = () => {
        menu?.classList.add("is-open");
        menu?.setAttribute("aria-hidden", "false");
        lock();
    };
    const closeMenu = () => {
        menu?.classList.remove("is-open");
        menu?.setAttribute("aria-hidden", "true");
        unlock();
    };

    document.querySelectorAll("[data-search-open]").forEach(el => el.addEventListener("click", openSearch));
    document.querySelectorAll("[data-search-close]").forEach(el => el.addEventListener("click", closeSearch));
    document.querySelectorAll("[data-menu-open]").forEach(el => el.addEventListener("click", openMenu));
    document.querySelectorAll("[data-menu-close]").forEach(el => el.addEventListener("click", closeMenu));

    document.addEventListener("click", event => {
        document.querySelectorAll("[data-user-menu][open]").forEach(details => {
            if (!details.contains(event.target)) details.removeAttribute("open");
        });
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            closeSearch();
            closeMenu();
            document.querySelectorAll("[data-user-menu][open]").forEach(details => {
                details.removeAttribute("open");
            });
        }
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
            event.preventDefault();
            openSearch();
        }
    });
})();
