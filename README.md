# LearnTrack

**Your AI learning continuity companion.** Remember what you learn. Pick up where you left off.

[![Product verification](https://github.com/NithishKumarAI/cognitive-memory-engine/actions/workflows/phase1-ci.yml/badge.svg?branch=main)](https://github.com/NithishKumarAI/cognitive-memory-engine/actions/workflows/phase1-ci.yml)

[Source](https://github.com/NithishKumarAI/cognitive-memory-engine) · [Walkthrough](DEMO_GUIDE.md) · [Screenshots](frontend/public/showcase) · **Live application: Current V1 deployment pending verification.**

## Why it exists

A study note often records what happened without helping you return. LearnTrack connects reviewed reflections, unresolved questions and intended next steps to their original evidence, so a later session can start with context.

The core differentiator is evidence-based learning continuity: checkpoints and recommendations trace back to confirmed records. The assistant supports this workflow; activity counts and self-reported understanding do not establish mastery.

## A look inside

Actual screenshots from existing browser tests, using synthetic Avery/Python learning records. They predate the LearnTrack rename and display the earlier name. Original [test evidence](test-artifacts/final-acceptance/screenshots) is preserved.

**Resume from a checkpoint**

![Synthetic dashboard with a decorators checkpoint](frontend/public/showcase/home.png)

**Inspect the evidence behind a next action**

![Synthetic recommendations with source links](frontend/public/showcase/recommendations.png)

**Understand recorded activity without invented mastery scores**

![Synthetic insights with logged time and confirmed reflections](frontend/public/showcase/analytics.png)

## What works

- Text capture and consented voice transcription, with an editable transcript.
- Structured AI drafts of topics, difficulties, questions and intentions; explicit human correction and confirmation before saving learning observations.
- Learning paths, study logs, saved captures and optional searchable memories.
- Resume checkpoints and deterministic recommendations with exact supporting-record links and persisted completion/resolution/dismissal feedback.
- Owner-scoped search and grounded assistant responses with cited saved evidence. Confirmed observations can be recalled without optional embeddings; keyword recall is not guaranteed paraphrase search.
- Recorded study time, activity patterns and confirmed-reflection counts; responsive navigation and light/dark/system appearance.
- An animated public `/` product story with original conceptual scenes, theme support, pause controls and reduced-motion behavior; the workspace stays authenticated under `/dashboard`.
- Password confirmation, accessible visibility controls and safe auth feedback, including recovery after account creation succeeds but automatic sign-in fails.

**Workflow:** text or consented audio → editable text → AI draft → user review → confirmed capture and observations → optional searchable memory → checkpoints, recommendations and grounded recall.

## Stack and architecture

Next.js App Router, React, TypeScript, Tailwind and Recharts; FastAPI, SQLAlchemy and Alembic; PostgreSQL with pgvector; Gemini for extraction/transcription/answers and SentenceTransformers for 768-dimensional embeddings.

```mermaid
flowchart LR
    Visitor[Public overview] --> UI[Next.js workspace]
    UI -->|Bearer token| API[FastAPI / owner checks]
    API --> DB[(PostgreSQL + pgvector)]
    API -->|Relevant text / consented audio| Gemini[Gemini]
    API --> Embeddings[Local SentenceTransformers]
    Embeddings --> DB
    DB --> Continuity[Confirmed evidence / continuity logic]
    Continuity --> API
```

AI suggestions remain separate from confirmed evidence. PostgreSQL persists captures, observations, optional memories, feedback and conversations. Existing API routes, database names, environment names and browser authentication keys are retained.

## Run locally on Windows

Follow [LOCAL_SETUP.md](LOCAL_SETUP.md). Install Python 3.12, Node 24 and local PostgreSQL/pgvector; create a **new separate development database**, then edit only `backend/.env` and `frontend/.env.local`. Both are gitignored.

Set `DATABASE_URL` and the explicit `ALEMBIC_DATABASE_URL` to that dedicated database. The local helpers read the two named database settings without weakening the existing Alembic guard:

```powershell
# From the repository root, after installing dependencies and configuring .env:
Set-Location backend
..\.venv\Scripts\python.exe scripts/check_local.py
..\.venv\Scripts\python.exe scripts/migrate_local.py
..\.venv\Scripts\python.exe scripts/check_local.py --database
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Stop if any readiness/migration command fails. In another terminal, run `npm ci` and `npm run dev` from `frontend`. Open `http://localhost:3000`; check backend `http://127.0.0.1:8000/health`. The public homepage works without the API, but signup and the workspace require a running API and initialized database. `AI_ENABLED=false` permits initial signup/login checks without Gemini; real capture/assistant operations need deliberate provider configuration.

## Manual testing

Follow [DEMO_GUIDE.md](DEMO_GUIDE.md): inspect the public page without signing in, create a synthetic account locally, capture and correct a note, confirm it, inspect a checkpoint/source, reload and record feedback. Live provider and microphone checks are optional, separately authorized checks, not established by mocked browser tests.

## Automated verification and CI

Use a **new disposable PostgreSQL instance** with pgvector and a database named `cme_phase1_test` on loopback. Test URLs never fall back to application configuration; PostgreSQL tests create random schemas. The role needs schema and extension provisioning permissions in this disposable instance. `.github/workflows/phase1-ci.yml` uses an isolated `pgvector/pgvector:pg16` service; CI verifies and does not deploy. The badge links to that workflow's current main status, not a claim that uncommitted edits ran remotely.

From the repository root, substituting your disposable instance's port and synthetic credentials:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-test.txt
$env:PHASE1_TEST_DATABASE_URL='postgresql+psycopg://phase1:test-only@127.0.0.1:55439/cme_phase1_test'
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q
```

Without this opt-in URL, PostgreSQL checks skip; that does not verify PostgreSQL. In another terminal at the repository root, against the same disposable instance, after backend tests finish:

```powershell
Set-Location frontend
npm ci
npm run test:release
npm run lint
$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8100'
$env:ALLOW_LOCAL_API_ORIGIN='1'
$env:NEXT_TELEMETRY_DISABLED='1'
npm run build
npx playwright install chromium
$env:E2E_PYTHON=(Resolve-Path ../.venv/Scripts/python.exe).Path
$env:PHASE4_E2E_DATABASE_URL='postgresql+psycopg://phase1:test-only@127.0.0.1:55439/cme_phase1_test'
$env:E2E_PRODUCTION='1'
$env:E2E_ARTIFACT_DIR='../test-artifacts/learntrack'
npm run test:e2e
```

Ports 3100 and 8100 must be free; the browser harness starts both services with synthetic accounts and mocked AI. It does not call paid Gemini or verify a physical microphone. See [frontend testing notes](frontend/README.md) and the [portfolio polish report](LEARNTRACK_PORTFOLIO_POLISH_REPORT.md) for local results.

## Live status, privacy and limits

**Current V1 deployment pending verification.** The repository homepage's historical Google Cloud deployment and older GitHub release do not establish that LearnTrack V1 is deployed. No current live application URL is advertised here. Use source, screenshots and the local walkthrough until an exact deployed revision passes acceptance.

Relevant reflections, consented audio and retrieved context can be sent to Gemini. Confirmed records and conversations persist in PostgreSQL; raw audio is not a saved learning record. Review provider retention, deletion/backups and cost controls before real use. Never log personal notes, tokens or audio.

JWTs remain in localStorage; injected scripts can expose them, and logout does not revoke an already issued token. Owner checks do not replace HTTPS, a reviewed session/CSP design or operational limits. `AI_ENABLED=false` blocks Gemini; `REGISTRATION_ENABLED=false` closes new accounts. Both default true for compatibility and neither provides quotas or distributed rate limits. The existing usage-limit table does not enforce spending limits. Search and displayed results are bounded, while owner-history metadata work can grow with history. No commercial usage, benchmark, mastery or accuracy claims are made.

Dependency advisories, Docker/image verification, live Gemini, microphone/HTTPS acceptance and production operating controls remain release gates; see [release checklist](RELEASE_CHECKLIST.md), [live acceptance guide](LIVE_ACCEPTANCE_GUIDE.md) and [unexecuted deployment plan](DEPLOYMENT_PLAN.md).

## Project history

**Previously developed as Cognitive Memory Engine.** Four development phases, V1 hardening and historical-recall acceptance are documented in the preserved [Phase 4 report](PHASE4_FINAL_PRODUCT_REPORT.md), [hardening report](V1_RELEASE_HARDENING_REPORT.md) and [final acceptance report](V1_FINAL_ACCEPTANCE_REPORT.md). This polish pass changes presentation, not authentication, AI algorithms or the database schema.

LearnTrack name uniqueness has not been confirmed. No trademark or domain ownership is claimed. [Portfolio/resume copy](PORTFOLIO_COPY.md) is available for factual reuse.
