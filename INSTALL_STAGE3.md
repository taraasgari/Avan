# AVAN — Stage 3: Wearable Designs + Explore

Prerequisite: AVAN Studio V1 is already installed (`apps.designs` exists and `designs.0001_initial` has been migrated).

## What this update adds

- Choose size inside AVAN Studio.
- Save the design and add that exact design to the shopping bag.
- Cart items can now reference a design and keep an immutable JSON design snapshot.
- Order items copy the customization snapshot so later edits/deletes cannot change an old order.
- Public Explore page at `/explore/`.
- Public design detail page at `/explore/<design-id>/`.
- Like / Save / Remix APIs and UI.
- Publish options: Allow Remix + Let Others Wear It.
- Public designs marked for sale can be added to a guest cart in an available size.
- Remix lineage is preserved through `parent_design`.
- Social notifications for likes/remixes.
- Admin visibility for custom cart/order data.
- Stage 3 tests.

## Install

1. Extract the ZIP.
2. Copy the CONTENTS of `avan-stage3-update` into your existing project root:

   `C:\Users\Tara\Desktop\avan-starter`

3. Allow Windows to replace matching files.
4. Do NOT replace `.env` (this update does not contain one).
5. Run:

```cmd
cd C:\Users\Tara\Desktop\avan-starter
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.designs
```

Expected: migrations apply and tests end with `OK`.

## Manual config check (normally already done in Studio V1)

`config/settings.py` must contain:

```python
"apps.designs",
```

`config/urls.py` must contain:

```python
path("", include("apps.designs.web_urls")),
path("api/designs/", include("apps.designs.urls")),
```

Do not add duplicate entries if they already exist.

## Test flow

### Own custom design

1. Sign in.
2. Open `/design/`.
3. Choose garment/color.
4. Add text/image.
5. Choose size.
6. Click `ADD CUSTOM DESIGN TO BAG`.
7. Open Bag -> Checkout -> create order.
8. Order API/page will keep design title, creator and design snapshot.

### Explore / marketplace flow

1. In Studio tick `ALLOW REMIX` and/or `LET OTHERS WEAR IT`.
2. Click `PUBLISH`.
3. Open `/explore/`.
4. Like / Save / Remix the design.
5. If `LET OTHERS WEAR IT` was enabled, open the public design, choose a size and add it to Bag.

## Pricing note

Stage 3 deliberately does not invent a printing surcharge or creator commission. The cart currently uses the selected garment variant price. A separate pricing/creator-payout rule can be added later without changing the design snapshot architecture.
