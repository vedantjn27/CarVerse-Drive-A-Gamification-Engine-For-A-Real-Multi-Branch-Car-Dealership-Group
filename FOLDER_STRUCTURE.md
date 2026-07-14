# CarVerse Drive — Folder Structure & Code Navigation

This guide explains what each important directory and file does. It is designed for a new developer, reviewer, or judge who needs to understand the project quickly.

```text
CarVerse Drive - A gamification engine for a real multi-branch car dealership group/
│
├── README.md                                      # Project story, capabilities, diagrams, impact, quick start
├── SETUP_GUIDE.md                                 # Full install, run, test, demo, environment and deployment guide
├── FOLDER_STRUCTURE.md                            # This navigation guide
├── requirements.txt                               # Root convenience entry point to backend dependencies
├── CARVERSE_BACKEND_IMPLEMENTATION_PLAN.md        # Original implementation plan + completed phase evidence
├── CARVERSE_FRONTEND_BACKEND_TEST_AND_DEMO_WORKFLOW.md
│                                                   # Click-by-click integration and judge demo workflow
├── TEST_LOGIN_IDS.txt                             # Local-only department/admin demo credentials; do not publish
├── startup.txt                                    # Short two-terminal startup reference
├── render.yaml                                    # Render backend Blueprint
├── .gitignore                                     # Excludes secrets, runtime DBs, dependencies, caches and builds
│
├── docs/                                          # README visual assets and documentation media
│   ├── banner.svg                                 # Animated project title / racing banner
│   ├── carverse-command-centre-hero.png           # Premium automotive command-centre hero visual
│   ├── carverse_architecture.png                  # Colour system architecture diagram
│   ├── carverse_workflow.png                      # Colour 12-stage dealership race workflow
│   └── impact_footer.svg                          # Animated impact-line footer visual
│
├── carverse files/                                # Original organizer-provided data exports — preserve untouched
│
├── backend/                                       # FastAPI service and game authority
│   ├── .env.example                               # Safe backend configuration template
│   ├── requirements.txt                           # Pinned Python runtime/test dependencies
│   ├── Procfile                                   # Production Uvicorn start command
│   ├── pytest.ini                                 # Pytest configuration and full-data marker
│   ├── README.md                                  # Backend lifecycle, endpoint, deployment and phase documentation
│   ├── data/                                      # Byte-for-byte organizer CSV copies and disposable local SQLite runtime DB
│   │   ├── z_locations.csv                        # 41 locations
│   │   ├── z_employees.csv                        # 6,037 employee records
│   │   ├── z_event_log_may_june_2026.csv          # 170,162 dealership event records
│   │   └── README.md                              # Data provenance and lifecycle note
│   ├── app/
│   │   ├── main.py                                # FastAPI app, lifespan, middleware, router registration
│   │   ├── api/
│   │   │   ├── health.py                          # Public readiness endpoint
│   │   │   └── v1/                                # Versioned HTTP/WebSocket endpoints
│   │   │       ├── auth.py                        # Employee ID + OTP JWT login
│   │   │       ├── users.py                       # Current user and profile statistics
│   │   │       ├── leaderboards.py                # Individual, branch and department boards
│   │   │       ├── bookings.py                    # Active work queue and booking race details
│   │   │       ├── quests.py                      # Verified mission retrieval and claiming
│   │   │       ├── boss_battles.py                # Boss battle progress and reward claims
│   │   │       ├── demo.py                        # Development-only interactive demo actions
│   │   │       ├── ai.py                          # Safe AI flavour endpoints
│   │   │       ├── admin.py                       # Admin anomaly, reingestion and scoring controls
│   │   │       ├── ws.py                          # Authenticated realtime leaderboard WebSocket
│   │   │       └── router.py                      # `/api/v1` route composition
│   │   ├── core/
│   │   │   ├── config.py                          # Pydantic environment configuration
│   │   │   ├── security.py                        # JWT and role authorization
│   │   │   ├── scoring_rules.py                   # 19 inspectable canonical scoring rules
│   │   │   └── state_machine.py                   # Booking lifecycle, ownership and progress rules
│   │   ├── db/
│   │   │   ├── session.py                         # Async database engine and sessions
│   │   │   └── models/                            # SQLAlchemy models: employee, booking, ledger, game state, operations
│   │   ├── seed/                                  # Source CSV ingestion and game/badge seed data
│   │   ├── services/                              # Domain services: scoring, booking, quest, boss, AI, anomaly, notification
│   │   └── scheduler/                             # Nightly / weekly lifecycle jobs
│   └── tests/                                    # Fast fixtures, contract tests, scoring tests and full-data audit tests
│
└── frontend/                                      # React/Vite game experience
    ├── .env.example                               # API and WebSocket base URL template
    ├── package.json                               # Frontend scripts and dependencies
    ├── vite.config.ts                             # Vite configuration
    ├── README.md                                  # Frontend routes and integration contract
    ├── index.html                                 # Vite document entry
    ├── src/
    │   ├── main.tsx                               # React bootstrap and global providers
    │   ├── App.tsx                                # Public/protected routes and motion configuration
    │   ├── assets/                                # Product imagery used by the UI
    │   ├── lib/                                   # Environment resolution and shared API client
    │   ├── types/                                 # API contracts used by the UI
    │   ├── styles/                                # Global, theme and readability styles
    │   ├── shared/                                # Page motion and not-found experience
    │   └── features/
    │       ├── auth/                              # Readiness gate, login and tab-scoped session state
    │       ├── dashboard/                         # Command centre, journey, shell and dashboard queries
    │       ├── gameplay/                          # Pit Wall, Race Track, leagues, missions and boss UI
    │       ├── enhancements/                      # Three.js garage, rewards, AI panels and profile drilldown
    │       ├── realtime/                          # WebSocket live feed and event-driven refresh
    │       ├── marketing/                         # Public animated brand story, Spline scene, steering wheel and F1 car
    │       ├── admin/                             # Protected anomaly and scoring management UI
    │       ├── theme/                             # Light/dark mode and preference persistence
    │       └── tv/                                # Authenticated rotating lobby / presentation display
    └── Landing page idea/                         # Original branding-page inspiration project retained as reference
```

