# AVAN Stage 7 — Owner Console

This update adds a dedicated superuser-only Owner Console and disables separate creator design pricing by default while preserving the Stage 6 schema for later use.

## 1) Copy the update

Copy the contents of `avan-stage7-update/` into the root of the existing AVAN project and replace matching files.

## 2) Add the owner app

In `config/settings.py`, keep all existing apps and add:

```python
"apps.owner",
```

Stage 6's `apps.marketplace` must remain installed.

## 3) Add the Owner Console URL

In `config/urls.py`, add:

```python
path("owner/", include("apps.owner.urls")),
```

Do not remove any of the existing web/API routes.

## 4) Apply migrations

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
```

Stage 7 adds:

- `owner.0001_initial` — owner operational settings
- `marketplace.0002...` — `creator_pricing_enabled` switch (default `False`)
- `cart.0004...` — removes old separate design fees from still-open carts when pricing is disabled

Paid/historical orders are intentionally not rewritten.

## 5) Create the site owner account

If `/admin/` previously rejected you because no admin credentials existed, create the first superuser interactively:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

Enter a username, email and password when prompted. The password is typed invisibly in the terminal — that is normal.

The same superuser credentials work for:

- `http://localhost:8000/admin/`
- `http://localhost:8000/owner/`

The custom `/owner/` console is superuser-only. Ordinary customers and normal staff cannot open it.

## 6) Verify

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check

docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check

docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.owner
```

Expected migration check:

```text
No changes detected
```

## Owner Console sections

Open:

```text
http://localhost:8000/owner/
```

Sections included:

- Overview / sales KPIs
- Products / basic product CRUD
- Warehouse / stock + price override + active state
- Orders / fulfillment-safe status transitions
- Customers / account status, orders, designs, notifications
- Design moderation
- Creator overview
- Marketing / coupons, Drops, Challenges
- Finance / creator wallets and payout workflow
- Staff access
- CSV reports
- All Data / lower-level module access
- Owner + marketplace settings

The Owner Console also links to Django Admin for advanced model-level editing such as product images, colors, sizes, garment mockups, reward ledgers, payment attempts and private operational records.

## Separate creator design pricing

Stage 7 sets `creator_pricing_enabled = False` by default.

While disabled:

- creators can still publish designs;
- `LET OTHERS WEAR IT` still works;
- other customers can buy/wear public designs;
- no extra creator fee is added to the garment;
- open carts left over from Stage 6 have their old design fee cleared by migration;
- existing historical orders are not modified.

Later, the owner can turn the switch on from:

```text
OWNER → SETTINGS → MARKETPLACE SETTINGS
```

No schema redesign will be required later.

## Recommended Git checkpoint

After verification:

```powershell
git add .
git commit -m "Add AVAN Stage 7 owner console and configurable creator pricing"
git push
```
