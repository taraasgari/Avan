(() => {
    "use strict";


    const STORAGE_KEY = "avan_cart_token";


    const drawer =
        document.querySelector("[data-cart-drawer]");

    const overlay =
        document.querySelector("[data-cart-overlay]");

    const drawerItems =
        document.querySelector("[data-cart-drawer-items]");

    const bagItems =
        document.querySelector("[data-bag-items]");


    const cartCountElements =
        document.querySelectorAll("[data-cart-count]");

    const drawerCount =
        document.querySelector("[data-cart-drawer-count]");

    const drawerTotal =
        document.querySelector("[data-cart-drawer-total]");


    const csrfToken =
        document.querySelector(
            '#avan-csrf input[name="csrfmiddlewaretoken"]'
        )?.value || "";


    let currentCart = null;


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


    function getToken() {
        return localStorage.getItem(STORAGE_KEY);
    }


    function clearToken() {
        localStorage.removeItem(STORAGE_KEY);
    }


    function openDrawer() {

        drawer?.classList.add("is-open");

        overlay?.classList.add("is-open");

        document.body.style.overflow = "hidden";
    }


    function closeDrawer() {

        drawer?.classList.remove("is-open");

        overlay?.classList.remove("is-open");

        document.body.style.overflow = "";
    }


    function itemCount(cart) {

        return cart?.items?.reduce(
            (total, item) =>
                total + Number(item.quantity),
            0
        ) || 0;
    }


    function emptyTemplate() {

        return `
            <div class="cart-empty">

                <strong>
                    YOUR BAG IS EMPTY.
                </strong>

                <span>
                    Find something you want to wear.
                </span>

                <a href="/shop/">
                    EXPLORE SHOP
                </a>

            </div>
        `;
    }


    function itemTemplate(item) {

        const image = item.product_image
            ? `
                <img
                    src="${escapeHtml(item.product_image)}"
                    alt="${escapeHtml(item.product)}"
                >
              `
            : `
                <div class="cart-item__placeholder">
                    AVAN
                </div>
              `;


        return `
            <article
                class="cart-item"
                data-cart-item="${item.id}"
            >

                <a
                    class="cart-item__image"
                    href="/shop/${escapeHtml(item.product_slug)}/"
                >
                    ${image}
                </a>


                <div>

                    <div class="cart-item__top">

                        <div>

                            <a
                                href="/shop/${escapeHtml(item.product_slug)}/"
                            >
                                <h3 class="cart-item__name">
                                    ${escapeHtml(item.product)}
                                </h3>
                            </a>

                            <p class="cart-item__variant">

                                ${escapeHtml(item.color)}

                                &nbsp;/&nbsp;

                                ${escapeHtml(item.size)}

                            </p>

                        </div>


                        <button
                            type="button"
                            class="cart-remove"
                            data-remove-item="${item.id}"
                        >
                            REMOVE
                        </button>

                    </div>


                    <div class="cart-item__bottom">

                        <div class="cart-quantity">

                            <button
                                type="button"
                                data-quantity-minus="${item.id}"
                                aria-label="Decrease quantity"
                            >
                                −
                            </button>

                            <span>
                                ${item.quantity}
                            </span>

                            <button
                                type="button"
                                data-quantity-plus="${item.id}"
                                aria-label="Increase quantity"
                                ${
                                    item.quantity >=
                                    item.available_stock
                                        ? "disabled"
                                        : ""
                                }
                            >
                                +
                            </button>

                        </div>


                        <strong class="cart-item__price">

                            ${money(item.line_total)}

                            <small>
                                TOMAN
                            </small>

                        </strong>

                    </div>

                </div>

            </article>
        `;
    }


    function renderCart(cart) {

        currentCart = cart;


        const count = itemCount(cart);


        cartCountElements.forEach(element => {
            element.textContent = count;
        });


        if (drawerCount) {
            drawerCount.textContent = count;
        }


        if (drawerTotal) {
            drawerTotal.textContent =
                money(cart?.totals?.subtotal);
        }


        const html = cart?.items?.length
            ? cart.items
                .map(itemTemplate)
                .join("")
            : emptyTemplate();


        if (drawerItems) {
            drawerItems.innerHTML = html;
        }


        if (bagItems) {
            bagItems.innerHTML = html;
        }


        renderSummary(cart);

        bindItemActions();
    }


    function renderEmpty() {

        renderCart({
            items: [],
            totals: {
                subtotal: 0,
                discount: 0,
                shipping: 0,
                total: 0,
            },
            coupon_code: null,
        });
    }


    function renderSummary(cart) {

        const totals = cart?.totals || {};


        const fields = {
            "[data-summary-subtotal]":
                totals.subtotal,

            "[data-summary-discount]":
                totals.discount,

            "[data-summary-shipping]":
                totals.shipping,

            "[data-summary-total]":
                totals.total,
        };


        Object.entries(fields).forEach(
            ([selector, value]) => {

                const element =
                    document.querySelector(selector);

                if (element) {
                    element.textContent =
                        money(value);
                }

            }
        );


        const checkoutButton =
            document.querySelector("[data-checkout]");

        if (checkoutButton) {

            checkoutButton.disabled =
                !cart?.items?.length;

        }


        const couponInput =
            document.querySelector(
                '[data-coupon-form] input[name="coupon"]'
            );


        if (
            couponInput &&
            cart?.coupon_code
        ) {

            couponInput.value =
                cart.coupon_code;
        }

    }


    async function loadCart() {

        const token = getToken();


        if (!token) {

            renderEmpty();

            return null;
        }


        try {

            const response = await fetch(
                `/api/cart/${token}/`,
                {
                    headers: {
                        "Accept":
                            "application/json",
                    },
                }
            );


            if (response.status === 404) {

                clearToken();

                renderEmpty();

                return null;
            }


            if (!response.ok) {

                throw new Error(
                    "Unable to load bag."
                );
            }


            const cart =
                await response.json();


            renderCart(cart);


            return cart;


        } catch (error) {

            console.error(error);

            return null;
        }

    }


    async function updateQuantity(
        itemId,
        quantity
    ) {

        const token = getToken();


        if (
            !token ||
            quantity < 1
        ) {
            return;
        }


        const response = await fetch(
            `/api/cart/${token}/items/${itemId}/`,
            {
                method: "PATCH",

                headers: {
                    "Content-Type":
                        "application/json",

                    "X-CSRFToken":
                        csrfToken,
                },

                body: JSON.stringify({
                    quantity,
                }),
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not update quantity."
            );
        }


        renderCart(data);
    }


    async function removeItem(itemId) {

        const token = getToken();


        if (!token) {
            return;
        }


        const response = await fetch(
            `/api/cart/${token}/items/${itemId}/`,
            {
                method: "DELETE",

                headers: {
                    "X-CSRFToken":
                        csrfToken,
                },
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not remove item."
            );
        }


        renderCart(data);
    }


    function bindItemActions() {

        document
            .querySelectorAll(
                "[data-quantity-minus]"
            )
            .forEach(button => {

                button.onclick = async () => {

                    const id =
                        button.dataset.quantityMinus;

                    const item =
                        currentCart?.items?.find(
                            item =>
                                String(item.id) ===
                                String(id)
                        );


                    if (
                        !item ||
                        item.quantity <= 1
                    ) {
                        return;
                    }


                    try {

                        await updateQuantity(
                            id,
                            item.quantity - 1
                        );

                    } catch (error) {

                        alert(error.message);

                    }

                };

            });


        document
            .querySelectorAll(
                "[data-quantity-plus]"
            )
            .forEach(button => {

                button.onclick = async () => {

                    const id =
                        button.dataset.quantityPlus;

                    const item =
                        currentCart?.items?.find(
                            item =>
                                String(item.id) ===
                                String(id)
                        );


                    if (!item) {
                        return;
                    }


                    try {

                        await updateQuantity(
                            id,
                            item.quantity + 1
                        );

                    } catch (error) {

                        alert(error.message);

                    }

                };

            });


        document
            .querySelectorAll(
                "[data-remove-item]"
            )
            .forEach(button => {

                button.onclick = async () => {

                    const id =
                        button.dataset.removeItem;


                    try {

                        await removeItem(id);

                    } catch (error) {

                        alert(error.message);

                    }

                };

            });

    }


    /* OPEN / CLOSE */


    document
        .querySelectorAll("[data-cart-open]")
        .forEach(button => {

            button.addEventListener(
                "click",
                async () => {

                    await loadCart();

                    openDrawer();

                }
            );

        });


    document
        .querySelectorAll("[data-cart-close]")
        .forEach(button => {

            button.addEventListener(
                "click",
                closeDrawer
            );

        });


    overlay?.addEventListener(
        "click",
        closeDrawer
    );


    document.addEventListener(
        "keydown",
        event => {

            if (event.key === "Escape") {
                closeDrawer();
            }

        }
    );


    /* PRODUCT DETAIL EVENT */

    window.addEventListener(
        "avan:cart-updated",
        event => {

            if (event.detail) {

                renderCart(event.detail);

            } else {

                loadCart();

            }


            openDrawer();

        }
    );


    /* COUPON */

    const couponForm =
        document.querySelector(
            "[data-coupon-form]"
        );


    couponForm?.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            const token = getToken();

            const input =
                couponForm.querySelector(
                    'input[name="coupon"]'
                );

            const message =
                document.querySelector(
                    "[data-coupon-message]"
                );


            const code =
                input.value.trim();


            if (!token) {

                message.textContent =
                    "YOUR BAG IS EMPTY.";

                return;
            }


            if (!code) {

                message.textContent =
                    "ENTER A COUPON CODE.";

                return;
            }


            message.textContent =
                "CHECKING...";


            try {

                const response = await fetch(
                    `/api/cart/${token}/coupon/`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",

                            "X-CSRFToken":
                                csrfToken,
                        },

                        body: JSON.stringify({
                            code,
                        }),
                    }
                );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        "INVALID COUPON."
                    );

                }


                renderCart(data);


                message.textContent =
                    `COUPON ${data.coupon_code} APPLIED ✓`;


            } catch (error) {

                message.textContent =
                    error.message;

            }

        }
    );


    /* CHECKOUT */

document
    .querySelector("[data-checkout]")
    ?.addEventListener(
        "click",
        () => {

            if (!currentCart?.items?.length) {
                return;
            }

            window.location.href =
                "/checkout/";

        }
    );


    /* INITIAL LOAD */

    loadCart();

})();