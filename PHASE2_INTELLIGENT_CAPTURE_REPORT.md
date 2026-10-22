# Phase 2 intelligent learning capture report

Date: 2026-10-22 (Asia/Calcutta).
Starting branch: main.
Starting HEAD: 9a18f3e6038e2260c598980b0455c2cb26d82f0a (matches expected Phase 1).
Starting working tree: clean.

## Implementation status

Implemented natural-language text capture, reviewable structured extraction,
editable voice transcription, confirmed observations and optional searchable
memories. Existing entities, authentication, RAG response shapes, embedding
contract and dashboard design remain in use. No Phase 3/4 features were added.

Final backend result: **128 passed, 0 failed, 0 skipped**, including 15 real
PostgreSQL integration cases and 113 isolated unit/HTTP/service cases. Frontend
npm ci, lint and production build passed. No live Gemini calls or real microphone
hardware were used for automated verification. No production resources were
accessed, and no commit, push or Git history operation was performed.

## 1. Migration repair and compatibility strategy

The migration gate was verified before adding capture entities: nine PostgreSQL
cases passed, including fresh bootstrap and synthetic Phase 1 head preservation.
The first bootstrap used a newly initialized database without vector pre-enabled.

Historical revision IDs and their dependency order remain intact:

- 3d0e118a4fdf now explicitly creates the original users/study_logs baseline,
  before notes and learning-track links are introduced. Narrow current-schema
  inspection preserves pre-existing baseline tables and requires expected columns.
- 86a536d3ece5 enables vector in public before creating Vector(768). The later
  existing extension revision remains idempotent.
- f20100000001 follows old head 903ce59b718d. It represents conversations and
  usage_limits with explicit DDL, preserving existing tables after column checks.
- f20200000002 adds capture and observation tables with explicit DDL.

Alembic never replays revisions already applied to an existing database. A Phase 1
head therefore receives only the new forward revisions. Tests cover initial,
intermediate and previous-head states, an unversioned synthetic legacy baseline,
and old head with manually provisioned conversations/usage rows and memory/vector
rows. Existing values survive upgrades. No create_all, drop_all, stamp, database
reset or destructive upgrade DDL was used.

Migrations now use model metadata independently of runtime engine configuration.
An explicit programmatic/INI sqlalchemy.url takes precedence; when absent,
ALEMBIC_DATABASE_URL is required. DATABASE_URL and application .env files are not
migration fallbacks. A subprocess bootstraps successfully with application DB,
Gemini and signing settings removed. URL values are not printed by migration code.

See backend/alembic/BOOTSTRAP_REPAIR.md for the reviewed strategy. Online schema
inspection is required; this repair does not support offline SQL generation.
The role must be allowed to enable pgvector in public. Existing column checks do
not certify arbitrary legacy type/constraint drift. Production rollout still
requires an explicit review of the actual deployed schema/revision and recovery
procedure. New revisions refuse automatic downgrade to avoid silently deleting
capture data or previously manual tables. No production migration was run.

## 2. Persistent entities

LearningCapture stores owner, text/voice source, original submitted text, proposed
and confirmed interpretation JSON, status, optimistic version, model/extraction
version, confirmation digest, timestamps, and nullable study-log/track links.
Status is pending, failed, confirmed or discarded. The original input is immutable
through these routes. Voice provenance denotes a transcript reviewed/edited by
the user; it does not imply that raw audio was retained or independently verified.

LearningObservation stores owner/capture, position, a small observation type,
topic, content, source excerpt, user_confirmed provenance, optional memory ID and
creation time. The five types are learned, understood_self_report, difficulty,
open_question and intended_next_step. No mastery state or confidence score exists.

A composite FK ties observation owner to capture owner. FKs protect capture,
user, track, study-log and memory links; nullable links use SET NULL. Owner-scoped
application queries validate existing track selection before persistence and again
after preparation. Unique capture/position and memory links prevent duplicate
observations/attachments; existing MemoryEmbedding.memory_id uniqueness remains.
Type/status/version/provenance checks and owner/capture indexes are explicit in
both models and migration DDL. Complete transcripts live once on the capture;
observations/memories contain individual statements and short evidence excerpts.

