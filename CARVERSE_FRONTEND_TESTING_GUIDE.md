# CarVerse Drive — Frontend + Backend Test and Demo Workflow

## Integration status

The frontend is structurally integrated with the FastAPI backend:

- REST routes use the implemented `/api/v1` API paths.
- Authenticated requests send `Authorization: Bearer <token>`.
- Realtime connects to `/ws/leaderboard?token=<raw-jwt>`.
- The frontend does not calculate XP, ranks, quest completion, boss rewards, or booking stages locally.
- The frontend production build has passed.

Before calling the integration fully verified, perform the live workflow below. The backend intentionally reseeds the full provided CSV dataset on startup, so its initial boot can take several minutes.

## 1. One-time setup

Open two PowerShell terminals at the project root.

In terminal 1, install backend dependencies and start the API:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Wait for Uvicorn to report that application startup is complete. Do not stop this terminal.

In terminal 2, start the frontend:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open the Vite URL printed in terminal 2, normally `http://localhost:5173`.

The frontend uses these defaults from `frontend/.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

If you change the backend host or port, create `frontend/.env` with matching values, then restart Vite.

## 2. Readiness check

1. Open `http://127.0.0.1:8000/health` directly in a browser.
2. Confirm a JSON response with `"status": "ok"` and `"database": "connected"`.
3. Open the frontend. Until health is ready, it should show the CarVerse warm-up screen rather than empty game data.

If the health endpoint does not become ready, keep the backend terminal open and read the visible error. The most common local setup issue is missing packages; rerun the backend dependency command above.

## 3. Obtain a valid demo login

The backend accepts an employee ID and OTP from the supplied `backend/data/z_employees.csv` dataset. For a safe local lookup, run this in a third terminal:

```powershell
Import-Csv backend/data/z_employees.csv | Select-Object -First 10 id, otp, name, department, role_rights | Format-Table
```

Use one returned `id` and `otp` at `/login`. Do not commit, screenshot, or publish real OTP values.

For ADMIN-only testing, choose an employee whose role resolves to `ADMIN`. If none is obvious in the CSV, inspect the backend’s role mapping rather than modifying frontend role checks.

## 4. Full frontend verification workflow

Use this exact sequence after logging in.

### A. Public branding and accessibility

1. Start at `/`.
2. Confirm the scrollable CarVerse branding story appears.
3. Interact with the supplied Spline car-race scene in the hero; it must respond to pointer interaction.
4. Scroll to confirm the separate F1-style milestone car moves along its visual track.
5. Check the support email link and “Enter the grid” navigation.
6. Turn on your operating-system reduced-motion preference and refresh. Motion should be substantially reduced.

### B. Authentication and readiness

1. Visit `/login`.
2. Try an empty submit: both required credentials should be requested.
3. Try an invalid ID/OTP pair: receive a neutral invalid-credentials message.
4. Sign in with a valid CSV-backed employee.
5. Refresh the browser: the tab session should remain active.
6. Open a new browser tab/session after closing the original tab: the session should require login again.
7. Click Sign out and confirm protected `/app/*` routes return to login.

### C. Command centre and personal journey

1. At `/app`, verify the returned user name, level, title, XP, streak, reputation, quest, boss, and weekly leaderboard use real values.
2. Check that the AI Coach card is visibly labelled as flavour/enrichment and does not claim to calculate scores.
3. Open `/app/journey`.
4. Verify title, progress bar, reputation ring, streak, performance record, and trophy garage correspond to API data.
5. Change a Driver Garage livery. It should persist locally after refresh but never alter XP/rank.
6. Toggle the sound control and theme control. Both preferences should persist locally.

### D. Race track

1. Open `/app/race`.
2. Change the department filter and confirm the active booking list updates.
3. Select a booking.
4. Confirm its stage nodes, current department, progress, milestones, owner, and XP ledger match backend data.
5. Click “Replay verified journey.” It must animate only the already-returned route; it must not award or fabricate any milestone.

### E. Leagues, recap, and profile drill-down

1. Open `/app/leagues`.
2. Switch between individual, branch, and department boards.
3. Switch week, month, and all-time scopes.
4. Confirm branch/department boards label normalized score fairly instead of presenting it as raw XP.
5. On a branch or department board, verify the AI recap card loads and is labelled as AI flavour.
6. Use the Share/Copy recap control. It should share or copy the visible recap text only.
7. On the individual board, click a player row. Confirm the profile drill-down reads `/users/{user_id}/stats` and shows returned stats.

