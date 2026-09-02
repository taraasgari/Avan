(() => {
    "use strict";

    const csrf = document.querySelector('#explore-csrf input[name="csrfmiddlewaretoken"]')?.value || "";

    async function jsonFetch(url, options = {}) {
        const response = await fetch(url, options);
        let data = {};
        try { data = await response.json(); } catch (_) {}
        if (response.status === 403) {
            const next = encodeURIComponent(location.pathname + location.search);
            location.href = `/account/login/?next=${next}`;
            throw new Error("Sign in required.");
        }
        if (!response.ok) throw new Error(data.detail || "Request failed.");
        return data;
    }

    document.querySelectorAll("[data-design-like]").forEach(button => {
        button.addEventListener("click", async () => {
            const id = button.dataset.designLike;
            button.disabled = true;
            try {
                const data = await jsonFetch(`/api/designs/${id}/like/`, {
                    method: "POST",
                    headers: {"X-CSRFToken": csrf, "Accept": "application/json"},
                });
                button.classList.toggle("is-active", data.active);
                const card = button.closest("[data-design-card]");
                const stat = card?.querySelector(".explore-card__stats span:first-child");
                if (stat) stat.textContent = `♥ ${data.count}`;
                const count = document.querySelector("[data-like-count]");
                if (count && document.querySelector(`[data-design-like="${id}"]`)) count.textContent = data.count;
            } catch (error) {
                if (error.message !== "Sign in required.") alert(error.message);
            } finally { button.disabled = false; }
        });
    });

    document.querySelectorAll("[data-design-save]").forEach(button => {
        button.addEventListener("click", async () => {
            const id = button.dataset.designSave;
            button.disabled = true;
            try {
                const data = await jsonFetch(`/api/designs/${id}/save/`, {
                    method: "POST",
                    headers: {"X-CSRFToken": csrf, "Accept": "application/json"},
                });
                button.classList.toggle("is-active", data.active);
                if (button.textContent.trim() === "SAVE" || button.textContent.trim() === "SAVED") {
                    button.textContent = data.active ? "SAVED" : "SAVE";
                }
            } catch (error) {
                if (error.message !== "Sign in required.") alert(error.message);
            } finally { button.disabled = false; }
        });
    });

    document.querySelectorAll("[data-design-remix]").forEach(button => {
        button.addEventListener("click", async () => {
            const id = button.dataset.designRemix;
            button.disabled = true;
            const original = button.textContent;
            button.textContent = "CREATING...";
            try {
                const data = await jsonFetch(`/api/designs/${id}/remix/`, {
                    method: "POST",
                    headers: {"X-CSRFToken": csrf, "Accept": "application/json"},
                });
                location.href = `/design/${data.id}/`;
            } catch (error) {
                if (error.message !== "Sign in required.") alert(error.message);
                button.disabled = false;
                button.textContent = original;
            }
        });
    });

    const productNode = document.getElementById("public-design-product-data");
    const wearButton = document.querySelector("[data-wear-design]");
    if (!productNode || !wearButton) return;

    const product = JSON.parse(productNode.textContent);
    const designRoot = document.querySelector("[data-public-design]");
    const designId = designRoot?.dataset.publicDesign;
    const designFee = Number(designRoot?.dataset.designFee || 0);
    const sizesBox = document.querySelector("[data-public-sizes]");
    const stockBox = document.querySelector("[data-public-stock]");
    const message = document.querySelector("[data-wear-message]");
    let selectedVariant = null;

    function renderSizes() {
        const sizes = [];
        const seen = new Set();
        product.variants.forEach(variant => {
            if (!seen.has(variant.size_id)) {
                seen.add(variant.size_id);
                sizes.push({id: variant.size_id, name: variant.size});
            }
        });
        sizesBox.innerHTML = sizes.map(size => {
            const available = product.variants.some(v => Number(v.size_id) === Number(size.id) && Number(v.stock) > 0);
            return `<button type="button" data-public-size="${size.id}" ${available ? "" : "disabled"}>${size.name}</button>`;
        }).join("");

        sizesBox.querySelectorAll("[data-public-size]").forEach(button => {
            button.addEventListener("click", () => {
                sizesBox.querySelectorAll("button").forEach(b => b.classList.remove("is-active"));
                button.classList.add("is-active");
                selectedVariant = product.variants.find(v => Number(v.size_id) === Number(button.dataset.publicSize) && Number(v.stock) > 0) || null;
                if (selectedVariant) {
                    stockBox.textContent = `${selectedVariant.stock} AVAILABLE / ${(Number(selectedVariant.price) + designFee).toLocaleString("en-US")} TOMAN TOTAL`;
                    wearButton.disabled = false;
                } else {
                    stockBox.textContent = "OUT OF STOCK";
                    wearButton.disabled = true;
                }
            });
        });
    }

    async function getCartToken() {
        let token = localStorage.getItem("avan_cart_token");
        if (token) {
            const response = await fetch(`/api/cart/${token}/`);
            if (response.ok) return token;
            localStorage.removeItem("avan_cart_token");
        }
        const response = await fetch("/api/cart/", {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
            body: "{}",
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Could not create bag.");
        localStorage.setItem("avan_cart_token", data.token);
        return data.token;
    }

    wearButton.addEventListener("click", async () => {
        if (!selectedVariant) return;
        wearButton.disabled = true;
        wearButton.textContent = "ADDING...";
        message.textContent = "";
        try {
            const token = await getCartToken();
            const response = await fetch(`/api/cart/${token}/items/`, {
                method: "POST",
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrf, "Accept": "application/json"},
                body: JSON.stringify({variant_id: selectedVariant.id, quantity: 1, design_id: designId}),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Could not add design to bag.");
            message.textContent = "ADDED TO YOUR BAG ✓";
            window.dispatchEvent(new CustomEvent("avan:cart-updated", {detail: data}));
        } catch (error) {
            message.textContent = error.message;
        } finally {
            wearButton.disabled = false;
            wearButton.textContent = "ADD DESIGN TO BAG";
        }
    });

    renderSizes();
})();
