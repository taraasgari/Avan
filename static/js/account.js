(() => {
    "use strict";


    const csrfToken =
        document.querySelector(
            '#account-csrf input[name="csrfmiddlewaretoken"]'
        )?.value || "";


    document
        .querySelectorAll(
            "[data-remove-wishlist]"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                async () => {

                    const productId =
                        button.dataset.removeWishlist;


                    button.disabled = true;


                    try {

                        const response =
                            await fetch(
                                `/api/wishlist/${productId}/`,
                                {
                                    method: "DELETE",

                                    headers: {
                                        "X-CSRFToken":
                                            csrfToken,
                                    },
                                }
                            );


                        if (!response.ok) {

                            throw new Error();

                        }


                        document
                            .querySelector(
                                `[data-wishlist-card="${productId}"]`
                            )
                            ?.remove();


                    } catch {

                        button.disabled = false;

                        alert(
                            "Could not remove this item."
                        );

                    }

                }
            );

        });

})();