# Phase 1 foundation report

Date: 2026-10-22 (Asia/Calcutta).
Baseline branch: `main`.
Baseline commit: `90c962eccb33088a5d41cf791b0233617eaa4e51`.

## Scope and baseline

Inspected backend entry point, auth/config/database/dependencies, models,
CRUD, routes, schemas, embedding/context/RAG services, embedding repair script,
all Alembic revisions and env configuration, backend dependencies, frontend
services and chat call sites, package/lockfile, README, architecture report and
progress documentation before implementing the scoped fixes.

The initial working tree already contained staged deletions of
`scripts/import_memories.py` and `scripts/memories.json`. Those were preserved.
No checkout, merge, reset, rebase, stash, commit or push was performed.
No production Neon/GCP resource was accessed. No real records were read or
modified, and no embedding repair script was run.

## Problems confirmed and changes

1. LearningTrack.study_logs had `cascade="all, delete"` despite the nullable
   foreign key's ON DELETE SET NULL. Removed the destructive cascade; normal
   SQLAlchemy relationship handling nulls the FK and preserves logs/memories.
   User deletion relationships and FK definitions were left intact.
2. Memory create/update committed text before embedding generation. Embeddings
   are now generated and validated (768 finite numeric values) before dependent
   ORM changes. Memory and embedding flush/commit together, with rollback on
   generation, validation, flush or commit failure. Update compares actual text
   values; unchanged text and metadata-only updates avoid generation. Existing
   embedding rows/model_name are updated, and missing rows are recreated.
   Low-level embedding helpers accept keyword-only `commit=False` so callers
   can own the transaction while existing standalone behavior remains available.
   Save failures return a generic 503 without exception details.
3. Authenticated users could enumerate/read other profiles. GET /users now
   returns only the current user in the existing list shape. GET /users/{id}
   returns the owner or a uniform 404 for every other ID. /me, register, login
   and password/JWT behavior are covered. Unrestricted user CRUD helpers have
   no remaining route callers; existing learning ownership checks were retained
   and tested, including related-record assignment on create/update.
4. Context positional numbers disagreed with actual source IDs. Context and
   prompt use real IDs, including [Memory 13] and [Memory 42]. Empty retrieval
   gives a deterministic unavailable answer without calling Gemini. Existing
   source response fields and actual-ID links remain intact. Source cards/badges
   now use [Memory ID]; wording describes retrieved memories rather than claiming
   every retrieved source was cited. No citation parser or new retrieval engine
   was introduced.
5. Health failure returned HTTP 200 with raw exception text. It now returns
   503 with generic database-unavailable JSON; success remains 200. The SELECT 1
   probe no longer prints its result.
6. Input schemas reject whitespace-only track names, topics, memory titles and
   content; durations must be positive. Explicit null is rejected for required
   database fields, including update notes/category. Omitted update fields remain
   omitted and nullable relationship IDs can still be explicitly unlinked.
   Validation does not trim stored text or impose extra business rules.
   Response schemas retain their prior permissiveness for historical records.
7. SentenceTransformer import is deferred until a model is actually needed.
   The production model name and Vector(768) contract remain unchanged.

## Files changed or added

Application changes:

- backend/app/models/learning_track.py
- backend/app/crud/memory.py
- backend/app/crud/memory_embedding.py
- backend/app/routes/user.py
- backend/app/routes/memory.py
- backend/app/main.py
- backend/app/db/database.py
- backend/app/schemas/learning_track.py
- backend/app/schemas/study_logs.py
- backend/app/schemas/memory.py
- backend/app/schemas/validation.py (new)
- backend/app/services/embedding_service.py
- backend/app/services/context_service.py
- backend/app/services/rag_service.py
- frontend/components/chat/chat-interface.tsx

Test, CI and documentation additions:

- backend/pytest.ini
- backend/requirements-test.txt
- backend/tests/conftest.py
- backend/tests/test_history.py
- backend/tests/test_memory_transactions.py
- backend/tests/test_api.py
- backend/tests/test_validation.py
- backend/tests/test_rag.py
- backend/tests/test_postgres.py
- backend/tests/README.md
- .github/workflows/phase1-ci.yml
- PHASE1_FOUNDATION_REPORT.md

## Automated coverage

The final suite has 76 passing cases with a disposable PostgreSQL instance:

- Track deletion with loaded/unloaded ORM relationships and direct database
  deletion, two logs, a linked memory, and another user's unaffected history.
- Memory/embedding creation, updates, generation and vector validation failures,
  existing values preserved on failure, flush and commit rollback, one embedding
  per memory, missing embedding recovery, unchanged text/metadata, sanitized API
  errors, and confirmation SentenceTransformer was never imported.
- Anonymous denial, two-user profile isolation, owner-only listing, invalid
  token, real local registration/password verification/login/JWT/me flow.
- Learning-track/study-log/memory read/update/delete/list ownership and related
  record assignment on create/update; explicit unlinking through the API.
- Required text/null/duration validation and omitted update fields.
- Mocked RAG retrieval/generation with IDs 13 and 42, source shape, owner filter
  forwarding, empty retrieval without a Gemini call; health success/failure.
- Real PostgreSQL checks for the three deletion paths, pgvector dimensions,
  cosine retrieval/ownership and the uniqueness constraint.
- An empty-schema Alembic test that reproduces the known bootstrap failure.
  This is a blocker characterization test, not a successful migration upgrade.

Tests overwrite configuration before app imports, disable dotenv loading,
create isolated stores/schemas, override database dependencies, and mock AI.
SQLite results are not presented as pgvector verification. Test fixtures create
individual current-model tables only in new temporary stores; no create_all,
drop_all, stamp or downgrade workaround is used.

