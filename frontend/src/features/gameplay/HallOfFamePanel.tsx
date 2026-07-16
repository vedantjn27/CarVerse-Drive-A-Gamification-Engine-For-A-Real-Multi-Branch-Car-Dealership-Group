import { AnimatePresence, motion } from 'framer-motion';
import { Award, Download, Medal, Sparkles, Trophy } from 'lucide-react';
import * as React from 'react';
import { useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import { playRewardSound } from '../enhancements/GameEnhancements';
import { exportLeaderboardPdf } from './leaderboardPdf';
import { usePresentationLeaderboard } from './usePresentationLeaderboard';
import './hall-of-fame.css';
import './hall-reveal.css';

const format = new Intl.NumberFormat('en-IN');
const name = (entry: Record<string, unknown>) => String(entry.name ?? entry.user_id ?? entry.location_name ?? entry.location_code ?? entry.department ?? 'Verified contender');
const score = (entry: Record<string, unknown>) => Number(entry.normalized_score ?? entry.leaderboard_xp ?? 0);
const sparks = Array.from({ length: 36 }, (_, index) => index);

function HallReveal({ open }: { open: boolean }) { return <AnimatePresence>{open && <motion.div className="hall-reveal" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>{sparks.map(index => <motion.i key={index} style={{ '--angle': `${index * 10}deg`, '--distance': `${95 + (index % 6) * 24}px`, background: index % 3 === 0 ? '#e9fb6b' : index % 3 === 1 ? '#38d6ff' : '#ffb74f' } as React.CSSProperties} initial={{ opacity: 1, scale: 0 }} animate={{ opacity: [1, 1, 0], scale: [0, 1, .25], rotate: index * 45 }} transition={{ duration: 1.25, delay: (index % 9) * .025 }}/>) }<motion.div initial={{ scale: .65, y: 22 }} animate={{ scale: 1, y: 0 }}><Trophy size={65}/><p>WEEKLY PODIUM REVEAL</p><strong>HALL OF FAME</strong></motion.div></motion.div>}</AnimatePresence>; }

export function HallOfFamePanel() {
  const session = useAuth().session!; const token = session.accessToken; const [kind, setKind] = useState<'individual' | 'branch' | 'department'>('individual'); const [reveal, setReveal] = useState(true);
  const individual = usePresentationLeaderboard(token, session.employeeId, session.expiresAt, 'individual'); const branches = usePresentationLeaderboard(token, session.employeeId, session.expiresAt, 'branch'); const departments = usePresentationLeaderboard(token, session.employeeId, session.expiresAt, 'department');
  useEffect(() => { void playRewardSound(); const timer = window.setTimeout(() => setReveal(false), 1450); return () => window.clearTimeout(timer); }, []);
  const board = kind === 'individual' ? individual.data : kind === 'branch' ? branches.data : departments.data; const champions = board?.entries.slice(0, 3) ?? [];
  return <section className="hall-of-fame"><HallReveal open={reveal}/><header><div><p className="eyebrow">WEEKLY FINISH LINE / VERIFIED PERFORMANCE</p><h2>Hall of <em>fame.</em></h2><p>Monitor the race all week, then celebrate the official podium holders once the period closes.</p></div><div className="hall-controls">{(['individual', 'branch', 'department'] as const).map(item => <button key={item} className={kind === item ? 'active' : ''} onClick={() => setKind(item)}>{item}</button>)}<button className="button button--primary" disabled={!board} onClick={() => board && exportLeaderboardPdf(board, kind)}><Download size={14}/> Share PDF</button></div></header><div className="hall-layout"><div className="hall-podium">{champions[1] && <Podium entry={champions[1]} rank={2}/>} {champions[0] && <Podium entry={champions[0]} rank={1}/>} {champions[2] && <Podium entry={champions[2]} rank={3}/>} {!champions.length && <p>Loading verified podium...</p>}</div><aside className="hall-honours"><p className="eyebrow">WEEKLY HONOURS</p><article><Award/><span>Fastest booking rescue<strong>{name(individual.data?.entries[0] ?? {})}</strong></span></article><article><Medal/><span>Best cross-team assist<strong>{name(departments.data?.entries[0] ?? {})}</strong></span></article><article><Sparkles/><span>Most improved branch<strong>{name(branches.data?.entries[1] ?? branches.data?.entries[0] ?? {})}</strong></span></article></aside></div><footer><Trophy size={15}/> The Hall of Fame is a recognition view: its champions come from the same authoritative, verified league data shown above.</footer></section>;
}
function Podium({ entry, rank }: { entry: Record<string, unknown>; rank: number }) { return <motion.article className={`hall-podium__place hall-podium__place--${rank}`} initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: rank * .1 }}><Trophy size={rank === 1 ? 62 : 43}/><span>#{rank}</span><strong>{name(entry)}</strong><b>{format.format(score(entry))}</b><small>{entry.normalized_score !== undefined ? 'NORMALIZED PACE' : 'VERIFIED XP'}</small></motion.article>; }
