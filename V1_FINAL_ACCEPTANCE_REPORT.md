# V1 final acceptance — historical memory reliability

Date: 2026-10-23. **NO-GO for unrestricted public production release.** The historical-recall correction and local product acceptance are implemented and verified as detailed below. Docker, live provider/model/hardware and required operational/security gates remain open. No commit, push, checkout, reset, merge, rebase, stash, production connection/migration/deployment, release or version tag was performed.

## 1. Baseline branch and commit

Started on `main` at `41ce67814d77b9d90bb478cc3c97dc4efeb6313b`, matching the request. Initial tree was clean. Read the Phase 4 and V1 hardening reports, release checklist, live acceptance and deployment plans, and relevant source/tests. All prior phase/hardening reports are intact. The product name, UI, auth design, optional-memory capture workflow and 768-dimensional vector model are unchanged.

Baseline GitHub Actions [39822655537](https://github.com/NithishKumarAI/cognitive-memory-engine/actions/runs/39822655537) was independently inspected through the GitHub connector: frontend job 119977679320 and backend job 119977679902 both completed successfully. This verifies baseline CI only; these local uncommitted changes have not run remotely. No workflow rerun was triggered.

## 2. Actual bugs identified

1. General RAG loaded the newest 30 owned observations and filtered keywords in Python. A matching confirmed record older than that window was invisible without a suitable indexed memory. It also attempted embedding generation before checking whether the owner had any indexed memories.
2. Deterministic continuity questions applied a recent 20-topic cap before selecting the requested topic or unresolved kind. This could claim no unresolved work existed, or answer about an unrelated recent topic, while old matching evidence remained.
3. Recommendations considered only 50 recent topic checkpoints before applying the existing ranking rules. Older high-priority difficulties and intended steps could never compete. Deduplication also omitted the learning-track identity, collapsing similar topic names from distinct tracks/unassigned learning.
4. General retrieval did not bound combined memory/observation context or projection sizes. Manual memory text can be large.
5. A targeted relevance test demonstrated that simple substring matching retrieved “Trust management” for “Rust.” Whole-term matching now prevents that false positive. Scoped negative continuity answers now describe no match for the question rather than falsely denying other recorded difficulties/questions.

## 3. Historical recall improvements

`observation_retrieval.py` extracts up to eight distinct explicit terms, removes conversational/continuity stop words and numbers, and limits term length to 64. Escaped whole-term regex patterns are SQL parameters, not executable user regex or interpolated SQL. C++, C# and SQL are covered. PostgreSQL filters both observation and parent-capture owner plus confirmed capture status, then ranks before LIMIT: distinct-term coverage, topic matches, content matches, confirmation/creation recency and stable observation ID. No newest-record horizon is applied. Pending, failed, discarded and other-owner observations are excluded in the database.

The query returns at most five projected observations (content 2,000 characters, evidence 400, topic 200). It does not hydrate thousands of text/JSON ORM bodies to find five matches. The original pgvector cosine search remains available and its default CRUD result shape is unchanged. RAG opts into a bounded projection, at most five memories, with the existing finite-distance <=0.5 relevance guard. Querying whether the owner has indexed memories comes first: histories without optional embeddings skip model initialization entirely; embedding failure can still fall back to eligible observations.

General evidence count is at most ten (five per kind). Returned sources keep real memory/observation/capture IDs and existing response fields. Each source has a bounded excerpt in a shared **16,000-character context**; the service clips the question to 4,000 characters (the API still validates/rejects longer requests). The current prompt template stays below **24,000 characters**, including instructions and question. Truncation is marked. Existing 2,048-token provider output cap is preserved. These character caps are not a token/spending quota.

Continuity eligibility now precedes its small display cap: filter matching topic terms and unresolved observation kind over metadata, then hydrate selected checkpoints. An explicit unknown topic does not fall back to unrelated learning. Recommendation generation considers all narrow topic metadata, preserves the established priority/category/topic/ID ordering and completion/dismissal rules, and hydrates only returned supporting records after ranking. Deduplication includes normalized topic and track identity. This fixes candidate loss/identity, not the ranking policy. Completed next steps stay closed; old unresolved steps/difficulties remain eligible.

## 4. Files modified

Only implementation-required README/live-checklist text was updated; older reports, release/deployment plans, dependency pins and production configuration are preserved. New tests/artifacts are synthetic.

- `.gitignore`
- `LIVE_ACCEPTANCE_GUIDE.md`
- `README.md`
- `V1_FINAL_ACCEPTANCE_REPORT.md`
- `backend/app/crud/retrieval.py`
- `backend/app/services/continuity_service.py`
- `backend/app/services/observation_retrieval.py`
- `backend/app/services/rag_service.py`
- `backend/tests/acceptance_restart.py`
- `backend/tests/test_historical_recall.py`
- `backend/tests/test_postgres.py`
- `frontend/e2e/journeys.spec.ts`
- `test-artifacts/final-acceptance/README.md`
- `test-artifacts/final-acceptance/baseline-ci.json`
- `test-artifacts/final-acceptance/npm-audit.json`
- `test-artifacts/final-acceptance/npm-runtime-audit.json`
- `test-artifacts/final-acceptance/persistence.json`
- `test-artifacts/final-acceptance/python-audit.json`
- `test-artifacts/final-acceptance/screenshots/analytics-dark-1440.png`
- `test-artifacts/final-acceptance/screenshots/analytics-light-1440.png`
- `test-artifacts/final-acceptance/screenshots/capture-dark-1440.png`
- `test-artifacts/final-acceptance/screenshots/capture-light-1440.png`
- `test-artifacts/final-acceptance/screenshots/chat-dark-1440.png`
- `test-artifacts/final-acceptance/screenshots/chat-light-1440.png`
- `test-artifacts/final-acceptance/screenshots/history-dark-1440.png`
- `test-artifacts/final-acceptance/screenshots/history-light-1440.png`
- `test-artifacts/final-acceptance/screenshots/home-dark-1440.png`
- `test-artifacts/final-acceptance/screenshots/home-dark-390.png`
- `test-artifacts/final-acceptance/screenshots/home-dark-768.png`
- `test-artifacts/final-acceptance/screenshots/home-light-1440.png`
- `test-artifacts/final-acceptance/screenshots/home-light-390.png`
- `test-artifacts/final-acceptance/screenshots/home-light-768.png`
- `test-artifacts/final-acceptance/screenshots/learning-tracks-dark-1440.png`
- `test-artifacts/final-acceptance/screenshots/learning-tracks-light-1440.png`
- `test-artifacts/final-acceptance/screenshots/memories-dark-1440.png`
- `test-artifacts/final-acceptance/screenshots/memories-light-1440.png`
- `test-artifacts/final-acceptance/screenshots/recommendations-dark-1440.png`
- `test-artifacts/final-acceptance/screenshots/recommendations-light-1440.png`
- `test-artifacts/final-acceptance/screenshots/search-dark-1440.png`
- `test-artifacts/final-acceptance/screenshots/search-light-1440.png`
- `test-artifacts/final-acceptance/screenshots/study-logs-dark-1440.png`
- `test-artifacts/final-acceptance/screenshots/study-logs-light-1440.png`

## 5. Database indexes and migrations

**No new or modified index, table, extension, column or migration.** Existing `ix_learning_observations_user_id`, `ix_learning_observations_capture_id`, `ix_learning_captures_user_id`, owner foreign keys and pgvector/HNSW path remain intact. The corrected query uses PostgreSQL filtering/ranking and LIMIT, with bounded projection; it does not require pg_trgm, another vector database, a search service or a full indexing subsystem. Current Alembic head remains `f40100000001` and historical migrations were not edited.

Existing owner indexes are available to the planner; this is not a claim that each small test query uses an index scan. Regex term filtering can still scan an owner's eligible text, and continuity metadata/action state grows with history. No constant-time, fixed-memory-at-unlimited-history or production latency/throughput claim is made. If real-scale profiling warrants a text index later, it needs a reviewed forward migration and its own deployment evidence.

## 6. Before/after retrieval behavior

- Old decorator observation + 35 or 130 unrelated newer records, no memories/embeddings: before it was outside the inspected window; after it supplies its real observation/capture IDs without initializing a model. Tests explicitly prove it is absent from the former newest-30 candidate set.
- PostgreSQL history with 140 newer unrelated observations and an indexed memory: after filtering, the old confirmed observation and actual pgvector memory both appear with real source IDs; pending/failed/discarded/other-user matches do not. The projected 50,000-character memory returns only the requested 2,000-character body.
- More than 100 newer topics and old Python difficulties in two paths plus unassigned learning: bounded recent display lists still show recent records, while historical questions and the ranked recommendation endpoint retain the old unresolved evidence. Similar names no longer collapse across paths. Completed next steps are excluded; pending steps remain.
- “Rust” against only “Trust management”: before substring matching falsely selected it; after whole-term matching there is no observation candidate. Generic/empty or unrelated queries do not invoke a model without usable evidence. Existing distant-vector rejection remains tested.
- Browser journeys with `create_memories=false` **and** true create a path, analyze a natural-language note with mocked extraction, correct and confirm, inspect actual records, resume, add 110 unrelated confirmed updates, sign out/in, inspect/complete the grounded intended step and ask about the original decorators. Inline citation navigation opens the exact preserved capture/observation; no study minutes or mastery are fabricated.

## 7. Retrieval limitations

This is deterministic explicit-term recall, not universal semantic search. It does not stem, translate, expand synonyms, resolve all paraphrases or disambiguate homonyms; conversational stop words, first-eight-term selection and 64-character term length can omit a useful term. Whole-term treatment may miss compound/variant spellings. Topic filtering for deterministic continuity is narrower than general topic/content retrieval. Any-term matching can still produce partial relevance; coverage/topic ranking helps but does not certify an answer. Bounded lists are not global totals.

Without indexed memories, a question sharing no supported terms may correctly return unavailable even if a human would recognize the paraphrase. With embeddings, prior vector behavior still depends on model quality and the existing threshold, not this test suite. Long evidence is excerpted and may omit relevant details. Historical conversation text still lacks persisted citation snapshots. Returned candidates do not assert that every source was cited, and the LLM can still produce inaccurate or unsupported references; exact known-source navigation is preserved, not a proof that all live answers are grounded. No mastery claim or new assessment is introduced.

## 8. Tests and local runtime results

**AUTOMATED PASS — backend:** **192 passed, 0 failed, 0 skipped**, 3 existing warnings, 12.46 seconds. Includes all 175 baseline tests and 17 added cases: older-than-30/100 recall, absent/present embeddings, irrelevant recent records, multiple users/statuses/topics/tracks, query/projection/context bounds, real IDs/URLs, stable RAG schema, old unresolved continuity, completed steps, short technical terms and low-relevance rejection. The real PostgreSQL/pgvector fixture is included; SQLite-only tests are not presented as PostgreSQL proof. Existing warnings remain Starlette TestClient/httpx and two Pydantic class-config deprecations.

**AUTOMATED PASS — frontend:** `npm ci` exit 0 (423 packages), `npm run test:release` 3 passed/0 failed/0 skipped, lint exit 0 and production build exit 0 with TypeScript/static page generation. Build uses `NEXT_PUBLIC_API_URL=http://127.0.0.1:8100`, explicit `ALLOW_LOCAL_API_ORIGIN=1` and synthetic test servers, never production credentials. The final clean-install/release/lint/build sequence ran after the last implementation edit.

**AUTOMATED PASS — browser:** **11 passed, 0 failed, 0 skipped**, 1.4 minutes, against the final production build. Original nine journeys are retained, plus two historical-recall variants. Existing responsive/axe sweep covers 60 route/theme/width combinations and 40 automated WCAG scans. Artifacts are isolated in `test-artifacts/final-acceptance/`; no previous screenshot/report was overwritten. Mocked recording/transcription is not physical microphone or live Gemini evidence.

**LOCAL RUNTIME PASS — restart:** `acceptance_restart.py seed` committed synthetic original text/correction and 140 newer unrelated observations in a random test schema. That Python process exited, the self-created PostgreSQL server was actually stopped/restarted, and a new Python service process verified preserved text/correction, old observation recall, zero embeddings and zero other-owner sources. Its own fixture schema was removed after verification. See `persistence.json`. This proves the tested database/service-process persistence path, not cloud backup restoration, live model behavior or a production restart.

`pip check` reports no broken requirements. `git diff --check` exits 0 without whitespace errors. Baseline CI success is separately evidenced in `baseline-ci.json`; no remote pass is claimed for local edits.

Initial/recovered failures are not hidden: an early existing continuity test exposed an omitted conversational stop word (“should”); fixed without weakening its assertion. The Rust/trust test intentionally failed before the matching correction and now passes. One browser-harness attempt exited before tests ran and left its known synthetic backend PID; only that PID was stopped and a captured-log rerun passed all journeys. The first manual restart start command omitted the custom port and failed to bind default localhost; restarting explicitly on 127.0.0.1:55439 succeeded. A verifier started before that correction produced no result and was interrupted; only the succeeding fresh-process run counts as evidence.

## 9. Docker evidence or blocker

**BLOCKED.** Docker CLI exists, but `docker info` still returns `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine ... The system cannot find the file specified.` No image build/start/size/UID/container PORT/model-cache permission/communication result is claimed. No Docker installation, WSL/service/context reconfiguration or production Cloud Run action was attempted. Local browser production startup remains verified by the suite, which does not establish container correctness.

Exact next Windows action: open Start, search **Docker Desktop**, launch it, complete its own startup prompts as appropriate and wait until its engine is running. Use Linux containers for these Linux Dockerfiles. In PowerShell run `docker info`; require a working **Server** section before repeating image acceptance. If Desktop cannot start, use its own diagnostic UI and the official Windows prerequisites guide rather than making guessed system-wide changes. See [Docker’s Windows startup instructions](https://docs.docker.com/desktop/setup/install/windows-install/#start-docker-desktop). Any WSL/virtualization/system change remains the user's deliberate action.

Then follow the existing `DEPLOYMENT_PLAN.md` disposable-image checklist: test-only tags, never push; non-default frontend/backend PORT; own pgvector instance; image sizes/effective UID; `/health`, browser-to-API auth/capture with mocked provider; writable trusted cache checked without loading/downloading weights. Stop only named test-created resources. Live model download still needs separate explicit approval.

## 10. Dependency audit changes

Fresh 2026-10-23 audits match the V1 hardening baseline: **four Python packages, six distinct advisory IDs (ten raw feed entries due to duplicates); five high frontend development nodes for the braces chain; zero npm runtime advisories.** Curated audit JSON is saved here. Audit exit 1 for remaining findings is expected, not a passing security gate. No version, lockfile or model change was made merely to suppress findings.

- cryptography 48.0.1: PYSEC-2026-3552/3553/3554, advertised fixes 49/50; runtime Google-auth dependency, no direct app PKCS7/certificate-chain endpoint. That does not prove transitive unreachability. A major upgrade needs compatible crypto/provider evidence; remains **BLOCKED** for remediation or explicit reviewed disposition.
- sentence-transformers 5.5.1: PYSEC-2026-4164, advertised fix 5.6.0; real lazy model loader/cache trust boundary. Actual model loading is not approved/available as acceptance evidence. Per the request, do not call a mocked constructor sufficient runtime evidence; remains a reviewed **BLOCKED** model-runtime upgrade.
- torch 2.12.0: PYSEC-2025-194, advertised fix 2.13.0; substantial runtime/platform change, not blindly upgraded. No live weights/inference compatibility or image-size proof; **BLOCKED** pending that work/disposition.
- setuptools 81.0.0: PYSEC-2026-3447, advertised fix 83; packaging/sdist path rather than an app request endpoint. Current Torch requires `setuptools<82`, so forcing 83 would conflict. Remains unresolved with the Torch/toolchain gate.
- eslint-config-next → @next/eslint-plugin-next → fast-glob → micromatch → braces: same dev/build stack-exhaustion advisory (GHSA-vfj7-8cjw-p6xm) and no compatible fix identified by the fresh audit. Do not force an untested major downgrade. Trusted reviewed sources/isolated CI reduce exposure but do not resolve the finding.

The existing PyJWT/fsspec hardening stays intact. Risk documentation is not remediation, and passing recall tests is not model-runtime or security certification.

## 11. Live acceptance still pending

**MANUAL TEST REQUIRED:** every live item in `LIVE_ACCEPTANCE_GUIDE.md` remains unchecked here: approved Gemini extraction, structured accuracy, user correction/confirmation with real provider output, physical recording/permission denial, live transcription/editable transcript, real embedding generation and 768-dimensional vectors, real pgvector relevance/RAG citation accuracy, actual hosted HTTPS/CORS and two-user privacy. The guide now includes historical recall after 100+ unrelated updates with optional memories both off/on. Only nonsensitive synthetic notes/accounts in an approved disposable staging environment are permitted.

No paid Gemini call, embedding-weight download, physical permission request, cloud billing change or secret-manager update was made. Real quota/timeout acceptance must use a controlled approved fault plan rather than flooding a provider. Manual checklist preparation does not grant authorization to incur cost or change a production account.

## 12. Operational controls still missing

**EXTERNAL CONFIGURATION REQUIRED:** distributed authenticated request/concurrency limits, global pre-parse body limits, per-user usage/window accounting, provider request/token quotas and verified spend protection/alert response, reviewed scaling/resource limits, redacted monitoring/retention and a tested backup restore. These are still absent/unverified. Existing UsageLimit rows remain inactive and untouched; no resets, counters or billing claims were introduced. Alerting alone is not proof that spend stops.

Registration closure (`REGISTRATION_ENABLED=false`) and Gemini kill switch (`AI_ENABLED=false`) remain implemented/tested from V1, with compatible true defaults. They need explicit deployed revision configuration; old/in-flight requests may complete, existing users are not rate-limited, and local embeddings/downloads are not disabled by the Gemini switch. They do not constitute distributed quotas.

Session security retains JWT/localStorage, verified expiry/owner checks, constrained redirects, no-store responses and explicit voice consent. XSS token exposure and lack of server-side logout revocation remain residual risks; no rushed cookie migration was shipped. Backup restoration, production migrations, HTTPS/CORS configuration, secret management and operational telemetry remain plans only. This task changes no database schema and executes migrations only inside owned disposable schemas.

## 13. Regressions and compatibility

All original backend/frontend tests are preserved. POST `/rag/ask` request/response schema and source types/IDs remain compatible; top_k's existing accepted range remains, with an explicit internal five-memory cap plus five observations to bound evidence. Default CRUD vector retrieval retains full ORM objects; only RAG opts into projected excerpts. Its cosine behavior is unchanged and tested in actual pgvector. Bounded recent display endpoints remain bounded; broad historical discovery is handled before their use for recall/recommendations.

No UI redesign, new agent, indexing service, model/version/name change, mastery/minutes fabrication or learning-history overwrite. No prior report is rewritten. New source limits and literal matching intentionally trade unbounded text/recall for bounded inputs; limitations are described above rather than hidden as universal recall guarantees.

## 14. Final decision

**NO-GO for unrestricted public production release.** Historical literal recall and the original learning journey are locally demonstrated, including without optional embeddings and after an actual disposable server restart. That is an acceptance improvement, not sufficient evidence to close the mandatory Docker, model/provider/hardware, security and operations gates. No unresolved automated product regression is accepted as a pass; any remaining external gate must be closed with actual evidence or the appropriate explicit owner decision.

## 15. Exact next human actions

1. **BLOCKED → enable local Docker:** launch Docker Desktop and wait for a healthy Linux engine; confirm `docker info` Server. Then authorize/repeat only the disposable image checklist in the existing deployment plan. Record sizes, effective UID, custom PORTs, health, communication and cache permissions without downloading weights.
2. **MANUAL TEST REQUIRED → approve staging acceptance deliberately:** name a disposable database/project and cost ceiling; explicitly approve any live Gemini call, physical microphone test or model-weight download. Execute the existing twelve-item live guide plus the historical-recall extension; record actual outcomes/citations/owner isolation. No real personal learning notes are needed.
3. **BLOCKED → dependency disposition:** review/test compatible crypto and model/toolchain remediation, including the Torch/setuptools constraint, and upstream braces status. Do not force versions; documentation alone does not close a vulnerability.
4. **EXTERNAL CONFIGURATION REQUIRED → operational evidence:** enforce gateway/distributed abuse/cost controls, registration policy, HTTPS/exact CORS, secrets, monitoring/retention and proven restore/rollback. Assess localStorage/session risk for any limited-access beta explicitly.
5. Re-run current checks and CI only after separately authorized commit/push; prior CI cannot certify these uncommitted edits. Review a concrete production rollout only after all mandatory gates have evidence, with explicit production approval. This task does not authorize committing, pushing, deployment or a new GitHub release.

Cleanup completed: the exact self-created temporary PostgreSQL cluster was stopped with pg_ctl fast/wait, its absolute path was verified, and its directory was removed only after the server marker disappeared. The fixture restart schema had already been removed by its verifier. Zero listeners remain on test ports 3100, 8100 and 55439. No existing database/service was stopped or removed; no production environment was modified.
