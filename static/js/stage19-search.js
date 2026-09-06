(() => {
  "use strict";
  const forms = document.querySelectorAll("[data-live-search-form]");
  if (!forms.length) return;

  forms.forEach((form) => {
    const input = form.querySelector("[data-live-search-input]");
    const box = form.querySelector("[data-search-suggestions]");
    if (!input || !box) return;
    let timer = null;
    let controller = null;
    let activeIndex = -1;

    const hide = () => { box.hidden = true; box.innerHTML = ""; activeIndex = -1; };
    const esc = (value) => String(value ?? "").replace(/[&<>'"]/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));

    function render(data) {
      const groups = data && Array.isArray(data.groups) ? data.groups : [];
      if (!groups.length) {
        box.innerHTML = `<div class="search-suggest-empty">${document.documentElement.dir === "rtl" ? "نتیجه‌ای پیدا نشد." : "No suggestions found."}</div>`;
        box.hidden = false;
        return;
      }
      box.innerHTML = groups.map((group) => `
        <section class="search-suggest-group">
          <strong>${esc(group.title)}</strong>
          ${group.items.map((item) => `
            <a class="search-suggest-item" href="${esc(item.url)}">
              ${item.image ? `<img src="${esc(item.image)}" alt="">` : `<span class="search-suggest-thumb">${esc((item.kind || "A").slice(0,1).toUpperCase())}</span>`}
              <div><strong>${esc(item.title)}</strong><small>${esc(item.subtitle)}</small></div>
              <em>↗</em>
            </a>`).join("")}
        </section>`).join("");
      box.hidden = false;
    }

    async function loadSuggestions() {
      const q = input.value.trim();
      if (q.length < 2) { hide(); return; }
      if (controller) controller.abort();
      controller = new AbortController();
      try {
        const res = await fetch(`/search/suggest/?q=${encodeURIComponent(q)}`, {headers:{"X-Requested-With":"XMLHttpRequest"}, signal:controller.signal});
        if (!res.ok) throw new Error("suggest failed");
        render(await res.json());
      } catch (err) {
        if (err.name !== "AbortError") hide();
      }
    }

    input.addEventListener("input", () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(loadSuggestions, 170);
    });
    input.addEventListener("focus", () => { if (input.value.trim().length >= 2) loadSuggestions(); });
    input.addEventListener("keydown", (event) => {
      const items = [...box.querySelectorAll(".search-suggest-item")];
      if (!items.length || box.hidden) return;
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        activeIndex += event.key === "ArrowDown" ? 1 : -1;
        if (activeIndex < 0) activeIndex = items.length - 1;
        if (activeIndex >= items.length) activeIndex = 0;
        items.forEach((item, index) => item.classList.toggle("is-active", index === activeIndex));
        items[activeIndex].scrollIntoView({block:"nearest"});
      } else if (event.key === "Enter" && activeIndex >= 0) {
        event.preventDefault();
        window.location.assign(items[activeIndex].href);
      } else if (event.key === "Escape") {
        hide(); input.blur();
      }
    });
    document.addEventListener("click", (event) => { if (!form.contains(event.target)) hide(); });
  });
})();
