# AVAN Stage 11 — Product & Content Power Tools

Stage 11 adds bilingual catalog content, collections, a self-hosted media library, SEO route management, sitemap/robots, and transactional bulk catalog CSV tools.

## 1) Copy update
Extract `avan-stage11-update` into the AVAN project root and replace matching files.

## 2) settings.py
Add to `INSTALLED_APPS`:

```python
"apps.contentstudio",
```

Stage 8's locale middleware must remain enabled:

```python
"apps.core.middleware.AvanLocaleMiddleware",
```

## 3) config/urls.py
Add:

```python
path("", include("apps.contentstudio.urls")),
```

Do not remove any existing routes.

## 4) Migrate and verify

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.contentstudio
```

## 5) Backfill legacy English content
This copies the current legacy product/category text into missing English fields only. It never fabricates Persian translations.

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py backfill_catalog_content
```

Then enter Persian copy manually in `/owner/content/`.

## 6) New owner tools

- `/owner/content/`
- `/owner/content/products/`
- `/owner/content/categories/`
- `/owner/content/collections/`
- `/owner/content/media/`
- `/owner/content/seo/`
- `/owner/content/bulk/`

## 7) Public content

- `/collections/`
- `/sitemap.xml`
- `/robots.txt`

## Bulk CSV behavior
Use **Validate only** before **Apply import**. Apply mode runs in a transaction: if validation fails, no catalog rows are written.

Minimum useful columns: `sku`, `product_slug`, `category_slug`, `base_price`, `color_slug`, `size`, `stock`.

Use the export button in Owner Content to download the full supported schema.

## SEO behavior
`SeoPage` can override title, description, canonical URL, noindex, and optional JSON-LD for exact public paths. Product/category SEO fields are stored independently for English and Persian for use by catalog pages and APIs.

## Git

```powershell
git add .
git commit -m "Add AVAN Stage 11 content SEO collections and bulk catalog tools"
git push
```
