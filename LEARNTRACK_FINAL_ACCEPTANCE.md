# LearnTrack final local acceptance — 29 October 2026

## 1. Starting repository state

Clean `main` at `d4f4efecd77b212f3bef79ba47950ff756c658e3`, with only main locally
and remotely. Baseline GitHub Actions run 40863465228 completed successfully.
The configured Git origin uses the older `semantic-progress-tracker` alias;
GitHub resolves both names to the same repository ID 1250291673. No remote
configuration, existing user changes, product records or production secrets were
overwritten.

## 2. Root causes and verified resolution

The existing frontend env file pointed at the legacy Cloud Run API instead of
localhost:8000. That exact remote backend returned health 200 and OpenAPI title
**Cognitive Memory Engine**, but returned **404** for overview, checkpoints,
recommendations and capture. Learning tracks and `/me` returned expected **401**
without credentials. Its OpenAPI document lacks the missing routes.

Home grouped those missing routes with successful reads; Capture grouped its
missing history route with tracks. Both groups turned a single failure into the
reported generic error. The local frontend URL now points to
`http://127.0.0.1:8000`, with the old env file preserved in an ignored backup.
The existing local backend independently returns health **200**, title LearnTrack,
and declares capture routes. No remote credentials were sent during diagnosis.

Freshly migrated PostgreSQL with a fresh registered account returns **200** for
all seven requested endpoints with AI both on and off. Frontend request failures
are now explicit and independent; input stays usable, and source links load even
if optional listings fail. The missing test-runtime `tzdata` dependency was also
added; the no-tzdata Windows failure was reproduced separately. It was not the
root cause of the missing remote Capture route.

Restart the frontend dev server, or rebuild a production frontend, to replace
the old bundled API origin. An account registered against the old remote API is
not automatically a local account; register separately in the local environment.

## 3. Product changes

LearnTrack naming is consistent in current UI, API and project prose. Repository
paths and authentication/database identifiers remain compatible. Current showcase
screenshots use the verified LearnTrack interface; original evidence is retained.

Home embeds shared text/voice capture, optional path selection, explicit review
and confirmation, manual drafts without provider calls, immediate summary refresh,
simple first-time guidance, source-backed continuity/actions and real activity
counts. The advanced Capture route and observation anchors are preserved.

Settings supports encrypted personal Gemini keys, replacement and removal. Tests
exercise actual authenticated owner selection, ciphertext owner binding, rotation
and absence of a global-key fallback. The forward credential migration does not
rewrite learning records. Original JWT/password compatibility and owner checks
are retained. Database errors return sanitized 503 responses.

## 4. Demo changes

The demo derives from verified product commit
`97b3c66f11a4ccd32b79dd9c96ae2e0ab8b6a63a`. Trusted backend configuration requires
separate demo storage and signing keys. Anonymous visitors get isolated two-hour
sessions with three paths, 15 confirmed updates, 24 observations, 15 study logs
(465 minutes) and three saved memories. Stats and evidence links are computed.

Guided examples are explicitly scripted. Manual capture, source exploration,
keyword search, grounded recall, feedback and reset use the actual engine.
Reset revokes only the caller's old session. Atomic database limits bound new
sessions and mutations across instances. Request bodies are bounded even when
chunked. Expired-session cleanup selects only issued expired guest owners.

All paid-provider calls and anonymous model indexing are server-blocked. Live
Gemini is intentionally unavailable until distributed AI quotas and operational
abuse controls are implemented and verified. This is a release blocker, not a
claim that a scripted response is live AI.

## 5. Branches and review

`main` remains at the starting commit. `codex/learntrack-product-v2` contains the
authenticated product changes for review. `demo` contains the separate guest
edition. Final commit SHAs and push/PR outcomes are reported in the chat; this
file cannot embed its own content-addressed commit SHA. No force push, merge to
main, automatic deployment or Google Cloud deployment is authorized/performed.

## 6. Automated verification

- Product baseline implementation: **219 backend tests passed**, **28 browser
  journeys passed**, **3 frontend release tests passed**. Lint, TypeScript,
  production build and diff validation passed.
- Final authenticated product branch with the additional persistence and
  ciphertext-rotation regressions: **221 passed, 0 failed, 0 skipped**. Its local
  readiness check passes, and its production frontend is rebuilt for the corrected
  local API on port 8000.
- Shared product/demo backend, including real process restart persistence,
  encryption owner binding/rotation, guarded local helper and concurrent demo
  reservations: **234 passed, 0 failed, 0 skipped**.
