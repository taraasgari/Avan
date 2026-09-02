# AVAN Stage 6 — Creator Commerce, Wallet, Points Coupons & For You

This update assumes Stages 1–5 are installed and the Stage 5 migration cleanup was completed (`makemigrations accounts designs orders` + `migrate`).

## What Stage 6 adds

- Per-design creator fee in AVAN Studio
- Public design total = garment price + creator design fee
- Immutable design-fee and commission snapshots in Cart/Order
- Creator earnings only after successful payment confirmation
- Idempotent earning ledger (one earning per paid order item)
- Configurable AVAN commission (no invented default: starts at 0% until admin sets it)
- Creator Wallet: available / pending payout / total earned / total paid
- Payout request workflow with Admin approve / paid / reject actions
- AVAN Points -> account-locked fixed coupon conversion, controlled by admin settings
- Rule-based `/for-you/` feed using local first-party signals only
- Creator Analytics now includes finalized revenue figures

## 1) Copy files

Extract the ZIP and copy the CONTENTS of `avan-stage6-update/` into:

`C:\Users\Tara\Desktop\avan-starter`

Choose Replace for matching files.

## 2) settings.py

Add to `INSTALLED_APPS` (keep all previous apps):

```python
"apps.marketplace",
```

Recommended placement: after `apps.experience` / `apps.designs` and before or after `apps.wardrobe`; Django dependency order is handled by migrations.

## 3) config/urls.py

Add to `urlpatterns`:

```python
path("", include("apps.marketplace.urls")),
```

Do not remove any existing web or API includes.

## 4) Migrate

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
```

Then:

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
```

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
```

```cmd
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.marketplace
```

## 5) Configure commerce before testing revenue

Open Django Admin -> **AVAN Creator Commerce -> Marketplace settings**.

The system intentionally does NOT invent your business rules. Defaults are safe/off:

- `commission_percent = 0`
- `minimum_payout_amount = 0`
- `points_redemption_cost = 0` (points conversion disabled)
- `points_coupon_value = 0`

Set your preferred values. Example numbers in tests are only test fixtures and are not production recommendations.

## 6) Test Creator Commerce

1. Creator signs in and opens `/design/`.
2. Create a design.
3. Enable `LET OTHERS WEAR IT`.
4. Set `CREATOR DESIGN FEE / TOMAN`.
5. Publish.
6. Use another account (or guest) to open the public design and add it to Bag.
7. Complete checkout and use the existing DEBUG payment simulator.
8. Sign back into the creator account and open:

`/account/creator/wallet/`

The earning should appear only after successful payment.

### Pricing snapshot rule

At checkout, AVAN snapshots:

- garment unit price
- creator design fee
- commission percent
- commission amount
- creator earning amount
- creator ID + design snapshot

Changing the design price or commission later does not mutate old orders.

Coupon discounts currently do not reduce the creator's snapshotted creator fee; AVAN absorbs the discount allocation. This is deliberate and can be changed later if your commercial policy requires proportional discount sharing.

## 7) Payout workflow

Creator: `/account/creator/wallet/` -> request payout.

Admin: **AVAN Creator Commerce -> Payout requests**.

Use Admin actions only:

- Approve selected payout requests
- Mark selected approved payouts as paid
- Reject selected payout requests and release balance

Stage 6 deliberately does not store bank/card details. Real payout-provider integration should be added only with the required security/compliance flow.

## 8) Points -> Coupon

After configuring Marketplace Settings, open:

`/rewards/`

The user can redeem the configured number of AVAN Points. The generated coupon is locked to that user account via `Coupon.assigned_user`; another account cannot use it.

## 9) For You

Open:

`/for-you/`

The initial recommendation engine is local and deterministic. It uses:

- followed creators
- saved designs / base products
- wishlist categories
- categories from paid orders
- popular public designs as fallback

It does not require external AI, an external recommendation API, Redis, or Celery.

## 10) GitHub checkpoint

After tests pass:

```cmd
git add .
git commit -m "Add AVAN Stage 6 creator commerce wallet rewards and For You"
git push
```
