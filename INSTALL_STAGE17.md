# AVAN Stage 17 — PLAY + Clothing Challenge Controls

This update adds a standalone AVAN PLAY hub with original single-player browser mini-games and gives the Owner Console a master visibility switch for every game and every clothing/design challenge.

## What is included

### AVAN PLAY
Public routes:
- `/play/`
- `/play/thread-runner/`
- `/play/print-catch/`
- `/play/closet-match/`
- `/play/color-lab/`

Games are lightweight Canvas/JavaScript games with desktop + touch controls. Logged-in users can save scores and earn AVAN Points. Guest users can still play but their score is not persisted.

Default games:
1. Thread Runner — endless runner in the AVAN workshop.
2. Print Catch — catch print tiles, avoid ink, build combo.
3. Closet Match — memory matching game.
4. Color Lab — fast color-recognition game.

The server issues a signed run token before each game and rejects obviously impossible scores. It is not intended to be an esports-grade anti-cheat system, but raw arbitrary scores are not blindly trusted.

### Owner visibility switches
New Owner route:
- `/owner/play/`

Every game and every challenge has an ON/OFF switch.
- ON = visible to users.
- OFF = hidden from the public site, without deleting scores, entries or configuration.

Challenge switches are backed by the new `Challenge.is_enabled` field. Enabling a draft challenge also publishes it so the simple Owner switch behaves as expected.

### Clothing challenge presets
The seed command creates these challenge presets **disabled**:
- Black Tee Challenge
- Persian Streetwear
- Two Colors Only
- Summer Drop
- Hoodie Concept
- Blind Brief: Future Tehran

Each challenge can be attached to one customizable garment from Stage 16. If a garment is selected, `START DESIGNING` opens Studio with that exact product.

### Rewards
Each game has Bronze / Silver / Gold score thresholds and configurable AVAN Points. A logged-in player can receive one points reward per game per day; repeated runs still save scores for leaderboard improvement.

## Install

Extract the ZIP and copy the contents of `avan-stage17-update` over:

`C:\Users\Tara\Desktop\avan-starter`

Choose Replace when Windows asks.

No new app needs to be added to `INSTALLED_APPS`; this update extends the existing `apps.experience` app.

Run:

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

Expected:

`No changes detected`

Create the four games + six challenge presets:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_play_experience
```

They are intentionally created OFF. Open:

`http://localhost:8000/owner/play/`

and enable only the games/challenges you want customers to see.

Run Stage 17 tests:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.experience.tests_stage17
```

## Quick verification

1. `/owner/play/` shows 4 games and 6 challenge presets.
2. Turn only `Thread Runner` ON.
3. `/play/` should show only Thread Runner.
4. Turn `Persian Streetwear` ON.
5. `/challenges/` should show only enabled challenges (plus any older challenge you previously left enabled).
6. Open a challenge, choose its customizable garment in Owner, and verify `START DESIGNING` opens `/design/?product=<id>`.
7. Play a game while logged in and verify score appears on the weekly board and AVAN Points are awarded only once per game per day.

## Git

```powershell
git add .
git commit -m "Add AVAN Stage 17 solo games and challenge visibility controls"
git push
```
