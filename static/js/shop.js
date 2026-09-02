(() => {
    const filters = document.querySelector("[data-filters]");
    const backdrop = document.querySelector("[data-filter-backdrop]");
    const openButton = document.querySelector("[data-filter-open]");
    const closeButton = document.querySelector("[data-filter-close]");

    if (!filters) return;

    const openFilters = () => {
        filters.classList.add("is-open");
        backdrop?.classList.add("is-open");
        document.body.style.overflow = "hidden";
    };

    const closeFilters = () => {
        filters.classList.remove("is-open");
        backdrop?.classList.remove("is-open");
        document.body.style.overflow = "";
    };

    openButton?.addEventListener("click", openFilters);
    closeButton?.addEventListener("click", closeFilters);
    backdrop?.addEventListener("click", closeFilters);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeFilters();
        }
    });
})();