## 3. Authenticated API routes

- POST /capture/analyze: text, source_type, optional owned learning_track_id;
  commits recoverable raw input, then attempts analysis outside a DB transaction.
- GET /capture: returns the owner's latest 20 captures, including drafts/failures.
- GET /capture/{capture_id}: owner-only original, proposal, confirmed result,
  links, observations and possible owned-track matches.
- POST /capture/{capture_id}/analyze: version-checked retry of the original input.
- POST /capture/{capture_id}/confirm: user-corrected interpretation, expected_version,
  optional selected track, and explicit create_memories choice.
- POST /capture/{capture_id}/discard: version-checked soft discard of an unconfirmed
  draft. Original text remains in the account; no automatic purge is introduced.
- POST /capture/transcribe: bounded raw WAV/MP3 body, correct audio Content-Type
  and X-Audio-Consent: true. Returns transcript only; creates no learning records.

All require authentication. Another user's capture returns the same 404 as an
unknown capture. LLM output contains no user IDs, authorized record IDs or write
instructions. No new admin capability or arbitrary model-driven DB write exists.

## 4. Structured extraction and correction

Pydantic Interpretation contains optional subject, deduplicated topics, typed
observations with exact evidence excerpts, optional positive integer minutes,
optional duration evidence and an ambiguity explanation. Extra fields are rejected.
Request/output sizes and observation/topic counts are bounded. Topic matching
normalizes case and spacing and searches only the signed-in user's tracks. No
tracks are automatically created or assigned; ambiguous matches require selection.

A separate system instruction treats submitted notes as untrusted data. It asks
for supported facts, distinguishes self-reported understanding from mastery,
handles multiple topics, questions, intentions and vague input, and forbids
invented accomplishments, progress, dates, duration and numeric confidence.
Output is validated locally. Extraction evidence must occur in the original text.
A proposed duration must have an exact original excerpt with a matching explicit
whole-number minute/hour quantity; otherwise analysis fails safely. Spelled or
fractional times may need manual correction rather than invented conversion.

The UI exposes editable subject/topics, per-observation type/topic/content,
optional minutes, source excerpts and uncertainty. Users can remove/add observations
or enter an interpretation manually after failure. Confirmation persists the
submitted corrections, independently of the older proposed JSON. Original and
proposed input remain available for provenance. A failed/unprocessed capture is
explicitly labeled as not understood by AI.

No study log is created without positive minutes supplied or confirmed by the
user. A log also needs a subject/topic. Question-only, intention-only, ambiguous
and unknown-duration captures remain valid without fabricated study sessions.

## 5. Confirmation, retries and transaction guarantees

Confirmation prepares all required vectors through Phase 1 validated_embedding
before taking a database row lock. A small stage_memory helper reuses memory and
embedding persistence without owning a commit; existing public memory CRUD still
owns its atomic commit/rollback. The 768-dimensional BGE contract is preserved.

After preparation, confirmation locks/reloads the owner-scoped capture, checks
version/status, revalidates the chosen track, and writes observations, optional
StudyLog and optional Memory/MemoryEmbedding pairs in one transaction. A canonical
confirmation digest makes identical retries return existing records. Different
payloads cannot overwrite a previously confirmed capture. Database constraints
provide additional duplicate protection. Flush/commit/vector failures roll back
the complete confirmation and leave the original draft retryable.

Independent PostgreSQL connection tests show simultaneous identical confirmations
create exactly one observation/memory/vector/study-log set. Discard during vector
preparation wins safely and prevents subsequent writes. Discard and confirm use
the same capture row lock. Analysis completes with a conditional version/status
update, so stale provider responses cannot overwrite confirmed/discarded state.
No transaction remains open while extraction or transcription calls Gemini.
RAG now snapshots sources and releases its retrieval transaction before generation.

