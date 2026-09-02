(() => {
    "use strict";

    const root = document.querySelector("[data-studio]");
    const productsScript = document.getElementById("studio-products-data");
    if (!root || !productsScript) return;

    const products = JSON.parse(productsScript.textContent || "[]");
    if (!products.length) return;

    const initialScript = document.getElementById("studio-initial-design");
    const initial = initialScript ? JSON.parse(initialScript.textContent || "null") : null;
    const authenticated = root.dataset.authenticated === "1";
    const csrf = document.querySelector('#studio-csrf input[name="csrfmiddlewaretoken"]')?.value || "";

    const els = {
        product: document.querySelector("[data-product-select]"),
        colors: document.querySelector("[data-color-options]"),
        stage: document.querySelector("[data-garment-stage]"),
        garmentImage: document.querySelector("[data-garment-image]"),
        garmentFallback: document.querySelector("[data-garment-fallback]"),
        printArea: document.querySelector("[data-print-area]"),
        garmentName: document.querySelector("[data-current-garment]"),
        sideName: document.querySelector("[data-current-side]"),
        price: document.querySelector("[data-studio-price]"),
        layers: document.querySelector("[data-layers-list]"),
        title: document.querySelector("[data-design-title]"),
        save: document.querySelector("[data-save-design]"),
        publish: document.querySelector("[data-publish-design]"),
        saveState: document.querySelector("[data-save-state]"),
        propEmpty: document.querySelector("[data-properties-empty]"),
        propPanel: document.querySelector("[data-properties-panel]"),
        propText: document.querySelector("[data-prop-text]"),
        propColor: document.querySelector("[data-prop-color]"),
        propFontSize: document.querySelector("[data-prop-font-size]"),
        propWidth: document.querySelector("[data-prop-width]"),
        propRotation: document.querySelector("[data-prop-rotation]"),
        fontSizeValue: document.querySelector("[data-font-size-value]"),
        widthValue: document.querySelector("[data-width-value]"),
        rotationValue: document.querySelector("[data-rotation-value]"),
        upload: document.querySelector("[data-image-upload]"),
        sizes: document.querySelector("[data-studio-sizes]"),
        stock: document.querySelector("[data-studio-stock]"),
        addBag: document.querySelector("[data-studio-add-bag]"),
        buyMessage: document.querySelector("[data-studio-buy-message]"),
        publishRemix: document.querySelector("[data-publish-remix]"),
        publishSale: document.querySelector("[data-publish-sale]"),
    };

    const freshDesignData = () => ({ version: 1, sides: { front: [], back: [] } });
    let state = {
        designId: initial?.id || null,
        productId: Number(initial?.product_id || products[0].id),
        colorId: initial?.color_id ? Number(initial.color_id) : null,
        sizeId: null,
        side: "front",
        selectedLayerId: null,
        designData: initial?.design_data?.sides ? initial.design_data : freshDesignData(),
        dirty: false,
    };

    const uid = () => window.crypto?.randomUUID?.() || `layer-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const productById = () => products.find(p => Number(p.id) === Number(state.productId)) || products[0];
    const currentLayers = () => state.designData.sides[state.side] || (state.designData.sides[state.side] = []);
    const selectedLayer = () => currentLayers().find(layer => layer.id === state.selectedLayerId) || null;
    const markDirty = () => { state.dirty = true; els.saveState.textContent = "UNSAVED"; };

    function ensureColor(product) {
        if (!product.colors.some(c => Number(c.id) === Number(state.colorId))) {
            state.colorId = product.colors[0]?.id || null;
        }
    }

    function pickMockup(product) {
        return product.mockups.find(m => m.side === state.side && Number(m.color_id) === Number(state.colorId))
            || product.mockups.find(m => m.side === state.side && m.color_id == null)
            || null;
    }

    function renderGarment() {
        const product = productById();
        ensureColor(product);
        els.product.value = String(product.id);
        els.garmentName.textContent = product.name;
        els.sideName.textContent = state.side.toUpperCase();
        els.price.textContent = Number(product.price || 0).toLocaleString("en-US");

        const mockup = pickMockup(product);
        const imageUrl = mockup?.url || product.image;
        if (imageUrl) {
            els.garmentImage.src = imageUrl;
            els.garmentImage.classList.add("is-visible");
            els.garmentFallback.classList.add("is-hidden");
        } else {
            els.garmentImage.classList.remove("is-visible");
            els.garmentImage.removeAttribute("src");
            els.garmentFallback.classList.remove("is-hidden");
        }

        const print = mockup?.print || { x:25, y:22, width:50, height:55 };
        Object.assign(els.printArea.style, {
            left: `${print.x}%`, top: `${print.y}%`, width: `${print.width}%`, height: `${print.height}%`,
        });

        els.colors.innerHTML = product.colors.map(color => `
            <button type="button" class="studio-color ${Number(color.id) === Number(state.colorId) ? "is-active" : ""}"
                style="--swatch:${color.hex}" data-studio-color="${color.id}" title="${escapeHtml(color.name)}"></button>
        `).join("");
        els.colors.querySelectorAll("[data-studio-color]").forEach(button => {
            button.addEventListener("click", () => {
                state.colorId = Number(button.dataset.studioColor);
                state.sizeId = null;
                markDirty();
                renderAll();
            });
        });
        renderSizes(product);
    }

    function matchingVariants(product) {
        return product.variants.filter(v => Number(v.color_id) === Number(state.colorId));
    }

    function selectedVariant() {
        const product = productById();
        return matchingVariants(product).find(v => Number(v.size_id) === Number(state.sizeId)) || null;
    }

    function renderSizes(product) {
        if (!els.sizes) return;
        const variants = matchingVariants(product);
        const seen = new Set();
        const sizes = [];
        variants.forEach(v => {
            if (!seen.has(v.size_id)) { seen.add(v.size_id); sizes.push({id:v.size_id, name:v.size}); }
        });
        els.sizes.innerHTML = sizes.map(size => {
            const variant = variants.find(v => Number(v.size_id) === Number(size.id));
            const available = variant && Number(variant.stock) > 0;
            return `<button type="button" data-studio-size="${size.id}" class="${Number(size.id) === Number(state.sizeId) ? "is-active" : ""}" ${available ? "" : "disabled"}>${escapeHtml(size.name)}</button>`;
        }).join("");
        els.sizes.querySelectorAll("[data-studio-size]").forEach(button => button.addEventListener("click", () => {
            state.sizeId = Number(button.dataset.studioSize);
            renderSizes(product);
            renderBuyState();
        }));
        renderBuyState();
    }

    function renderBuyState() {
        const variant = selectedVariant();
        if (!els.stock || !els.addBag) return;
        if (!state.sizeId) { els.stock.textContent = "SELECT A SIZE"; els.addBag.disabled = true; return; }
        if (!variant || Number(variant.stock) <= 0) { els.stock.textContent = "OUT OF STOCK"; els.addBag.disabled = true; return; }
        els.stock.textContent = `${variant.stock} AVAILABLE`;
        els.addBag.disabled = false;
    }

    function escapeHtml(value) {
        return String(value ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
    }

    function layerElement(layer) {
        const el = document.createElement("div");
        el.className = `design-layer design-layer--${layer.type}${layer.id === state.selectedLayerId ? " is-selected" : ""}`;
        el.dataset.layerId = layer.id;
        el.style.left = `${layer.x}%`;
        el.style.top = `${layer.y}%`;
        el.style.width = `${layer.width}%`;
        el.style.zIndex = String(layer.z || 0);
        el.style.transform = `translate(-50%, -50%) rotate(${layer.rotation || 0}deg)`;

        if (layer.type === "text") {
            el.textContent = layer.text || "YOUR TEXT";
            el.style.fontSize = `${layer.fontSize || 38}px`;
            el.style.color = layer.color || "#111111";
            el.style.fontWeight = layer.fontWeight || "800";
            el.style.textAlign = layer.align || "center";
        } else {
            const img = document.createElement("img");
            img.src = layer.url;
            img.alt = "Uploaded design asset";
            el.appendChild(img);
        }

        const handle = document.createElement("span");
        handle.className = "layer-resize-handle";
        handle.dataset.resizeHandle = "1";
        el.appendChild(handle);

        el.addEventListener("pointerdown", event => startLayerPointer(event, layer));
        return el;
    }

    function renderLayers() {
        els.printArea.innerHTML = "";
        currentLayers().sort((a,b) => (a.z||0) - (b.z||0)).forEach(layer => els.printArea.appendChild(layerElement(layer)));
        els.layers.innerHTML = currentLayers().slice().sort((a,b)=>(b.z||0)-(a.z||0)).map(layer => `
            <button type="button" class="layer-row ${layer.id === state.selectedLayerId ? "is-active" : ""}" data-layer-row="${layer.id}">
                <span>${escapeHtml(layer.type === "text" ? layer.text : "IMAGE")}</span><small>${layer.type.toUpperCase()}</small>
            </button>
        `).join("") || '<div style="color:#999;font-size:.65rem">NO LAYERS</div>';
        els.layers.querySelectorAll("[data-layer-row]").forEach(button => button.addEventListener("click", () => {
            state.selectedLayerId = button.dataset.layerRow;
            renderLayers();
            renderProperties();
        }));
    }

    function startLayerPointer(event, layer) {
        event.preventDefault();
        state.selectedLayerId = layer.id;
        renderLayers();
        renderProperties();
        const isResize = event.target.matches("[data-resize-handle]");
        const rect = els.printArea.getBoundingClientRect();
        const startX = event.clientX;
        const startY = event.clientY;
        const original = { x: layer.x, y: layer.y, width: layer.width };

        function move(ev) {
            if (isResize) {
                const deltaPct = ((ev.clientX - startX) / rect.width) * 100;
                layer.width = Math.max(5, Math.min(100, original.width + deltaPct * 2));
            } else {
                layer.x = Math.max(0, Math.min(100, original.x + ((ev.clientX - startX) / rect.width) * 100));
                layer.y = Math.max(0, Math.min(100, original.y + ((ev.clientY - startY) / rect.height) * 100));
            }
            markDirty();
            renderLayers();
            renderProperties();
        }
        function up() {
            window.removeEventListener("pointermove", move);
            window.removeEventListener("pointerup", up);
        }
        window.addEventListener("pointermove", move);
        window.addEventListener("pointerup", up, { once:true });
    }

    function renderProperties() {
        const layer = selectedLayer();
        els.propEmpty.hidden = Boolean(layer);
        els.propPanel.hidden = !layer;
        if (!layer) return;
        document.querySelectorAll(".property-text-only").forEach(el => el.hidden = layer.type !== "text");
        if (layer.type === "text") {
            els.propText.value = layer.text || "";
            els.propColor.value = /^#[0-9a-f]{6}$/i.test(layer.color || "") ? layer.color : "#111111";
            els.propFontSize.value = layer.fontSize || 38;
            els.fontSizeValue.textContent = `${Math.round(layer.fontSize || 38)}PX`;
        }
        els.propWidth.value = layer.width || 35;
        els.propRotation.value = layer.rotation || 0;
        els.widthValue.textContent = `${Math.round(layer.width || 35)}%`;
        els.rotationValue.textContent = `${Math.round(layer.rotation || 0)}°`;
    }

    function renderAll() {
        renderGarment();
        renderLayers();
        renderProperties();
    }

    function addText() {
        const layers = currentLayers();
        const layer = { id:uid(), type:"text", text:"YOUR TEXT", x:50, y:45, width:55, rotation:0, fontSize:38, color:"#111111", fontWeight:"800", align:"center", z: layers.length + 1 };
        layers.push(layer);
        state.selectedLayerId = layer.id;
        markDirty();
        renderLayers();
        renderProperties();
    }

    async function uploadImage(file) {
        if (!authenticated) {
            window.location.href = `/account/login/?next=${encodeURIComponent(location.pathname + location.search)}`;
            return;
        }
        const form = new FormData();
        form.append("image", file);
        els.saveState.textContent = "UPLOADING...";
        const response = await fetch("/api/designs/assets/", { method:"POST", headers:{"X-CSRFToken":csrf}, body:form });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Image upload failed.");
        const layers = currentLayers();
        const layer = { id:uid(), type:"image", assetId:data.id, url:data.url, x:50, y:45, width:42, rotation:0, z:layers.length + 1 };
        layers.push(layer);
        state.selectedLayerId = layer.id;
        markDirty();
        renderLayers(); renderProperties();
    }

    function designPayload() {
        return {
            title: els.title.value.trim() || "Untitled Design",
            base_product: state.productId,
            base_color: state.colorId,
            design_data: state.designData,
        };
    }

    async function saveDesign() {
        if (!authenticated) {
            window.location.href = `/account/login/?next=${encodeURIComponent(location.pathname + location.search)}`;
            return null;
        }
        els.save.disabled = true;
        els.saveState.textContent = "SAVING...";
        const response = await fetch(state.designId ? `/api/designs/${state.designId}/` : "/api/designs/", {
            method: state.designId ? "PATCH" : "POST",
            headers:{"Content-Type":"application/json","X-CSRFToken":csrf,"Accept":"application/json"},
            body:JSON.stringify(designPayload()),
        });
        const data = await response.json();
        els.save.disabled = false;
        if (!response.ok) {
            els.saveState.textContent = "SAVE FAILED";
            throw new Error(data.detail || Object.values(data)[0] || "Could not save design.");
        }
        state.designId = data.id;
        state.dirty = false;
        els.saveState.textContent = "SAVED ✓";
        if (!location.pathname.includes(data.id)) history.replaceState({}, "", `/design/${data.id}/`);
        return data;
    }

    async function publishDesign() {
        const saved = await saveDesign();
        if (!saved) return;
        const allowRemix = Boolean(els.publishRemix?.checked);
        const isForSale = Boolean(els.publishSale?.checked);
        els.publish.disabled = true;
        els.saveState.textContent = "PUBLISHING...";
        const response = await fetch(`/api/designs/${state.designId}/publish/`, {
            method:"POST", headers:{"Content-Type":"application/json","X-CSRFToken":csrf}, body:JSON.stringify({allow_remix:allowRemix,is_for_sale:isForSale}),
        });
        const data = await response.json();
        els.publish.disabled = false;
        if (!response.ok) throw new Error(data.detail || "Could not publish design.");
        els.saveState.textContent = "PUBLISHED ✓";
    }

    async function getCartToken() {
        let token = localStorage.getItem("avan_cart_token");
        if (token) {
            const check = await fetch(`/api/cart/${token}/`);
            if (check.ok) return token;
            localStorage.removeItem("avan_cart_token");
        }
        const response = await fetch("/api/cart/", {method:"POST", headers:{"Content-Type":"application/json","X-CSRFToken":csrf}, body:"{}"});
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Could not create bag.");
        localStorage.setItem("avan_cart_token", data.token);
        return data.token;
    }

    async function addCustomDesignToBag() {
        const variant = selectedVariant();
        if (!variant) throw new Error("Choose an available size.");
        if (!authenticated) {
            location.href = `/account/login/?next=${encodeURIComponent(location.pathname + location.search)}`;
            return;
        }
        const saved = await saveDesign();
        if (!saved) return;
        els.addBag.disabled = true;
        els.addBag.textContent = "ADDING...";
        els.buyMessage.textContent = "";
        try {
            const token = await getCartToken();
            const response = await fetch(`/api/cart/${token}/items/`, {
                method:"POST",
                headers:{"Content-Type":"application/json","X-CSRFToken":csrf,"Accept":"application/json"},
                body:JSON.stringify({variant_id:variant.id,quantity:1,design_id:state.designId}),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Could not add design to bag.");
            els.buyMessage.textContent = "ADDED TO YOUR BAG ✓";
            window.dispatchEvent(new CustomEvent("avan:cart-updated", {detail:data}));
        } finally {
            els.addBag.textContent = "ADD CUSTOM DESIGN TO BAG";
            renderBuyState();
        }
    }

    els.addBag?.addEventListener("click", async () => {
        try { await addCustomDesignToBag(); } catch (error) { els.buyMessage.textContent = error.message; renderBuyState(); }
    });

    els.product.addEventListener("change", () => {
        state.productId = Number(els.product.value);
        state.colorId = null;
        state.sizeId = null;
        state.selectedLayerId = null;
        markDirty(); renderAll();
    });
    document.querySelectorAll("[data-side]").forEach(button => button.addEventListener("click", () => {
        state.side = button.dataset.side;
        state.selectedLayerId = null;
        document.querySelectorAll("[data-side]").forEach(b => b.classList.toggle("is-active", b === button));
        renderAll();
    }));
    document.querySelector("[data-add-text]")?.addEventListener("click", addText);
    els.upload?.addEventListener("change", async () => {
        const file = els.upload.files?.[0];
        if (!file) return;
        try { await uploadImage(file); } catch (error) { alert(error.message); }
        els.upload.value = "";
    });
    els.save?.addEventListener("click", async () => { try { await saveDesign(); } catch (error) { alert(error.message); } });
    els.publish?.addEventListener("click", async () => { try { await publishDesign(); } catch (error) { alert(error.message); } });
    els.title?.addEventListener("input", markDirty);

    function updateSelected(key, value) {
        const layer = selectedLayer(); if (!layer) return;
        layer[key] = value; markDirty(); renderLayers(); renderProperties();
    }
    els.propText?.addEventListener("input", () => updateSelected("text", els.propText.value));
    els.propColor?.addEventListener("input", () => updateSelected("color", els.propColor.value));
    els.propFontSize?.addEventListener("input", () => updateSelected("fontSize", Number(els.propFontSize.value)));
    els.propWidth?.addEventListener("input", () => updateSelected("width", Number(els.propWidth.value)));
    els.propRotation?.addEventListener("input", () => updateSelected("rotation", Number(els.propRotation.value)));
    document.querySelector("[data-delete-layer]")?.addEventListener("click", () => {
        const layers = currentLayers();
        const index = layers.findIndex(l => l.id === state.selectedLayerId);
        if (index >= 0) layers.splice(index, 1);
        state.selectedLayerId = null; markDirty(); renderLayers(); renderProperties();
    });
    document.querySelector("[data-layer-up]")?.addEventListener("click", () => {
        const layer = selectedLayer(); if (!layer) return;
        layer.z = Math.max(...currentLayers().map(l => l.z || 0), 0) + 1; markDirty(); renderLayers();
    });
    document.querySelector("[data-layer-down]")?.addEventListener("click", () => {
        const layer = selectedLayer(); if (!layer) return;
        layer.z = Math.min(...currentLayers().map(l => l.z || 0), 0) - 1; markDirty(); renderLayers();
    });
    window.addEventListener("beforeunload", event => { if (state.dirty) { event.preventDefault(); event.returnValue = ""; } });

    renderAll();
})();
