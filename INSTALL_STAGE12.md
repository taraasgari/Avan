# AVAN Stage 12 — Growth, Technical SEO, Trust & Security

Stage 12 is an overlay for a project that already has Stages 1–11 installed.

## What this stage adds

- Dynamic product/collection/design/creator SEO metadata.
- Product + Organization + Website + Breadcrumb structured data.
- Correct IRR values in Product structured data while AVAN UI still displays Toman.
- Stable crawlable `?lang=en` / `?lang=fa` language variants.
- `hreflang` EN / FA / x-default.
- Expanded bilingual sitemap with products, collections, public designs and creators.
- OpenGraph/Twitter metadata.
- Owner-managed permanent 301 redirects.
- Content reporting + owner moderation queue.
- Notification preferences.
- Rate limiting for sensitive write routes.
- Login brute-force throttling.
- Hashed-IP security telemetry.
- Image byte validation using Pillow, dimension/pixel limits, not only extensions.
- CSP, Referrer-Policy, Permissions-Policy, COOP and other response headers.
- Optional production HTTPS/HSTS/security-cookie switches.
- Argon2 as the preferred password hasher.
- PWA icons + safer offline behavior; transactional/private pages remain network-authoritative.
- `avan_security_audit` deployment audit command.

## 1. Copy files

Copy everything inside `avan-stage12-update/` into the AVAN project root and replace matching files.

## 2. settings.py

Add:

```python
"apps.growth",
```

to `INSTALLED_APPS`.

In `MIDDLEWARE`, keep `AvanLocaleMiddleware` and add Stage 12 middleware in this order:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.core.middleware.AvanLocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.growth.middleware.SeoRedirectMiddleware",
    "apps.growth.middleware.AvanSecurityMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

At the very end of `config/settings.py` add:

```python
from config.security_settings import apply_security_settings
apply_security_settings(globals())
```

Do NOT turn `AVAN_PRODUCTION_SECURE=1` on while using plain `http://localhost:8000`.

## 3. urls.py

Add:

```python
path("", include("apps.growth.urls")),
```

Do not remove existing URL includes.

## 4. Rebuild because Argon2 was added

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Then:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
```

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
```

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check
```

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test apps.growth
```

## 5. Test the public SEO layer

Open a real product and View Source. The `<head>` should contain canonical, hreflang, OpenGraph and Product JSON-LD.

Test both deterministic language URLs:

```text
http://localhost:8000/shop/PRODUCT-SLUG/?lang=en
http://localhost:8000/shop/PRODUCT-SLUG/?lang=fa
```

Also inspect:

```text
http://localhost:8000/sitemap.xml
http://localhost:8000/robots.txt
```

## 6. Owner pages

```text
/owner/growth/
/owner/growth/redirects/
/owner/moderation/
/owner/security/
```

Use 301 redirects whenever a public slug/URL changes after it has been indexed or shared.

## 7. User safety/preferences

```text
/account/notification-preferences/
```

Public designs and public creator profiles receive Report links for signed-in users.

## 8. Local security test

Deliberately enter a wrong password several times. AVAN records hashed-IP security events and throttles repeated failures.

Run:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py avan_security_audit
```

On local development it is EXPECTED to warn about DEBUG, HTTPS cookies and HSTS.

## 9. Production switches — do this only at Stage 13 deployment

Production `.env` will use values similar to:

```env
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<long random secret>
DJANGO_ALLOWED_HOSTS=your-domain.example,www.your-domain.example
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.example,https://www.your-domain.example
AVAN_PRODUCTION_SECURE=1
AVAN_BEHIND_HTTPS_PROXY=1
AVAN_TRUST_X_FORWARDED_FOR=1
AVAN_CSP_ENFORCE=1
ENABLE_REDIS_CACHE=1
```

Only enable `AVAN_TRUST_X_FORWARDED_FOR` when traffic is guaranteed to arrive through your trusted reverse proxy.

## Important SEO note

This stage gives AVAN a strong technical SEO foundation. It cannot guarantee a Google position or sales. Ranking and conversion still depend on product demand, useful content, page speed in production, backlinks/brand signals, stock/price competitiveness, user behavior and ongoing Search Console data. Stage 13 will add production performance, monitoring and CI gates; post-Stage-13 work can then focus on commercial SEO/content strategy and conversion optimization.
