# Phase 2 migration repair strategy

Historical revision IDs and their dependency order are preserved.

- `3d0e118a4fdf`: replace the original empty upgrade with explicit users and
  study_logs baseline DDL (before notes and track links existed). Inspect only
  the current schema. If a table already exists, require the expected baseline
  columns and preserve it. Never replace existing tables or data.
- `86a536d3ece5`: enable vector in public before creating Vector(768), in addition
  to the existing later idempotent extension revision.
- `f20100000001` after old head `903ce59b718d`: create missing conversations and
  usage_limits explicitly, or preserve pre-existing tables after checking columns.
- `f20200000002`: add learning_captures and learning_observations, indexes,
  foreign keys, type/status/provenance checks and retry uniqueness constraints.

Applied historical revisions are never replayed by Alembic. An installation at
Phase 1 head therefore executes only the forward revisions. Existing unversioned
baseline tables are also supported by the initial revision's narrow guards.
Partially applied or inconsistent schemas require explicit reconciliation; these
checks do not certify every possible legacy column type or constraint variation.
Do not blindly stamp an unknown schema or apply historical downgrades.
The two new revisions deliberately refuse automatic downgrade because rolling
back tables with capture data or previously manual tables needs a retention review.

Metadata lives in app/db/base.py independently of app database initialization.
Migrations require an explicit programmatic/INI sqlalchemy.url, or a separately
provided ALEMBIC_DATABASE_URL when that option is empty. They do not fall back to
DATABASE_URL, read an application .env file or require application secrets.
Explicit programmatic/INI configuration takes precedence. Migration code never
prints the URL. Online migrations are required for legacy schema inspection;
offline SQL generation for this repair is not supported.

Local-only example from backend/, targeting a NEW disposable test database:

```powershell
$env:ALEMBIC_DATABASE_URL = 'postgresql+psycopg://phase1:phase1-test-only@127.0.0.1:55439/cme_phase1_test'
..\.venv\Scripts\python.exe -m alembic upgrade head
Remove-Item Env:ALEMBIC_DATABASE_URL
```

The PostgreSQL server must have pgvector installed and the migration role must
be permitted to enable it in public. Migrations run only when explicitly invoked;
application startup never creates or migrates tables.

Verification uses disposable PostgreSQL schemas, genuine fresh bootstrap,
earlier revision states, a Phase 1 head with manual conversations/usage rows and
existing memory/vector rows, and a subprocess without application settings.
No production inspection or migration was performed. Before a later production
rollout, review the actual revision/schema state and backup/recovery procedure.
That rollout is not part of this implementation.
