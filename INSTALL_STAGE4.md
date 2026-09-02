# AVAN Stage 4 — Community + Drops + Challenges + Rewards

This update is designed to be copied **on top of Stage 3**.

## What Stage 4 adds

- Creator public profiles
- Creator avatar / bio / privacy toggle
- Follow / unfollow creators
- Follow notifications
- Saved Explore designs inside My AVAN
- Full Notification Center + unread badge
- Drops and curated Drop items
- Challenges with design submission
- Finalist / winner states
- AVAN Points wallet + immutable reward ledger
- Admin action to award challenge winners safely/idempotently
- My AVAN dashboard shortcuts and activity
- Demo seed command for one Drop and one Challenge

## 1) Copy the update

Copy the contents of `avan-stage4-update/` directly into your existing `avan-starter/` folder and replace matching files.

Do not delete `.env`, media, database volumes, or your existing project folder.

## 2) Add the Experience app

Open `config/settings.py` and add this one entry to `INSTALLED_APPS`:

```python
"apps.experience",
```

Keep `"apps.designs"` from Stage 3.

## 3) Add Experience URLs

Open `config/urls.py` and add this one web include inside `urlpatterns`:

```python
path("", include("apps.experience.urls")),
```

Your existing Stage 3 includes for accounts/designs/API should stay exactly as they are.

## 4) Run migrations

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
```

Then:

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
```

Then ensure there are no missing migrations:

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
```

## 5) Run tests

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.experience
```

You can also re-run Stage 3 design tests:

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.designs
```

## 6) Create demo Experience data

This creates a test Drop called **RED DISTRICT** and a test Challenge called **RED SIGNAL**. It uses an existing product and, when available, an existing published public design.

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_experience_demo
```

Expected output:

```text
AVAN demo Drop and Challenge are ready.
```

## 7) Test these pages

```text
/account/profile/
/account/notifications/
/account/saved-designs/
/creator/<your-username>/
/drops/
/drops/red-district/
/challenges/
/challenges/red-signal/
/rewards/
```

### Creator test

1. Open `/account/profile/`.
2. Add display name / bio / avatar.
3. Enable `PUBLIC CREATOR PROFILE`.
4. Open `/creator/<username>/`.
5. Use a second user to test Follow.
6. The creator should receive a Social notification.

### Saved-design test

1. Open `/explore/`.
2. Save a public design.
3. Open `/account/saved-designs/`.
4. The design should be listed there.
5. REMOVE toggles the real DesignSave record through the Stage 3 API.

### Challenge test

1. Have at least one public published design.
2. Open `/challenges/red-signal/`.
3. Select your design and submit it.
4. Open Django admin > AVAN Experience > Challenge entries.
5. Select the entry and run:
   `Mark selected entries as winners and grant configured points`
6. Open `/rewards/`.
7. The configured points should appear in the wallet ledger.
8. Running the award action again will not duplicate the reward.

## Important architecture decisions

- Following is stored in PostgreSQL, not Redis.
- Notifications remain non-critical to checkout.
- Reward balance is server-side and has a transaction ledger.
- Reward grants can use unique references for idempotency.
- Coupon conversion is intentionally NOT hardcoded yet.
- Challenge reward values are admin-configured, not embedded in frontend code.
- Drops can mix normal AVAN products and published creator designs.
- Public creator profiles are opt-in via `public_profile_enabled`.
