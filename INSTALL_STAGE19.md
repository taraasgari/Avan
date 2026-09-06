# AVAN Stage 19 — Persian-first UI, Support, Live Search, Staff Access

## What changes
- Persian is the default UI language for new/no-cookie sessions.
- Header V4: explicit navigation (no MORE/+), live search suggestions, support link, sun/moon theme control.
- Stronger light/dark contrast and larger Persian readability.
- Product `search_tags` managed in Owner > Products and used by live suggestions.
- Search suggestions are grouped into Products, Categories, Collections, Designs and Creators.
- Customer support tickets under `/account/support/`.
- Owner/authorized staff support desk under `/owner/support/` with replies, priority and close/reopen.
- Staff access is now granular per Owner Console section using checkboxes.

## Install
Copy the contents of `avan-stage19-update` over the project root and replace files.

Run:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
```

Expected final migration check:

```text
No changes detected
```

Because development runs with `--noreload`, restart the web service after copying Python/template changes:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart web
```

Then hard-refresh the browser:

```text
Ctrl + F5
```

## Tests

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.core.tests_stage19 apps.accounts.tests_stage19 apps.launchops.tests_stage19
```

## Quick verification
1. Open `/` in a private/no-cookie window: it should default to Persian + RTL.
2. Toggle moon/sun and verify text remains readable in both themes.
3. Open `/owner/products/<id>/` and add comma-separated Search Tags.
4. Type one of those tags in the header search bar and confirm grouped suggestions appear.
5. As a customer open `/account/support/`, create a ticket and reply.
6. As owner open `/owner/support/`, reply to the ticket and close/reopen it.
7. Open `/owner/staff/`, grant a staff user only one or two sections, then log in as that user and verify unrelated Owner routes return 403.

## Notes
- Product names, creator bios, addresses and other user-entered content are never machine-translated.
- `Staff` and `Launch / Ops` remain superuser-only to prevent privilege escalation.
- Existing legacy staff permissions are migrated into the new section-permission list.
