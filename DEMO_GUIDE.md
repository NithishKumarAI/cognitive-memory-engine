# LearnTrack public interactive demo — V2

The `demo` branch provides temporary anonymous workspaces. The product branch
`codex/learntrack-product-v2` requires registration. Both use the same learning
engine. Remote main is updated only after review and owner approval.

## Start the demo locally on Windows

Use Python 3.12, Node 24 and a **new separate PostgreSQL/pgvector database** named
`learntrack_demo`, with its own database role. Never use product credentials.
From the repository root on the demo branch:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-test.txt
if (-not (Test-Path backend/.env.demo.local)) {
  Copy-Item backend/.env.demo.example backend/.env.demo.local
}
```

Edit the ignored `backend/.env.demo.local`. Set matching explicit database and
migration URLs, a separate 32+ character `DEMO_SECRET_KEY`, and a different
`SECRET_KEY`. Keep `APP_EDITION=demo`, `DEMO_STORAGE_ENABLED=true`,
`REGISTRATION_ENABLED=false` and `AI_ENABLED=false`. The local helper reads only
this file, so your product `.env` stays untouched. No Gemini key is needed.

```powershell
.\.venv\Scripts\python.exe backend/scripts/demo_local.py migrate
.\.venv\Scripts\python.exe backend/scripts/demo_local.py check
.\.venv\Scripts\python.exe backend/scripts/demo_local.py serve --port 8001
```

In another PowerShell terminal:

```powershell
Set-Location frontend
npm ci
$env:APP_EDITION='demo'
$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8001'
$env:ALLOW_LOCAL_API_ORIGIN='1'
$env:NEXT_TELEMETRY_DISABLED='1'
npm run build
$env:PORT='3001'
npm start
```

Open `http://localhost:3001`. Add that exact origin to the demo backend's
`FRONTEND_ORIGINS` (for example `http://localhost:3001,http://127.0.0.1:3001`) before
starting it. Root, login and registration pages redirect to the demo workspace
when the frontend is built with `APP_EDITION=demo`. Backend authorization always
uses its own trusted edition setting.

## Explore the workflow

1. Home already contains 15 synthetic learning updates across three paths.
2. Follow a checkpoint or recommendation to its actual supporting record.
3. Search for closures or SQL. Ask the Assistant “Where did I stop?” or
   “What should I practice next?” for evidence-based recall.
4. Choose **Try guided example** to review a clearly labeled scripted SQL draft.
   Correct it and confirm; your Home counts update immediately.
5. Write your own synthetic note and choose **Review manually** for the normal
   non-AI workflow. Avoid personal information in a disposable demonstration.
6. Open another private browser context to see a different isolated visitor.
7. Choose **Reset Demo** to replace only your current visitor workspace.

Guest access expires after two hours. A new guest session gets fresh seed data.
Run the explicit maintenance command regularly in a deployed demo:

```powershell
.\.venv\Scripts\python.exe backend/scripts/demo_local.py cleanup
```

Each batch selects at most 100 expired issued guest owners. It does not select
active guests or unrelated accounts. Provision and monitor maintenance in your
hosting environment; the app does not create a scheduled job automatically.

## Boundaries and live AI

Live Gemini, voice transcription, model indexing and semantic model search are
server-blocked in this edition. There is no owner-key configuration to expose.
Keyword search, manual capture and evidence-based recall remain usable.
The demo enforces 64 KiB upload bodies, 100 mutations per guest, 500 new sessions
per UTC day and ten new sessions per socket peer per hour. These durable limits
do not implement paid-provider quotas. Live AI stays disabled until distributed
cost controls and operational abuse defenses are independently verified.

Use separate databases, roles and secrets for product and demo. Add HTTPS,
trusted-proxy rules, edge rate limits, monitoring and verified backups before
public hosting. See [the demo report](LEARNTRACK_DEMO_REPORT.md) and
[final acceptance](LEARNTRACK_FINAL_ACCEPTANCE.md) for unresolved release gates.
No cloud deployment has been performed.

---

## Historical authenticated walkthrough

The following older walkthrough is retained for the authenticated product. It
is not the public guest demo described above.

# LearnTrack walkthrough

Your AI learning continuity companion. Remember what you learn. Pick up where you left off.

## Start with the public overview

