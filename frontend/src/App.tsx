import { AnimatePresence, MotionConfig } from 'framer-motion';
import { Route, Routes, useLocation } from 'react-router-dom';
import { LandingPage } from './features/marketing/LandingPage';
import { NotFoundPage } from './shared/NotFoundPage';
import { LoginPage } from './features/auth/LoginPage';
import { ReadinessGate } from './features/auth/ReadinessGate';
import { RequireSession } from './features/dashboard/RequireSession';
import { AppShell } from './features/dashboard/AppShell';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { JourneyPage } from './features/dashboard/JourneyPage';
import { LeaguesPage, RacePage } from './features/gameplay/GameplayPages';
import { BossBattlesPage, QuestsPage } from './features/gameplay/RewardPages';
import { AdminPage } from './features/admin/AdminPage';
import { RequireAdmin } from './features/admin/RequireAdmin';
import { TvPage } from './features/tv/TvPage';
import { PitWallPage } from './features/gameplay/PitWallPage';
import { HierarchySimulator } from './features/simulation/HierarchySimulator';
import { RaceControlPage } from './features/race-control/RaceControlPage';

export default function App() {
  const location = useLocation();

  return (
    <MotionConfig reducedMotion="user">
      <AnimatePresence mode="wait" initial={false}>
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<ReadinessGate><LoginPage /></ReadinessGate>} />
          <Route element={<RequireSession />}>
            <Route path="/app" element={<AppShell />}>
              <Route index element={<DashboardPage />} />
              <Route path="journey" element={<JourneyPage />} />
              <Route path="race" element={<RacePage />} />
              <Route path="leagues" element={<LeaguesPage />} />
              <Route path="quests" element={<QuestsPage />} />
              <Route path="boss-battles" element={<BossBattlesPage />} />
              <Route path="pit-wall" element={<PitWallPage />} />
              <Route path="hierarchy" element={<HierarchySimulator />} />
              <Route path="race-control" element={<RaceControlPage />} />
              <Route path="admin" element={<RequireAdmin><AdminPage /></RequireAdmin>} />
              <Route path="tv" element={<TvPage />} />
            </Route>
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AnimatePresence>
    </MotionConfig>
  );
}
