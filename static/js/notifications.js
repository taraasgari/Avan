(() => {
    "use strict";

    const csrfToken = document.querySelector(
        '#notifications-csrf input[name="csrfmiddlewaretoken"]'
    )?.value || "";

    function updateHeader(unread) {
        document.querySelectorAll("[data-notification-badge]").forEach(el => {
            el.textContent = unread;
            el.hidden = unread <= 0;
        });
    }

    async function markRead(id) {
        const response = await fetch(`/account/notifications/${id}/read/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "Accept": "application/json",
            },
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Unable to update notification.");

        const row = document.querySelector(`[data-notification="${id}"]`);
        row?.classList.remove("is-unread");
        row?.querySelector(`[data-read-notification="${id}"]`)?.remove();
        updateHeader(data.unread);
    }

    document.querySelectorAll("[data-read-notification]").forEach(button => {
        button.addEventListener("click", async () => {
            button.disabled = true;
            try {
                await markRead(button.dataset.readNotification);
            } catch (error) {
                alert(error.message);
                button.disabled = false;
            }
        });
    });

    document.querySelectorAll("[data-open-notification]").forEach(link => {
        link.addEventListener("click", async event => {
            const id = link.dataset.openNotification;
            if (!id) return;
            event.preventDefault();
            const href = link.href;
            try {
                await markRead(id);
            } finally {
                window.location.href = href;
            }
        });
    });

    document.querySelector("[data-read-all]")?.addEventListener("click", async () => {
        const response = await fetch("/account/notifications/read-all/", {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "Accept": "application/json",
            },
        });
        if (!response.ok) return;
        document.querySelectorAll(".notification-row").forEach(row => row.classList.remove("is-unread"));
        document.querySelectorAll("[data-read-notification]").forEach(button => button.remove());
        updateHeader(0);
    });
})();
