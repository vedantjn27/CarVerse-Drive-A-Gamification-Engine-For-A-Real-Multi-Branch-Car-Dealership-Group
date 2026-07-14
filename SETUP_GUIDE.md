# CarVerse Drive — Setup, Run, Test & Demo Guide

This guide starts the complete CarVerse Drive experience: FastAPI backend, full CSV seed, React frontend, authenticated player loop, tests, and deployment preparation.

> Need the judge-facing click path? Use [`CARVERSE_FRONTEND_BACKEND_TEST_AND_DEMO_WORKFLOW.md`](CARVERSE_FRONTEND_BACKEND_TEST_AND_DEMO_WORKFLOW.md). Need a map of the codebase? Use [`FOLDER_STRUCTURE.md`](FOLDER_STRUCTURE.md).

## 1. Prerequisites

Install these before beginning:

- **Windows PowerShell** (the included commands use it).
- **Python 3.12** (3.12.11 matches the deployment blueprint).
- **Node.js 20 LTS** and npm.
- A modern browser such as Chrome, Edge, or Firefox.

Verify them:

```powershell
python --version
node --version
npm --version
```

## 2. What must stay in place

Do not move or rename these files before starting:

- `backend/data/z_locations.csv`
- `backend/data/z_employees.csv`
- `backend/data/z_event_log_may_june_2026.csv`

The backend validates their names and headers, then rebuilds the local SQLite database from them. The originals in `carverse files/` are retained as the untouched organizer source exports.

## 3. First-time setup

Open PowerShell at the repository root.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` and set a unique `JWT_SECRET` with at least 32 characters. The provided AI keys are optional—CarVerse falls back to deterministic game copy if they are blank.

Example only:

```env
JWT_SECRET=replace-with-a-unique-long-random-secret
MISTRAL_API_KEY=
GEMINI_API_KEY=
```

### Frontend

Open a second PowerShell terminal at the repository root.

```powershell
cd frontend
npm.cmd install
Copy-Item .env.example .env
```

The default local configuration is already correct:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

Only change it if the backend is served on another host or port.

## 4. Start the application

### Terminal 1 — Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On first startup, wait for the full data rebuild. It validates the supplied CSVs, recreates the disposable SQLite schema, ingests every row, replays the booking lifecycle, materializes gamification records, and then exposes the API.

Confirm readiness:

```text
http://127.0.0.1:8000/health
```

Expected indicators include `"status": "ok"` and `"database": "connected"`.

### Terminal 2 — Frontend

```powershell
cd frontend
npm.cmd run dev
```

Open the Vite URL shown in the terminal—normally:

```text
http://localhost:5173
```

Also available once the API is ready:

```text
http://127.0.0.1:8000/docs
```

## 5. Sign in safely

Use a local test account listed in [`TEST_LOGIN_IDS.txt`](TEST_LOGIN_IDS.txt). The file has one active employee per department plus an admin account.

1. Open `/login`.
2. Enter the Employee ID and OTP from that local file.
3. Select **Enter command centre**.

Keep this file private. Do not publish, commit, or display employee OTPs in a public demo recording.

## 6. Demonstrate the actual game loop

For the most reliable walkthrough, use the Finance account and the detailed instructions in the demo workflow. The short version is:

1. Open **Pit wall**.
2. Optionally select a focus mission; it changes no score.
3. Use **Record daily check-in** once for a capped +2 XP action.
4. Open a Finance Pit Stop race, confirm it is waiting at **Discount Approved**, return to Pit Wall, then choose **Complete next demo action**.
5. Watch the booking advance to **Finance Approved**; it then leaves Finance and becomes work for Accounts.
6. Inspect updated XP, mission progress, boss contribution, league rank, garage reward, live feed, and journey panels.

The demo action is intentionally only available outside production. It validates the next stage and department exactly like a real upstream integration would; it does not permit Finance to complete PDI or Sales work.

## 7. Test the project

### Backend fast suite

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

This uses compact fixtures and covers the state machine, scoring, anti-gaming, auth, APIs, gamification, realtime, admin controls, and scheduler behavior.

### Backend complete dataset audit

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -m full_data
```

