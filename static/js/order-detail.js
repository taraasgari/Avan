(() => {
    "use strict";
    const page = document.querySelector("[data-order-page]");
    if (!page) return;
    const number = page.dataset.orderNumber;
    const csrfToken = document.querySelector('#order-csrf input[name="csrfmiddlewaretoken"]')?.value || "";

    const money = value => Number(value || 0).toLocaleString("en-US");
    const esc = value => String(value ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
    const statusTitle = status => ({pending_payment:"WAITING FOR PAYMENT.",paid:"ORDER CONFIRMED.",processing:"WE'RE PREPARING IT.",shipped:"ON THE WAY.",delivered:"DELIVERED.",cancelled:"ORDER CANCELLED.",needs_review:"PAYMENT NEEDS REVIEW."}[status] || "YOUR ORDER.");
    const statusLabel = status => String(status).replaceAll("_"," ").toUpperCase();

    function itemTemplate(item) {
        const custom = item.is_customized ? `
            <div style="margin-top:8px;padding:8px 10px;background:#111;color:white;font-size:.58rem;font-weight:900;display:inline-block">
                CUSTOM DESIGN${item.design_title ? ` / ${esc(item.design_title)}` : ""}
            </div>
            ${item.design_owner_name ? `<p>DESIGN BY ${esc(item.design_owner_name)}</p>` : ""}
        ` : "";
        return `
            <article class="order-item">
                <div>
                    <h3>${esc(item.product_name)}</h3>
                    <p>${esc(item.color_name)} / ${esc(item.size_name)} / QTY ${item.quantity}</p>
                    ${custom}
                </div>
                <strong>${money(item.line_total)} TOMAN</strong>
            </article>`;
    }

    function paymentBlock(order) {
        const payment = order.payment;
        if (!payment) return '<div class="order-payment-state">PAYMENT NOT INITIALIZED</div>';
        if (payment.status === "succeeded") return '<div class="payment-success">PAYMENT SUCCESSFUL ✓</div>';
        return `
            <div class="order-payment-state">PAYMENT STATUS: ${esc(payment.status.toUpperCase())}</div>
            <button type="button" class="dev-pay-button" data-dev-payment data-payment-id="${payment.id}">SIMULATE SUCCESSFUL PAYMENT</button>`;
    }

    function render(order) {
        page.innerHTML = `
            <div class="order-result">
                <span class="order-status-label">${statusLabel(order.status)}</span>
                <h1>${statusTitle(order.status)}</h1>
                <div class="order-number">ORDER ${esc(order.number)}</div>
                <div class="order-card">
                    <section class="order-products">
                        ${order.items.map(itemTemplate).join("")}
                        <div class="shipping-address">
                            <h2>SHIPPING TO</h2>
                            <p>${esc(order.customer_name)}<br>${esc(order.phone)}<br><br>${esc(order.province)}, ${esc(order.city)}<br>${esc(order.address)}${order.postal_code ? `<br>${esc(order.postal_code)}` : ""}</p>
                        </div>
                    </section>
                    <aside class="order-summary-card">
                        <div class="order-summary-line"><span>SUBTOTAL</span><strong>${money(order.subtotal)}</strong></div>
                        <div class="order-summary-line"><span>DISCOUNT</span><strong>− ${money(order.discount_amount)}</strong></div>
                        <div class="order-summary-line"><span>SHIPPING</span><strong>${money(order.shipping_amount)}</strong></div>
                        <div class="order-summary-line order-summary-total"><span>TOTAL</span><strong>${money(order.total_amount)} TOMAN</strong></div>
                        ${order.reservation_expires_at && order.status === "pending_payment" ? `<div class="reservation-box">STOCK RESERVED UNTIL<br><br>${new Date(order.reservation_expires_at).toLocaleString()}</div>` : ""}
                        <div class="order-payment">${paymentBlock(order)}</div>
                    </aside>
                </div>
                <div class="order-actions"><a href="/shop/">CONTINUE SHOPPING</a><a href="/">HOME</a></div>
            </div>`;
        bindPayment();
    }

    async function loadOrder() {
        const response = await fetch(`/api/orders/${number}/`, {headers:{"Accept":"application/json"}});
        if (!response.ok) { page.innerHTML = '<div class="order-loading">ORDER NOT FOUND.</div>'; return; }
        render(await response.json());
    }

    function bindPayment() {
        const button = document.querySelector("[data-dev-payment]");
        if (!button) return;
        button.addEventListener("click", async () => {
            const paymentId = button.dataset.paymentId;
            button.disabled = true; button.textContent = "PROCESSING...";
            try {
                const response = await fetch(`/api/payments/${paymentId}/dev-success/`, {method:"POST",headers:{"X-CSRFToken":csrfToken,"Accept":"application/json"}});
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || "Payment failed.");
                await loadOrder();
            } catch (error) { alert(error.message); button.disabled = false; button.textContent = "SIMULATE SUCCESSFUL PAYMENT"; }
        });
    }

    loadOrder();
})();
