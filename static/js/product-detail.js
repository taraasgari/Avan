(() => {
    "use strict";

    const variantsElement = document.getElementById(
        "product-variants-data"
    );

    if (!variantsElement) return;

    const variants = JSON.parse(
        variantsElement.textContent
    );

    const colorButtons = [
        ...document.querySelectorAll("[data-color]")
    ];

    const sizeButtons = [
        ...document.querySelectorAll("[data-size]")
    ];

    const addButton =
        document.querySelector("[data-add-to-cart]");

    const status =
        document.querySelector("[data-variant-status]");

    const price =
        document.querySelector("[data-product-price]");

    const colorLabel =
        document.querySelector("[data-selected-color]");

    const message =
        document.querySelector("[data-product-message]");

    const csrfToken =
        document.querySelector(
            'input[name="csrfmiddlewaretoken"]'
        )?.value || "";

    let selectedColor = null;
    let selectedSize = null;
    let selectedVariant = null;


    function money(value) {
        return Number(value).toLocaleString("en-US");
    }


    function availableForColor(colorId) {
        return variants.filter(
            variant =>
                String(variant.color_id) === String(colorId)
                && variant.stock > 0
        );
    }


    function refreshSizes() {

        sizeButtons.forEach(button => {

            const sizeId = button.dataset.size;

            const available = variants.some(
                variant =>
                    String(variant.color_id) === String(selectedColor)
                    &&
                    String(variant.size_id) === String(sizeId)
                    &&
                    variant.stock > 0
            );

            button.classList.toggle(
                "is-unavailable",
                selectedColor && !available
            );

        });

    }


    function refreshVariant() {

        selectedVariant = variants.find(
            variant =>
                String(variant.color_id) === String(selectedColor)
                &&
                String(variant.size_id) === String(selectedSize)
        );

        status.classList.remove(
            "is-in-stock",
            "is-out"
        );

        if (!selectedColor || !selectedSize) {

            status.textContent =
                "SELECT COLOR & SIZE";

            addButton.disabled = true;

            return;
        }

        if (!selectedVariant || selectedVariant.stock <= 0) {

            status.textContent =
                "OUT OF STOCK";

            status.classList.add("is-out");

            addButton.disabled = true;

            return;
        }

        status.textContent =
            `${selectedVariant.stock} AVAILABLE`;

        status.classList.add("is-in-stock");

        price.innerHTML =
            `${money(selectedVariant.price)} <small>TOMAN</small>`;

        addButton.disabled = false;
    }


    colorButtons.forEach(button => {

        button.addEventListener("click", () => {

            selectedColor = button.dataset.color;

            colorButtons.forEach(item =>
                item.classList.remove("is-selected")
            );

            button.classList.add("is-selected");

            colorLabel.textContent =
                button.dataset.colorName;

            refreshSizes();

            if (
                selectedSize &&
                !variants.some(
                    variant =>
                        String(variant.color_id) === String(selectedColor)
                        &&
                        String(variant.size_id) === String(selectedSize)
                        &&
                        variant.stock > 0
                )
            ) {

                selectedSize = null;

                sizeButtons.forEach(item =>
                    item.classList.remove("is-selected")
                );

            }

            refreshVariant();
        });

    });


    sizeButtons.forEach(button => {

        button.addEventListener("click", () => {

            if (
                button.classList.contains(
                    "is-unavailable"
                )
            ) return;

            selectedSize = button.dataset.size;

            sizeButtons.forEach(item =>
                item.classList.remove("is-selected")
            );

            button.classList.add("is-selected");

            refreshVariant();
        });

    });


    async function getOrCreateCart() {

        let token =
            localStorage.getItem("avan_cart_token");

        if (token) {

            const response = await fetch(
                `/api/cart/${token}/`
            );

            if (response.ok) {
                return token;
            }

            localStorage.removeItem(
                "avan_cart_token"
            );
        }

        const response = await fetch(
            "/api/cart/",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: "{}",
            }
        );

        if (!response.ok) {
            throw new Error(
                "Could not create cart."
            );
        }

        const cart = await response.json();

        localStorage.setItem(
            "avan_cart_token",
            cart.token
        );

        return cart.token;
    }


    addButton?.addEventListener(
        "click",
        async () => {

            if (!selectedVariant) return;

            addButton.disabled = true;
            addButton.textContent = "ADDING...";

            message.textContent = "";

            try {

                const token =
                    await getOrCreateCart();

                const response = await fetch(
                    `/api/cart/${token}/items/`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json",

                            "X-CSRFToken":
                                csrfToken,
                        },

                        body: JSON.stringify({
                            variant_id:
                                selectedVariant.id,

                            quantity: 1,
                        }),
                    }
                );

                const data =
                    await response.json();

                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        "Unable to add product."
                    );

                }

                message.textContent =
                    "ADDED TO YOUR BAG ✓";

                window.dispatchEvent(
                    new CustomEvent(
                        "avan:cart-updated",
                        { detail: data }
                    )
                );

            } catch (error) {

                message.textContent =
                    error.message;

            } finally {

                addButton.disabled = false;
                addButton.textContent =
                    "ADD TO BAG";

            }

        }
    );


    /* wishlist */

    const wishlistButton =
        document.querySelector("[data-wishlist]");

    wishlistButton?.addEventListener(
        "click",
        async () => {

            const productId =
                wishlistButton.dataset.productId;

            try {

                const response = await fetch(
                    "/api/wishlist/",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json",

                            "X-CSRFToken":
                                csrfToken,
                        },

                        body: JSON.stringify({
                            product_id: productId,
                        }),
                    }
                );

                if (response.status === 403) {

                    message.textContent =
                        "SIGN IN TO USE WISHLIST";

                    return;
                }

                if (!response.ok) {
                    throw new Error();
                }

                wishlistButton.classList.add(
                    "is-active"
                );

                wishlistButton.textContent = "♥";

                message.textContent =
                    "SAVED TO WISHLIST";

            } catch {

                message.textContent =
                    "WISHLIST IS UNAVAILABLE";

            }

        }
    );


    /* size guide */

    const sizeGuide =
        document.querySelector("[data-size-guide]");

    document
        .querySelector("[data-size-guide-open]")
        ?.addEventListener("click", () => {

            sizeGuide.classList.add("is-open");
            document.body.style.overflow = "hidden";

        });


    document
        .querySelectorAll("[data-size-guide-close]")
        .forEach(button => {

            button.addEventListener("click", () => {

                sizeGuide.classList.remove("is-open");
                document.body.style.overflow = "";

            });

        });

})();