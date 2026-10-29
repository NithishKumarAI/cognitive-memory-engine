# Product V2 additions

If Home/Capture shows a generic load error while local health is healthy, check
`frontend/.env.local` first: this checkout previously pointed at a legacy Cloud
Run backend with missing capture/continuity routes. For local development use
`NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`, then restart the frontend (or rebuild a
production frontend). The previous file is retained locally as the ignored
`.env.local.before-learntrack-v2`. Register separately in the local database if
your earlier registration reached that remote API.

The product name is **LearnTrack**. Repository paths and existing database/session
identifiers retain their original spelling for compatibility.

Use a separate local development database. Set both `DATABASE_URL` and
`ALEMBIC_DATABASE_URL` to that exact database; neither helper guesses a migration
target. Back up an existing database before applying forward migrations.

1. Install `backend/requirements-test.txt` for the small test/API runtime, or
   `backend/requirements.txt` when local embedding features are needed. Both
   include Windows timezone data.
2. Keep `APP_EDITION=product`. Start with `AI_ENABLED=false`; Home capture works
   through **Review manually → Add observation → Confirm and save**.
3. Run the migration and readiness commands below, then start backend and frontend.
4. For personal Gemini keys, configure `AI_KEY_ENCRYPTION_KEYS` through your
   server's secret manager using a valid Fernet encryption key. Do not paste that
   operator key into the browser or commit it. Restart the backend after changing
   server configuration, set `AI_ENABLED=true`, and add a personal Gemini key at
   **Settings → AI Configuration**. Saving a key makes no paid validation call.
5. For encryption-key rotation, put the new key first in the comma-separated
   list, retain old keys until users replace/re-save their credentials, then
   retire old keys only after backup and migration review. Removing the only
   decrypting key makes existing credentials unusable. Backups need protected
   access to both encrypted records and their corresponding encryption keys.

No global Gemini key is used in product V2. Existing saved learning survives the
forward migration. Already running provider calls may finish after key removal.

---

# Run LearnTrack locally

The public homepage works with only the frontend. Creating an account needs **the backend and PostgreSQL too**. No Python source changes are required. Configure only `backend/.env` and `frontend/.env.local`; never commit either file.

## 1. Install the tools once

