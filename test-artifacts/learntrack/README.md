# LearnTrack synthetic browser evidence

2026-10-26 local production-mode Playwright run: 14 passed. The API used an isolated disposable PostgreSQL schema and mocked AI. No live Gemini or physical microphone verification.

`screenshots/` contains 30 synthetic images: 24 authenticated workspace views from the existing journey and 6 public overview views, light/dark at 390/768/1440px. Public overview tests also checked loaded images, no overflow, no API requests, metadata/icon, WCAG 2 A/AA and 2.1 A/AA, and sign-in/register navigation.

The public overview intentionally reuses the older approved screenshots in `frontend/public/showcase/`, with prior-name disclosure. These newer images record the completed branding. Earlier test evidence is preserved.
