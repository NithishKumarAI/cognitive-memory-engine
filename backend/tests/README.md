# Backend regression tests

From the repository root in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-test.txt
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q
```

Use an existing virtual environment if present. `requirements-test.txt` is the
small application test runtime; it excludes Torch and SentenceTransformer.
Phase 4 also updates compatible security patches in the production dependency file; real model-runtime compatibility is not established by the mocked test runtime.

The default suite uses a fresh in-memory SQLite database for each test, with
foreign keys enabled. It tests ORM transactions, ownership, authentication,
validation and service contracts. It does **not** validate PostgreSQL vector
storage, cosine search, indexes, or migration compatibility.

Before app imports, conftest disables dotenv and overwrites DATABASE_URL,
SECRET_KEY and GEMINI_API_KEY with test-only values. Dependency overrides route
all application SQL to the fixture. AI entry points fail closed unless mocked;
no SentenceTransformer import/model download or Gemini request is required.

## Real PostgreSQL and pgvector

Create a new disposable local database named `cme_phase1_test` in a separate
test instance. Never use the application's DATABASE_URL or a database containing
real data. Migrations now enable vector themselves; do not pre-provision tables
or stamp revisions. For example, on an available Docker engine:

```powershell
docker run --name cme-phase1-tests --rm -d -p 127.0.0.1:55439:5432 -e POSTGRES_USER=phase1 -e POSTGRES_PASSWORD=phase1-test-only -e POSTGRES_DB=cme_phase1_test pgvector/pgvector:pg16
# Wait until pg_isready reports ready:
docker exec cme-phase1-tests pg_isready -U phase1 -d cme_phase1_test
$env:PHASE1_TEST_DATABASE_URL = 'postgresql+psycopg://phase1:phase1-test-only@127.0.0.1:55439/cme_phase1_test'
..\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:PHASE1_TEST_DATABASE_URL
docker stop cme-phase1-tests
```

Run these commands from `backend/` after the test environment is installed.
The Docker password above is synthetic test configuration.
The fixture refuses non-loopback hosts and any other database name. It creates
random schemas and removes only those schemas. Do not configure this variable
unless the named local database is disposable. Without it, PostgreSQL checks
are explicitly skipped. With it, connection/extension failures fail the tests.

Run only PostgreSQL tests with `python -m pytest -q -m postgres` using the test
virtual environment. CI supplies its own ephemeral pgvector service.

SQLite fixtures create individual current-model tables in new in-memory stores.
PostgreSQL fixtures now bootstrap exclusively through Alembic in fresh random
schemas. Tests require successful bootstrap, preserve synthetic earlier-revision
and Phase 1 head data, verify capture constraints and run concurrent confirmations
and a discard race with independent connections. An additional subprocess verifies
that Alembic needs no application database URL, Gemini key or JWT signing key.

The SDK is exercised with an httpx MockTransport for structured extraction and
inline audio serialization, in addition to mocked service-level tests. No HTTP
request reaches Google, and no microphone hardware is needed. No tests call
create_all, drop_all, stamp, downgrade, or embedding repair scripts.
