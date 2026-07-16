import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ArrowRight, Flame, Gauge, Medal, Sparkles, Target, Trophy, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { PageMotion } from '../../shared/PageMotion';
import { getBoard, getBosses, getNudge, getProfile, getQuests } from './dashboardApi';
import { DriverGarage, PlayerCard } from '../enhancements/GameEnhancements';

const number = new Intl.NumberFormat('en-IN');
const entryText = (entry: Record<string, unknown>, keys: string[]) => keys.map(key => entry[key]).find(value => typeof value === 'string') as string | undefined;

export function DashboardPage() {
  const token = useAuth().session!.accessToken;
  const profile = useQuery({ queryKey: ['profile'], queryFn: () => getProfile(token) });
  const nudge = useQuery({ queryKey: ['nudge'], queryFn: () => getNudge(token), retry: false });
  const leaders = useQuery({ queryKey: ['leaders', 'all'], queryFn: () => getBoard(token, 'individual', 'all') });
  const bosses = useQuery({ queryKey: ['bosses'], queryFn: () => getBosses(token) });
  const quests = useQuery({ queryKey: ['quests'], queryFn: () => getQuests(token) });
  const user = profile.data;
  const levelProgress = user ? Math.min(100, Math.round((user.current_level_xp / Math.max(user.next_level_xp, 1)) * 100)) : 0;
  const activeQuest = quests.data?.quests.find(quest => !quest.claimed);
  const teamBoss = bosses.data?.battles.find(battle => battle.department === user?.department) ?? bosses.data?.battles[0];
  return <PageMotion><section className="dashboard-hero"><div><p className="eyebrow">COMMAND CENTRE / LIVE</p><h1>{user ? <>Ready to make<br />momentum, <em>{user.name?.split(' ')[0] ?? 'driver'}.</em></> : 'Loading your drive...'}</h1><p>Verified performance, made visible across every dealership handoff.</p></div><div className="hero-orb"><Gauge size={32} /><span>LEVEL<br /><strong>{user?.level ?? '—'}</strong></span></div></section>
    <section className="dashboard-grid dashboard-grid--stats"><Stat icon={Zap} label="TOTAL XP" value={user ? number.format(user.total_xp) : '—'} note={`${user?.leaderboard_xp ?? 0} competitive XP`} /><Stat icon={Flame} label="CURRENT STREAK" value={user ? `${user.current_streak} days` : '—'} note={`Best: ${user?.longest_streak ?? 0} days`} /><Stat icon={Medal} label="REPUTATION" value={user ? `${user.reputation}/100` : '—'} note="Clean work compounds" /></section>
    <section className="dashboard-grid dashboard-grid--main"><article className="dash-card xp-card"><div className="card-heading"><span><Sparkles size={17} /> YOUR PROGRESSION</span><Link to="/app/journey">Open journey <ArrowRight size={14} /></Link></div><h2>{user?.title ?? 'Calculating title'}</h2><p>Level {user?.level ?? '—'} · {number.format(user?.total_xp ?? 0)} lifetime XP</p><div className="progress-track"><motion.span initial={{ width: 0 }} animate={{ width: `${levelProgress}%` }} transition={{ type: 'spring', stiffness: 70, damping: 18 }} /></div><div className="progress-caption"><span>{number.format(user?.current_level_xp ?? 0)} XP into this level</span><span>{number.format(user?.next_level_xp ?? 0)} to next level</span></div></article><article className="dash-card coach-card"><div className="card-heading"><span>AI COACH / FLAVOUR</span><span className="coach-pulse" /></div><blockquote>{nudge.data?.text ?? 'Your coach is checking the latest verified performance.'}</blockquote><p>{nudge.data ? `${nudge.data.provider.toUpperCase()} · ${nudge.data.cached === 'true' ? 'CACHED' : 'LIVE'}` : 'OPTIONAL ENRICHMENT'}</p></article></section>
    <section className="dashboard-grid dashboard-grid--content"><article className="dash-card quest-card"><div className="card-heading"><span><Target size={17} /> NEXT MISSION</span><Link to="/app/quests">All missions <ArrowRight size={14} /></Link></div>{activeQuest ? <><h3>{activeQuest.title}</h3><p>{activeQuest.description}</p><div className="progress-track"><span style={{ width: `${Math.min(100, activeQuest.progress / Math.max(activeQuest.target_count, 1) * 100)}%` }} /></div><div className="progress-caption"><span>{activeQuest.progress} / {activeQuest.target_count} verified actions</span><strong>+{activeQuest.reward_xp} XP</strong></div></> : <p>All available missions have been claimed or are loading.</p>}</article><article className="dash-card boss-card"><div className="card-heading"><span><Trophy size={17} /> TEAM BOSS</span><Link to="/app/boss-battles">Battle view <ArrowRight size={14} /></Link></div>{teamBoss ? <><h3>{teamBoss.title}</h3><p>{teamBoss.department} · {teamBoss.canonical_event.replace(/_/g, ' ')}</p><div className="boss-bar"><motion.span initial={{ width: 0 }} animate={{ width: `${Math.min(100, teamBoss.progress / Math.max(teamBoss.target_count, 1) * 100)}%` }} /></div><div className="progress-caption"><span>{teamBoss.progress} / {teamBoss.target_count} toward target</span><strong>{teamBoss.remaining} remaining</strong></div></> : <p>Active battle status is loading.</p>}</article></section>
    <section className="dash-card leaderboard-card"><div className="card-heading"><span><Trophy size={17} /> ALL-TIME INDIVIDUAL LEAGUE</span><Link to="/app/leagues">Full leagues <ArrowRight size={14} /></Link></div><div className="leader-list">{leaders.data?.entries.map((entry, index) => <motion.div className="leader-row" layout key={String(entry.user_id ?? entry.employee_id ?? index)}><strong>0{String(entry.rank ?? index + 1)}</strong><span>{entryText(entry, ['name', 'user_id', 'employee_id']) ?? 'Verified competitor'}</span><small>{entryText(entry, ['department', 'location_code']) ?? ''}</small><b>{number.format(Number(entry.leaderboard_xp ?? 0))} XP</b></motion.div>) ?? <p>Loading the verified standings…</p>}</div></section><section className="enhancement-grid"><DriverGarage employeeId={user?.employee_id} /><PlayerCard profile={user} quests={quests.data}/></section>
  </PageMotion>;
}

function Stat({ icon: Icon, label, value, note }: { icon: typeof Zap; label: string; value: string; note: string }) { return <motion.article className="stat-card" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}><Icon size={17} /><p>{label}</p><strong>{value}</strong><span>{note}</span></motion.article>; }
