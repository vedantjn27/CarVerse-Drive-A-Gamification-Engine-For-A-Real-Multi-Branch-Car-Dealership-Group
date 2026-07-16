import { Gauge, GitBranch, LayoutDashboard, LogOut, Medal, MonitorPlay, Moon, Route, ShieldCheck, Sun, Target, Trophy, UserRound, Flag } from 'lucide-react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { LiveFeed } from '../realtime/LiveFeed';
import { useTheme } from '../theme/ThemeContext';
import { SoundControl } from '../enhancements/GameEnhancements';
import { usePresentationLeaderboard } from '../gameplay/usePresentationLeaderboard';

const nav = [{ to: '/app', label: 'Command centre', icon: LayoutDashboard, end: true }, { to: '/app/pit-wall', label: 'Pit wall', icon: Gauge }, { to: '/app/journey', label: 'My journey', icon: UserRound }, { to: '/app/race', label: 'Race track', icon: Route }, { to: '/app/leagues', label: 'Leagues', icon: Trophy }, { to: '/app/quests', label: 'Missions', icon: Target }, { to: '/app/boss-battles', label: 'Boss battles', icon: Medal }];

export function AppShell() {
  const { session, clearSession } = useAuth(); const navigate = useNavigate(); const { theme, toggle } = useTheme();
  usePresentationLeaderboard(session?.accessToken ?? '', session?.employeeId ?? 'anonymous', session?.expiresAt ?? 0, 'individual');
  usePresentationLeaderboard(session?.accessToken ?? '', session?.employeeId ?? 'anonymous', session?.expiresAt ?? 0, 'branch');
  usePresentationLeaderboard(session?.accessToken ?? '', session?.employeeId ?? 'anonymous', session?.expiresAt ?? 0, 'department');
  const visibleNav = session?.role === 'ADMIN' ? [...nav, { to:'/app/admin', label:'Admin controls', icon:ShieldCheck }] : [...nav, { to:'/app/race-control', label:'Race control', icon:Flag }, { to:'/app/hierarchy', label:'Hierarchy simulator', icon:GitBranch }];
  return <div className="app-shell"><aside className="sidebar"><Link to="/" className="brand"><span className="brand-mark">CV</span><span>CARVERSE<span className="brand-dot">.</span></span></Link><p className="sidebar-label">PERFORMANCE GRID</p><nav className="app-nav">{visibleNav.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} className={({ isActive }) => `app-nav-link${isActive ? ' active' : ''}`}><Icon size={17} />{label}</NavLink>)}</nav><div className="sidebar-footer"><span className="online-dot" /> Live backend connected</div></aside><div className="app-frame"><header className="app-topbar"><div><p className="breadcrumb">CARVERSE / PERFORMANCE OS</p><p className="topbar-name">{session?.employeeId}</p></div><div className="topbar-actions"><Link to="/app/tv" className="text-link"><MonitorPlay size={14}/> Lobby mode</Link><Link to="/" className="text-link">Branding page</Link><SoundControl/><button className="icon-button" onClick={toggle} aria-label="Toggle theme">{theme==='dark'?<Sun size={16}/>:<Moon size={16}/>}</button><button className="icon-button" onClick={() => { clearSession(); navigate('/login'); }} aria-label="Sign out"><LogOut size={17} /></button></div></header><Outlet /><LiveFeed /></div></div>;
}