## Commands executed and actual results

- `git status --short`, `git branch --show-current`, `git rev-parse HEAD`, file
  enumeration/reads, call-site searches and `git diff`: baseline inspected.
- Python 3.14.5, Node v24.15.0, npm 11.12.1 identified locally.
- `python -m pip show pytest` and virtual-environment package inspection:
  pytest was initially missing; application dependencies existed in `.venv`.
- `.venv\Scripts\python.exe -m pip install pytest`: restricted-network attempt
  failed DNS; retry with network access succeeded, installing pytest 9.1.1.
- `npm ci` in frontend: initial restricted attempt failed with npm's exit-handler
  error; network-enabled retry succeeded (418 packages). Existing lockfile kept.
  npm reported 17 dependency advisories: 2 moderate, 14 high, 1 critical.
- `npm run lint` in frontend: PASS, exit 0.
- `npm run build` in frontend: first restricted run stalled and was stopped;
  a concurrent retry was rejected by the active build lock. After stopping the
  stalled run, the unrestricted retry PASSED, exit 0, compiled/TypeScript checked
  and generated all 13 pages. Existing .env.local was loaded by Next without
  printing its contents.
- `python -m pytest -q` in backend using the repository virtual environment:
  restricted run stalled and was stopped; unrestricted runs passed. Intermediate
  run: 71 passed, 4 PostgreSQL skips. Final PostgreSQL-enabled run: **76 passed,
  0 skipped**, 4 existing dependency/config deprecation warnings, exit 0.
- `docker info`: unavailable; Docker Desktop engine was stopped.
- Local PostgreSQL 18.4 binaries and vector extension were available. Used
  `initdb` to create a brand-new randomly named temp-directory cluster, then
  `pg_ctl start` bound to 127.0.0.1:55439. Created only the disposable
  `cme_phase1_test` database and enabled vector there. Set the explicit
  PHASE1_TEST_DATABASE_URL to this cluster for the final test run. No developer
  DATABASE_URL, existing PostgreSQL database or production service was used.
- Tests ran Alembic upgrade only inside an empty random schema in that new
  disposable database and confirmed the missing-study_logs failure.
- `pg_ctl stop -m fast -w`: PASS. The temporary cluster was stopped, its exact
  temp-directory path verified, and only that newly created cluster directory
  and the temporary workspace path marker were removed.
- `git diff --check`: PASS, exit 0 (rechecked after final documentation).

The added GitHub Actions workflow has backend tests with an ephemeral pgvector
service and frontend npm ci/lint/build jobs, read-only repository permissions,
and no deployment job. The hosted workflow itself has not been executed in
this session; its equivalent local commands passed. Windows instructions are
in backend/tests/README.md.

## Migration findings and remaining bootstrap blocker

Revision chain confirmed from source:

`3d0e118a4fdf -> 9de2f17eda3a -> 305e4c8b7844 -> 86a536d3ece5 -> c08a51cd4965 -> e81f0948c07e -> 903ce59b718d`.

- Initial revision 3d0e118a4fdf does no DDL.
- Next revision 9de2f17eda3a immediately alters study_logs to add notes. No
  revision creates users or study_logs. Empty-schema upgrade was actually run
  against disposable PostgreSQL and failed with `relation "study_logs" does
  not exist`. The initial baseline therefore depends on tables provisioned
  outside Alembic. The legacy app/create_tables.py also exists, but was not run.
- 305e4c8b7844 creates memories with references to users and study_logs.
- 86a536d3ece5 creates Vector(768) before c08a51cd4965 enables vector. This ordering
  is confirmed from source; an empty extension-free database would require vector
  enabled earlier, after the missing baseline tables are addressed. That later
  failure was not reached during the empty-schema runtime check.
- e81f0948c07e creates the HNSW index after enabling vector; 903ce59b718d adds
  tracks and a nullable SET NULL study-log link.
- No revision creates conversations or usage_limits, although current models
  and application code reference them.
- alembic.ini has an empty sqlalchemy.url; env.py uses that option rather than
  loading DATABASE_URL into Alembic configuration. Tests explicitly inject their
  disposable URL. Do not assume app dotenv setup configures migration targets.

Historical migrations are unchanged. Repairing a new head cannot create tables
before the already failing second revision. Reconstructing the historical
baseline, reconciling model-only tables and extension ordering requires a
controlled bootstrap design and compatibility checks for already deployed
revision states. No minimal repair meeting those conditions was demonstrated,
so the exact blocker is documented rather than rewriting history or using
create_all/stamp/reset. A fresh database is **not** currently bootstrap-ready.

## Remaining limitations and discovered regressions

- No production smoke tests or migrations were performed. Persistence and
  vector behavior were verified with synthetic local records only.
- Existing data with missing/stale embeddings is not repaired automatically.
- RAG sources remain retrieval candidates, not a new verified-citation contract;
  no live LLM was evaluated for citation compliance.
- Existing Google generativeai end-of-support, Starlette httpx TestClient and
  Pydantic class-config warnings remain; upgrading those dependencies is outside
  the scoped fixes.
- npm's dependency advisories remain unresolved; no forced upgrades or lockfile
  rewrite were applied.
- Older architecture/progress documents describe earlier project stages; this
  report describes the inspected current implementation.
- No application regression was observed in the executed tests, lint or build.
  Migration bootstrap failure and dependency warnings are confirmed baseline
  limitations, not successful checks.

No Phase 2 features, new agents, frontend redesign, deployment, commit or push
were introduced.
