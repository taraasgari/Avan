# AVAN Stage 14 — Owner UX + Visual Site Appearance

Stage 14 starts the post-infrastructure refinement phase. It keeps all Stage 1–13 commerce/security behavior and focuses on day-to-day usability.

## What changes

- Owner Console navigation is grouped into clear areas instead of one long flat list.
- Owner Console navigation search (`Ctrl/Cmd + K`) filters sections instantly.
- Larger Persian typography and larger controls/tables/forms across the Owner Console.
- More readable dashboard with quick actions.
- Product list gets thumbnails and direct Edit / Images / Variants / Store shortcuts.
- Product form is reorganized into Basic Information and Selling/Visibility sections.
- New superuser-only visual editor at `/owner/appearance/`.
- Live Light/Dark and Desktop/Mobile preview.
- Safe presets plus controls for accent color, light/dark surfaces, EN/FA base font sizes, content width, gutters, header height, section spacing, card/button radius and card shadow.
- Site appearance is stored as constrained design tokens; arbitrary CSS is not accepted.
- Storefront typography defaults are increased to 17px English and 18px Persian and shared spacing/card styling is cleaned up.

## Install

Copy the contents of `avan-stage14-update` over the project root and replace matching files.

No new Django app is added. `apps.owner` is already installed.

Run:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.owner.tests_stage14
```

Expected migration: `owner.0002_siteappearance`.

## Test manually

1. Open `/owner/` in Persian and verify the sidebar, tables and controls are comfortably readable.
2. Press `Ctrl+K` and search for a panel section.
3. Open `/owner/appearance/` as the superuser.
4. Change Persian font size, accent color, card radius and preview Light/Dark + Mobile/Desktop.
5. Save and open the storefront in a new tab. The saved appearance should persist after refresh.
6. Open `/owner/products/` and verify the direct Images / Variants / Edit actions.

## Git

```powershell
git add .
git commit -m "Redesign AVAN owner console and add visual site appearance editor"
git push
```
