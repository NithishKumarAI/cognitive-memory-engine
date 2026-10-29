# LearnTrack — landing, authentication and clean database readiness

Date: 2026-10-26. Started on clean `main` at `979f8da2ffa476a6d554b1eeccee22b3a5d6a0b1` (`final`). No commit, push, checkout/reset/rebase/merge/stash, release or deployment performed.

## Implemented files

Public presentation:
- `frontend/app/page.tsx`: original animated product story, replacing the public screenshot gallery.
- `frontend/app/landing.css`: scoped typography, responsive scenes, particle motion, themes, focus-compatible interactions and reduced-motion behavior.
- `frontend/components/landing/landing-motion.tsx`: reveal/visibility observers, pause control and listener cleanup.

Authentication:
- `frontend/app/register/page.tsx`, `frontend/app/login/page.tsx`: accessible forms, password controls, loading states, validation, safe errors and account-created recovery.
- `frontend/app/register/layout.tsx`, `frontend/app/login/layout.tsx`: distinct browser titles and shared LearnTrack description.
- `frontend/components/ui/password-input.tsx`: shared labelled visibility control, with `type=button`, preserved input value and forwarded form ref.
- `frontend/lib/auth-feedback.ts`: bounded signup-password validation and explicit safe feedback; raw server details never rendered.
- `frontend/hooks/useAuth.ts`: distinguish saved account from failed automatic login, clear incomplete session, guide to sign in.
- `frontend/services/auth.ts`: whitelist registration/login payload fields and bound auth requests to 15 seconds. Confirmation never leaves the form.
- `backend/app/schemas/user.py`: signup username/email bounds and bcrypt-safe password validation; existing login rules and hash format retained.
- `backend/app/routes/user.py`: sanitized database failures and race-safe uniqueness conflict handling/rollback.
- `backend/app/main.py`: redact rejected input/context from auth validation responses only; other validation behavior preserved.

Setup/documentation:
- `backend/.env.example`: explicit migration target, clear placeholder signing key and AI-disabled first-run example.
- `backend/scripts/check_local.py`: local-only configuration readiness, optional read-only database/head/pgvector checks and redacted output.
- `backend/scripts/migrate_local.py`: normal migration upgrade using the explicit matching local target from configuration. Refuses remote targets; underlying Alembic guard unchanged.
- `LOCAL_SETUP.md`: simple two-file setup, new database guidance, commands, signup check and failure diagnosis.
- `README.md`, `DEMO_GUIDE.md`: current landing/auth behavior and setup links; existing screenshot/history evidence retained.
- `.gitignore`: temporary UI/auth verification state excluded. Both actual environment files remain ignored.

Verification:
- `backend/tests/test_registration.py`: validation/redaction, bcrypt boundaries/legacy compatibility, duplicate identities, service errors and race conflict rollback.
- `backend/tests/test_local_setup.py`: missing/remote/maintenance targets refused; no settings or credentials exposed in readiness output.
- `backend/tests/auth_restart.py`: explicit opt-in empty-database proof with real API requests and account/path persistence across service restarts.
- `backend/tests/test_historical_recall.py`: fixture timestamps given explicit day ordering to remove an observed same-clock-tick ordering failure. No algorithm or assertion was weakened.
- `frontend/e2e/auth.spec.ts`: 11 registration/login browser regressions.
- `frontend/e2e/overview.spec.ts`: 3 updated overview checks plus normal-motion/pause/reveal/backend-independence check.
- `frontend/e2e/journeys.spec.ts`: existing registration journey fills the new confirmation field; remaining journeys retained.
- `test-artifacts/ui-auth/`: new synthetic screenshots, persistence evidence and index.

## Landing page design and interaction

