# LearnTrack interactive demo

The `demo` branch derives from verified product commit
`97b3c66f11a4ccd32b79dd9c96ae2e0ab8b6a63a`. It uses the same learning capture,
confirmation, continuity, recommendations, history and analytics implementation.
No second learning engine or unrelated application was created.

## Visitor experience

Visitors enter Home without registering. The backend issues a two-hour JWT guest
session and creates an isolated synthetic workspace. The frontend keeps this
temporary token in sessionStorage, separate from existing product sign-in data.
The demo banner explains the synthetic records, expiry and disabled live AI.
Product information and Reset Demo are visible throughout the workspace.

Each visitor starts with Python Foundations, SQL Fundamentals and Data Structures:
15 confirmed captures, 15 timed study sessions totaling 465 minutes (7.75 hours),
24 observations, and three saved memories without model indexes. Different
historical dates populate real continuity, review actions and activity charts.
All displayed statistics and source links come from those database records.
The fixture is explicitly synthetic; its confirmed provenance represents the
demonstration persona's reviewed records, not a claim about a real learner.

Visitors can save manual captures, review a clearly labeled scripted SQL example,
edit/remove/add draft observations, confirm changes, follow evidence, search,
record feedback, explore paths/history/insights and ask grounded recall questions.
Deterministic recall and keyword evidence excerpts use the existing retrieval
engine; excerpts are labeled as saved evidence with live AI disabled.

Reset issues a newly seeded identity and expires only the caller's old identity
in one transaction. Other sessions and unrelated accounts are not selected.
Old tokens fail the server's expiry check. Existing records remain until the
explicit expired-session cleanup runs; expiry is not a physical deletion promise.

## Storage, authorization and limits

Backend `APP_EDITION=demo`, `DEMO_STORAGE_ENABLED=true`, a PostgreSQL database
whose name ends `_demo`, and a distinct 32+ character demo signing secret are all
required. Startup and seeding refuse other configurations. Product mode rejects
demo bootstrap; demo mode rejects product authentication and key configuration.
Guest JWTs have a separate signing key, demo claim and audience. Every existing
owner check remains enforced. Frontend flags never authorize backend access.

Alembic `f60100000001` adds guest-session metadata and an issuance budget without
rewriting product records. A PostgreSQL row lock serializes guest issuance across
instances: at most 500 new sessions per UTC day and ten per socket peer per hour.
Peer addresses are HMAC-hashed in storage. Socket-peer limits do not replace edge
abuse controls, especially behind a reverse proxy. Trust proxy forwarding only
with an explicitly reviewed configuration.

Authenticated mutations reserve one of 100 changes using an atomic conditional
UPDATE. Uploads are limited to 64 KiB, including chunked bodies. Schema limits
continue to apply. These are storage/interaction limits, **not AI quotas**.

`scripts/cleanup_demo.py` is an explicit, guarded maintenance command. It deletes
at most 100 expired issued guest owners per batch and their owned records;
unrelated accounts and active visitors remain. It never resets a database.
Deployers must arrange and monitor periodic cleanup themselves.

## Live AI status — disabled

All Gemini calls are blocked in the shared backend provider in demo mode,
regardless of environment keys. Analysis, retries and audio transcription are
also refused at their routes. Personal-key endpoints reject writes. Local model
indexing and semantic model search are disabled to avoid anonymous model work.
Ordinary confirmed observations, keyword search and deterministic recall work.

No owner Gemini key is provisioned, saved in fixtures, returned to browsers or
used. The scripted example is labeled before and after creation; it is not
presented as a live result. Live demo AI is an explicit **release blocker** until
durable per-visitor/window/global-day reservations, concurrent leases, bounded
outputs, timeouts, repeated-failure backoff and a kill switch are implemented and
verified across instances. Provider-project quotas and infrastructure controls
must also be reviewed. Billing alerts do not stop spending.

## Local verification

The combined backend suite currently reports **234 passed**, no failures or skips,
using separate disposable product and demo PostgreSQL databases. Demo coverage
checks isolation/reset, synthetic statistics, idempotent seeding, provider denial,
cross-edition tokens, streaming request limits, atomic concurrent guest/change
limits, expiry and selective cleanup. Two independent production-browser demo
journeys pass, including six theme/viewport combinations and accessibility scans.
Final rerun counts and GitHub branch status are in final acceptance.

No cloud deployment or paid provider request has been made. Current dependency
advisories, infrastructure validation, backup/recovery, real-device voice and
original-error reproduction remain separately documented release limitations.

The original errors were subsequently identified as a frontend origin mismatch
to an older remote backend with missing routes; see the product report. Final
demo browser rerun: **2 passed**, including direct login/register redirects.