Use Python 3.12, Node 24 and PostgreSQL with the pgvector extension installed on the server. From PowerShell in `C:\My PC\git\cognitive-memory-engine`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
if (-not (Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
if (-not (Test-Path frontend/.env.local)) { Copy-Item frontend/.env.example frontend/.env.local }
```

Skip virtual-environment creation if your Python 3.12 `.venv` already exists. These copy commands preserve existing configuration. Do not replace an existing `.env` just to start fresh.

## 2. Create a separate development database

In your local PostgreSQL admin tool, create a **new, empty database** owned by a development role. The examples use role/database `cme_dev`; use that name only if it is new. If it already exists, choose another unused database name and update **both URLs** below. Do not delete, reset or reuse an existing database to make it empty.

An authorized local administrator must enable pgvector **inside the new database** (replace connection options for your installation):

```powershell
psql -h 127.0.0.1 -p 5432 -U your-local-admin-role -d cme_dev -c 'CREATE EXTENSION IF NOT EXISTS vector;'
```

If `vector` is unavailable, install pgvector for your PostgreSQL version first. Grant the development role the privileges needed to own/migrate its dedicated database. Nothing here needs Neon, Cloud Run or production credentials.

## 3. Edit the two environment files

In `backend/.env`, use your own local values. The following are **placeholders**, not usable credentials:

```dotenv
DATABASE_URL=postgresql+psycopg://cme_dev:replace-me@127.0.0.1:5432/cme_dev
ALEMBIC_DATABASE_URL=postgresql+psycopg://cme_dev:replace-me@127.0.0.1:5432/cme_dev
SECRET_KEY=replace-with-your-own-random-secret-at-least-32-characters
GEMINI_API_KEY=replace-with-your-key
GEMINI_MODEL=gemini-2.5-flash
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
REGISTRATION_ENABLED=true
AI_ENABLED=false
```

- `DATABASE_URL` is the application's dedicated development database. URL-encode special characters in your database password.
- `ALEMBIC_DATABASE_URL` is the **explicit migration target**. For this local setup, make it exactly the same as `DATABASE_URL`. It is not inferred automatically. The local migration helper reads this explicit setting from `backend/.env`; the underlying Alembic environment is unchanged.
- `SECRET_KEY` signs existing-style login tokens. Supply your own random value with at least 32 characters. Keep it stable for existing local sessions; do not put it in browser configuration.
- `GEMINI_API_KEY` is needed only when enabling real cloud AI. Keep AI off for the initial account/setup check. The example contains no real key.
- `GEMINI_MODEL` names the configured Gemini model for optional authorized AI use.
- `FRONTEND_ORIGINS` lists exact browser origins allowed by CORS. Use the origin where you open the frontend, including its port.
- `REGISTRATION_ENABLED=true` permits account creation. False deliberately closes signup.
- `AI_ENABLED=false` disables Gemini operations. Signup, login and learning paths still work. Enable AI only with your own key, consent and cost controls; this switch does not disable local embeddings/downloads or provide usage quotas.

In `frontend/.env.local`:

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

That is the backend origin reachable by your browser, not the frontend URL. It is public and embedded at build time. Restart the frontend after changing it; rebuild production-mode frontend bundles. Never put keys or database URLs in `NEXT_PUBLIC_*` variables.

## 4. Check configuration and initialize the new database

In PowerShell at the repository root:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe scripts/check_local.py
if ($LASTEXITCODE -ne 0) { throw 'Fix the named configuration entries first.' }
..\.venv\Scripts\python.exe scripts/migrate_local.py
if ($LASTEXITCODE -ne 0) { throw 'Migration did not finish. Check the local database and pgvector.' }
..\.venv\Scripts\python.exe scripts/check_local.py --database
if ($LASTEXITCODE -ne 0) { throw 'Database is not ready yet.' }
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Both helpers refuse remote database targets. They hide settings/SQL errors and never call an AI provider. The readiness database check is read-only: connectivity, pgvector, `users` table and current Alembic head. It does not create accounts or claim the frontend is configured. The migration helper runs only normal `upgrade head`; no reset, create-all or stamping. An empty database should reach `f40100000001` using the existing migrations. Use the underlying Alembic command only with an explicitly configured migration URL; these local helpers are not deployment tools.

Open `http://127.0.0.1:8000/health`. It must say `healthy` and `connected`. If it does not, stop and fix the backend/database; frontend startup alone cannot fix registration.

## 5. Start the frontend in a second terminal

From the repository root:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Open `http://localhost:3000`. Keep both terminals running. Stop an existing dev server with Ctrl+C before `npm ci` if Windows reports a locked native CSS file. For a local production-mode build, explicitly set `$env:ALLOW_LOCAL_API_ORIGIN='1'` before `npm run build`, then `npm start`; do not use this loopback opt-in in a hosted release.

## 6. Try the account flow

1. Visit the public homepage. Explore the story and pause animation if desired. It should still work with the backend stopped.
2. Start the backend again, then choose **Get Started**.
3. Use a synthetic username, example.com email and a unique test password. Enter it again in **Confirm Password**. Use either eye button to check it; eye buttons never submit.
4. Use at least 8 characters and no more than 72 UTF-8 bytes. Some symbols use several bytes. The same signup rules are checked on the server. Existing bcrypt hashes and login credentials are not migrated.
5. Choose **Create account** once. Successful registration, login and `/me` verification open Home.
6. Add a learning path, sign out and sign in again. Stop/restart the services and confirm that the path is still there. Persistence depends on keeping the same database and signing key; stopping a service does not erase it.

For extraction, voice, checkpoints and grounded answers, follow [DEMO_GUIDE.md](DEMO_GUIDE.md) with your own authorized AI setup. Those operations are intentionally unavailable with Gemini disabled.

## If account creation fails

- **Unable to connect to the LearnTrack server:** start/check the backend, API URL and matching CORS origin. Browser network errors cannot reliably distinguish an offline backend from blocked CORS; the message is useful guidance, not a definitive diagnosis.
- **Email already registered / username already taken:** sign in or choose a different identity. Retry does not create another account.
- **Invalid form values:** fix the marked fields. Password confirmation stays in the browser and is never sent or stored.
- **Registration temporarily disabled:** check `REGISTRATION_ENABLED` in your local backend configuration and restart the API.
- **Database or service unavailable:** run the local readiness check with `--database`; confirm PostgreSQL, pgvector and migrations. Private connection details are not shown in the form.
- **Account created but automatic sign-in did not finish:** use the provided sign-in link. Your account already exists; do not keep creating accounts.
- A lost response may occur after the account was saved. Try signing in before retrying. Database uniqueness checks prevent duplicate identities.

Current V1 deployment pending verification. This local setup does not complete Docker, security, live AI, HTTPS or production operating acceptance.
