# Hendy Telegram Bot

Telegram control bot (Python 3.13 / aiogram 3.31.0) for the `hendy-server-AI-hub` organization. It provides five separated modules: GitHub, Render, AI, server health, and security.

## Capabilities

| Module | Commands | Capability |
|---|---|---|
| GitHub | `/gh_repos`, `/gh_repo`, `/gh_file`, `/gh_workflows` | List repositories, inspect metadata, read text files, list Actions workflows |
| GitHub write | `/gh_dispatch`, `/gh_issue` | Dispatch a workflow and create an issue (requires corresponding token permissions) |
| Render | `/render_services`, `/render_service`, `/render_deploy` | List services, inspect recent deploys, request a deploy after inline confirmation |
| AI | `/ask <question>` | OpenAI Responses API with `store=false` and input size limit |
| Server | `/server_status` | HTTPS health checks against URLs explicitly configured by the operator |
| Security | `/security` | Admin/token/configuration posture report; unauthorized Telegram IDs are denied |

The bot intentionally does not provide arbitrary shell execution, remote terminal access, repository deletion, token display, or unrestricted URL fetching. Deploying Render services requires a second confirmation button. This is a security boundary, not a missing feature.

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
- `TELEGRAM_ADMIN_IDS`: numeric Telegram user IDs, comma-separated. This is mandatory; empty admin lists fail closed.
- `GITHUB_ORG`: defaults to `hendy-server-AI-hub`.
- `GITHUB_TOKEN`: Fine-grained Personal Access Token (PAT), scoped to the Hendy organization and only the repositories the bot needs.
- `RENDER_API_KEY`: API key from Render account/workspace settings.
- `OPENAI_API_KEY`: optional until `/ask` is used.
- `SERVER_HEALTH_URLS`: optional semicolon-separated fixed URLs, e.g. `studio=https://studio.example.com/health;admin=https://admin.example.com/health`.

Start:

```bash
python -m app.main
```

## GitHub token permissions

Recommended fine-grained token resource owner: `hendy-server-AI-hub`. Select only the repositories this bot should manage. Grant:

- **Metadata: Read-only** — list organization repositories and read repo metadata.
- **Actions: Read and write** — list workflows and dispatch workflows.
- **Issues: Read and write** — create issues.
- **Contents: Read-only** — read text files with `/gh_file` (no source write permission is used).

The current code does not write source files or delete repositories, so do not grant Contents write, Administration write, or organization owner permissions just to run these modules. Organization approval may be required for the PAT.

## Render deployment

1. Push this repository to `hendy-server-AI-hub/hendy-telegram-bot`.
2. In Render, create a Blueprint from this repo and review `render.yaml`.
3. The Blueprint creates a **Background Worker** (long polling). Worker plans can incur charges; review the plan and current pricing in Render before applying.
4. Set the secret environment variables in the Render dashboard: `BOT_TOKEN`, `TELEGRAM_ADMIN_IDS`, `GITHUB_TOKEN`, `RENDER_API_KEY`, and optionally `OPENAI_API_KEY` / `SERVER_HEALTH_URLS`.
5. Apply the Blueprint and review logs. Verify `/start`, `/gh_repos`, `/render_services`, `/security` from an admin Telegram account.

Do not put secrets in GitHub Actions YAML, `render.yaml`, commits, screenshots, or chat messages. `sync: false` tells Render to prompt for secret values rather than storing them in the Blueprint file.

## CI and local checks

```bash
ruff check .
python -m compileall -q app tests
pytest -q
```

GitHub Actions runs lint, dependency audit, application import smoke test, compile, and unit tests on pushes and pull requests. The included Blueprint uses `autoDeployTrigger: checksPass` so Render waits for GitHub checks before deploying.

## Environment reference

| Variable | Required | Description |
|---|---:|---|
| `BOT_TOKEN` | Yes | Telegram bot token |
| `TELEGRAM_ADMIN_IDS` | Yes | Allowlisted numeric Telegram user IDs |
| `GITHUB_ORG` | No | GitHub organization slug |
| `GITHUB_TOKEN` | GitHub module | Fine-grained GitHub token |
| `RENDER_API_KEY` | Render module | Render API key |
| `OPENAI_API_KEY` | AI module | OpenAI API key |
| `OPENAI_MODEL` | No | Default `gpt-6-luna`; change to a model enabled for your API project |
| `SERVER_HEALTH_URLS` | No | Static HTTPS health endpoints |
| `HTTP_TIMEOUT_SECONDS` | No | External API timeout, 3–60 seconds |
| `LOG_LEVEL` | No | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `AI_MAX_INPUT_CHARS` | No | Maximum AI prompt length; default 4000 |

## Operational notes

- Use one production BotFather token per environment. Do not run two long-polling replicas with the same token.
- Use a unique Render API key dedicated to this integration where possible; Render API keys can access resources across the workspaces associated with the key unless a scoped key is available/enabled.
- Configure `TELEGRAM_ADMIN_IDS` carefully; anyone on this list can invoke enabled GitHub/Render/AI operations.
- The server module checks only configured HTTPS endpoints and does not accept URLs from Telegram messages, reducing SSRF exposure.
- Error messages shown to Telegram are sanitized; raw request bodies and secrets are not logged.
- Rate limiting is per process. For horizontally scaled deployments, add shared Redis-backed throttling before scaling beyond one worker.

## Project layout

```text
app/
  config.py
  main.py
  handlers/       # Telegram command routing, one router per module
  middlewares/    # allowlist auth + throttle
  services/       # GitHub, Render, AI, server and security services
.github/workflows/ci.yml
render.yaml
Dockerfile
requirements.txt
requirements-dev.txt
tests/
```
