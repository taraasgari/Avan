# AVAN Stage 13 — Launch Hardening / Production Operations

Stage 13 closes the infrastructure phase. It intentionally focuses on launch safety and operations rather than redesigning storefront behavior.

## What is added

- `apps.launchops`
- least-privilege Owner Console staff permissions
- superuser-only Launch / Ops dashboard
- Owner Console write audit trail
- request IDs + optional JSON container logs
- liveness / readiness endpoints
- token-protected metrics endpoint
- strict production go/no-go command
- non-destructive smoke test command
- production Dockerfile + production Compose stack
- hardened Nginx production config
- PostgreSQL + media backup/restore scripts for Linux and PowerShell
- GitHub CI workflow
- manual protected GitHub production deploy workflow
- launch, security and backup runbooks

## Install

Extract `avan-stage13-update` into the project root and replace files.

### 1. `INSTALLED_APPS`

If you are applying files manually instead of replacing `config/settings.py`, add:

```python
"apps.launchops",
```

### 2. Middleware

Stage 13 needs these two middleware entries:

```python
"apps.launchops.middleware.RequestTelemetryMiddleware",
```

after Django `SecurityMiddleware`, and:

```python
"apps.launchops.middleware.OwnerAuditMiddleware",
```

after `AuthenticationMiddleware`.

### 3. URLs

If applying manually, include:

```python
path("", include("apps.launchops.urls")),
```

Stage 13 also makes the Django admin route configurable with `DJANGO_ADMIN_URL`. The development default remains `admin/`.

### 4. Launch settings

At the end of `config/settings.py`:

```python
from config.launch_settings import apply_launch_settings
apply_launch_settings(globals())
```

The ZIP already contains the updated files, so these edits are only needed if you choose not to replace them.

## Local Stage 13 verification

No new Python dependency is required, so a Docker rebuild is optional. Run:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.launchops
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py avan_smoke_test
```

`makemigrations --check` must say `No changes detected`.

On localhost, the following command is expected to WARN/FAIL production-only items such as HTTPS/HSTS/DEBUG/secret configuration:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py launch_check
```

Do **not** use `--strict` on your current localhost development environment.

## New Owner pages

- `/owner/launch/` — superuser only
- `/owner/launch/audit/` — superuser only
- `/owner/staff/` — now contains real section permissions

Health endpoints:

- `/_health/live/`
- `/_health/ready/`
- `/_metrics/` — hidden unless `AVAN_METRICS_TOKEN` is configured and the request sends it in `X-AVAN-Metrics-Token`

## Staff access behavior

`is_staff=True` no longer automatically means access to the entire Owner Console. A staff account also needs a Stage 13 `StaffAccess` profile.

The first time you use `MAKE STAFF`, the conservative `Customer Support` preset is created. The superuser can then choose a role preset or explicit section permissions.

Unknown Owner Console routes fail closed for staff users.

## Production

Do not reuse `.env` from localhost.

Copy:

```text
.env.production.example
```

to:

```text
.env.production
```

on the production server and replace all placeholder secrets/domains.

Production boot:

```bash
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d
docker compose -f docker-compose.production.yml exec -T web python manage.py launch_check --strict
docker compose -f docker-compose.production.yml exec -T web python manage.py check --deploy
docker compose -f docker-compose.production.yml exec -T web python manage.py avan_smoke_test
```

Read `docs/LAUNCH_RUNBOOK.md` before exposing production traffic.

## Git

After local verification:

```powershell
git add .
git commit -m "Add AVAN Stage 13 production hardening and launch operations"
git push
```
