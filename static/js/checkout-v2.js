(() => {
  "use strict";
  const page = document.querySelector("[data-checkout-page]");
  if (!page) return;
  const form = page.querySelector("[data-checkout-form]");
  const errorBox = page.querySelector("[data-checkout-error]");
  const itemsBox = page.querySelector("[data-checkout-items]");
  const subtotalEl = page.querySelector("[data-checkout-subtotal]");
  const discountEl = page.querySelector("[data-checkout-discount]");
  const shippingEl = page.querySelector("[data-checkout-shipping]");
  const totalEl = page.querySelector("[data-checkout-total]");
  const submit = form?.querySelector("button[type=submit]");
  const csrf = form?.querySelector('input[name="csrfmiddlewaretoken"]')?.value || "";
  const token = localStorage.getItem("avan_cart_token");
  let cart = null;
  let idempotencyKey = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;

  const money = value => new Intl.NumberFormat(document.documentElement.lang === "fa" ? "fa-IR" : "en-US", {maximumFractionDigits:0}).format(Number(value || 0));
  const showError = message => { if(!errorBox)return; errorBox.hidden=false; errorBox.textContent=message || "Checkout failed."; };
  const clearError = () => { if(errorBox){errorBox.hidden=true;errorBox.textContent="";} };
  const selectedShipping = () => form?.querySelector('input[name="shipping_method"]:checked');
  const shippingPrice = () => Number(selectedShipping()?.dataset.shippingPrice || 0);

  function renderMoney(){
    if(!cart) return;
    const sub=Number(cart.totals?.subtotal||0), discount=Number(cart.totals?.discount||0), shipping=shippingPrice();
    subtotalEl.textContent=money(sub); discountEl.textContent=money(discount); shippingEl.textContent=money(shipping); totalEl.textContent=money(Math.max(0,sub-discount+shipping));
  }
  function renderCart(){
    if(!cart || !cart.items?.length){ itemsBox.innerHTML="<p>YOUR BAG IS EMPTY.</p>"; if(submit)submit.disabled=true; return; }
    itemsBox.innerHTML=cart.items.map(item=>`<div class="checkout-summary-item"><div><strong>${item.product}</strong><small>${item.color} / ${item.size} · ${item.quantity} × ${money(item.unit_price)}</small></div><b>${money(item.line_total)}</b></div>`).join("");
    renderMoney();
  }
  async function loadCart(){
    if(!token){showError("Your bag is empty. Add a product before checkout."); if(submit)submit.disabled=true; return;}
    try{const r=await fetch(`/api/cart/${token}/`,{headers:{Accept:"application/json"}});if(!r.ok)throw new Error("Could not load your bag.");cart=await r.json();renderCart();}catch(e){showError(e.message);if(submit)submit.disabled=true;}
  }

  form?.querySelectorAll('input[name="shipping_method"]').forEach(r=>r.addEventListener("change",renderMoney));
  const addressRadios=[...(form?.querySelectorAll('input[name="address_choice"]')||[])];
  const manualWrap=page.querySelector("[data-manual-address]");
  function syncAddress(){ if(!manualWrap||!addressRadios.length)return; const selected=form.querySelector('input[name="address_choice"]:checked'); manualWrap.hidden=!!selected && selected.value!=="manual"; }
  addressRadios.forEach(r=>r.addEventListener("change",syncAddress)); syncAddress();

  form?.addEventListener("submit", async event => {
    event.preventDefault(); clearError(); if(!cart||!token)return showError("Bag unavailable.");
    const ship=selectedShipping(); if(!ship)return showError("Choose a shipping method.");
    const fd=new FormData(form); const selectedAddress=form.querySelector('input[name="address_choice"]:checked');
    const payload={shipping_method_id:Number(ship.value),customer_note:String(fd.get("customer_note")||""),email:String(fd.get("email")||""),idempotency_key:idempotencyKey};
    if(selectedAddress && selectedAddress.value!=="manual") payload.address_id=Number(selectedAddress.value);
    else Object.assign(payload,{customer_name:String(fd.get("customer_name")||""),phone:String(fd.get("phone")||""),province:String(fd.get("province")||""),city:String(fd.get("city")||""),address:String(fd.get("address")||""),postal_code:String(fd.get("postal_code")||"")});
    submit.disabled=true; submit.dataset.originalText=submit.textContent; submit.textContent="PROCESSING...";
    try{
      const r=await fetch(`/api/checkout/${token}/`,{method:"POST",headers:{"Content-Type":"application/json","X-CSRFToken":csrf,Accept:"application/json"},body:JSON.stringify(payload)});
      const data=await r.json().catch(()=>({})); if(!r.ok)throw new Error(data.detail || Object.values(data).flat().join(" ") || "Checkout failed.");
      localStorage.removeItem("avan_cart_token"); window.dispatchEvent(new CustomEvent("avan:cart-changed",{detail:null})); location.href=`/orders/${data.number}/`;
    }catch(e){showError(e.message);submit.disabled=false;submit.textContent=submit.dataset.originalText||"PLACE ORDER →";}
  });
  loadCart();
})();
