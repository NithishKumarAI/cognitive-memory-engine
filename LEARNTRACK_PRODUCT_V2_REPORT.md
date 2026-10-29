# LearnTrack product V2 — implementation record

## Starting state and architecture assessment

Started on 29 October 2026 with a clean checkout of `main`, commit
`d4f4efecd77b212f3bef79ba47950ff756c658e3`. Only `main` and cached `origin/main`
existed. Work is isolated on `codex/learntrack-product-v2`; remote main requires
the owner's approval. The product already used LearnTrack in the UI and API.
Remaining prose in progress/architecture documents has been renamed too.

The existing engine uses Next.js client components, FastAPI, owner-scoped JWT
authentication, SQLAlchemy, PostgreSQL/pgvector and forward Alembic migrations.
Capture stores original input before analysis; confirmation persists reviewed
observations, optional memories and optional study time. Continuity and recall
already use those records. Preserve this engine and the existing capture links.

## Initial findings before feature changes

- Home and Capture use `Promise.all` for unrelated initial reads. A single
  rejection prevents all successful results from being applied.
- The test dependency file omits `tzdata`; production requirements include it.
  This can break non-UTC overview requests on Windows, but cannot by itself
  explain Capture history failures. This machine currently has tzdata installed.
- The configured local application database was checked read-only outside the
  sandbox: all six inspected learning/user tables exist and Alembic is at
  `f40100000001`. No existing data was changed. The local configuration checker
  flags missing `ALEMBIC_DATABASE_URL`; that is a setup issue, not proof of the
  historical dashboard failure.
- A sandboxed database check misleadingly failed with OperationalError. The
  same read-only check succeeds outside the sandbox. TestClient tests also
  stalled inside the sandbox; verification must use the approved runtime.
- Baseline backend suite: **212 passed**, 3 deprecation warnings, against a new
  disposable PostgreSQL container on port 55441. No production credentials or
  paid Gemini calls were used.

The exact historical backend failure has not yet been reproduced. Do not claim
the frontend request grouping identifies which endpoint originally failed.

## Verified product changes

Home embeds the shared CaptureInterface with text first and optional voice input.
Manual drafts use `/capture/manual`, never invoke Gemini, preserve original input,
and require a separate confirmation. Confirming on Home refreshes continuity and
overview state without navigation. The advanced Capture page and observation
anchors remain available. Optional paths/history load independently from source
links; failures have explicit retry messages and are not presented as empty data.

Settings → AI Configuration supports adding, replacing and removing personal keys.
The `f50100000001` migration only adds `ai_credentials`; no historical learning
records are reset. Fernet authenticated encryption binds each key to its owner.
Server configuration supplies encryption keys, with newest-first MultiFernet
rotation. Missing encryption configuration disables saving keys. Gemini's shared
provider reads the authenticated owner through a request context copied into
worker threads. Product requests have no global-key fallback. Key deletion and
rotation affect subsequent requests; existing in-flight calls can finish.

Registration, password hashing, existing JWT wire format, browser token storage,
owner checks, retrieval, learning actions and historical record links are retained.
SQLAlchemy errors now return a sanitized 503 without SQL or credentials.

The fresh-account matrix passes on migrated PostgreSQL: `/me`, `/learning/overview`
(Asia/Calcutta), `/learning/checkpoints`, `/learning/recommendations`,
`/learning-tracks`, `/capture` and `/health` each return **200** with AI enabled
and disabled. Existing unit/provider tests mock all AI calls. The historical
failure itself remains unconfirmed because the original failing environment was
not available; the currently configured local schema is complete.

Baseline remote CI was independently read through the public GitHub API:
[run 40863465228](https://github.com/NithishKumarAI/cognitive-memory-engine/actions/runs/40863465228)
completed successfully at the baseline SHA. The connector's commit-workflow tool
returned no entries because it filters pull-request events. Remote branch search
returned only `main`. These results do not verify unpushed V2 changes remotely.

At this stage the backend suite reports **219 passed, 0 failed, 0 skipped** with
three existing deprecation warnings. Frontend release tests report **3 passed**;
lint and TypeScript pass, and the production frontend build succeeds. Browser
verification and final branch status are recorded separately in final acceptance.

Current advisory checks initially found one high npm advisory in transitive Zod;
updating Zod removed it. Cryptography and dnspython were updated to the audit's
fixed versions (50.0.0 and 2.9.0) and backend verification was rerun. Additional
model/toolchain advisories remain and prevent an unconditional release claim.

Final product browser run: **28 passed, 0 failed, 0 skipped**, against the
production build and disposable PostgreSQL. Includes 390/768/1440 light/dark
layouts, axe accessibility scans, historical recall after 110 updates, Home
manual confirmation/refresh and capture deep links despite failed optional
listings. An earlier run had a test-locator ambiguity from a second Learning
Paths link; the locator was scoped to workspace navigation, then the complete
suite was rerun. No existing tests were removed.

Post-fix npm audit: **0 vulnerabilities**. The Python environment still reports
**22 advisory entries across five packages** (some advisory IDs repeat): filelock,
pip, sentence-transformers, setuptools and torch. See the saved before/after JSON
under `test-artifacts/`. These are unresolved release risks, not waived findings.

On this Windows Python, running `ZoneInfo('Asia/Calcutta')` with site packages
disabled reproduces `ModuleNotFoundError: tzdata` / `ZoneInfoNotFoundError`.
The normal runtime succeeds. This validates the dependency requirement while
remaining insufficient to establish the original Capture failure's cause.

## Original failure identified — configured legacy API

A later direct check of the ignored `frontend/.env.local` found
`NEXT_PUBLIC_API_URL` pointing to the existing legacy Cloud Run origin rather
than the local backend on port 8000. Read-only **unauthenticated** requests to
that exact configured origin returned:

- `/health`: **200**.
- `/openapi.json`: **200**, title **Cognitive Memory Engine**. It declares learning
  tracks but none of the new `/learning/*` continuity or `/capture` routes.
- `/me`: **401**, as expected without a token.
- `/learning/overview`: **404**.
- `/learning/checkpoints`: **404**.
- `/learning/recommendations`: **404**.
- `/learning-tracks`: **401**, as expected without a token.
- `/capture`: **404**.

This supplies direct evidence for both reported failures: Home's request group
includes missing continuity routes; Capture's group includes missing capture
history. A healthy legacy backend is not compatible with the current frontend.
Successful registration against that API cannot establish route compatibility.
The independent PostgreSQL matrix establishes the same required endpoints exist
and return 200 in the current local code with an empty account.

The local frontend setting is now `http://127.0.0.1:8000`; its previous file is
preserved as the ignored `.env.local.before-learntrack-v2`. Other settings and
production credentials were not changed. Restart `npm run dev`, or rebuild a
production frontend, to replace the old API origin embedded in JavaScript. Users
registered through the legacy remote API must register separately in their local
database; accounts are not copied or silently migrated between environments.
No Cloud Run deployment or remote data mutation was performed.

The earlier uncertainty entries above record the investigation in order; this
direct endpoint evidence supersedes the initial unknown-cause disposition.
