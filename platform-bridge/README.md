# PHP platform bridge contract

The Telegram bot talks to the existing Hendy PHP application through a narrow, read-only API. It does not connect directly to PostgreSQL and does not accept arbitrary SQL, shell commands, hostnames, or URLs from Telegram messages.

## Required routes

Mount the following routes in the PHP application under `/api/integrations/telegram/v1`:

| Method | Path | Expected JSON |
|---|---|---|
| GET | `/status` | `{ "ok": true, "app": "hendy-platform", "version": "...", "database": "connected" }` |
| GET | `/jobs` | `{ "items": [...], "total": 0 }` |
| GET | `/orders` | `{ "items": [...], "total": 0 }` |
| GET | `/metrics` | `{ "users": 0, "jobs": 0, "orders": 0 }` |

Every route must enforce all of the following server-side:
1. Require HTTPS.
2. Compare the bearer token against a secret held in server environment configuration using a constant-time comparison.
3. Apply a rate limit by token and source IP.
4. Return only operational fields needed by administrators. Never expose password hashes, session data, payment credentials, bot tokens, API keys, or full personal information.
5. Use parameterized database queries and a bounded page size (maximum 50).
6. Log a request ID and actor, but never the Authorization header or token.

The PHP Admin dashboard must continue to use its existing session/CSRF protection. This bot bridge is a separate service credential, not a replacement for browser authentication.

## Environment

Set in the Python worker:

- `HENDY_PLATFORM_API_URL=https://your-php-platform.example`
- `HENDY_PLATFORM_API_TOKEN=<long random secret>`

Set the matching token only in the PHP service's secret environment as `TELEGRAM_BRIDGE_TOKEN`. Do not commit either value.

The Telegram implementation is intentionally read-only until the PHP service exposes and tests the routes above. Mutating operations (wallet, orders, VIP, vouchers, or video jobs) require a separate reviewed endpoint, explicit operation-level authorization, idempotency keys, and confirmation in Telegram.
