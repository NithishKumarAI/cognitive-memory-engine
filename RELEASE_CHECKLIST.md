# Release checklist — approval required before production actions

Phase 4 is local work. No production migration, deployment, cloud change, commit or push was performed. Historical demo URLs do not verify this version.

- [ ] Resolve or explicitly accept the dependency advisories recorded in `PHASE4_FINAL_PRODUCT_REPORT.md`, with owner and rationale. Re-run both audits on the release date. Do not use forced major upgrades without compatibility tests.
- [ ] Run the full backend suite against disposable PostgreSQL + pgvector, `npm ci`, lint, build, and the isolated browser suite. Verify real microphone capture and live Gemini separately with authorized accounts and nonsensitive inputs.
- [ ] Review secret-manager values: `DATABASE_URL`, strong `SECRET_KEY`, `GEMINI_API_KEY`, model, timeout and token lifetime. Set public `NEXT_PUBLIC_API_URL` at frontend build time. Never use example credentials.
- [ ] Restrict `FRONTEND_ORIGINS` to explicit HTTPS origins, validate CORS preflight and bearer-token handling, terminate HTTPS at the trusted ingress and configure microphone permissions. Set request-body, concurrency, user rate and daily spend limits at the gateway; configure Gemini project quota/budget alerts. The app does not enforce a distributed per-user quota.
- [ ] Restrict database network access and least-privilege application roles; provision pgvector separately with an authorized migration role. Verify model assets/runtime memory and outbound provider configuration.
- [ ] Back up the database, record the current Alembic revision and test restoration into a separate database before changing production. Retain the previous image and matching configuration.
- [ ] Review all migration SQL, especially the additive nullable `learning_actions.request_digest` in `f40100000001`. Existing rows remain intact; no digest is fabricated for legacy rows. Do not auto-run a downgrade or schema reset. Do not alter historical migrations.
- [ ] Obtain explicit user approval for the named production migration/deployment after the above evidence is ready. Apply migrations through a controlled job, then deploy the reviewed images. Docker definitions have not been locally image-built in this session.
- [ ] Check `/health` (including database connectivity), authentication, owner isolation, capture confirmation, retrieval, exact links and analytics using a dedicated smoke-test account. Do not put tokens, reflections, audio or provider payloads in logs.
- [ ] Configure redacted error monitoring, request latency, database pool saturation, timeout and cost alerts, backup retention and deletion policies. Review user-facing cloud-processing consent and privacy notice.
- [ ] For rollback, restore the previous application image only if it tolerates the additive column. Prefer a forward repair for database issues. Use the tested backup recovery plan under approved downtime if data restoration is necessary; never assume the guarded migration supports destructive downgrade.

JWTs currently use localStorage with an existing twelve-hour default expiry and no server-side logout revocation. An HttpOnly-cookie/session architecture and restrictive CSP need a separate reviewed design. React renders learning text as text; this reduces injection exposure but does not remove the localStorage risk.
