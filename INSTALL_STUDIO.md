# AVAN Studio V1 update

Copy the `apps`, `templates`, and `static` folders into the existing AVAN project and replace/merge when Windows asks.

Then make these small manual edits:

## config/settings.py
Add this line to INSTALLED_APPS:

    "apps.designs",

## config/urls.py
Add these two lines to urlpatterns BEFORE API catch-all routes if possible:

    path("", include("apps.designs.web_urls")),
    path("api/designs/", include("apps.designs.urls")),

## templates/accounts/dashboard.html
Change the MY DESIGNS link from `/design/` to `/account/designs/`.

Then run:

    docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
    docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
    docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.designs

Open:

    http://localhost:8000/design/?product=1
    http://localhost:8000/account/designs/

Studio V1 includes front/back design state, text layers, image uploads, drag, resize, rotate, layer order, garment/color switching, draft save, publish, remix-ready lineage, and admin garment mockups with configurable print areas.
