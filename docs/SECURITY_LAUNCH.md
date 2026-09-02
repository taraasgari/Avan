# AVAN Security Launch Notes

Stage 12 introduced application security controls (Argon2, brute-force throttling, image validation, CSP/security headers, Security Center). Stage 13 adds operational controls around them.

## Stage 13 additions

- least-privilege Owner Console staff access
- superuser-only staff administration and launch controls
- state-changing Owner Console audit trail
- request IDs and structured JSON logs
- production health/readiness endpoints
- token-protected metrics endpoint
- production deployment checks
- hardened production Nginx defaults
- private backend Docker network for PostgreSQL and Redis
- production container health checks and restart policies
- verified backup/restore scripts
- CI migration/test/security gates
- manual protected production deployment workflow

## Important limits

No application can be called "secure forever". Keep Python/Django/PostgreSQL/Redis/Nginx images patched, rotate leaked credentials, review dependencies, keep backups off-server, monitor security events and use TLS on every production request.

The default CSP still permits inline scripts/styles because the existing AVAN frontend uses inline UI code. Removing `'unsafe-inline'` and moving to nonces/hashes is a worthwhile post-launch hardening change, but doing it blindly at Stage 13 could break the current storefront.
