# Repository audit — 10 November 2026

Base: `fc8983c77288d60ddd1cbfb82227dcac4e11f158` (`main`). Development branch: `development/vivian-liquid-glass`.

## Confirmed from source

- FastAPI monolith, SQLite persistence with additive schema updates, React/Vite JavaScript dashboard.
- Existing tasks, notes, contacts, memories, reminders, calls, approvals, preferences, activity, JSON export.
- Chat Completions integration with one tool round and an optional API-token guard. Missing credentials previously produced an assistant-role configuration message.
- Reminders were stored only. No scheduler or push delivery existed.
- Android companion sends HTTPS requests to `/api/chat` with `x-vivian-token`. Kept intact.
- Call screening is explicitly a simulator. No Exotel client, credentials, webhook handler or live transport exists in this checkout.
- No Google OAuth, GitHub account integration, SQLAlchemy, Alembic or PostgreSQL integration exists.
- Five initial backend tests. No frontend tests, lockfile or CI workflow.

## Implementation decisions

Keep existing endpoints and database records; add schema columns and new tables rather than replace the persistence engine during the core milestone. The existing dashboard source remains in `frontend/src/main.jsx` and `style.css` for reference; the entry point is now TypeScript `main.tsx` with the original Liquid Glass design.

Preserve the application-owned tool loop and upgrade its provider transport to Responses API. The model is mandatory environment configuration. No live provider credential is required to use local workspace features.

Durable jobs use database transactions, a separate worker process, unique occurrence keys and a persistent inbox. This supports application/browser restarts and overdue jobs without presenting OS push as configured.

Owner authentication fails closed unless the explicit local-only development override is enabled. Browser sessions use expiring hashed tokens and HttpOnly cookies; Android retains its existing token header.

## Follow-up engineering

PostgreSQL/SQLAlchemy/Alembic migration, account-level OAuth integrations, rich project milestones, document extraction/retrieval and summaries, conversation threads/compaction, Web Push, production session hardening and runtime monitoring remain separate work. SQLite is intentionally retained for backward compatibility in this milestone; this is not a claim that the requested PostgreSQL architecture is finished.
