(() => {
  "use strict";
  const bindFilter = (inputSelector, rowSelector) => {
    const input = document.querySelector(inputSelector);
    if (!input) return;
    const rows = [...document.querySelectorAll(rowSelector)];
    input.addEventListener("input", () => {
      const q = input.value.trim().toLowerCase();
      rows.forEach((row) => { row.hidden = q && !row.textContent.toLowerCase().includes(q); });
    });
  };
  bindFilter("[data-content-filter]", "[data-content-row]");
  bindFilter("[data-product-picker-filter]", "[data-product-picker-row]");
})();