This performs the slower validation against the complete organizer data.

### Frontend production build

```powershell
cd frontend
npm.cmd run build
```

## 8. Reset behaviour

The default local setup uses a disposable database and `AUTO_RESEED_ON_STARTUP=true`.

- **Restarting the backend** rebuilds the baseline from supplied CSVs.
- Live demo claims, demo workstation actions, and runtime scoring changes are intentionally ephemeral.
- A clean restart returns the app to the reproducible source-data baseline.

To trigger the same reset manually:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.seed.seed_from_csv
```

## 9. Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `JWT_SECRET` | Yes | At least 32 characters; signs API access tokens |
| `DATABASE_URL` | Local default | Async SQLAlchemy database URL |
| `AUTO_RESEED_ON_STARTUP` | Local default | Rebuild the local data model from CSVs at startup |
| `CORS_ALLOWED_ORIGINS` | Local default | Allowed frontend origins; `*` is suitable only for the hackathon setup |
| `MISTRAL_API_KEY` | No | Primary AI flavour provider |
| `GEMINI_API_KEY` | No | AI fallback provider |
| `SCHEDULER_ENABLED` | Local default | Enables scheduled rebuild, cache refresh, anomaly scan, and snapshots |
| `VITE_API_BASE_URL` | Frontend | HTTP API base URL baked in by Vite |
| `VITE_WS_BASE_URL` | Frontend | WebSocket base URL baked in by Vite |

Never commit `backend/.env` or `frontend/.env`. Templates are included as `.env.example` files.

## 10. Common issues

### The frontend shows the warm-up/readiness screen

The backend is still rebuilding the full CSV dataset or is not reachable. Keep the backend terminal open, wait for startup completion, then open `/health`.

### Login fails

Use an active account from `TEST_LOGIN_IDS.txt`, confirm there are no extra spaces, and make sure the backend has completed seeding. A normal restart resets the demo database, not the supplied employee source data.

### The selected department has no Pit Stop

This is expected when no active booking is currently waiting for that department. Start with the upstream department in the relay; after its valid action, the same booking appears in the next department queue. Support departments can use **Operational Handoff** instead.

### A demo action is rejected

The current employee does not own the next stage, the booking is terminal, or the stage has already been awarded. This is intentional anti-gaming behavior. Select a current Pit Stop or use the account for the owning department.

### No AI key is configured

The game remains functional. CarVerse returns deterministic fallback content for nudges, recaps, missions, boss flavour, and anomaly explanation.

### `npm.cmd` or Python cannot be found

Install the prerequisite runtime, reopen PowerShell, and run the command again. On a shell where execution policy blocks activation, skip `Activate.ps1` and call `backend\.venv\Scripts\python.exe` directly as shown above.

## 11. Deployment notes

### Backend on Render

1. Push the repository to your Git provider.
2. Create a Render Blueprint using the root [`render.yaml`](render.yaml).
3. Supply a secure `JWT_SECRET` and optional AI keys.
4. Warm `/health` before a presentation because the backend reseeds its demo dataset on startup.

### Frontend on Vercel or similar

1. Set the project root to `frontend/`.
2. Build with `npm run build`.
3. In **Project Settings → Environment Variables → Production**, set the values in [`frontend/.env.production.example`](frontend/.env.production.example):

   ```env
   VITE_API_BASE_URL=https://carverse-drive-a-gamification-engine-for.onrender.com
   VITE_WS_BASE_URL=wss://carverse-drive-a-gamification-engine-for.onrender.com
   ```

   These are public frontend URLs, not secrets. Local `frontend/.env` remains pointed at `localhost:8000`.
4. Rebuild after changing any `VITE_*` variable, because Vite embeds them at build time.

For a long-running production deployment, move from disposable SQLite to managed persistence while preserving the existing state-machine and ledger rules.
