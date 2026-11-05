# Hendy Telegram Bot

Telegram control bot (Python 3.13 / aiogram 3.31.0) for the `hendy-server-AI-hub` organization. Admin-only commands are split into GitHub, Render, AI, server health, security, and an optional read-only PHP platform bridge.

## Capabilities

| Module | Commands | Capability |
|---|---|---|
| GitHub | `/gh_repos`, `/gh_repo`, `/gh_file`, `/gh_workflows` | List repositories, inspect metadata, read text files, list Actions workflows |
| GitHub write | `/gh_dispatch`, `/gh_issue` | Dispatch a workflow and create an issue (requires corresponding token permissions) |
| Render | `/render_services`, `/render_service`, `/render_deploy` | List services, inspect recent deploys, request a deploy after inline confirmation |
| AI | `/ask <question>` | OpenAI Responses API with `store=false` and a bounded input |
| Server | `/server_status` | HTTPS health checks against operator-configured URLs only |
| Security | `/security` | Admin/token/configuration posture report; non-admin Telegram IDs are denied |
| PHP platform | `/platform`, `/platform_jobs`, `/platform_orders`, `/platform_metrics` | Read allowlisted operational status, jobs, orders and metrics over the restricted bridge |

The bot intentionally does not provide arbitrary shell execution, remote terminal access, repository deletion, token display, unrestricted URL fetching, or arbitrary SQL. Render deploys require a second confirmation. The platform bridge accepts only GET requests for four fixed resources and requires a bearer token.

## Local setup

Requirements: Python 3.11–3.14.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Fill `.env` with real values:

- `BOT_TOKEN`: create a bot with Telegram BotFather.
- `TELEGRAM_ADMIN_IDS`: numeric Telegram user IDs, comma-separated. This is mandatory; an empty admin list fails closed.
- `GITHUB_ORG`: defaults to `hendy-server-AI-hub`.
- `GITHUB_TOKEN`: fine-grained PAT scoped only to the repositories the bot needs.
- `RENDER_API_KEY`: API key from Render account/workspace settings.
- `OPENAI_API_KEY`: optional until `/ask` is used.
- `SERVER_HEALTH_URLS`: optional semicolon-separated fixed HTTPS URLs.
- `HENDY_PLATFORM_API_URL` and `HENDY_PLATFORM_API_TOKEN`: optional URL and shared secret for the PHP read-only bridge.

Start:

```bash
python -m app.main
```

## PHP platform bridge

This repository contains the narrow PHP adapter under `platform-bridge/`; the customer-facing PHP application must mount the adapter in its existing API router and provide the data callbacks. The adapter exposes:

- `GET /api/integrations/telegram/v1/status`
- `GET /api/integrations/telegram/v1/jobs`
- `GET /api/integrations/telegram/v1/orders`
- `GET /api/integrations/telegram/v1/metrics`

The Python client requires HTTPS, does not follow redirects, rejects unknown resources, and sends a bearer token. Use a random token of at least 32 characters, shared only between the worker and the PHP service. Provider callbacks must return bounded, explicitly allowlisted fields; never return payment details, passwords, session material, or full personal records. The PHP adapter rate-limits requests and fails closed if it cannot apply the rate limit.

**Repository scope:** this repository contains the Python operations bot and PHP bridge adapter/example. The complete customer-facing PHP website, Admin dashboard, Mini App, and PostgreSQL application are included in the separate integrated source bundle, not in this GitHub repository's current tree.

## GitHub token permissions

Recommended fine-grained token resource owner: `hendy-server-AI-hub`. Select only the repositories this bot should manage. Grant:

- **Metadata: Read-only** — list organization repositories and read repository metadata.
- **Actions: Read and write** — list workflows and dispatch workflows.
- **Issues: Read and write** — create issues.
- **Contents: Read-only** — read text files with `/gh_file`.

Do not grant Contents write, Administration write, or organization owner permissions just to run these modules. Organization approval may be required for the PAT.

## Render deployment

1. Connect this repository to Render and create a Blueprint from `render.yaml`.
2. Review the Background Worker plan and current pricing before applying.
3. Set `BOT_TOKEN`, `TELEGRAM_ADMIN_IDS`, `GITHUB_TOKEN`, and `RENDER_API_KEY` in Render Environment. Add `OPENAI_API_KEY` only if the AI module is enabled.
4. To use the PHP bridge, also set `HENDY_PLATFORM_API_URL` and the matching `HENDY_PLATFORM_API_TOKEN` in the worker environment. Configure the same token in the PHP service.
5. Apply the Blueprint and review logs. Verify `/start`, `/gh_repos`, `/render_services`, and `/security` from an admin Telegram account. Test the platform commands only after the PHP bridge is mounted.

Do not put secrets in GitHub Actions YAML, `render.yaml`, commits, screenshots, or chat messages. `sync: false` tells Render to prompt for secret values rather than storing them in the Blueprint file.

## CI and local checks

```bash
ruff check .
python -m compileall -q app tests
pytest -q
```

GitHub Actions runs lint, dependency audit, import smoke test, compile, and unit tests on pushes and pull requests. The Blueprint uses `autoDeployTrigger: checksPass` so Render waits for GitHub checks before deploying.

## Environment reference

| Variable | Required | Description |
|---|---:|---|
| `BOT_TOKEN` | Yes | Telegram control-bot token |
| `TELEGRAM_ADMIN_IDS` | Yes | Allowlisted numeric Telegram user IDs |
| `GITHUB_ORG` | No | GitHub organization slug |
| `GITHUB_TOKEN` | GitHub module | Fine-grained GitHub token |
| `RENDER_API_KEY` | Render module | Render API key |
| `OPENAI_API_KEY` | AI module | OpenAI API key |
| `OPENAI_MODEL` | No | Default `gpt-6-luna` |
| `SERVER_HEALTH_URLS` | No | Fixed HTTPS health endpoints |
| `HENDY_PLATFORM_API_URL` | Platform module | HTTPS base URL of the PHP platform |
| `HENDY_PLATFORM_API_TOKEN` | Platform module | Shared bridge secret (minimum 32 characters) |
| `HTTP_TIMEOUT_SECONDS` | No | External API timeout, 3–60 seconds |
| `LOG_LEVEL` | No | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `AI_MAX_INPUT_CHARS` | No | Maximum AI prompt length; default 4000 |

## Operational notes

- Use one production BotFather token per environment. Do not run two long-polling replicas with the same token.
- Use a unique Render API key dedicated to this integration where possible.
- Anyone in `TELEGRAM_ADMIN_IDS` can invoke enabled GitHub/Render/AI operations; keep the list short.
- Server checks accept only configured HTTPS endpoints, reducing SSRF exposure.
- Error messages are sanitized; raw request bodies and secrets are not logged.
- Rate limiting is per process. Keep one worker replica unless shared throttling is introduced.

## Project layout

```text
app/
  config.py
  main.py
  handlers/       # Telegram command routing
  middlewares/    # allowlist auth + throttle
  services/       # GitHub, Render, AI, server, security, platform
platform-bridge/  # PHP read-only adapter and router example
.github/workflows/ci.yml
render.yaml
Dockerfile
requirements.txt
requirements-dev.txt
tests/
```