Inspected the live [Robin reference](https://robinpa.in/) in the browser: dark cinematic hero, a moving point cloud, strong typography and transition into a conversational feature scene. Used the interaction/storytelling direction only; no Robin code, branding, images, purple orb or exact identity was copied.

LearnTrack now tells eight chapters: hero → fragmented study context → capture → reviewed interpretation → connected memory → resume checkpoint → honest insights → final account CTA. Original teal SVG knowledge connections and CSS product scenes replace screenshots on `/`. Every illustrative UI scene is labelled; no fake functional AI, microphone button, live score, customer count or mastery percentage is shown. Actual historical screenshots remain in the README/public asset directory and earlier evidence, unchanged.

Hero/navigation provide Get Started, Sign in and Explore links. Light/dark/system appearance reuses the existing control. Public content has no backend dependency, API requests, auth bootstrap or private data. Existing authenticated dashboard styling and navigation remain intact.

Performance bounds: one SVG, 28 decorative points, a few static connections/orbits; no WebGL, canvas loop, animation framework, external font/image request or additional dependency. CSS handles transforms/opacity; IntersectionObserver reveals each story block once and suspends the hero when off-screen. Hidden-tab hero motion pauses; observers/media/visibility listeners disconnect on unmount. User pause applies across decorative animations. Reduced-motion disables animation, transitions and smooth scrolling and leaves all content readable. Layout dimensions stay fixed while animated elements transform. These are implementation bounds and tested behaviors, not a benchmark or guarantee for every low-end device.

Accessibility: semantic headings, visible focus, skip link, labelled forms/buttons and keyboard-accessible controls. The desktop header's redundant accessible-name override was removed after axe correctly found it excluded the visible tagline.

## Signup and login behavior

Signup keeps username, email and password; adds required Confirm Password and independent eye toggles. Confirmation is validated only in the browser and omitted from the explicit API payload. There is no database column or migration for it. All form messages are associated with their inputs. Busy forms disable submission and show progress.

New signup passwords require at least 8 Unicode characters, at most 72 UTF-8 bytes, nonblank content and no null characters. Frontend and backend enforce the same rules; this prevents bcrypt silently truncating newly chosen long passwords. Usernames are trimmed and limited to 3–50 characters, matching the existing column. Emails are validated server-side and capped at the existing 255-character capacity. More detailed email rules remain authoritative on the server.

Bcrypt/passlib settings and stored hashes are unchanged. Existing shorter-password accounts can still log in; new signup rules are not applied retrospectively to login. Legacy HS256 token compatibility and the `cme_access_token` key remain covered by the existing suite. Existing ownership checks, token signing/lifetimes, logout semantics and no-store behavior remain intact.

The form distinguishes offline/network, conflicts, invalid input, registration closure, service/database outage, wrong login and account-created/session-incomplete outcomes. Raw FastAPI details/arrays, rejected passwords, SQL errors and stack traces are not rendered. Auth API validation responses exclude submitted `input` and exception context. Database exceptions on registration/login are rolled back and mapped to a generic 503.

If registration succeeds but automatic login or `/me` verification fails, the UI states that the account **was created**, clears the partial session, removes the create button and offers sign-in. A lost registration response is inherently ambiguous, so the form advises trying sign-in before retrying. Unique indexes/preflight checks and race handling prevent duplicate identities; no mock account success is displayed.

## Registration diagnosis: established facts and limits

At inspection, this repository's Next.js development server was listening on port 3000; no API was listening on the expected local port 8000. The frontend can serve a public page alone, but cannot create a real account without the API and initialized PostgreSQL. This supports the reported frontend-only scenario. It does **not** prove the exact cause of the earlier failed attempt: no original network trace was supplied, and existing private environment values/production services were not inspected or contacted.

Confirmed source gaps were unsafe rendering of arbitrary server `detail`, no useful network diagnosis, missing backend signup bounds, and treating post-registration login failure as failed account creation. Those are corrected. Password hashing works with the pinned bcrypt/passlib dependencies and the unchanged scheme in both the suite and real disposable PostgreSQL requests; no hashing-library replacement was needed.

A browser network error cannot identify whether the underlying cause is an offline API, wrong URL or CORS. The UI gives the requested useful message; the setup guide walks through API origin, CORS, database reachability, migrations, registration switch and signing/provider configuration. It makes no claim that the user's existing private settings were verified.

## Clean database and preservation proof

A brand-new temporary PostgreSQL 18 cluster was initialized on `127.0.0.1:55439`. The normal integration/browser tests used explicitly disposable `cme_phase1_test` schemas. A separate, actually empty `learntrack_ui_auth_test_retry` database was verified to have no tables before the normal migration helper ran.

- Existing migrations initialized the schema and pgvector and reached **`f40100000001`**, with zero accounts and learning tracks before the test flow.
- Real Uvicorn API process: register two synthetic accounts → bcrypt hash → login → `/me` → create a learning track (existing **201 Created** contract) → retry duplicate signup → verify owner isolation.
- API stopped. The exact disposable PostgreSQL instance was stopped and restarted. A new API process successfully logged in to the same accounts and loaded the original track.
- After restart: exactly **2 synthetic accounts and 1 track**, duplicate retry rejected; the second account could not access the first account's profile or tracks.
- Evidence: `test-artifacts/ui-auth/database-readiness.json`.

The first standalone proof attempt used an incorrect test expectation of HTTP 200 for track creation; the endpoint correctly returned 201. The harness was corrected and rerun against another new empty disposable database, without resetting the earlier one.

No SQLAlchemy models, database schema definitions or migration files were changed. No existing personal/development/production database was opened, erased, reset or seeded. No `create_all`, `drop_all`, stamp, destructive migration shortcut, Neon access or Cloud Run connection was used. Existing test fixture schema cleanup remains confined to disposable test stores. All real user records remain untouched.

## Configuration the user edits

Only `backend/.env` and `frontend/.env.local`, both gitignored (verified with `git check-ignore`). No real key/password was generated or written to those files.

Backend: development `DATABASE_URL`; explicit matching `ALEMBIC_DATABASE_URL`; stable strong `SECRET_KEY`; optional `GEMINI_API_KEY`/`GEMINI_MODEL`; exact `FRONTEND_ORIGINS`; `REGISTRATION_ENABLED`; `AI_ENABLED`. Frontend: browser-reachable `NEXT_PUBLIC_API_URL` only. See [LOCAL_SETUP.md](LOCAL_SETUP.md) for meanings and placeholder-only examples. Environment-file edits require API restart/frontend restart or rebuild.

The local helpers read only the explicitly named local target and refuse remote/maintenance database URLs. They do not change Alembic's existing no-fallback policy. Configuration-only readiness does not claim database connectivity; `--database` does the actual read-only check. It never checks a production URL or calls Gemini.

## Verification results

- Backend: **212 passed**, including all PostgreSQL integration checks and 20 added registration/local-setup checks; 3 existing Pydantic/Starlette deprecation warnings.
- `npm ci`: passed with unchanged package/lockfiles after stopping this repository's identified dev processes holding a Windows native CSS binary. npm reported one high-severity vulnerability; no unrelated audit fix applied.
- `npm run test:release`: **3 passed**.
- Final frontend lint/build: passed; landing remains statically generated.
- Final full Playwright run: **26 passed (1.9 minutes)** — all 11 existing workspace journeys, 11 new auth tests, 3 updated responsive public checks and 1 normal-motion check.
- Public page at **390/768/1440**, light/dark: no screenshot gallery, working auth links, correct metadata/icon, zero public API requests, no horizontal overflow and no axe WCAG 2 A/AA or 2.1 A/AA violations (6 combinations). Auth forms at all three widths also passed axe and overflow checks.
- Normal-motion test: point animation present, user pause/resume works, reveal markers activate, off-screen hero pauses and a runtime switch to reduced motion disables animation. Existing workspace visual/accessibility and all nav/capture/history/isolation journeys passed.
- Successful registration/browser flow: no unexpected console errors or page errors. Deliberate network/error cases display their explicit messages; browser network diagnostics in those intentionally failed requests are expected.
- **Actual API stopped** standalone check on a temporary frontend-only server: public hero loaded with zero API requests/page errors; signup showed the required connection guidance instead of reporting success. Evidence: `test-artifacts/ui-auth/backend-stopped.json`.
- `git diff --check`: passed after removing whitespace-only blank-line indentation. New text files also checked for trailing whitespace.
- **38 new synthetic screenshots** retained under `test-artifacts/ui-auth/screenshots/`: 24 authenticated workspace, 6 overview/theme/width, 6 signup/login/width, 1 hero viewport and 1 actual-backend-stopped form. Earlier screenshots/assets remain intact.
- Visually inspected the new overview at 390 and 768 light and 1440 dark, the 1440 hero, mobile signup and tablet login; also manually inspected the live dark hero/form in the browser.
- Cleanup completed: the task-created PostgreSQL instance and scratch files removed; no listeners remain on 3100/8100/8117/3117/55439. No real application configuration or database was changed.

The backend fixture timestamp failure was resolved with explicit ages only. Early browser runs corrected test locator/whitespace/viewport assumptions, then found and fixed the real desktop label issue. The final results below supersede those incomplete runs; failures are not hidden as successful tests.

Manual browser interaction in the isolated environment confirmed the implemented hero, Explore transition, signup navigation, visible password-mismatch feedback, corrected submission, a loading state and navigation to the real authenticated Home. No AI request was made. Screenshot inspection at 390/768/1440 and the final browser accessibility results are recorded below.

## Very simple manual test

1. Follow [LOCAL_SETUP.md](LOCAL_SETUP.md). Create a **separate new database**, keep any existing database, and fill the two environment files with your own local settings.
2. Keep `AI_ENABLED=false` initially. Run the configuration check, normal migration helper and database check. Stop if a command fails.
3. Start the backend terminal. Open `http://127.0.0.1:8000/health`; expect healthy/connected.
4. In another terminal start the frontend (`npm run dev` in `frontend`). Open `http://localhost:3000`.
5. Explore the public story, switch appearance and pause/resume motion. Stop the backend briefly: the public page should still work, while submitting signup should show the connection guidance. Start the backend again.
6. Choose Get Started. Use synthetic details. Enter a different confirmation once and verify the mismatch. Check both eye controls, then enter matching valid passwords and submit once.
7. Confirm Home opens. Create a learning path. Sign out and sign in. Stop/restart the API and frontend and confirm the path remains.
8. Repeat signup with the same identity: expect a conflict, not another account. Use another synthetic account to check that the first account's records stay private.
9. Only with your own key, explicit consent and cost controls, enable optional Gemini/voice/capture checks from the demo guide. Automated mocks do not establish live model or microphone acceptance.

This pass verifies normal migrations and API startup with the existing Python 3.12 environment; a full fresh install of heavyweight model dependencies and real downloads was not repeated. Physical hardware, arbitrary browser/device performance and live provider acceptance remain separate.

## Release status

**Current V1 deployment pending verification.** No public-production readiness claim. Remaining gates include Docker/image validation, exact deployed revision/HTTPS, dependency advisories, live Gemini/embedding model/microphone checks, session/CSP review, distributed limits, enforced quotas/provider cost controls and production privacy/backup/deletion/monitoring choices. Existing JWT/localStorage risks and non-revoking logout remain documented.

Temporary verification services and stores were stopped and removed after verification. The old local frontend process was stopped for `npm ci`; use the setup guide to start both actual services. No real backend/database configuration was modified to pretend setup had succeeded.
