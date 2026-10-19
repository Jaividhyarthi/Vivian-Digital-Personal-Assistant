# Vivian — Digital Personal Assistant

Local-first, warm ivory-and-sage digital assistant with a React/Vite dashboard and a FastAPI/SQLite backend. **This is a tested development build, not a fully autonomous production phone agent.**

## Features available now

- Two-space (personal/professional) OpenAI-backed chat; explicit local task and note tool calls
- Tasks, notes, explicit memory vault, contacts with trusted flags, reminders (stored only), call records, approvals, activity feed, preferences and JSON export
- Browser speech-to-text on supported browsers, local call screening **simulation**, and integration-status dashboard
- Non-destructive SQLite table migrations; local-first data stored in `backend/vivian.db`
- No real outgoing actions without configured provider and consent

## Requirements

Python 3.11+ and Node.js 20+. OpenAI API key and separate paid API credits for AI replies.

## Run — two terminals (Windows PowerShell recommended for frontend)

**Backend (PowerShell):**

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item ..\.env.example ..\.env
# Edit ..\.env with OPENAI_API_KEY; do not commit secrets.
python -m uvicorn main:app --reload --port 8000
```

**Backend (WSL Bash alternative):**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp ../.env.example ../.env
# Edit ../.env; then:
python -m uvicorn main:app --reload --port 8000
```

**Frontend (second Windows PowerShell terminal):**

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Backend docs: http://localhost:8000/docs. **If using WSL 1, run frontend in Windows PowerShell** to avoid Windows Node.js/WSL compatibility errors.

## Security and data

- Never commit `.env`, credentials, call recordings or SQLite database files. `.gitignore` excludes them.
- The default local development setup has no production-grade authentication. Do **not** expose port 8000 or 5173 to the internet.
- `VIVIAN_API_TOKEN` is an optional development guard, but the browser needs a matching token; it is **not** secure public authentication.
- Database is created on first start. New installations do not need to copy data from old versions.
- `GET /api/export` exports local data. Protect this endpoint; it contains sensitive information.
- User-saved memories are included in AI context; don't store sensitive information you don't want sent to the AI provider.

## Important limitations / roadmap

**Not connected:** real mobile SIM forwarding, purchased phone number, live telephony, call recording, voicemail, live transfer, native Android application, background notifications, Gmail/Calendar/Drive/GitHub OAuth, automatic external actions, device control, wake word, always-on agent, production auth. The call lab is explicitly a simulator. Stored reminders do not trigger OS notifications yet.

For real telephone receptionist service you need an eligible Indian telecom/voice provider, number provisioning, webhook security, call audio streaming, appropriate recording consent and carrier conditional forwarding. None is silently enabled.

## Tests

```bash
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Frontend build: `cd frontend && npm install && npm run build`.

## Publish

Create a new GitHub repository called `Vivian-Digital-Personal-Assistant` under your account, **without initializing README**, then in the extracted project root:

```bash
git init
git add .
git commit -m "Initial Vivian Digital Personal Assistant release"
git branch -M main
git remote add origin https://github.com/Jaividhyarthi/Vivian-Digital-Personal-Assistant.git
git push -u origin main
```

You must authenticate GitHub when prompted. Do not run git commands from a folder containing `.env` unless `.gitignore` is present and verified.