## Where to make common changes

| If you need to… | Start here |
|---|---|
| Add or change a real scoring action | `backend/app/core/scoring_rules.py`, then scoring tests |
| Change a booking stage, owner, or order | `backend/app/core/state_machine.py` and `backend/app/api/v1/demo.py` |
| Add an authenticated backend endpoint | `backend/app/api/v1/`, then compose it in `router.py` and add API tests |
| Change XP materialization, ranks, badges, or progression | `backend/app/services/gamification_service.py` and related models/tests |
| Change booking race data | `backend/app/services/booking_service.py` and `backend/app/api/v1/bookings.py` |
| Change the player UI | the matching module under `frontend/src/features/` |
| Change frontend API integration | `frontend/src/lib/api.ts`, `frontend/src/types/api.ts`, and feature query modules |
| Change the public brand experience | `frontend/src/features/marketing/` |
| Change Driver Garage / visual reward behavior | `frontend/src/features/enhancements/ThreeGarage.tsx` and `GameEnhancements.tsx` |
| Update a demo script | `CARVERSE_FRONTEND_BACKEND_TEST_AND_DEMO_WORKFLOW.md` |
| Change local/deployment config | `backend/.env.example`, `frontend/.env.example`, and `render.yaml` |

## Important boundaries

- The **backend** is the sole authority for real XP, ranks, booking state, mission completion, boss progress, and admin actions.
- The **frontend** can animate and present data, store visual preferences/cosmetics locally, and invoke authenticated APIs—but must not create authoritative score logic.
- `carverse files/` remains the original organizer dataset; `backend/data/` is the verified deployment copy used by the seed pipeline.
- `backend/data/carverse.db`, virtual environments, `node_modules`, build outputs, logs, and caches are runtime artifacts and are intentionally ignored by Git.
