# AVAN Stage 8 — Operations + Theme + English/Persian

This update adds:

- Light / Dark mode for storefront and Owner Console
- English / Persian UI switch with RTL/LTR switching
- Shared legacy-label translator for Stage 1–7 templates
- User Address Book
- User Return Requests
- Owner Operations dashboard
- Shipping / tracking workflow
- Return review workflow
- Audited inventory movements
- Supplier management
- Production batch tracking

## 1) Copy update

Copy the **contents** of `avan-stage8-update/` into the AVAN project root and replace matching files.

## 2) settings.py

Add:

```python
"apps.operations",
```

to `INSTALLED_APPS`.

Recommended language settings:

```python
LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("fa", "فارسی"),
]
```

Add this middleware immediately after `SessionMiddleware`:

```python
"apps.core.middleware.AvanLocaleMiddleware",
```

Example:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.core.middleware.AvanLocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    # ...
]
```

The UI switch still reads the language cookie in templates, but the middleware also activates Django's current request locale.

## 3) config/urls.py

Add to urlpatterns:

```python
path("", include("apps.operations.urls")),
```

Do not remove any existing Stage 1–7 URLs.

## 4) Migrate

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
```

Then:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
```

Then:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
```

Expected: `No changes detected`.

## 5) Tests

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.operations
```

## 6) Optional shipping defaults

This creates two shipping methods with **price 0**. It intentionally does not invent production prices.

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_operations_defaults
```

Set real shipping prices later before production.

## 7) Test pages

Customer:

- `/account/addresses/`
- `/account/returns/`

Owner:

- `/owner/operations/`
- `/owner/shipping/`
- `/owner/returns/`
- `/owner/inventory-movements/`
- `/owner/production/`

## Theme / language behavior

- Theme is saved locally as `avan_theme`.
- Language is saved in cookie `avan_language` and localStorage.
- Persian switches the document to RTL.
- English switches it back to LTR.
- Product names, creator bios, design text, customer addresses, and other user-entered content are **not machine-translated**. Only the application UI is translated.
- The legacy translator translates exact known UI labels from older stages without touching arbitrary product/user content.

## Return safety

Owner return status changes do **not** automatically send refunds. `REFUNDED` is an operational record only. Actual payment-provider refunds should be integrated later through the payment adapter.

## Inventory safety

Use `/owner/inventory-movements/` for manual stock adjustments. Every change records:

- SKU / variant
- movement type
- delta
- stock before
- stock after
- owner/staff actor
- note
- time

## Git

After checks pass:

```powershell
git add .
git commit -m "Add AVAN Stage 8 operations bilingual UI and dark mode"
git push
```