Run the application with the [Windows local setup](README.md#run-locally-on-windows), then visit `http://localhost:3000/`. No account is required to explore the animated capture, review, memory, checkpoint and insights scenes. These are labelled conceptual illustrations, not a functional anonymous AI demo. Pause animation or use your system reduced-motion setting. Historical synthetic screenshots remain in the README and test evidence. Sign in/register links lead to the existing authenticated workspace; there is no anonymous live AI demo.

Current V1 deployment pending verification. The historical Cloud homepage is not evidence of a deployed LearnTrack V1. No shared public demo account is provided.

## Prepare a private, synthetic walkthrough

Use the [simple local setup](LOCAL_SETUP.md) with a dedicated new development PostgreSQL database, pgvector, Python 3.12 and Node 24. Set both `DATABASE_URL` and `ALEMBIC_DATABASE_URL` explicitly before `alembic upgrade head`, as shown in the README. Run the API on 8000 and frontend on 3000; check API `/health`. Create your own synthetic account with an example.com email and a unique password. Do not reuse real credentials or record tokens.

The automated suite uses a mocked provider and a disposable database; it is the provider-free way to exercise the full capture journey. A normal local server requires your own authorized Gemini configuration for extraction. Do not enable unrestricted shared usage to make a presentation work. Manual `AI_ENABLED=false` inspection can cover the overview, authentication and non-AI pages, but capture analysis will be unavailable.

## Capture, review and confirm

1. Create a learning path named **Python foundations**.
2. Open **Capture Learning**, select that path and enter this synthetic update:

   > I studied Python decorators. Closures are confusing. Next I will practice decorators with a small logging wrapper.

3. Choose **Analyze Learning**. Expect a draft describing decorators, a reported difficulty around closures and a practice intention. Live model wording and the number of observations can vary; the browser harness deliberately returns deterministic synthetic observations.
4. Read the original input and every proposed item. Correct an item in **What to save**, remove unsupported suggestions, and check that questions/difficulties are represented honestly. Analysis alone is not confirmed learning or mastery.
5. Optionally check **Also create a searchable memory**. Leave it off for an observation-only walkthrough. Choose **Confirm and save**, reload and verify your correction remains under **Saved interpretation**. Save the capture link privately for your own local navigation.

## Return to the evidence

- Return to **Home** and use **Resume learning** to inspect the checkpoint. Follow its supporting capture/observation; your original input and corrected interpretation should agree with what you saved.
- Open **Next Actions**. Inspect **View supporting record** before completing, resolving or dismissing an action. Reload to verify feedback persists. The action records your choice, not demonstrated skill.
- Search your saved history for **decorators**. In **Assistant**, ask “What difficulty did I record about closures?” Inspect **Open source** links on a new answer and compare with the exact record. Retrieved context and cited evidence are distinguished; older conversations without stored citations do not acquire invented ones. An unsupported question may have no relevant evidence. Keyword recall is literal, not guaranteed semantic paraphrase matching.
- Visit **Insights**. Captures without logged minutes add no study time. Add a synthetic 25-minute study log if you want an activity chart; self-reported understanding and consistency describe records, not assessed mastery.

## Optional live checks

Only with your own provider key, explicit cost controls and synthetic content: test real extraction and grounded answers. In a supported localhost/HTTPS browser, explicitly start voice capture, stop it, review consent before sending audio, and edit the transcription before analysis. Test denial/cancel as well. Physical microphone, browser codec and provider behavior require real acceptance; mocked tests do not prove these work on your hardware.

For optional semantic memory, enable searchable-memory creation for one synthetic capture and inspect its saved memory. First use may download embedding weights. Confirm the model cache/network deliberately; `AI_ENABLED=false` does not disable local embeddings. Observation-only history can still support keyword recall without these embeddings.

## Suggested recording sequence

No video or GIF is supplied or claimed. If recording later, use only a synthetic local workspace:

1. Public overview and promise (5–10 seconds).
2. Text update → review/correct → confirm (20–30 seconds).
3. Home checkpoint → exact supporting record (10 seconds).
4. Next action → evidence link → feedback (10 seconds).
5. Grounded answer/source and honest Insights (15–20 seconds).

Use an already prepared synthetic record where waiting for AI would interrupt the recording. Label any mocked environment. Hide developer tools, credentials, terminal environments and account passwords; avoid recording a real reflection. Voice can be a separate explicitly consented clip.

## Limits before a public demo

Current V1 deployment pending verification. Real provider/model, microphone/HTTPS, Docker image and deployed-revision checks remain open alongside documented dependency advisories, session/CSP review, rate limits, quotas and cost controls. See [release gates](RELEASE_CHECKLIST.md) and [live acceptance](LIVE_ACCEPTANCE_GUIDE.md). Do not advertise unlimited paid AI, shared credentials or a completed production release. LearnTrack name uniqueness is unconfirmed.
