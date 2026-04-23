# Security Notes

## Current State

This project now uses environment-based configuration through `config.py`, `.env`, and `.env.template`.

Implemented in the codebase:
- Session and JWT secrets are read from environment variables.
- Database credentials, CORS origins, cache settings, logging, and SMTP settings are env-backed.
- Session cookie flags are configurable from env.
- SQL access uses parameterized queries throughout the data layer.
- Visitor and employee records now support soft-disable fields (`is_active`) in the aligned schema.

Not fully implemented yet:
- CSRF protection is not enforced server-side.
- Rate limiting is configured in env, but no limiter middleware is wired in the Flask apps.
- Security headers are defined in config, but no Talisman-style middleware is currently active.
- Admin authentication still allows legacy plaintext passwords; migrate stored admin passwords to hashes.

## Local Setup

1. Copy `.env.template` to `.env` if you need a clean local config.
2. Replace the placeholder secrets in `.env` with strong random values.
3. Set `SESSION_COOKIE_SECURE=True` when serving behind HTTPS.
4. Restrict `ALLOWED_ORIGINS` to the exact frontend origins you trust.
5. Replace any default admin credentials in the database before deploying.

## Recommended Next Hardening Steps

- Hash all admin passwords with `werkzeug.security.generate_password_hash`.
- Add real CSRF protection for form and JSON write endpoints.
- Add server-side rate limiting to login and attendance mutation routes.
- Serve both Flask apps behind HTTPS and a reverse proxy.
- Review database accounts so the app does not run as MySQL `root`.
