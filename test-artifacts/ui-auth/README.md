# LearnTrack UI/auth verification evidence

2026-10-26, local production-mode frontend, synthetic accounts and disposable PostgreSQL. No live Gemini or real microphone used.

- Backend: 212 passed; final full Playwright: 26 passed. Release: 3 passed; lint/build/whitespace passed.
- `database-readiness.json`: empty database → existing migrations/pgvector/head → real signup/login/path → physical PostgreSQL and API restart → persisted accounts/path, duplicate rejection and owner privacy.
- `backend-stopped.json`: public frontend works with the API actually stopped; signup displays the connection failure and never fabricates success.
- `screenshots/`: 38 new synthetic captures. `hero-dark-1440.png` is a single viewport preview. `overview-{light,dark}-{390,768,1440}.png` show the full public story. `register-{390,768,1440}.png` and `login-{390,768,1440}.png` cover forms. `registration-backend-stopped.png` shows the actual offline behavior. Remaining 24 images preserve the existing workspace journey coverage in the new run.

Public overview: 6 light/dark/width combinations, no horizontal overflow, zero API requests and zero axe WCAG 2 A/AA/2.1 A/AA violations. Auth forms also passed axe/overflow at each requested width. A normal-motion test checks animation, pause/resume, reveal/visibility state and reduced-motion changes.

Earlier `phase4`, `v1`, `final-acceptance` and `learntrack` evidence remains unchanged. Current V1 deployment pending verification. See `LEARNTRACK_UI_AUTH_FINAL_REPORT.md` at the repository root for scope, diagnosis limits and release blockers.
