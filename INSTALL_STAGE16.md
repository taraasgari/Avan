# AVAN Stage 16 — Product Upload + Customizable Garments Workflow

This update makes the owner product workflow explicit and connects customizable catalog products directly to AVAN Studio.

## What changes

- Product creation now has two clear types:
  - Ready to sell
  - Customizable garment
- Customizable products automatically get a Studio garment profile.
- New owner workflow:
  1. Product information
  2. Product images
  3. Color / size / SKU / stock
  4. Studio setup (customizable products only)
- New owner Studio setup page per product:
  - garment type: Tee / Hoodie / Crop
  - default fabric
  - enable/disable in Studio
  - front/back/left-sleeve/right-sleeve reference images
  - optional GLB/GLTF product-specific 3D model
- Owner Products can be filtered by Ready vs Customizable.
- New public garment picker: `/design/garments/`
- Main Design navigation now opens garment picker first.
- Clicking a garment opens Studio with that exact catalog product selected: `/design/?product=PRODUCT_ID`
- Store colors, sizes, SKU stock and base price continue to come from the same Product/Variant records.

## Important distinction

The catalog-to-Studio connection is now exact at the data level: the same Product, colors, sizes, price and stock are used.

For exact 3D appearance, upload the product-specific GLB/GLTF file in Owner > Product > Studio Setup. Stage 16 stores and exposes that asset to Studio. The final real-GLB renderer can then use it instead of a generic garment mesh.

## Install

Copy the contents of `avan-stage16-update` into the project root and replace matching files.

Then run:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.owner.tests_stage16
```

Expected migration:

`designs.0006_garment_product_assets`

## Owner workflow

Open:

`http://localhost:8000/owner/products/new/`

Choose **Ready to sell** for normal shop products.

Choose **Customizable garment** for a product that should also appear in Studio. After saving a new customizable product, Owner is sent directly to its Studio Setup page.

Then add:

- Product images
- Color/size variants and stock
- Studio references/model

Customizable products can be viewed at:

`http://localhost:8000/design/garments/`

## Git

```powershell
git add .
git commit -m "Add AVAN Stage 16 customizable garment product workflow"
git push
```
