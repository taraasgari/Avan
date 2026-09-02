# AVAN Stage 9 — Owner Product Manager + Real Checkout + Analytics

Stage 9 does **not** add a new Django app or database table. It upgrades the apps already installed in Stages 1–8.

## What this stage adds

- Owner Catalog Manager: categories, colors and sizes without Django Admin.
- Full Product Media Manager: multi-image upload, primary image, ordering, deletion.
- Full Variant Manager: color × size SKU creation/editing, price override, active state and audited stock changes.
- Shipping Method Manager: English/Persian names, price, ETA, active state.
- Checkout now uses real ShippingMethod prices.
- Logged-in customers can select a saved Address Book entry during checkout.
- Manual address checkout remains available for guests or new addresses.
- Order creates a Shipment snapshot linked to the selected shipping method.
- New Owner Analytics page with 30-day revenue/order charts, order/cart/shipping status and top products.
- No external chart CDN: analytics rendering is local JavaScript.

## Install

Copy the **contents** of `avan-stage9-update` over the project root and replace matching files.

No `INSTALLED_APPS` or URL include changes are required if Stages 7 and 8 are already installed.

Run:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.owner.tests_stage9
```

Expected migration check:

```text
No changes detected
```

## Owner pages

```text
/owner/analytics/
/owner/catalog/
/owner/shipping-methods/
/owner/products/<id>/media/
/owner/products/<id>/variants/
```

## Checkout test

1. In `/owner/shipping-methods/`, set the real shipping prices you want.
2. Log in as a customer and save an address at `/account/addresses/`.
3. Add an item to Bag.
4. Open `/checkout/`.
5. Select a saved address and shipping method.
6. Place the order.
7. Verify `shipping_amount` on the order and the shipment in `/owner/shipping/`.

## Important behavior

- Shipping price is selected on the server from an active `ShippingMethod`; the browser cannot choose an arbitrary price.
- Saved addresses are looked up by both address ID **and current user**, so one account cannot use another account's saved address.
- Variant stock changes from the new Product Variant Manager go through `InventoryMovement` instead of silently overwriting stock.
- Existing orders remain snapshots; changing a shipping method price later does not change old `Order.shipping_amount` values.

## Git

```powershell
git add .
git commit -m "Add AVAN Stage 9 product manager checkout shipping and analytics"
git push
```
