# CarVerse Drive Backend

FastAPI backend for a data-driven gamification engine built around the supplied
dealership event, employee, and location CSV exports.

## Current status

Phases 0 through 9 are complete. Every supplied location, employee, and event row
is loaded and deterministically replayed through the booking state machine,
18-rule XP engine, progression system, badge engine, and leaderboard aggregates
on startup. Authentication and the first frontend-ready APIs are operational.

## Structure

```text
backend/
|-- app/
|   |-- api/              # health endpoint and versioned route composition
|   |-- core/             # environment-driven settings
|   |-- db/               # async engine, sessions, and model package
|   |-- scheduler/        # scheduled jobs added in Phase 8
|   |-- seed/             # deterministic seeds added by feature phases
|   `-- services/         # domain services added by feature phases
|-- data/                 # organizer CSV copies and disposable SQLite database
|-- tests/                # automated backend tests
|-- .env.example
`-- requirements.txt
```

Files for later capabilities are added in their implementation phase rather than
being committed as empty or non-functional placeholders.

## Local setup

From this `backend` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. Readiness is available at both `/health` and
`/api/v1/health`.

Run tests with:

```powershell
python -m pytest
```

Normal tests use a compact deterministic SQLite fixture (six employees, two
locations, and five bookings) and finish in about a second. They cover the API,
state machine, scoring, progression, and gameplay behaviour without replaying
every organizer profile. The full source-data audit is retained separately and
can be run before a demo or deployment:

```powershell
python -m pytest -m full_data
```

## Configuration

Configuration is loaded from environment variables, with `backend/.env` used for
local development. The root `.gitignore` excludes `.env`, the virtual environment,
caches, and disposable database files. `.env` must never be deployed or committed.
Copy `.env.example` for a new environment and supply a unique `JWT_SECRET` of at
least 32 characters. Mistral and Gemini keys are optional: deterministic fallback
text is returned if neither provider is configured or either provider fails.

`CORS_ALLOWED_ORIGINS=*` currently permits any frontend origin for the hackathon.
Credential sharing is automatically disabled in this wildcard mode, as required
by browser CORS rules. Set explicit comma-separated origins before a credentialed
production frontend is introduced.

`SCHEDULER_ENABLED=true` starts four in-process APScheduler jobs in a running
non-test service: nightly source-data rebuild, nightly quest-flavour refresh,
nightly anomaly scan, and weekly league snapshot. They intentionally do not run
under the test environment. On a free Render instance, jobs run only while the
web service is awake; every startup rebuilds the same deterministic baseline.

The local SQLite database is disposable by design. Every application startup:

1. validates that all three organizer files exist with exact expected headers;
2. drops and recreates the complete registered schema;
3. ingests locations, employees, then events in transactional batches;
4. replays events in `(created_date, raw_event.id)` order into bookings and XP;
5. materializes levels, streaks, reputation, badges, ranks, and team aggregates;
   and
6. reports seed, scoring, and gamification totals in application logs.

## Available API endpoints

- `POST /api/v1/auth/login`
- `GET /api/v1/users/me`
- `GET /api/v1/users/{user_id}/stats`
- `GET /api/v1/leaderboards/individual?scope=week|month|all`
- `GET /api/v1/leaderboards/branch?scope=week|month|all`
- `GET /api/v1/leaderboards/department?scope=week|month|all`
- `GET /api/v1/bookings/{location_code}/{enquiry_no}`
- `GET /api/v1/bookings/active?location_code=&department=`
- `GET /api/v1/quests/me` and `POST /api/v1/quests/{quest_code}/claim`
- `GET /api/v1/boss-battles/active` and `GET /api/v1/boss-battles/{battle_id}`
- `GET /api/v1/ai/nudge/me`, `/api/v1/ai/recap/{department_or_location}`, and
  `/api/v1/ai/quests/me`
- `GET /api/v1/ai/boss-battles/{battle_id}/flavour`
- `GET /api/v1/admin/anomalies`, `POST /api/v1/admin/anomalies/{id}/resolve`,
  `POST /api/v1/admin/ingest`, and `POST /api/v1/admin/scoring-rules` (ADMIN)
- `WS /ws/leaderboard?token={bearer_jwt}`
- `GET /health` and `GET /api/v1/health`

