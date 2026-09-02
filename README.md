# AVAN

Independent Django commerce foundation for the AVAN clothing brand.

Current stage: **Phase 2 — Commerce Core**.

AVAN is intentionally separated from the previous cosmetics-store project. It has its own codebase, database, Docker services, static/media storage, and future API clients.

## Current stack

- Django 5.2 LTS
- Django REST Framework
- PostgreSQL 17
- Nginx
- Redis + Celery for non-critical async work
- Docker Desktop / WSL2 for local development
- Local/self-hosted CSS, JS, fonts, icons and media strategy
- PWA-ready foundation

## Phase 2 capabilities

- Clothing products with color + size variants
- Per-variant stock
- Persistent carts
- Stock reservations during payment
- Orders and order item snapshots
- Coupons
- Checkout idempotency
- Gateway-neutral payment state machine
- Wishlist
- In-site notifications

See `docs/PHASE2_COMMERCE.md` for details.

## Start locally

If `.env` already exists, keep it.

```cmd
docker compose up --build
```

Open:

- Store: http://localhost:8080
- Health: http://localhost:8080/health/
- Catalog API: http://localhost:8080/api/catalog/products/
- Admin: http://localhost:8080/admin/

Create a superuser:

```cmd
docker compose exec web python manage.py createsuperuser
```

Create demo clothing data:

```cmd
docker compose exec web python manage.py seed_demo_catalog
```

Run Phase 2 tests:

```cmd
docker compose exec web python manage.py test apps.orders
```

## Non-negotiable AVAN rules

- Core shopping must remain usable without AI/social/analytics services.
- No critical frontend dependency may come from a foreign CDN.
- Redis/Celery outage must not block cart/checkout/order creation.
- Payment gateways are adapters, never hard-coded into checkout.
- Production deployment must be planned for availability during international-network disruption.