- Shared branch rebuilt in product mode: all **28 product browser journeys
  passed**; signup/login protection remains enforced.
- Independent demo browser journeys: **2 passed, 0 failed, 0 skipped** in the
  final production run, including direct login/register redirects. An earlier
  run selected a hidden dropdown option instead of the visible path heading;
  the locator was corrected and the complete demo suite rerun successfully.
- Published demo commit `69a7814d5983183975b2fce3f273df3b73a7fb3e` also passed
  [GitHub Actions run 40871303503](https://github.com/NithishKumarAI/cognitive-memory-engine/actions/runs/40871303503).
- Both browser suites cover **390, 768 and 1440 pixels**, light/dark themes,
  evidence navigation and axe accessibility scans. Synthetic screenshots are in
  `test-artifacts/product-v2`, `product-v2-shared` and `demo-v2`.
- All provider calls in product tests are mocked. Demo tests install a provider
  boundary that fails on any attempted call. No paid Gemini or real microphone
  call was made. Actual hardware/HTTPS/provider checks remain unexecuted.
- Three existing Python deprecation warnings remain (Starlette/httpx TestClient
  and two Pydantic model configuration warnings).

Earlier intermediate fixture/locator failures were repaired and the relevant
complete suites rerun. No existing tests were removed or assertions weakened.

## 7. Security status

Fresh npm audit initially found a high Zod advisory; its transitive update leaves
**zero npm advisories**. Cryptography and dnspython were patched and verified.
The full installed Python environment still reports **22 advisory entries in
five packages**, including repeated IDs: filelock, pip, sentence-transformers,
setuptools and torch. Before/after JSON is saved under `test-artifacts/`.

Those model/toolchain risks are not waived. Public release also requires HTTPS,
exact CORS origins, edge rate limits, trusted proxy configuration, monitored
cleanup, backup restoration and operational log review. Existing JWT localStorage
remains an XSS exposure to manage. Unit tests do not establish production security.
No personal API key or operator signing/encryption variable is bundled publicly.

## 8. Gemini configuration

Product: the operator provisions `AI_KEY_ENCRYPTION_KEYS` through protected
server configuration, then each user saves their own key in Settings. Missing
encryption configuration fails closed. The newest configured Fernet key encrypts;
retained old keys decrypt during rotation. Users can replace or delete their
credential. Existing provider calls can finish after replacement/removal.
No owner key substitutes for a missing personal key.

Demo: no owner key is provisioned or read. Capture analysis, audio transcription,
retries and the shared provider all deny live AI in demo mode. Paid AI quotas,
concurrency leases, time windows and failure backoff remain unimplemented; AI
cannot be enabled merely by putting a key in an environment variable.

## 9. Beginner local testing

Product: use [LOCAL_SETUP.md](LOCAL_SETUP.md), a deliberately chosen local
database, matching explicit migration URL, and forward migrations. Start the
backend on port 8000 and frontend on port 3000. Register locally, open Home,
write a synthetic update, choose **Review manually**, add an observation and
**Confirm and save**. Follow its checkpoint/source and reload to verify history.
Configure personal AI only after secure key storage is provisioned.

Demo: switch to `demo`, follow [DEMO_GUIDE.md](DEMO_GUIDE.md), copy only the demo
example to the ignored demo env file, provision separate storage/secrets, then
run the guarded `demo_local.py migrate/check/serve` commands. Build/start its
frontend with server `APP_EDITION=demo` and the demo API origin. Two browser
contexts receive different workspaces; resetting one does not reset the other.

The verified existing local `learntrack_dev` database was backed up and advanced
from `f40100000001` to `f50100000001`, adding only the personal-key table. All six
existing user/learning table counts remained unchanged. The missing local
`ALEMBIC_DATABASE_URL` was set to the same already configured loopback database;
existing credential values were unchanged. Private database and env backups are
kept under ignored `.local-backups/`. The database backup was successfully restored
into a newly created disposable database and all six original counts matched.
That proves this local backup archive, not the future deployment's recovery plan.

No production database was migrated or reset. Other environments still require
reviewed forward migrations and their own backup verification. No real operator
encryption or demo signing secrets were created for you.

## 10. Deployment disposition

**Prepared for review; not an unconditional public-release approval.** Product
main promotion still requires owner approval. Both editions need deployment and
operational verification. Demo live AI remains disabled and has an explicit
release blocker. Resolve/assess remaining advisories, prove backup recovery,
provision separate credentials and test the published origins before public use.
No Cloud Run or other cloud deployment was performed.