Login accepts an active organizer employee ID and its supplied OTP. It returns a
Bearer JWT; profile and leaderboard endpoints require that token. Role rights are
mapped to `AGENT`, `MANAGER`, or `ADMIN`. OTPs, mobile numbers, and the JWT secret
are never returned by an API.

Run the same full reset manually:

```powershell
python -m app.seed.seed_from_csv
```

Run an idempotent insert-only pass without resetting the schema:

```powershell
python -m app.seed.seed_from_csv --no-reset
```

## Phase record

### Phase 0 — Project scaffold

- Created separate `backend/` and reserved `frontend/` workspaces.
- Added a FastAPI application factory and clean async lifespan.
- Added environment validation through `pydantic-settings`.
- Added async SQLAlchemy sessions backed by `aiosqlite`.
- Added configurable CORS and active departments.
- Added real database-backed health checks at `/health` and `/api/v1/health`.
- Added pinned direct dependencies and Phase 0 tests.
- Preserved the organizer CSVs in their original folder; no ingestion has run.

Verification on Python 3.12.5:

- `python -m compileall -q app tests` — passed
- `python -m pytest -W error` — 4 passed, zero warnings
- `python -m pip check` — no broken requirements
- OpenAPI exposes exactly the two Phase 0 readiness routes; later routes are not
  advertised before they work.

### Phase 1 — Data ingestion and normalization

- Copied all three organizer CSVs into `backend/data/`; SHA-256 comparisons prove
  that every deployed copy is byte-for-byte identical to its source.
- Added relational `locations`, `employees`, and immutable `raw_events` models.
- Stored original values beside normalized stage, category, department, source,
  outlet, and action values for auditability.
- Implemented uppercase/trim/whitespace normalization, explicit `CCM` and `RTO`
  department aliases, `RGISTRATION_*`/`REGISTARTION_*` correction, and safe
  `DOCUMENTS_OTHER - ...` family bucketing.
- Converted the paired `-` booking sentinels to database nulls while preserving
  their raw values.
- Added exact-header validation, typed timestamp/integer parsing, configurable
  batch sizes, transactional file loads, and conflict-safe source-ID deduplication.
- Added the startup drop/recreate/full-reseed lifecycle and the standalone
  `seed_from_csv` command.
- Confirmed actual source counts: 41 locations, 6,037 employees, and 170,162
  events. These intentionally supersede the slightly inaccurate counts in the
  original planning document.
- Confirmed zero orphan event users and zero orphan event locations. The 4,636
  employee home-location codes absent from the location export remain preserved
  without fabricated foreign-key mappings.
- Confirmed 23,251 `DOCUMENTS_OTHER` events and 5,938 actions containing known
  registration misspellings are classified without losing their raw text.
- Confirmed a second pass reads all 176,240 source rows and inserts zero.
- Full test suite: 11 passed with warnings treated as errors.

### Phase 2 — State machine, scoring, and anti-gaming

- Added all 18 canonical actions as immutable structured rule data, safely below
  the hackathon maximum of 20.
- Added the max-reached booking state machine. Out-of-order source milestones
  cannot regress progress, while first legitimate occurrences can still score.
- Added composite-key `bookings` and append-only `xp_ledger` tables with both a
  deterministic dedupe key and source-event/canonical-event/beneficiary uniqueness.
- Replays raw events in `(created_date, id)` order for identical cold-start output.
- Derives full document sets only from the eight exact required document actions;
  `DOCUMENTS_PANIC BUTTON` and individual uploads never score directly.
- Collapses both invoice approval legs and both dispatch legs to one payout per
  booking, and derives delivery only from the first `DELIVERED` stage row.
- Attributes delivery to the deterministic Sales booking owner even when the
  stage transition is carried by an Accounts gatepass row. `CREDIT_APPROVED` is
  retained as the only real approval signal, with XP attributed to its real
  Accounts actor rather than inventing a Finance user.
- Implements branch rolling-median fast-delivery bonuses and exact integer team
  bonus splits whose shares always sum to the configured pool.
- Implements login/day and follow-up/booking/day caps, daily and weekly
  leaderboard XP caps, the five-delivery daily leaderboard cap, and preserves all
  legitimate lifetime XP beyond leaderboard caps.
- Implements different-user/different-department collaboration guards, four
  business-hour handoff checks, a six-handoff booking cap, 24-hour escalation
  resolution, cancellation saves, terminal cancellation freezing, reversible
  dormant state, and the configurable 15% rework discount after two escalations.
