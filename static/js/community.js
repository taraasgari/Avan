(() => {
    "use strict";

    const csrfToken = document.querySelector(
        '#community-csrf input[name="csrfmiddlewaretoken"]'
    )?.value || "";

    const followButton = document.querySelector("[data-follow-creator]");

    followButton?.addEventListener("click", async () => {
        const username = followButton.dataset.followCreator;
        followButton.disabled = true;

        try {
            const response = await fetch(`/creator/${encodeURIComponent(username)}/follow/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "Accept": "application/json",
                },
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Unable to update follow.");

            followButton.classList.toggle("is-active", data.active);
            followButton.textContent = data.active ? "FOLLOWING" : "FOLLOW";

            const count = document.querySelector("[data-followers-count]");
            if (count) count.textContent = data.followers;
        } catch (error) {
            alert(error.message);
        } finally {
            followButton.disabled = false;
        }
    });

    document.querySelectorAll("[data-unsave-design]").forEach(button => {
        button.addEventListener("click", async () => {
            const designId = button.dataset.unsaveDesign;
            button.disabled = true;

            try {
                const response = await fetch(`/api/designs/${designId}/save/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken,
                        "Accept": "application/json",
                    },
                });

                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || "Unable to remove saved design.");

                if (!data.active) {
                    document.querySelector(`[data-saved-card="${designId}"]`)?.remove();
                }
            } catch (error) {
                alert(error.message);
                button.disabled = false;
            }
        });
    });
})();
