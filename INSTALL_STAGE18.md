# AVAN Stage 18 — PLAY V3 + Private Rewards + Header V3

## What changed

- Replaced the Stage 17 solo-game concepts with four new, harder AVAN-native games:
  - Needle Grid
  - Pattern Drop
  - Signal Forge
  - Tag Strike
- Difficulty now ramps aggressively during each run.
- WebAudio sound effects + per-user SOUND ON/OFF toggle. No external audio/CDN dependency.
- `/play/`, individual games, `/challenges/` and challenge details now require login.
- Public game pages no longer reveal medal thresholds or reward values.
- Owner can configure per game and per medal:
  - required score
  - AVAN Points
  - discount percent
  - purchase credit in Toman
  - reward expiry days
- Game discount / purchase-credit rewards are account-locked one-use coupons.
- Challenge reward settings now support Points + discount + purchase credit.
- When a ChallengeEntry is marked WINNER, its configured reward bundle is granted automatically.
- Existing/new challenge presets remain independently ON/OFF from Owner → Play.
- Added additional clothing challenge presets: Back Print Only, Sleeve Story, One Hour Tee.
- Redesigned AVAN PLAY into a darker, more premium game hub.
- Rebuilt the public header into two calmer layers:
  - logo + real search field + account/bag/actions
  - compact primary navigation + More menu
- Mobile still uses the dedicated mobile navigation and gets a full-width search field.

## Install

Extract this update and copy the CONTENTS of `avan-stage18-update` into your project root:

`C:\Users\Tara\Desktop\avan-starter`

Choose Replace for existing files.

No new Django app needs to be added to settings or urls.

### 1. Migrate

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
```

This package includes the Stage 17 index-rename migration as `experience.0003` plus the new Stage 18 reward-control migration `experience.0004`.

### 2. Django checks

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
```

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
```

Expected: `No changes detected`.

### 3. Upgrade game presets and add challenge presets

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_play_experience
```

Existing game visibility switches are preserved. New challenge presets start OFF.

### 4. Tests

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.experience.tests_stage18
```

You can also rerun Stage 17 tests if desired.

## Owner controls

Open:

`http://localhost:8000/owner/play/`

Each game has a private scoring/reward editor. None of the configured numbers are shown to users before a run.

For every Bronze / Silver / Gold medal you can set:

- Score needed
- AVAN Points
- Discount %
- Purchase credit (Toman)

Discount and purchase-credit rewards create one-use coupons locked to the winning user's account. The user can see earned coupons in `/rewards/` only after earning them.

For challenges you can separately set:

- visibility ON/OFF
- customizable garment
- winner AVAN Points
- winner discount %
- winner purchase credit
- reward expiry

Marking an entry as WINNER grants the configured challenge reward bundle once.

## Login rule

These pages now require authentication:

- `/play/`
- `/play/<game>/`
- game start/submit endpoints
- `/challenges/`
- `/challenges/<challenge>/`

Unauthenticated users are redirected to login with `next=` back to the requested page.

## Public header

The old crowded one-line header has been replaced with:

- AVAN logo
- persistent search bar
- theme/language/account/bag actions
- a short primary nav row
- a `MORE` dropdown for secondary destinations

If old styles remain visible, use `Ctrl + F5` after replacing files.
