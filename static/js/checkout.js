(() => {
    "use strict";


    const CART_KEY =
        "avan_cart_token";

    const IDEMPOTENCY_PREFIX =
        "avan_checkout_idempotency_";


    const form =
        document.querySelector(
            "[data-checkout-form]"
        );

    if (!form) {
        return;
    }


    const itemsElement =
        document.querySelector(
            "[data-checkout-items]"
        );


    const submitButton =
        document.querySelector(
            "[data-place-order]"
        );


    const errorElement =
        document.querySelector(
            "[data-checkout-error]"
        );


    const csrfToken =
        document.querySelector(
            '#checkout-csrf input[name="csrfmiddlewaretoken"]'
        )?.value || "";


    let cart = null;


    function money(value) {

        return Number(value || 0)
            .toLocaleString("en-US");

    }


    function escapeHtml(value) {

        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");

    }


    function setText(selector, value) {

        const element =
            document.querySelector(selector);

        if (element) {

            element.textContent =
                money(value);

        }

    }


    function cartItemTemplate(item) {

        const image = item.product_image
            ? `
                <img
                    src="${escapeHtml(item.product_image)}"
                    alt="${escapeHtml(item.product)}"
                >
            `
            : `
                <div class="checkout-item__placeholder">
                    AVAN
                </div>
            `;


        return `
            <article class="checkout-item">

                <div class="checkout-item__image">
                    ${image}
                </div>


                <div class="checkout-item__body">

                    <div class="checkout-item__top">

                        <div>

                            <h3>
                                ${escapeHtml(item.product)}
                            </h3>

                            <p class="checkout-item__variant">

                                ${escapeHtml(item.color)}

                                /

                                ${escapeHtml(item.size)}

                            </p>

                            <span class="checkout-item__quantity">
                                QTY ${item.quantity}
                            </span>

                        </div>


                        <strong class="checkout-item__price">

                            ${money(item.line_total)}

                            TOMAN

                        </strong>

                    </div>

                </div>

            </article>
        `;
    }


    function renderCart() {

        if (!cart?.items?.length) {

            window.location.href =
                "/bag/";

            return;
        }


        itemsElement.innerHTML =
            cart.items
                .map(cartItemTemplate)
                .join("");


        setText(
            "[data-checkout-subtotal]",
            cart.totals.subtotal
        );

        setText(
            "[data-checkout-discount]",
            cart.totals.discount
        );

        setText(
            "[data-checkout-shipping]",
            cart.totals.shipping
        );

        setText(
            "[data-checkout-total]",
            cart.totals.total
        );

    }


    async function loadCart() {

        const token =
            localStorage.getItem(CART_KEY);


        if (!token) {

            window.location.href =
                "/bag/";

            return;
        }


        const response = await fetch(
            `/api/cart/${token}/`,
            {
                headers: {
                    "Accept":
                        "application/json",
                },
            }
        );


        if (!response.ok) {

            localStorage.removeItem(CART_KEY);

            window.location.href =
                "/bag/";

            return;
        }


        cart =
            await response.json();


        renderCart();

    }


    function createUuid() {

        if (
            window.crypto &&
            crypto.randomUUID
        ) {

            return crypto.randomUUID();

        }


        return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
            .replace(
                /[xy]/g,
                character => {

                    const random =
                        Math.random() * 16 | 0;

                    const value =
                        character === "x"
                            ? random
                            : (random & 0x3 | 0x8);

                    return value.toString(16);

                }
            );

    }


    function idempotencyKey(cartToken) {

        const storageKey =
            IDEMPOTENCY_PREFIX +
            cartToken;


        let key =
            sessionStorage.getItem(
                storageKey
            );


        if (!key) {

            key = createUuid();

            sessionStorage.setItem(
                storageKey,
                key
            );

        }


        return key;

    }


    function formPayload() {

        const data =
            new FormData(form);


        return {
            customer_name:
                data
                    .get("customer_name")
                    ?.trim(),

            phone:
                data
                    .get("phone")
                    ?.trim(),

            email:
                data
                    .get("email")
                    ?.trim(),

            province:
                data
                    .get("province")
                    ?.trim(),

            city:
                data
                    .get("city")
                    ?.trim(),

            address:
                data
                    .get("address")
                    ?.trim(),

            postal_code:
                data
                    .get("postal_code")
                    ?.trim(),

            customer_note:
                data
                    .get("customer_note")
                    ?.trim(),
        };

    }


    form.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            errorElement.textContent = "";


            if (!form.reportValidity()) {
                return;
            }


            const token =
                localStorage.getItem(
                    CART_KEY
                );


            if (!token) {

                window.location.href =
                    "/bag/";

                return;
            }


            const payload =
                formPayload();


            payload.idempotency_key =
                idempotencyKey(token);


            submitButton.disabled = true;

            submitButton.textContent =
                "CREATING ORDER...";


            try {

                const response = await fetch(
                    `/api/checkout/${token}/`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",

                            "Accept":
                                "application/json",

                            "X-CSRFToken":
                                csrfToken,
                        },

                        body:
                            JSON.stringify(
                                payload
                            ),
                    }
                );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        "Unable to create order."
                    );

                }


                /*
                 * Cart is converted by backend after
                 * successful order creation.
                 */

                localStorage.removeItem(
                    CART_KEY
                );


                sessionStorage.removeItem(
                    IDEMPOTENCY_PREFIX +
                    token
                );


                window.location.href =
                    `/orders/${data.number}/`;


            } catch (error) {

                errorElement.textContent =
                    error.message;


                submitButton.disabled = false;

                submitButton.textContent =
                    "PLACE ORDER →";

            }

        }
    );


    loadCart();

})();