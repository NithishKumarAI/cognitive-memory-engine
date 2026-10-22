# Cognitive Memory Engine

A personal learning workspace for capturing reflections, reviewing AI interpretations and resuming learning from saved evidence. Phase 4 is verified locally; no Phase 4 production deployment has been performed. Older demo deployments and screenshots are historical and do not establish the current release state.

## What you can do

- Capture text or record audio in a supported secure browser. Audio is sent for cloud transcription only after explicit consent; the transcript stays editable before analysis.
- Review structured AI suggestions (learned, self-reported understanding, difficulties, open questions and intended next steps), correct them, then explicitly confirm. Analysis alone does not establish confirmed learning or mastery.
- Organize learning paths, study logs and manual memories. Confirmed captures and observations preserve their source; creating a searchable memory is optional.
- Resume from checkpoints, inspect exact supporting captures/observations, and record completion, resolution or dismissal with retry-safe feedback.
- Search your owned paths, logs, memories, captures and observations. Review saved capture history and earlier assistant conversations.
- Ask grounded questions over owned saved history. Live answers separate referenced evidence from retrieved context; older answers do not pretend to have persisted citations.
- Explore recorded time, activity patterns and confirmed-learning counts. Activity is not a mastery score. Light, dark and system appearance work with desktop and mobile navigation.

## Architecture

Next.js App Router / React / TypeScript / Tailwind / Recharts talks to FastAPI through a bearer-token Axios client. SQLAlchemy and Alembic manage PostgreSQL with pgvector. Gemini provides structured extraction, transcription and contextual answers; SentenceTransformers supplies 768-dimensional embeddings. Confirmed evidence and deterministic continuity logic remain separate from model suggestions. The existing JWT/localStorage architecture is preserved.

`Text or consented audio → editable text → AI draft → user review → confirmed capture + observations → optional memory/embedding → continuity, retrieval and recommendations`

Deleting a learning path detaches historical records instead of erasing the history. Checkpoint summaries bound displayed evidence bodies while retaining global unresolved counts. Search returns at most 30 results, chat history pages at most 50, capture history pages at most 50; the interface requests smaller pages.

## Local development

Use Python 3.12, Node 24 and a **development-only** PostgreSQL database with pgvector. Never use production credentials for local tests. Configure a role and database according to your local PostgreSQL installation; install `vector` with an authorized database role.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env.local
```

Replace placeholders locally; never commit real secrets. Backend configuration: `DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_TIMEOUT_MS`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `FRONTEND_ORIGINS`. The public `NEXT_PUBLIC_API_URL` is compiled into the frontend at build time. An embedding model download may be required on first real use; provision network access/model caching deliberately.

After reviewing migrations and confirming the target is your disposable development database:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

In another terminal, `cd frontend`, `npm ci`, `npm run dev`. Open `http://localhost:3000`; database-aware health is `http://127.0.0.1:8000/health`. For a production frontend build locally use `npm run build` then `npm start`. A browser-reachable HTTPS backend URL is required for a hosted frontend.

## Isolated verification

The test suite never falls back to the configured application database. Ordinary tests use fresh in-memory stores and mocked AI; PostgreSQL tests use explicitly opted-in, randomly named schemas.

Create a **new disposable PostgreSQL instance** with pgvector and a database named `cme_phase1_test` on loopback. The CI workflow uses a dedicated `pgvector/pgvector:pg16` service with synthetic credentials. On Windows an independent `initdb` directory and unused loopback port also work; do not reuse a production or personal database just because its name matches. The test role must be able to create schemas and provision pgvector in this disposable instance.

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-test.txt
$env:PHASE1_TEST_DATABASE_URL='postgresql+psycopg://phase1:test-only@127.0.0.1:5432/cme_phase1_test'
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q
```

Without the opt-in URL, PostgreSQL tests skip: that is not proof of PostgreSQL correctness. Browser instructions are in [frontend/README.md](frontend/README.md); they use real disposable PostgreSQL, synthetic accounts and mocked AI. No paid provider call, physical microphone or live deployment is verified by these tests.

```powershell
cd frontend
npm ci
npm run lint
npm run build
npm run test:e2e
```

See [PHASE4_FINAL_PRODUCT_REPORT.md](PHASE4_FINAL_PRODUCT_REPORT.md) for actual results, screenshot evidence, remaining advisories and manual Windows checks. See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) before any production action. CI definitions add verification only; they do not deploy.

## Privacy and limitations

Reflections, transcripts and retrieved context can be sent to Gemini during relevant operations. Voice processing requires consent; raw audio is not a saved learning record. Confirmed text, observations, optional memories and conversations persist in PostgreSQL. Configure provider retention, database backups, deletion policy and redacted monitoring for your environment. Do not put personal reflections, tokens, audio or provider responses into logs.

JWTs remain in localStorage: injected script could read them. Logout clears local credentials but does not revoke an issued token server-side. Owner checks and no-store responses protect API access; they do not replace HTTPS or a reviewed session/CSP design. Search is bounded literal matching, not a full-text engine. Continuity still scans narrow owner metadata, so it is not constant-memory at unlimited history sizes. Semantic relevance thresholds need calibration against a real authorized corpus. The application does not implement distributed user quotas; gateway limits and Gemini budget controls are release requirements. Dependency advisories, real provider/microphone checks and Docker/cloud verification are recorded explicitly in the report.
