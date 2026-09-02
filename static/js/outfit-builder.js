(() => {
    "use strict";

    const page = document.querySelector("[data-outfit-id]");
    if (!page) return;

    const outfitId = page.dataset.outfitId;
    const csrf = document.querySelector('#wardrobe-csrf input[name="csrfmiddlewaretoken"]')?.value || "";
    const selected = document.querySelector("[data-selected-items]");
    const message = document.querySelector("[data-builder-message]");
    const count = document.querySelector("[data-piece-count]");
    const addOutfitButton = document.querySelector("[data-add-outfit-to-bag]");
    const CART_KEY = "avan_cart_token";

    const esc = value => String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

    const money = value => Number(value || 0).toLocaleString("en-US");

    function itemCount() {
        return selected.querySelectorAll("[data-outfit-item]").length;
    }

    function refreshCount() {
        const total = itemCount();
        count.textContent = total;
        addOutfitButton.disabled = total === 0;
        selected.querySelector("[data-selected-empty]")?.remove();
        if (!total) {
            selected.innerHTML = '<div class="builder-selected-empty" data-selected-empty><strong>START YOUR FIT.</strong><span>Add pieces from the catalog →</span></div>';
        }
    }

    function itemHtml(item) {
        const image = item.image
            ? `<img src="${esc(item.image)}" alt="${esc(item.product)}">`
            : "<span>AVAN</span>";
        return `
            <article class="builder-selected-item" data-outfit-item="${item.item_id}" data-variant-id="${item.id}">
                <div class="builder-selected-item__image">${image}</div>
                <div><small>${esc(item.position).toUpperCase()}</small><h3>${esc(item.product)}</h3><p>${esc(item.color)} / ${esc(item.size)}</p><strong>${money(item.price)} TOMAN</strong></div>
                <button type="button" data-remove-outfit-item="${item.item_id}">×</button>
            </article>`;
    }

    async function addItem(button) {
        const card = button.closest(".builder-product");
        const variantId = card.querySelector("[data-variant-select]").value;
        const position = card.querySelector("[data-position-select]").value;
        button.disabled = true;
        message.textContent = "ADDING PIECE...";
        try {
            const response = await fetch(`/api/outfits/${outfitId}/items/`, {
                method: "POST",
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
                body: JSON.stringify({variant_id: variantId, position}),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Could not add piece.");
            const existing = selected.querySelector(`[data-outfit-item="${data.item.item_id}"]`);
            if (existing) existing.outerHTML = itemHtml(data.item);
            else selected.insertAdjacentHTML("beforeend", itemHtml(data.item));
            refreshCount();
            bindRemoveButtons();
            message.textContent = data.created ? "PIECE ADDED ✓" : "PIECE UPDATED ✓";
        } catch (error) {
            message.textContent = error.message;
        } finally {
            button.disabled = false;
        }
    }

    async function removeItem(button) {
        const id = button.dataset.removeOutfitItem;
        button.disabled = true;
        try {
            const response = await fetch(`/api/outfits/${outfitId}/items/${id}/`, {
                method: "DELETE",
                headers: {"X-CSRFToken": csrf},
            });
            if (!response.ok) throw new Error("Could not remove piece.");
            button.closest("[data-outfit-item]")?.remove();
            refreshCount();
            message.textContent = "PIECE REMOVED";
        } catch (error) {
            button.disabled = false;
            message.textContent = error.message;
        }
    }

    function bindRemoveButtons() {
        document.querySelectorAll("[data-remove-outfit-item]").forEach(button => {
            button.onclick = () => removeItem(button);
        });
    }

    document.querySelectorAll("[data-add-outfit-item]").forEach(button => {
        button.addEventListener("click", () => addItem(button));
    });
    bindRemoveButtons();

    document.querySelector("[data-save-title]")?.addEventListener("click", async event => {
        const title = document.querySelector("[data-outfit-title]").value.trim();
        if (!title) return;
        const button = event.currentTarget;
        button.disabled = true;
        try {
            const response = await fetch(`/outfits/${outfitId}/update/`, {
                method: "PATCH",
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
                body: JSON.stringify({title}),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Could not save title.");
            message.textContent = "OUTFIT NAME SAVED ✓";
        } catch (error) {
            message.textContent = error.message;
        } finally {
            button.disabled = false;
        }
    });

    document.querySelector("[data-outfit-search]")?.addEventListener("input", event => {
        const q = event.target.value.trim().toLowerCase();
        document.querySelectorAll(".builder-product").forEach(card => {
            card.hidden = q && !card.dataset.productName.includes(q);
        });
    });

    async function getOrCreateCart() {
        let token = localStorage.getItem(CART_KEY);
        if (token) {
            const existing = await fetch(`/api/cart/${token}/`);
            if (existing.ok) return token;
            localStorage.removeItem(CART_KEY);
        }
        const response = await fetch("/api/cart/", {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
            body: "{}",
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Could not create bag.");
        localStorage.setItem(CART_KEY, data.token);
        return data.token;
    }

    addOutfitButton?.addEventListener("click", async () => {
        const items = [...selected.querySelectorAll("[data-outfit-item]")];
        if (!items.length) return;
        addOutfitButton.disabled = true;
        addOutfitButton.textContent = "ADDING FIT...";
        message.textContent = "CHECKING STOCK...";
        try {
            const token = await getOrCreateCart();
            let latestCart = null;
            for (const item of items) {
                const response = await fetch(`/api/cart/${token}/items/`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
                    body: JSON.stringify({variant_id: Number(item.dataset.variantId), quantity: 1}),
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || "One outfit piece could not be added.");
                latestCart = data;
            }
            message.textContent = "OUTFIT ADDED TO BAG ✓";
            window.dispatchEvent(new CustomEvent("avan:cart-updated", {detail: latestCart}));
        } catch (error) {
            message.textContent = error.message;
        } finally {
            addOutfitButton.disabled = false;
            addOutfitButton.textContent = "ADD OUTFIT TO BAG →";
        }
    });

    refreshCount();
})();
