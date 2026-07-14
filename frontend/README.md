# CarVerse Drive Frontend

Premium React/TypeScript frontend for the CarVerse FastAPI backend. It uses the backend as the source of truth for scoring, booking state, ranks, quests, boss battles, and admin controls.

## Run locally

1. Copy `.env.example` to `.env` and set the backend origin if it is not `http://localhost:8000`.
2. Start the backend from `backend/`.
3. Run `npm.cmd install` once, then `npm.cmd run dev` from this folder.
4. Open the Vite URL (normally `http://localhost:5173`).

Use `npm.cmd run build` for a production verification/build.

## Configuration

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

The client sends bearer tokens to REST endpoints and uses the raw JWT in `/ws/leaderboard?token=...`. Tokens are stored only in `sessionStorage` and are cleared on logout/tab close.

## Routes

- `/` — scrollable public CarVerse branding page, including the interactive supplied Spline scene and F1-style milestone animation.
- `/login` — backend readiness check and employee ID/OTP authentication.
- `/app` — command centre.
- `/app/journey` — progression, reputation, streak and badges.
- `/app/race` — active booking race track.
- `/app/leagues` — individual, branch and department leaderboards.
- `/app/quests` — backend-verified weekly missions.
- `/app/boss-battles` — department battle progress.
- `/app/admin` — ADMIN-only anomaly, reingest and base-XP controls.
- `/app/tv` — authenticated read-only lobby presentation.

## Important integration rules

- No score, rank, progress, or reward is calculated in the browser.
- AI copy is shown as optional flavour only.
- On cold deployment startup, the readiness screen waits for the backend to reseed before login.
- WebSocket events refresh authoritative cached data; REST remains usable if realtime reconnects.
- The backend supports base-XP tuning only, not browser-editable caps/cooldowns.
- The lobby route is read-only but remains authenticated because the backend APIs require JWTs. Use a dedicated display account for a shared screen.

The complete functional contract remains in `../CARVERSE_FRONTEND_BUILD_SPEC.md`.
