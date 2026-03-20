# LMS Telegram Bot Development Plan

This document outlines the development approach for building a Telegram bot that integrates with the LMS backend. The bot allows users to check system health, browse labs and scores, and ask questions in plain language using an LLM for intent understanding.

## Task 1: Scaffold and Architecture

**Goal:** Establish a testable project structure with handler separation.

**Approach:**
- Create a `bot/` directory with a clear separation between handlers (business logic) and the Telegram transport layer
- Implement `--test` mode in the entry point (`bot.py`) that calls handlers directly without Telegram
- Handlers are pure functions: they take command input and return text responses
- This architecture enables offline testing, unit tests, and easy debugging

**Files created:**
- `bot/bot.py` — Entry point with `--test` mode and production Telegram polling
- `bot/handlers/` — Command handlers (no Telegram dependencies)
- `bot/config.py` — Environment variable loading from `.env.bot.secret`
- `bot/pyproject.toml` — Bot dependencies (aiogram, python-dotenv, httpx)

## Task 2: Backend Integration

**Goal:** Connect slash commands to real LMS backend data.

**Approach:**
- Create an API client service that wraps HTTP calls to the LMS backend
- Use Bearer token authentication with the `LMS_API_KEY`
- Update handlers to call the API client instead of returning placeholders
- Handle errors gracefully: if the backend is down, show a friendly message

**Files created:**
- `bot/services/api_client.py` — HTTP client for LMS API calls
- Updated handlers in `bot/handlers/commands.py`

**Endpoints to implement:**
- `/health` → `GET /health` on backend
- `/labs` → `GET /items/` (filter for labs)
- `/scores <lab>` → `GET /analytics/` (filter by lab)

## Task 3: Intent-Based Natural Language Routing

**Goal:** Enable plain text queries interpreted by an LLM.

**Approach:**
- Wrap all backend endpoints as LLM "tools" with clear descriptions
- Use an LLM (via OpenRouter or local model) to decide which tool to call based on user input
- The LLM receives tool descriptions and returns structured tool calls
- Execute the selected tool and return the result to the user

**Files created:**
- `bot/services/llm_client.py` — LLM client with tool-calling support
- `bot/handlers/intent_router.py` — Routes plain text to LLM for interpretation

**Key insight:** Tool description quality matters more than prompt engineering. If the LLM picks the wrong tool, improve the description — don't add regex-based routing.

## Task 4: Containerization and Deployment

**Goal:** Deploy the bot alongside the existing backend using Docker Compose.

**Approach:**
- Create a `Dockerfile` for the bot (Python base image, copy bot code, run with uv)
- Add the bot as a service in `docker-compose.yml`
- Use Docker networking: bot connects to backend via service name, not `localhost`
- Document deployment steps and troubleshooting

**Files created:**
- `bot/Dockerfile` — Container image for the bot
- Updated `docker-compose.yml` with bot service
- Updated `README.md` with deployment documentation

**Docker networking note:** Inside containers, use service names (e.g., `http://backend:42002`) instead of `localhost`.

## Testing Strategy

1. **Unit tests:** Test handlers directly with known inputs/outputs
2. **Test mode:** `uv run bot.py --test "/command"` for quick verification
3. **Integration tests:** Test API client against running backend
4. **Manual Telegram testing:** Deploy and verify in real Telegram

## Git Workflow

For each task:
1. Create an issue on GitHub
2. Create a branch: `task-1-scaffold`
3. Commit changes with clear messages
4. Open a PR with "Closes #..." in the description
5. Partner review, then merge
