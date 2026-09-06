(() => {
    "use strict";

    const openButton = document.querySelector("[data-owner-menu-open]");
    const closeButtons = document.querySelectorAll("[data-owner-menu-close]");
    const setOpen = (value) => document.body.classList.toggle("owner-menu-open", value);

    openButton?.addEventListener("click", () => setOpen(true));
    closeButtons.forEach((button) => button.addEventListener("click", () => setOpen(false)));

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") setOpen(false);
    });

    const search = document.querySelector("[data-owner-nav-search]");
    const nav = document.querySelector("[data-owner-nav]");
    const empty = document.querySelector("[data-owner-nav-empty]");

    const filterNavigation = () => {
        if (!search || !nav) return;
        const term = search.value.trim().toLocaleLowerCase();
        let visibleCount = 0;

        nav.querySelectorAll(".owner-nav-group").forEach((group) => {
            let groupVisible = 0;
            group.querySelectorAll("a").forEach((link) => {
                const haystack = (link.textContent || "").toLocaleLowerCase();
                const show = !term || haystack.includes(term);
                link.hidden = !show;
                if (show) groupVisible += 1;
            });
            group.hidden = groupVisible === 0;
            visibleCount += groupVisible;
        });

        if (empty) empty.hidden = visibleCount !== 0;
    };

    search?.addEventListener("input", filterNavigation);

    // Ctrl/Cmd+K focuses the Owner Console navigation search.
    document.addEventListener("keydown", (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k" && search) {
            event.preventDefault();
            if (window.innerWidth <= 900) setOpen(true);
            requestAnimationFrame(() => search.focus());
        }
    });
})();