- Same-source derived milestones cannot generate artificial collaboration XP.
- Verified full replay: 3,800 bookings (1,578 won, 472 lost, 319 dormant, 1,431
  active), 37,739 ledger awards, 511,237 lifetime XP, and 482,868 leaderboard XP.
- Verified zero duplicate milestone-per-booking awards and zero duplicate
  source-event/canonical-event/beneficiary ledger entries.
- Test suite includes judge-readable cases for 50 logins, 50 notes, duplicate
  invoices, exact document sets, self-collaboration, cancellation freezing,
  rework discounts, delivery ownership, and lifetime-vs-leaderboard caps.
- Final Phase 2 verification: 25 tests passed with warnings treated as errors;
  Python compilation and dependency integrity checks also passed.

### Phase 3 — Progression, badges, authentication, and leaderboards

- Added a configurable `100 × level^1.5` progression curve and six seeded title
  tiers from Rookie Closer through Delivery Legend.
- Materializes one `user_stats` row for every one of the 6,037 supplied employees;
  407 currently have earned XP and the rest receive valid level-one profiles.
- Computes current and longest streaks exclusively from real milestones, never
  from login or capped follow-up activity.
- Grants configured 3/7/14/30-day streak XP exactly once through a separate
  progression-bonus ledger, preserving the 18-action scoring cap and keeping
  progression bonuses outside competitive leaderboard XP. The supplied data
  produces 222 awards worth 2,820 progression XP, with zero duplicate bonuses.
- Computes a separate 0–100 reputation score from clean outcomes, escalation
  recovery, and inverse rework rate using environment-configured weights.
- Seeded all eight planned data-driven badges and awarded 333 evidence-backed
  user badges. Thresholds not met by the dataset remain honestly unawarded.
- Added materialized department and branch statistics. All 41 locations are
  represented; branch normalized score is leaderboard XP per booking attempt.
- Added deterministic all-time, department, and location user ranks.
- Added weekly, monthly, and all-time individual, branch, and department APIs.
  Historical scopes anchor to the latest supplied event timestamp, keeping the
  May/June 2026 demo meaningful after wall-clock time advances.
- Department competition exposes the configured five headline departments while
  the combined Dealership Score still includes the complete ledger.
- Added active-employee OTP login with constant-time comparison, signed JWTs,
  expiry/issuer/audience validation, and data-derived AGENT/MANAGER/ADMIN roles.
- Added authenticated current-user and employee-stat APIs with badges and ranks;
  sensitive source fields are excluded from responses.
- Confirmed a no-reset rerun inserts zero CSV rows and zero XP awards while
  reproducing the same 6,037 stats, 333 badges, and 41 location aggregates.
- Reconciled every profile total against the immutable XP ledger plus the
  progression-bonus ledger: 514,057 total XP and zero mismatched profiles.
- Final Phase 3 verification: 36 tests pass with warnings treated as errors;
  compilation and all declared runtime dependency imports pass.

### Phase 4 — Booking race, quests, and boss battles

- Added authenticated booking race APIs. Every response is built from the
  materialized composite booking plus its immutable canonical-milestone ledger,
  exposing the ordered track, actual reached milestones, owner, contributors,
  status, and progress percentage without inventing workflow state.
- Added a filterable active-race list for race-track screens. Terminal WON and
  LOST bookings are excluded; filtering by branch or a touched department is
  supported with bounded pagination.
- Seeded four static, inspectable weekly quest templates. Completion is computed
  solely from the canonical XP ledger during the event-data week; claiming a
  completed quest is one-time and writes an auditable progression-bonus entry.
- Added five weekly department boss battles, each tied to a real canonical
  milestone. Progress is a live ledger count; a completed battle splits its
  configured pool deterministically among the actual qualifying contributors,
  never creating a new scoring action.
- Added a compact test fixture and a `full_data` pytest marker. Normal work now
  runs 33 tests in about one second; the retained full organizer replay runs
  seven audit tests in about one minute.

### Phase 5 — Optional AI enrichment

- Added one cache-backed AI gateway. It attempts Mistral chat completions first,
  then Gemini `generateContent`; cached results respect `AI_CACHE_TTL_SECONDS`.
  The provider is the only module permitted to make AI HTTP calls.
- Added deterministic fallback text for every AI feature, so missing keys,
  provider failure, timeouts, and rate limits never block the core game.
