# Vivian — Personal Digital Assistant

Original Liquid Glass workspace with your approved Vivian character, a FastAPI backend, persistent local data, and a separate reminder worker. Development branch: `development/vivian-liquid-glass`.

**Working core build.** Live OpenAI and ElevenLabs verification is pending credentials. Google OAuth integrations, PostgreSQL migration, local wake word and OS push are not implemented yet. See [implementation status](docs/IMPLEMENTATION_STATUS.md) and [repository audit](docs/REPOSITORY_AUDIT.md).

## Run locally

Requires Python 3.11+ and Node.js 22+. From the repository root:

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
cp .env.example .env
# PowerShell instead: Copy-Item .env.example .env
```

Set `VIVIAN_API_TOKEN` in the ignored `.env` to a unique random secret of at least 32 characters. This is your owner login token, not a provider API key. Keep it private. For local HTTP use `VIVIAN_COOKIE_SECURE=0`. OpenAI and ElevenLabs keys can remain blank.

```bash
cd frontend
npm ci
npm run dev
```

The development launcher starts the API, reminder worker and Vite together. Open the Local URL printed by Vite (normally `http://localhost:5173`). Enter your owner token. If Python uses another command, set `PYTHON` before starting the launcher. To run servers separately, use `npm run dev:frontend` and `python -m uvicorn main:app --port 8000` from `backend`.

If running the servers separately, start reminder delivery in another activated terminal:

```bash
cd backend
python worker.py
```

The API and worker must use the same `VIVIAN_DB`. Data defaults to `backend/vivian.db`; files default to `backend/private-files`. Existing records are preserved by additive migrations. Back up both before deployment/upgrades. The worker must remain running for timely delivery; overdue jobs catch up when it restarts. Delivery goes to the durable **Vivian inbox**. No OS push or closed-browser audio is claimed.

## Configure providers later

Edit the ignored backend environment, then restart the API:

```dotenv
OPENAI_API_KEY=
VIVIAN_MODEL=
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=VnvaVe7ctz87lJj9udKY
ELEVENLABS_MODEL=eleven_multilingual_v2
VIVIAN_TIMEZONE=Asia/Kolkata
```

Choose a Responses API model with function calling available to your API project. The model has no hardcoded fallback. Missing configuration yields HTTP 503 and a visible setup message, never a simulated AI answer. ChatGPT subscription access does not configure API access.

Microphone input uses browser speech recognition where supported, which may use the browser vendor's remote speech service. Review the transcript before sending. ElevenLabs keys remain backend-only. Playback can be interrupted using Stop. The supplied GIF has one frame; true avatar lip-sync and local wake-word support remain pending.

## Verify

```bash
cd backend
python -m pytest -q
cd ../frontend
npm test
npm run build
```

Tests isolate their database and provider transport. They cover auth, cross-origin writes, persistent reminder delivery across processes, deduplication, recurrence, memory approvals, tool failures, unknown tools, spaces and file access. They do not establish live provider functionality.

## Container deployment

Configure `.env` first, then:

```bash
docker compose up --build -d
```

The web service binds to `127.0.0.1:8080`, proxies the API internally and serves the built frontend. API/worker share a named data volume. For remote access place a trusted HTTPS reverse proxy in front, set `VIVIAN_COOKIE_SECURE=1`, and set `VIVIAN_ALLOWED_ORIGINS` to the exact HTTPS origin. Never expose the development server publicly. Keep `VIVIAN_DEV_NO_AUTH` unset. No secrets, database files or private uploads belong in Git.

Docker configuration is provided but has not been run in this environment. Keep SQLite deployment to one host with the shared volume; a PostgreSQL migration is still required for distributed deployment.

## Compatibility and boundaries

Android source is unchanged; its `/api/chat` and `x-vivian-token` contract remains. Existing notes, contacts, calls, call simulation, approvals and settings endpoints remain available. No Exotel integration was present in the audited repository; the simulator remains explicitly labelled.

AI tools are allowlisted to local task creation, reminder creation and proposed memory. Memory proposals require approval before saving. No email, payment, telephony, publishing or arbitrary shell tool is exposed. Provider failures after a local action are audited and do not silently retry that action. Review Activity before retrying an interrupted request.

[Maintainer](https://github.com/Jaividhyarthi) · [Portfolio](https://jaividhyarthi.github.io/jv-portfolio)
