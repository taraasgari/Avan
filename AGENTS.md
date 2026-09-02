# AVAN Engineering Rules

These rules are architectural constraints, not suggestions.

1. AVAN is an independent project. Never modify, import from, or write into the cosmetics-store project/repository.
2. Core purchase path must remain available even when optional systems fail:
   Product -> Variant -> Cart -> Checkout -> Payment -> Order.
3. AI, social features, challenges, analytics, push/SMS/email, Redis, and background workers are optional layers. Their failure must not block commerce.
4. Do not use external CDNs for critical JS, CSS, fonts, icons, images, or runtime libraries. Vendor required assets locally.
5. Keep the frontend PWA-ready. Do not cache authoritative cart, checkout, payment, stock, or authenticated API responses as offline truth.
6. PostgreSQL is the source of truth for durable commerce data. Redis is not the source of truth.
7. Use provider interfaces for payment/notification integrations. Do not hard-code one external vendor into domain logic.
8. AVAN sells garments manufactured by AVAN. Users customize supported products; they do not construct garment shapes from scratch.
9. Social is lightweight and conversion-oriented: public creator profile, designs, likes/follows, discover, remix. Avoid building a general-purpose social network.
10. Notifications are first-class: in-site now; PWA/mobile push later. Notification failures must be non-blocking.
11. Brand name may change. Do not hard-code `AVAN` throughout business logic or templates; use settings/context where practical.
12. Mobile-first responsive behavior is mandatory. Future clients may include PWA, Android, and iOS using the same backend APIs.

## Phase 2 commerce invariants
- PostgreSQL is authoritative for carts, stock, reservations, orders, payments and coupons.
- Never make checkout depend on Redis/Celery availability.
- Never decrement physical stock at order creation; reserve first, consume only after confirmed payment.
- All checkout retries must support idempotency to prevent duplicate orders.
- Payment callbacks must update orders through the shared payment/order service, not bypass inventory rules.
- Social, AI, push, SMS, email and analytics failures must never fail an order transaction.
