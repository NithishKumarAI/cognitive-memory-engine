# LearnTrack branding and portfolio polish

Date: 2026-10-26. Starting point: clean `main` at `0cb72812d8a841f07bfb1eb99cf5e1cca6dd3ec7`.

## Changes

- `frontend/lib/branding.ts`: LearnTrack, consistent subtitle and core promise; existing root metadata consumes the shared branding.
- `frontend/app/login/page.tsx`, `frontend/app/register/page.tsx`, `frontend/components/dashboard/sidebar.tsx`: shared name/subtitle. Existing login, redirect, storage and session logic retained.
- `backend/app/main.py`: API title, description and root display message only. API paths, version and response contracts otherwise retained.
- `frontend/app/icon.svg`: simple teal book/check vector app icon, replacing the default `frontend/app/favicon.ico`.
- `frontend/app/page.tsx`: public static overview in the existing off-white/teal design, with text/consented voice capture, review, confirmed evidence, optional memory, checkpoints, grounded recommendations and honest analytics. Uses existing buttons/theme control and responsive semantic sections. Sign in/register lead to existing routes. No public API/AI demo or account data fetch.
- `frontend/public/showcase/{home,recommendations,analytics}.png` and `README.md`: inspected, byte-identical copies of existing synthetic screenshots and provenance notes. Earlier visible branding is explicitly disclosed.
- Root `README.md`: professional showcase, three selected real screenshots, workflow, stack/architecture, Windows setup, explicit migration URL, isolated verification, truthful live status, privacy and project history.
- `frontend/README.md`: frontend title updated.
- `DEMO_GUIDE.md`: synthetic local walkthrough, expected human review, checkpoints/source links, optional provider/voice/memory checks, limitations and suggested recording sequence. No video claimed or shared account introduced.
- `PORTFOLIO_COPY.md`: factual project card, resume description, proposed repository description and manual About/homepage guidance.
- `frontend/e2e/overview.spec.ts`: public page checks at 390/768/1440, light/dark, metadata/icon, image loading, overflow, WCAG checks, API-request absence and actual auth navigation.

No database schema/migration, auth implementation, browser storage key, internal database/environment name, AI/retrieval/recommendation algorithm or dependency/lockfile changes. Historical reports, screenshots and releases are preserved. No trademark/domain ownership claim; name uniqueness remains unconfirmed.

## Manual setup verification

Used a newly initialized temporary PostgreSQL 18 instance on loopback port 55439 with installed pgvector. No configured application or production database was used. A separate empty `cme_portfolio_dev` database verified:

1. `CREATE EXTENSION IF NOT EXISTS vector` with an authorized disposable role.
2. Explicit `DATABASE_URL` and `ALEMBIC_DATABASE_URL`, followed by `python -m alembic upgrade head` and `alembic current`: reached `f40100000001 (head)` with existing migrations.
3. Actual `python -m uvicorn app.main:app --host 127.0.0.1 --port 8117` startup with synthetic configuration and `AI_ENABLED=false`.
4. Database-aware `/health`, root LearnTrack message, `/docs` and OpenAPI name/subtitle returned successfully. Server stopped afterwards.

README instructions use the same commands with the user's dedicated development role/port. The existing Python 3.12 virtual environment was used; a new environment/full model installation and download were not repeated. Frontend installation/build/start is exercised below. No live Gemini, embedding model download or physical microphone was used. Windows restricted execution initially stalled npm/initdb; only this task's processes were stopped and the checks restarted outside that sandbox.

## Verification results

- Full backend suite with disposable PostgreSQL/pgvector: **192 passed**, no skipped PostgreSQL checks; three existing Pydantic/Starlette deprecation warnings.
- `npm ci`: passed from unchanged lockfile. npm reported one high-severity vulnerability; no automatic dependency fix was applied in this presentation task. Historical dependency dispositions remain in the V1 reports, not a fresh Python security audit.
- `npm run test:release`: **3 passed**.
- `npm run lint`: passed.
- `npm run build`: passed; `/` and `/icon.svg` are statically generated.
- Full Playwright suite: **14 passed (1.5 minutes)**: all 11 existing journeys plus 3 new public tests. Existing account isolation, capture/review/confirmation, persisted feedback, session handling, mobile navigation, historical recall with/without memory, and voice shortcut checks passed.
- Public overview at **390, 768 and 1440px**, in light/dark appearance: loaded all three screenshots, no horizontal overflow, no WCAG 2 A/AA or 2.1 A/AA violations reported by axe (6 combinations); verified title, subtitle metadata, SVG icon and sign-in/register destinations. **Zero API requests** during public overview inspection. Existing workspace visual/accessibility coverage also passed.
- Visually inspected the new mobile and desktop light overview captures; read-only screenshot links expose full-size synthetic examples on small screens.
- `git diff --check`: passed. New text files checked for trailing whitespace; public screenshot copies verified byte-identical to the approved historical sources.
- Final scope review: changes confined to branding, public overview/assets, documentation and browser verification/evidence. No migration/auth/AI algorithm changes.
- Temporary database instance stopped and both task-created temporary directories removed. Scratch markers/logs removed; no listeners remain on 3100, 8100, 8117 or 55439.

## Screenshot evidence

Public/README assets remain unchanged copies of `test-artifacts/final-acceptance/screenshots/*-light-1440.png`:

- `frontend/public/showcase/home.png` SHA-256 `fe985134f91d3310a77936e6cada40b5a1123cd017410a898c91c0543d8f774d`
- `frontend/public/showcase/recommendations.png` SHA-256 `612527086096c0ebb7c985b4e9d87563db71cada4baf6081067e433b1e1cd182`
- `frontend/public/showcase/analytics.png` SHA-256 `fc2d77e04837c849ce0e92049d2e573ddfd8a6cf6676694a598287da6c165489`

**30 new synthetic screenshots** (24 existing workspace views plus 6 public light/dark/viewport views) are saved separately under `test-artifacts/learntrack/screenshots/`, preserving earlier phase, hardening and acceptance evidence. New test screenshots are evidence of this implementation, not substituted for the approved historical images on the public overview.

## Live status and manual GitHub actions

**Current V1 deployment pending verification.** The historical Cloud homepage and older release do not prove this revision is deployed. No new live URL is invented. Source, selected screenshots and local walkthrough are linked in the README and portfolio copy.

The owner may manually update GitHub About with the proposed description and remove/qualify the historical homepage. Add a website only after deploying and verifying the exact desired revision through the existing release gates. No repository settings, name or release were changed. The README badge points to the existing Product verification workflow's current main status; these local uncommitted edits have not run remotely.

Remaining gates: exact deployed-revision/HTTPS and Docker image verification, authorized real Gemini/model and microphone acceptance, documented dependency advisories, session/CSP review, distributed request limits, quota/provider spending controls and production privacy/backup/deletion/monitoring choices. Existing kill switches do not supply quotas or token revocation. This pass does not establish a public-release go decision.

No commit, push, release creation/replacement or deployment performed.