- Added factual nudge, recap, quest-board flavour, boss-battle flavour, and
  anomaly-explanation APIs. AI receives only structured facts and can never
  create XP, alter a quest target, change a score, or resolve an anomaly.

### Phase 6 — Anomaly detection and admin controls

- Added a z-score scan of leaderboard XP per real booking touched, evaluated
  within each department. It creates human-review flags only; it never mutates
  the XP ledger, changes a rank, or penalizes an employee.
- Added ADMIN-only anomaly listing/resolution, full re-ingestion, and live
  base-XP scoring-rule tuning. A tuning request preserves prior overrides,
  rebuilds from the original organizer CSVs, and replays deterministically so
  its effect is real rather than a display-only setting.

### Phase 7 — Realtime

- Added an authenticated in-process WebSocket feed at `/ws/leaderboard`.
  It emits `xp_gain` for every inserted award while clients are connected,
  `boss_progress` for booking-scoped progress, and `leaderboard_rebuilt` after
  an admin rebuild. Disconnected clients are cleaned up safely.
- Final Phases 5–7 verification: 36 fast tests passed in 1.95 seconds and the
  seven full-data audit tests passed in 60.08 seconds, all with warnings treated
  as errors.

### Phase 8 — Scheduler wiring

- Added four AsyncIO scheduler jobs with single-instance, coalesced execution:
  deterministic nightly re-ingestion (while preserving live rule overrides),
  nightly quest-flavour cache refresh for active players, nightly anomaly scan,
  and weekly individual/branch/department leaderboard snapshots.
- Snapshot records store the reporting window, rank, raw score, normalized score
  where applicable, and a JSON copy of each rendered entry for audit.
- Scheduler configuration is environment-driven and disabled in tests, keeping
  routine verification fast and deterministic.

### Phase 9 — Deployment packaging

- Added the root [render.yaml](</C:/Users/vedan/Documents/My_Projects/CarVerse Drive - A gamification engine for a real multi-branch car dealership group/render.yaml>)
  Blueprint with `rootDir: backend`, Python runtime, health check, safe secret
  prompts, and deliberately no persistent disk.
- Added [Procfile](</C:/Users/vedan/Documents/My_Projects/CarVerse Drive - A gamification engine for a real multi-branch car dealership group/backend/Procfile>)
  and [.python-version](</C:/Users/vedan/Documents/My_Projects/CarVerse Drive - A gamification engine for a real multi-branch car dealership group/backend/.python-version>)
  for a consistent `uvicorn app.main:app --host 0.0.0.0 --port $PORT` deployment.
- Deployment procedure: push the repository, create a Render Blueprint from the
  root `render.yaml`, supply `JWT_SECRET` and optional AI keys, then warm `/health`
  before presenting so reseeding completes before the demo.
- Final Phases 8–9 verification: 39 fast tests passed in 2.18 seconds and the
  seven full-data audit tests passed in 61.77 seconds, all with warnings treated
  as errors.

### Phase 10 — Final full-data validation and demo polish

- Compared every planned backend capability against the implementation: ingestion,
  scoring, anti-gaming, progression, badges, authenticated APIs, race tracks,
  quests, boss battles, optional AI, anomaly review, admin controls, realtime,
  scheduling, and deployment packaging are present and connected.
- Added a full-data API smoke test spanning health, OTP/JWT authentication,
  profiles, all leaderboard boards, active booking race data, quests, boss
  battles, AI fallbacks, WebSocket authentication, weekly snapshots, and ADMIN
  scoring-rule replay.
- Added a cold-start determinism test that rebuilds the full organizer dataset
  twice and compares all materialized profile and progression-bonus rows.
- Demo-ready examples from the supplied data: `BAA6879` (Manoj Kumar B R, PDI)
  leads the all-time profile ranking with 44,090 XP; YESHWANTHAPURA (`YSH`)
  leads the normalized branch board; booking `BDC / ENQ26000068` provides a
  traceable won lifecycle with 11 earned milestones. OTPs and other sensitive
  employee fields are intentionally not documented or exposed.
- Final full-data materialization: 170,162 raw events, 3,800 bookings, 37,739
  ledger awards, 6,037 profiles, 263 progression bonuses, 333 badges, five boss
  battles, and nine human-review anomaly flags.

### Next phase

Backend implementation is complete. The remaining project work is the separate
frontend implementation and deployment configuration with real production
secrets.
