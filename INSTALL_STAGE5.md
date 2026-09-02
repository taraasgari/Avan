# AVAN Stage 5 — Fit, Outfits, Feed, Analytics & Mobile Shell

This update assumes Stages 1–4 are already installed.

## What Stage 5 adds

- Private Size Passport
- Saved Outfit Builder using real ProductVariant rows
- Add an entire saved outfit to the existing Bag
- Following feed for creators the user follows
- Creator Analytics (likes, saves, remixes, followers, paid wears/orders)
- Global search across products, public designs and creators
- Mobile menu + mobile bottom navigation
- Search overlay + Ctrl/Cmd+K shortcut
- Safer PWA cache rules for transactional/private routes

## 1) Copy files

Extract the ZIP and copy the CONTENTS of `avan-stage5-update/` into the existing project root:

`C:\Users\Tara\Desktop\avan-starter`

Choose Replace for matching files.

## 2) settings.py

Add this to `INSTALLED_APPS`:

```python
"apps.wardrobe",
```

Keep `apps.designs` and `apps.experience` from previous stages.

## 3) config/urls.py

Add both includes to the web URL section:

```python
path("", include("apps.wardrobe.urls")),
path("", include("apps.core.search_urls")),
```

Do NOT remove the existing design/experience/cart/order API includes.

## 4) Migrate and verify

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
```

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
```

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
```

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.wardrobe
```

## 5) Test pages

- `/size-passport/`
- `/outfits/`
- `/following/`
- `/account/creator/analytics/`
- `/search/?q=avan`

### Outfit test

1. Open `/outfits/`.
2. Create a new outfit.
3. Add 2+ real in-stock variants.
4. Click `ADD OUTFIT TO BAG`.
5. Existing AVAN Bag drawer should open with those variants.

### Size Passport test

1. Open `/size-passport/`.
2. Choose your usual top size.
3. Return to an Outfit Builder.
4. Variant options matching that size show `YOUR SIZE`.

### Following feed test

1. Follow a public creator.
2. Open `/following/`.
3. Their published public designs should appear.

### Creator analytics test

Open `/account/creator/analytics/` while logged in. It reports public design counts, social interactions and paid wears using `OrderItem.design_id_snapshot`. It intentionally does NOT invent creator revenue before AVAN's commission rules exist.

## 6) Commit to GitHub after tests pass

```cmd
git add .
git commit -m "Add AVAN Stage 5 wardrobe feed analytics and mobile UX"
git push
```

## Architecture notes

- Size Passport measurements are private account data; public creator templates never receive them.
- Outfits persist exact ProductVariant IDs, so color/size are explicit and stock is rechecked when adding to Bag.
- Checkout remains independent of Size Passport, feed, search and creator analytics.
- PWA service worker treats `/api/`, `/checkout/`, `/orders/`, `/bag/`, `/account/`, `/size-passport/` and `/outfits/` as network-authoritative.
