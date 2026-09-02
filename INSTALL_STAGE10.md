# AVAN Stage 10 — Commerce Engine

Stage 10 deliberately freezes product/UI redesign decisions and focuses on launch-critical commerce infrastructure.

## Adds
- Configurable free-shipping threshold.
- Province/city/subtotal shipping rules with backend-authoritative quotes.
- Campaign windows connected to existing coupons.
- Abandoned-cart detection + recovery ledger.
- Refund ledger with idempotency key and hard cap against paid order total.
- Fulfillment event audit model.
- Commerce maintenance command for scheduled operational checks.
- Owner Commerce Console.

## Safety defaults
- Payment provider remains `dev` by default.
- Auto-cancel expired orders is OFF.
- Free shipping is disabled until an owner enters a threshold.
- No external refund is falsely reported as executed; owner can only mark a refund succeeded after actual gateway/manual confirmation until a concrete gateway adapter is configured.

## Install
1. Copy this update over the project root.
2. Add `"apps.commerce",` to `INSTALLED_APPS`.
3. Add `path("", include("apps.commerce.urls")),` to root `urlpatterns`.
4. Run migrations/check/tests.

Commands:

    docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
    docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
    docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
    docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.commerce

Optional maintenance scan:

    docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py commerce_maintenance

Owner pages:
- /owner/commerce/
- /owner/commerce/shipping-rules/
- /owner/commerce/campaigns/
- /owner/commerce/abandoned-carts/
- /owner/commerce/refunds/
