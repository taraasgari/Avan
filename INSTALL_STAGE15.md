# AVAN Stage 15 — 3D Studio Pro

This update replaces the old flat Studio with a self-hosted CSS-3D garment configurator and keeps the existing cart/order snapshot architecture.

## What is included
- Free drag rotation and wheel/pinch-style zoom controls
- Focus presets: full garment, collar, front, back, left sleeve, right sleeve
- Live garment color changes from real catalog variants
- Fabric presets with visibly different weave/sheen characteristics
- Independent design surfaces: front, back, left sleeve, right sleeve
- Text, image, global sticker and private user sticker layers
- Persian/English-capable font picker; owner can add system CSS stacks or upload WOFF/WOFF2 fonts
- AI prompt-to-image endpoint using OpenAI GPT Image when `OPENAI_API_KEY` is configured
- Local background-removal/stickerization helper for user assets
- Pinterest inspiration search link (no scraping/import of third-party images)
- Owner Studio drawer on the same page for garments, fabrics, fonts, sticker categories/assets and feature toggles
- Garment profiles are ready for T-shirt, Hoodie and Crop; T-shirt is the primary polished presentation
- Full Studio state stays in `design_data`, so cart/order snapshots preserve fabric, color, surfaces, fonts and layers

## Install
Extract the ZIP and copy the contents of `avan-stage15-update` over your project root.

No settings.py or config/urls.py edit is required because this update extends the existing `apps.designs` app and existing URL includes.

Run:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.designs.tests_stage15
```

## AI configuration
AI generation is deliberately server-side. Do not put the API key in JavaScript.

Add to your local `.env` / production secret store:

```env
OPENAI_API_KEY=your_server_side_key
```

Then restart the `web` container. The model defaults to `gpt-image-2` and can be changed from the StudioSettings record if required.

If no key is configured, the rest of Studio works normally and the AI dialog explains that owner setup is required.

## Pinterest
Stage 15 opens a Pinterest search for inspiration. It does not scrape or directly import Pinterest images. Users should upload artwork they own or have permission to use.

## Git
After verification:

```powershell
git add .
git commit -m "Upgrade AVAN Studio to 3D Pro configurator"
git push
```
