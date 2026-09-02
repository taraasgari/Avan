# AVAN Production Launch Runbook — Stage 13

This runbook is intentionally conservative. Do not enable production HTTPS/HSTS settings until the real domain is already serving valid HTTPS through a trusted reverse proxy.

## 1. Server prerequisites

- Docker Engine + Docker Compose v2
- Git
- A reverse proxy / TLS terminator on the host (Traefik, Caddy or Nginx) with a valid certificate
- Persistent disk space for PostgreSQL, media and backups
- Firewall: expose only SSH and the public TLS proxy. `docker-compose.production.yml` binds AVAN Nginx to `127.0.0.1:8080` by default.

## 2. Production environment

Copy `.env.production.example` to `.env.production` and replace every `REPLACE_...` value.

Generate strong secrets locally, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

At minimum verify:

- `DJANGO_DEBUG=0`
- 64+ character random `DJANGO_SECRET_KEY`
- real `DJANGO_ALLOWED_HOSTS`
- HTTPS-only `DJANGO_CSRF_TRUSTED_ORIGINS`
- non-default `DJANGO_ADMIN_URL`
- random PostgreSQL password
- `AVAN_PRODUCTION_SECURE=1`
- `AVAN_BEHIND_HTTPS_PROXY=1`
- `AVAN_CSP_ENFORCE=1`
- 32+ character `AVAN_METRICS_TOKEN`

Only set `AVAN_TRUST_X_FORWARDED_FOR=1` when untrusted clients cannot bypass the trusted reverse proxy and talk directly to the AVAN container port.

## 3. First production boot

```bash
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d
docker compose -f docker-compose.production.yml exec -T web python manage.py migrate --noinput
docker compose -f docker-compose.production.yml exec -T web python manage.py collectstatic --noinput
```

Then run the blocking go/no-go checks:

```bash
docker compose -f docker-compose.production.yml exec -T web python manage.py launch_check --strict
docker compose -f docker-compose.production.yml exec -T web python manage.py check --deploy
docker compose -f docker-compose.production.yml exec -T web python manage.py avan_smoke_test
```

Do not open public traffic while `launch_check --strict` fails.

## 4. Health and monitoring

- `/_health/live/` — process liveness, public and minimal
- `/_health/ready/` — database readiness; Redis becomes required only when Redis cache is explicitly enabled
- `/_metrics/` — disabled unless `AVAN_METRICS_TOKEN` is configured. Send the token only in `X-AVAN-Metrics-Token`.
- `/owner/launch/` — superuser-only launch dashboard
- `/owner/launch/audit/` — superuser-only Owner Console write audit

Production logs should use `AVAN_JSON_LOGS=1`. Every response gets an `X-Request-ID` that is also emitted into request logs.

## 5. Staff permissions

Stage 13 changes Owner Console access from superuser-only to least privilege staff access.

Superusers remain unrestricted and are the only accounts allowed to grant/revoke staff access or open Launch / Ops.

Preset staff roles:

- Manager
- Catalog / Content
- Warehouse / Fulfillment
- Customer Support
- Marketing / Community
- Finance
- Security / Audit
- Custom

Each staff account can be customized per section from `/owner/staff/`.

## 6. Backups

Before every release and at least daily in production:

```bash
./scripts/backup.sh
```

The backup contains:

- PostgreSQL custom-format dump
- media archive
- SHA-256 checksums
- manifest timestamp

Copy backups off the server as well. A backup stored only on the same VPS is not disaster recovery.

Restore is intentionally destructive and requires explicit confirmation:

```bash
AVAN_RESTORE_CONFIRM=YES ./scripts/restore.sh backups/20260903T000000Z
```

Always test restore procedures on a staging server before relying on them in production.

## 7. GitHub CI/CD

`.github/workflows/ci.yml` runs:

- migration drift check
- migrations
- Django checks
- Django deployment checks
- full tests
- collectstatic
- Stage 13 strict launch checks
- smoke test
- production Docker image build

`deploy-production.yml` is manual (`workflow_dispatch`) and uses a protected GitHub `production` environment.

Required repository/environment secrets:

- `PROD_HOST`
- `PROD_USER`
- `PROD_SSH_KEY`
- `PROD_PATH`

Require manual approval on the GitHub `production` environment before enabling deployment for real customers.

## 8. Release order

1. Take a verified backup.
2. Confirm CI is green.
3. Deploy code/image.
4. Apply migrations.
5. Collect static files.
6. Run `launch_check --strict`.
7. Run `avan_smoke_test`.
8. Check `/owner/launch/` and security events.
9. Open traffic.
10. Watch error logs, 5xx responses, order flow and payment flow.

## 9. Rollback principle

Application rollback is `git checkout`/redeploy of the previous known-good commit. Database rollback is not the same as code rollback: if a release includes destructive schema changes, restore a verified pre-release backup or write a deliberate reverse migration. Never blindly run `migrate <old-number>` in production without reviewing the migration operations.
