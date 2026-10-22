# Cognitive Memory Engine frontend

Next.js App Router, React, TypeScript, Tailwind, Recharts. Use Node 24 (also pinned in `.nvmrc`, Docker and CI).

From this directory:

```powershell
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Set `NEXT_PUBLIC_API_URL` to the reachable backend origin before building. This is embedded in browser JavaScript, not a secret. Configure backend `FRONTEND_ORIGINS` to the exact browser origin.

```powershell
npm run lint
npm run build
npm start
```

Home, Capture Learning, Learning Paths, Next Actions, Memory, Learning History, Assistant, Insights and Study Logs share responsive navigation. Header search searches owned saved records. Appearance supports light, dark and system preferences. Branding defaults are centralized in `lib/branding.ts`.

Browser tests use synthetic accounts and mocked AI with real disposable PostgreSQL. From this directory, with that disposable database running:

```powershell
$env:E2E_PYTHON='C:\path\to\repo\.venv\Scripts\python.exe'
$env:PHASE4_E2E_DATABASE_URL='postgresql+psycopg://phase1:test-only@127.0.0.1:5432/cme_phase1_test'
npx playwright install chromium
npm run test:e2e
```

For production-mode browser verification, build with `NEXT_PUBLIC_API_URL=http://127.0.0.1:8100`, then set `E2E_PRODUCTION=1` and run the same tests. Ports 3100 and 8100 must be free. The test harness rejects a non-loopback database or a different database name and creates a random schema. Never point it at an existing data store. The dedicated CI service provides a safe example.

The suite checks synthetic recording/consent/transcription, not physical microphones or live Gemini. Screenshots contain synthetic data under `../test-artifacts/phase4/screenshots`. JWTs remain in browser localStorage; XSS can expose them. Server authorization remains authoritative. No Phase 4 deployment has been performed.
