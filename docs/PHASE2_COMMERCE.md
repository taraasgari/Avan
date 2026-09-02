# AVAN Phase 2 — Commerce Core

This phase adds the purchase backbone without making checkout depend on Redis, Celery, AI, social features, or external services.

## Added

- Persistent guest/user carts with UUID cart tokens
- Cart items based on ProductVariant (product + color + size)
- Available stock = physical stock - active reservations
- Coupon engine: fixed/percent, validity window, minimum subtotal, max discount, global/per-user limits
- Checkout with idempotency key support
- Orders and immutable order-item snapshots
- 20-minute stock reservations (configurable)
- PaymentAttempt state machine, still gateway-neutral
- Development-only payment success simulator when DJANGO_DEBUG=1
- Wishlist for authenticated users
- In-site order notifications for authenticated users
- Cleanup command for expired reservations
- Demo catalog seed command

## Core resilience rules

1. Adding to cart, checkout, order creation and stock reservations use PostgreSQL as the source of truth.
2. Redis/Celery failure does not block checkout.
3. Stock is not decremented when an order is merely created. It is reserved first and only consumed after confirmed payment.
4. External payment providers are adapters; no gateway SDK is hard-coded into order logic.
5. A repeated checkout request may send the same `idempotency_key` to avoid duplicate orders.

## Local update/run

```cmd
docker compose up --build
```

The web container runs migrations automatically.

Create demo products:

```cmd
docker compose exec web python manage.py seed_demo_catalog
```

Run tests:

```cmd
docker compose exec web python manage.py test apps.orders
```

Release stale reservations manually (optional housekeeping):

```cmd
docker compose exec web python manage.py release_expired_reservations
```

## API flow for local testing

1. `GET /api/catalog/products/`
2. `POST /api/cart/` -> returns a cart token
3. `POST /api/cart/<token>/items/` with `{ "variant_id": 1, "quantity": 1 }`
4. `POST /api/checkout/<token>/` with shipping/contact data
5. The order response contains `payment.id`
6. In development only, `POST /api/payments/<payment-id>/dev-success/` simulates a successful payment
7. `GET /api/orders/<order-number>/` shows the final order state

A real Iranian payment gateway is intentionally not wired yet. It will plug into the existing payment provider contract later without changing order/stock logic.