## 6. Supported Gemini SDK and RAG compatibility

Replaced google-generativeai 0.8.6 with google-genai 2.32.0. Central LLMService
creates/closes supported clients per request and applies a 30,000 ms timeout and
one attempt. GEMINI_MODEL defaults to the existing gemini-2.5-flash;
GEMINI_TIMEOUT_MS is configurable. GEMINI_API_KEY remains the required application key; Vertex AI and ambient
credential fallback are disabled for this integration.
No unnecessary model upgrade was introduced. Exceptions become generic retryable
provider errors, not raw provider messages or prompt logs.

RAG retains its existing generate_response facade, endpoint, answer/source shape,
real memory IDs and no-results behavior. Its route sanitizes provider failures.
All existing RAG tests remain, with the DB stub extended to verify transaction
release. New tests pass actual SDK structured-output and audio request construction
through httpx.MockTransport; no network reaches Google.

That deeper test caught the SDK's rejection of exclusiveMinimum. Integer duration
validation now uses the equivalent minimum: 1, preserving positivity while fitting
the SDK schema converter. Both extraction and audio serialization pass.

Official API references checked during implementation:
[Google GenAI Python SDK](https://googleapis.github.io/python-genai/) and
[Gemini inline audio input](https://ai.google.dev/gemini-api/docs/generate-content/audio).
Implementation uses documented models.generate_content, GenerateContentConfig
with Pydantic response_schema, and Part.from_bytes for bounded inline audio.

## 7. Voice behavior and cloud disclosure

Start Recording explicitly requests microphone access. Stop and Cancel, active
recording/processing indicators, denied/unsupported microphone feedback and a
text-only fallback are provided. Recordings stop after approximately 119 seconds,
below the 120-second limit. Browser recordings and uploaded WAV/MP3 are decoded
locally and converted to mono 16 kHz PCM WAV. The user can listen locally, consent,
then click Send audio for transcription. Transcription is editable before analysis.
Recording tracks/timers/blob previews are cleaned up on cancel/unmount; generation
checks ignore stale async results. No wake word, voice response or voice agent exists.

Backend accepts PCM WAV and MP3 up to 4 MiB / 120 seconds. Upload buffering is bounded.
It checks file signatures, parses WAV frame data or MP3 metadata, and rejects empty,
spoofed, truncated, oversized, overlong and unsupported uploads. Client MIME alone
is not trusted. MP3 validation uses mutagen; WAV validation uses the standard library.
No shared filenames, local audio files or provider-hosted Files API uploads are used.

Audio is sent inline only after explicit consent. The app does not persist raw
audio. Google still processes the audio/text under its applicable service terms;
inline input does not promise zero provider retention. Cancel after sending cannot
retract provider processing already started. The app does not log transcripts,
raw audio, prompts, keys or provider exception bodies. Avoid enabling SDK wire/debug
logging for private traffic. This phase adds no provider-side deletion or retention
policy control. Discarding a draft retains text rather than erasing account data.

## 8. Frontend implementation

/dashboard/capture uses the existing UI components/Tailwind design and adds:

- capture-interface.tsx: text/editable transcript, track selection, analysis preview,
  corrections, retry/discard/reload, explicit confirmation and optional memories.
- voice-input.tsx: recording, local conversion/preview, upload validation and consent.
- services/capture.ts and types/capture.ts: typed API boundary.
- A sidebar entry and a dashboard link visible on small screens.

Accessible native labels, selects, keyboard buttons, status/alert regions, responsive
layout, disabled/loading states, empty/failure states and saved-record links are
included. The capture ID is placed in the URL; recent owned captures support later
inspection/retry. Success reports actual saved observation/memory counts and whether
a study log was created. The rest of the dashboard, chat and design system are intact.

## 9. Verification results and dependency changes

Executed using repository Python 3.12.10, PostgreSQL 18.4 with locally installed
pgvector, Node 24.15.0 and npm 11.12.1:

- Baseline git status/branch/HEAD and source/call-site inspection: complete.
- Local temporary initdb / pg_ctl cluster on 127.0.0.1:55439, followed by creation
  of only cme_phase1_test: successful. No extension was manually enabled before
  the first migration gate. Each integration case used its own random schema.
- Initial migration gate: 9 passed before capture tables were introduced.
- Final `python -m pytest -q` in backend with PHASE1_TEST_DATABASE_URL pointing to
  that temporary cluster: **128 passed, 0 failed, 0 skipped**, 3 existing warnings,
  exit 0. Includes all retained Phase 1 regressions (bootstrap failure expectation
  intentionally replaced by a successful-bootstrap requirement).
- `npm ci`: passed, 418 packages, existing package-lock.json unchanged.
- `npm run lint`: passed, exit 0, no final warnings/errors.
- `npm run build`: passed, exit 0, TypeScript checked, all 14 pages generated.
- `python -m pip check`: passed, no broken requirements.
- Temporary PostgreSQL teardown: pg_ctl stop succeeded; the exact newly created
  temp-directory path was verified, then only that cluster and its workspace
  path marker were removed.
- `git diff --check`: passed after final changes.

Temporary verification failures were corrected: React audio-preview effect linting,
a recording cancellation variable scope error, overlong synthetic pytest IDs on
Windows, the SDK exclusiveMinimum incompatibility, and a transport assertion using
the wrong SDK JSON alias. Synthetic fixture errors did not touch user data.

Production dependencies change only the SDK, its google-auth lower-bound requirement
(2.55.0 to 2.62.0), and mutagen 1.48.1. The test dependency list has the supported SDK
and mutagen too; no Torch/model download is required for tests. The existing UTF-16
production requirements file was normalized to UTF-8 to keep the edited pins valid.
Other existing pinned dependencies were retained, including legacy transitive Google
packages that can be cleaned up separately. No frontend dependency versions changed.

npm still reports 17 advisories (2 moderate, 14 high, 1 critical). No audit fix or
forced upgrade was applied. Existing Pydantic class-config and Starlette TestClient
warnings remain. The deprecated Google generativeai import warning is gone.

CI workflow .github/workflows/phase1-ci.yml now runs the expanded suite on its
fresh pgvector service, without pre-enabling vector, plus npm ci/lint/build.
There is no deployment job. Hosted CI was not triggered or claimed passed in this
session because no commit/push was requested. Local equivalent checks passed.
Windows commands are documented in backend/tests/README.md.

## 10. Tests and remaining limitations

Coverage includes fresh/earlier/legacy-head bootstrap, original data preservation,
new constraints and owner isolation, extraction scenarios, malformed output,
unsupported duration/evidence, timeouts, correction precedence, optional logs and
memories, repeated/concurrent confirmation, discard race, whole-transaction rollback,
track ambiguity/ownership, voice consent, file validation and provider errors, plus
real SDK serialization over a mocked transport and all existing Phase 1 checks.

No paid-model accuracy, real account credentials, physical microphone, browser E2E
interaction or production smoke test was used. Frontend verification is lint/build;
the manual text/voice walkthrough below remains necessary on supported browsers.
Model instructions/evidence validation reduce unsupported output but do not prove
semantic truth; explicit user review remains essential. No claims of live Gemini
availability or transcription quality are made from mocked tests.

Other intentional limits: latest-20 list without pagination, no draft text-edit API
(create a new capture for changed original input), no raw-audio storage/replay after
leaving the page, no automatic purge, no background processing/queues, and no general
schema-drift repair. Known/spelled/fractional duration ambiguity may require manual
entry. There is no mastery model, ranking change, graph, agent or Phase 3 dashboard.

## 11. Manual local walkthrough and Phase 3 handoff

Use only a new disposable PostgreSQL instance, configured as described in the test
README. Set an explicit ALEMBIC_DATABASE_URL and run alembic upgrade head. Separately
configure backend DATABASE_URL to that disposable database, a local signing key and
a Gemini key, with GEMINI_MODEL=gemini-2.5-flash if desired. Keep secrets outside Git
and command output. Start backend uvicorn and frontend npm run dev with a local API
URL. Enabling a real Gemini key makes explicit Analyze/Transcribe actions paid cloud
requests; automated tests do not require it.

1. Register/sign in with a synthetic local account. Open Capture Learning.
2. Submit the Python decorators/closures example from the task. Analyze, review
   types/content/source excerpts, edit one observation, choose/leave an existing
   track and leave minutes empty. Confirm. Expect confirmed observations, optional
   memories if opted in, and no study log. Open saved memory links and reload the
   capture URL to inspect persisted corrections and original text.
3. Create a separate capture with explicitly stated minutes, verify/correct them
   and confirm. Expect one study log with those confirmed minutes. Try a question
   or vague note; no completion/time/mastery should be invented.
4. Test provider outage/no key: original input remains in a failed capture, clearly
   unprocessed. Retry later or manually enter and confirm an interpretation.
5. Start Recording, grant permission, stop, listen locally, then explicitly consent
   and send audio. Review/edit the transcript before Analyze Learning. Also test
   Cancel, permission denial, WAV/MP3 upload, overlong/oversized/invalid input and
   leaving the page while recording. Text entry remains available.
6. Retry confirmation without changing the payload after a simulated lost response;
   expect the existing saved result. A different payload after confirmation is a
   conflict, not an overwrite. Use Reload to inspect the saved outcome.
7. With another synthetic account, confirm private captures/tracks are unavailable.
   Exercise existing memory CRUD and RAG against synthetic records as desired.

Phase 3 should consume user-confirmed LearningObservation rows and confirmed
capture provenance, preserving the distinction between self-report, difficulty,
question and intention. Pending/failed proposals are not confirmed learning facts.
Duration remains nullable through capture; this phase supplies no invented session,
mastery score, completion signal or recommendation-ranking event.

## 12. Files changed

- .github/workflows/phase1-ci.yml
- PHASE2_INTELLIGENT_CAPTURE_REPORT.md
- backend/alembic/BOOTSTRAP_REPAIR.md
- backend/alembic/env.py
- backend/alembic/versions/3d0e118a4fdf_initial_schema.py
- backend/alembic/versions/86a536d3ece5_test_memory_embedding.py
- backend/alembic/versions/f20100000001_complete_baseline.py
- backend/alembic/versions/f20200000002_learning_capture.py
- backend/app/core/config.py
- backend/app/crud/memory.py
- backend/app/db/base.py
- backend/app/db/database.py
- backend/app/main.py
- backend/app/models/__init__.py
- backend/app/models/conversation.py
- backend/app/models/learning_capture.py
- backend/app/models/learning_track.py
- backend/app/models/memory.py
- backend/app/models/memory_embedding.py
- backend/app/models/study_log.py
- backend/app/models/usage_limit.py
- backend/app/models/user.py
- backend/app/routes/capture.py
- backend/app/routes/rag.py
- backend/app/schemas/capture.py
- backend/app/services/audio_service.py
- backend/app/services/capture_service.py
- backend/app/services/extraction_service.py
- backend/app/services/llm_service.py
- backend/app/services/rag_service.py
- backend/requirements-test.txt
- backend/requirements.txt
- backend/tests/README.md
- backend/tests/conftest.py
- backend/tests/test_capture.py
- backend/tests/test_postgres.py
- backend/tests/test_rag.py
- frontend/app/dashboard/capture/page.tsx
- frontend/app/dashboard/page.tsx
- frontend/components/capture/capture-interface.tsx
- frontend/components/capture/voice-input.tsx
- frontend/components/dashboard/sidebar.tsx
- frontend/services/capture.ts
- frontend/types/capture.ts
