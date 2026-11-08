# AVAN Stage 20 — UX Consolidation

This update combines the requested owner/site redesign before stabilization:

- Persian-first storefront copy and improved light/dark contrast
- New explicit two-row storefront header with large live search and account dropdown
- Support moved into the account menu
- Owner visual page designer with draft/preview/publish workflow
- 2D garment Studio rebuilt around the exact customizable product reference images
- Front / back / left sleeve / right sleeve / neck-label views and configurable print zones
- Owner + private customer sticker libraries retained
- Automatic AVAN order tracking and per-item production/tracking codes
- `/track/` order status page
- Support tickets can be attached to an order
- Owner order search supports AVAN order code, item code and carrier tracking code
- Customer notification when order status changes

## Install

Extract the archive and copy the contents of `avan-stage20-update` over the project root:

`C:\Users\Tara\Desktop\avan-starter`

Choose Replace when Windows asks.

Because the development server is running with `--noreload`, restart `web` after applying migrations.

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart web
```

`makemigrations --check` should end with `No changes detected`.

Then hard-refresh the browser with `Ctrl + F5`.

## First checks

- `/` — Persian-first hero + new header
- `/owner/design/` — visual page designer
- `/owner/products/` — product workflow
- for a customizable product: `/owner/products/<id>/studio/` — five 2D reference views and print zones
- `/design/garments/` then Studio — exact product reference images
- `/account/support/` — ticket linked to an order
- `/track/` — AVAN tracking page
- `/owner/orders/` — search by AVAN/order/item/carrier codes

## Notes

- The new Studio intentionally removes the 3D/Pinterest-heavy workflow. The source-of-truth is now the exact garment/product reference views supplied by the owner.
- For automatic recoloring, use a neutral/light base garment PNG where possible. Individual color-specific image overrides can be added later if required.
- Existing user-created migration files from earlier stages (for example the locally generated index-rename migrations) should remain in the project; do not delete them.