### F. Missions and boss battles

1. Open `/app/quests`.
2. Confirm static quest progress comes from `/quests/me`.
3. Confirm the AI-flavoured quest section uses deterministic progress/criteria and clearly labels AI flavour.
4. Only if a quest is complete, click Claim. Confirm the success/achievement animation occurs after backend success.
5. Refresh and confirm the claimed state remains in the running backend instance.
6. Open `/app/boss-battles`.
7. Confirm each battle uses returned department, event, target, progress, contributors, and reward pool.
8. Confirm boss flavour is displayed as optional AI text, not as a scoring rule.

### G. Realtime and lobby presentation

1. Keep `/app` open in one browser tab.
2. Open `/app/tv` in another authenticated tab.
3. Confirm lobby mode auto-rotates branch league and boss-battle presentation.
4. Keep the app open while an admin rebuild is performed. The live feed should show the rebuild event and refresh authoritative data.
5. If no event occurs, confirm the live feed displays a connected status; REST content must still remain usable if the socket reconnects.

### H. Admin workflow (ADMIN only)

1. Log in as an ADMIN. Confirm “Admin controls” appears in navigation.
2. Log in as an AGENT/MANAGER. Confirm both the navigation item and direct `/app/admin` route are inaccessible.
3. In `/app/admin`, open an anomaly’s AI triage explanation. Treat it as human-review help only.
4. Enter a human resolution note and resolve one anomaly. Confirm it leaves the OPEN list after successful API response.
5. Test Base-XP tuning with a single canonical event and value from 0–500. Confirm the confirmation dialog appears; do not use this during the final polished demo unless planned.
6. Test Full Data Rebuild only after noting that live claims/tuning are ephemeral. Confirm it triggers a deterministic rebuild and the frontend refetches after completion.

## 5. Recommended judging demo workflow

Warm the backend 5–10 minutes before presenting. Keep the backend terminal running.

1. **Brand story (45 seconds):** show the Spline race hero and scroll to the CarVerse tagline.
2. **Authentic data (45 seconds):** log in and show the Command Centre’s real XP, reputation, quest, and leaderboards.
3. **Core differentiator (60 seconds):** open a booking race; explain that the car moves only through backend-verified dealership milestones.
4. **Game loop (45 seconds):** show a quest, badge/trophy garage, boss battle, and AI flavour distinction.
5. **Fair competition (45 seconds):** switch to Branch League and explain normalized score.
6. **Trust (45 seconds):** use the Admin anomaly queue to show human review, anti-gaming design, and optional AI explanation.
7. **Big finish (30 seconds):** open TV/lobby mode, show live league/boss visuals, then return to the tagline.

### Interactive demo workstation (development/demo mode only)

1. Restart the backend after pulling the latest code, then log in with a department test account from `TEST_LOGIN_IDS.txt`.
2. Open **Pit wall** from the sidebar. Choose a focus mission; this is a preference only and grants no points.
3. Select the displayed Pit Stop for your department and use **Complete next demo action**.
4. The backend permits only the next valid stage for the employee's department, records an append-only `DEMO WORKSTATION` milestone, advances the real booking race, awards canonical XP, refreshes mission/boss/league data, and emits a live update.
5. Use **Run shift replay** to narrate the complete verified lifecycle. Claim a weekly mission only after its configured target is genuinely complete.
6. Explain clearly to judges: production receives the same verified milestone from the dealership system; the button exists only to make the live event loop demonstrable without an external DMS connection.

### All-department player loop

- Every active employee has a **Daily Shift Check-in**: the existing once-per-day, low-value 2-XP rule.
- Sales, Finance, Accounts, Customer Care, RTO / Registration, and PDI use **Complete next demo action** to advance a valid real booking stage.
- EDP, Accessories, TrueValue, Security, Service, Transport, CCM, and any other support department use a department-labelled **Operational Handoff**. It is capped to one demo work item per employee/day and awards the single canonical `OPERATIONAL_HANDOFF_COMPLETED` action.
- The latter is the nineteenth scoring action, preserving the hackathon limit of at most 20. It drives the same XP ledger, Operations Relay mission, department boss battle, cosmetic unlocks, league refresh, and live-feed update as lifecycle actions.

### Why a department can sometimes have no Pit Stop

A Pit Stop is a live work queue, not a catalogue of every booking a department touched in the past. It shows only bookings waiting for that department's next verified action.

- Finance begins with **Discount Approved** bookings. Completing one changes it to **Finance Approved**, so it leaves Finance and appears for Accounts.
- Accounts can complete an **Invoice Approved** booking to create **Gatepass Issued** work for Customer Care.
- Customer Care completes that gatepass lane to create **Insurance Approved** work for RTO / Registration.
- RTO completes it to create **RTO Registration Completed** work for PDI.
- PDI dispatches it and Sales completes final delivery. Final delivery marks the booking as completed and removes it from all active queues.

Therefore, Customer Care and RTO may initially show “No action waiting for your team” with this supplied CSV snapshot. That is correct. Use the upstream department action above, refresh Pit Wall, and the same booking appears in the next department's queue. This is the intended cross-department relay demo.

Avoid triggering a full reingest during the live demo unless it is rehearsed; it intentionally rebuilds the full dataset and can take time.

## 6. Final pass checklist

- [ ] `/health` is ready before the demonstration.
- [ ] Frontend loads without browser-console errors.
- [ ] Valid login works and invalid login fails safely.
- [ ] Every protected route works for the signed-in user.
- [ ] Admin routes work only for ADMIN.
- [ ] No page shows mock XP, mock rank, fake player, or fabricated booking stage as real data.
- [ ] AI copy is always treated as flavour.
- [ ] Race, leaderboard, quest, boss, admin, and TV screens are demonstrated.
- [ ] WebSocket connected state is visible; REST fallback remains functional.
- [ ] Theme, reduced motion, mobile layout, and logout have been checked.

## 7. Simple click-by-click Finance employee demo

Use this active Finance test account from `TEST_LOGIN_IDS.txt`:

- **Employee ID:** `10`
- **OTP:** `2330`
- **Employee:** Praphulla Lunawat
- **Department:** Finance

Restart the backend before this demo so the latest Demo Workstation routes, quests, and boss battles are loaded.

### A. Login

1. Open the frontend and click **Sign in** or **Enter the grid**.
2. Enter the Finance Employee ID and OTP above.
3. Click **Enter command centre**.

What should happen: the Command Centre opens and shows this employee's own XP, level, reputation, mission, boss battle, and league position.

What it means: each employee has a separate secure game profile. Finance does not see a fake shared profile.

### B. Command Centre

1. Look at **Total XP**, **Current Streak**, and **Reputation**.
2. Click **Open journey**.

What should happen: the values belong to the signed-in Finance employee and will refresh after a verified/demo action.

What it means: XP is not merely a number on a landing page; it drives the employee's progression.

3. Return to **Command centre** using the sidebar.
4. Click **All missions** in the Next Mission card.

What should happen: the Mission page opens with weekly targets, progress bars, XP rewards, and a disabled **In progress** button until a target is met.

What it means: points cannot be claimed just by clicking. A verified event must first complete the target.

### C. Pit Wall: the interactive employee loop

1. Click **Pit wall** in the sidebar.
2. Under **My Next Move**, click one of the small mission buttons.

What should happen: the selected mission becomes highlighted and its title/progress becomes the employee's focus.

What it means: the employee chooses what to pursue. This selection gives no XP, so it cannot be gamed.

3. In **All-Department Shift Check-in**, click **Record daily check-in**.

What should happen: an achievement animation appears showing `+2 XP`; Total XP, league data, and the live feed refresh. A second click on the same day should be rejected.

What it means: every department has one small, capped daily action. It demonstrates a streak loop without allowing repetitive XP farming.

4. In the Finance **Pit Stop** card, note the booking number and current stage. Finance sees only bookings waiting at **Discount Approved**—the stage immediately before Finance’s action. Click **Open this race track**.
5. The Race Track opens that exact booking automatically, with **Finance** selected. The car should be stopped at **Discount Approved** and the next highlighted node should be **Finance Approved**. Return to Pit Wall.
6. Click **Complete next demo action**.

What should happen: the backend allows the action because Finance owns this exact next stage. The selected booking changes from **Discount Approved** to **Finance Approved**; its car moves to the Finance node and Finance receives canonical XP. When the data refreshes, that booking leaves the Finance queue because it is now waiting for **Accounts**. It will appear in the Accounts employee’s Pit Stop instead. Mission, boss, garage, league, and live-feed queries refresh from the same append-only event.

What it means: this is the full employee gameplay loop: work action -> verified milestone -> XP -> personal progress -> team impact -> league movement. In production, the Finance system/API sends this same event; the button is present only for a live hackathon demo.

If the button says that another department owns the next action, choose another displayed active booking or log in as that department. This is correct anti-gaming behavior: Finance must not approve Sales or PDI work.

6. Click **Join the rally** under Team Rally.

What should happen: the button changes to a joined state.

What it means: the employee publicly commits to the department goal, but gets no free XP. A real Finance approval is what increases the team boss progress.

7. Click **Run shift replay**.

What should happen: a car travels across Sales, Finance, Accounts, PDI, and Delivery; then a completion animation appears.

What it means: this is a visual replay of the dealership workflow for judges. It explains how one booking becomes a cross-department race; it does not create fake XP.

8. Read **Near Miss** and click **View live league**.

What should happen: the League page opens.

What it means: a nearby competitor gives the employee a reason to complete the next real milestone, while the leaderboard remains backend-controlled.

### D. Race Track

1. Click **Race track** in the sidebar.
2. Use the department filter and click an active booking in the left list.
3. Inspect each stage, the current stage, milestone ledger, responsible department, and awarded XP.
4. Click **Replay verified journey**.

What should happen: the booking track animates without changing the backend data.

What it means: the application can explain every handoff and show exactly which verified action earned points. It demonstrates collaboration, not just individual sales volume.

### E. Missions and rewards

1. Click **Missions** in the sidebar.
2. Read the progress and reward XP on each card.
3. After enough verified Finance actions have completed a target, click **Claim reward**.

What should happen: an achievement celebration appears; the reward XP is added immediately to the profile and leaderboard, and the mission changes to **Claimed**.

What it means: the employee performs the final player action, but the claim is unlocked only by real verified work.

### F. Boss battles, garage, and personal journey

1. Click **Boss battles**.
2. Find the Finance battle, **Approval Avalanche**.

What should happen: its progress increases when Finance approvals are recorded; contributors and remaining target are visible.

What it means: Finance employees win as a crew, not by competing only against teammates.

3. Click **My journey**.

What should happen: level, rank, reputation, streak, badges, clean-booking statistics, and earned rewards are visible.

What it means: the game rewards quality, consistency, and collaboration in addition to raw activity.

4. Return to **Command centre** and use the **Driver Garage** livery choices.

What should happen: the selected car livery changes and is saved for that browser.

What it means: cosmetics make progression feel game-like but never alter scores or business outcomes.

### G. League, lobby, and visual controls

1. Click **Leagues** and switch between individual, department, branch, weekly, and all-time controls where available.

What should happen: standings change scope while remaining based on backend-calculated XP/normalization.

What it means: employees can compete fairly at several levels.

2. Click **Lobby mode** in the top bar.

What should happen: a TV-style screen rotates through the branch league and boss battle.

What it means: the dealership can make the competition visible on a shared screen.

3. Click the sun/moon icon.

What should happen: the theme changes and remains readable.

4. Click the sound icon.

What should happen: achievement-sound preference toggles for the browser.

5. Click the logout icon.

What should happen: the session is cleared and protected pages require login again.

### H. What a Finance dashboard can and cannot demonstrate

A Finance employee can demonstrate almost the entire employee experience: login, personal profile, daily action, Finance work action, XP gain, race progression, mission progress and claiming, boss participation, garage cosmetics, journey, leagues, live feed, replay, lobby, theme, sound, and logout.

A Finance employee **cannot** demonstrate an action owned by another department, such as Sales delivery or PDI completion. That is intentional anti-gaming protection. Use a separate department account to demonstrate those role-specific action buttons.

A Finance employee also cannot demonstrate **Admin controls** because they are restricted to Admin/Super Admin accounts. Use the EDP Super Admin account in `TEST_LOGIN_IDS.txt` for re-ingestion, anomaly review, and scoring-rule controls.
