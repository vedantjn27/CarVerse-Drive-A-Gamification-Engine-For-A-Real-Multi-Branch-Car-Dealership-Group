import { motion } from 'framer-motion';
import { ArrowUpRight, BriefcaseBusiness, Building2, CarFront, Crown, Network, Play, RotateCcw, Sparkles, Trophy, UserRound, UsersRound, Zap, type LucideIcon } from 'lucide-react';
import { useState, type CSSProperties } from 'react';
import { Navigate } from 'react-router-dom';
import { PageMotion } from '../../shared/PageMotion';
import { useAuth } from '../auth/AuthContext';
import './hierarchy.css';
import './hierarchy-explainer.css';

type RoleNode = { slot: string; title: string; name: string; reward: string; icon: LucideIcon; activeAt: number; tone?: string };
const particles = Array.from({ length: 26 }, (_, index) => index);
const hierarchy: RoleNode[] = [
  { slot: 'ceo', title: 'DEALERSHIP CEO', name: 'Aarav Mehta', reward: '+4 strategic XP', icon: Crown, activeAt: 3, tone: 'gold' },
  { slot: 'manager', title: 'REGIONAL MANAGER', name: 'Nisha Rao', reward: '+6 leadership XP', icon: BriefcaseBusiness, activeAt: 3, tone: 'cyan' },
  { slot: 'lead', title: 'FINANCE TEAM LEAD', name: 'Kabir Sethi', reward: '+8 rally XP', icon: UsersRound, activeAt: 3 },
  { slot: 'team-one', title: 'SQUAD MEMBER', name: 'Devika Singh', reward: '+10 shared XP', icon: UserRound, activeAt: 2, tone: 'cyan' },
  { slot: 'team-two', title: 'SQUAD MEMBER', name: 'Rohan Verma', reward: '+10 shared XP', icon: UserRound, activeAt: 2, tone: 'cyan' },
  { slot: 'team-three', title: 'SQUAD MEMBER', name: 'Isha Kapoor', reward: '+10 shared XP', icon: UserRound, activeAt: 2, tone: 'cyan' },
  { slot: 'team-four', title: 'SQUAD MEMBER', name: 'Yuvraj Nair', reward: '+10 shared XP', icon: UserRound, activeAt: 2, tone: 'cyan' },
  { slot: 'employee', title: 'VERIFIED FINANCE SPECIALIST', name: 'Mira Shah', reward: '+40 verified XP', icon: Trophy, activeAt: 1 },
];

function Confetti({ run }: { run: number }) { return <div className="hierarchy-confetti" key={run}>{particles.map(particle => <i key={particle} style={{ '--particle': particle } as CSSProperties} />)}</div>; }

function TreeNode({ node, step }: { node: RoleNode; step: number }) { const Icon = node.icon; const active = step >= node.activeAt; return <motion.article className={`hierarchy-node hierarchy-node--${node.slot} hierarchy-node--${node.tone ?? 'lime'}${active ? ' is-active' : ''}`} animate={active ? { y: [0, -6, 0], scale: [1, 1.045, 1] } : { y: 0, scale: 1 }} transition={{ duration: .65 }}><span className="hierarchy-node__icon"><Icon size={17} /></span><div><small>{node.title}</small><strong>{node.name}</strong><b>{active ? node.reward : 'Awaiting simulation'}</b></div>{active && <Sparkles className="hierarchy-node__spark" size={15} />}</motion.article>; }

export function HierarchySimulator() {
  const { session } = useAuth();
  const [step, setStep] = useState(0); const [run, setRun] = useState(0);
  const captions = ['Simulate employee win', 'Route squad contribution', 'Launch leadership cascade', 'Simulation complete'];
  const status = ['A verified Finance approval is ready to recognise.', 'Mira receives direct XP for the verified approval.', 'The four-person squad shares the momentum signal.', 'The achievement moves through lead, manager, and CEO.'];
  const reasons = ['No reward has been issued yet. The simulation is waiting for proof of the Finance approval.', 'Mira receives +40 XP because she completed the approval herself. Direct ownership earns the largest reward.', 'Each squad member receives +10 shared XP because the approval helps the team meet a common service goal. Their reward is smaller because they did not complete the approval directly.', 'Kabir, Nisha, and Aarav receive smaller recognition signals (+8, +6, and +4) because they enable the team through coaching, oversight, and support. Leadership recognition never replaces the employee reward.'];
  const carPosition = [{ top: '80%', left: '50%' }, { top: '80%', left: '50%' }, { top: '60%', left: '50%' }, { top: '11%', left: '50%' }][step];
  const total = step === 0 ? 0 : step === 1 ? 40 : step === 2 ? 80 : 98;
  const next = () => { if (step < 3) { setStep(value => value + 1); setRun(value => value + 1); } };
  const reset = () => { setStep(0); setRun(value => value + 1); };
  if (session?.role === 'ADMIN') return <Navigate to="/app/admin" replace />;
  return <PageMotion><main className="app-page hierarchy-page"><header className="page-title hierarchy-title"><div><p className="eyebrow">HIERARCHY SIMULATOR / VISUAL DEMO</p><h1>See momentum<br />travel <em>upward.</em></h1><p>See how a Finance win can become shared recognition across a dealership hierarchy. This presentation layer is simulated only and never writes real XP, rank, booking, or backend data.</p></div><div className="hierarchy-score"><Zap size={18}/><small>SIMULATED IMPACT</small><strong>+{total} XP</strong></div></header>
    <section className="hierarchy-stage"><div className="hierarchy-grid" /><div className="hierarchy-glow hierarchy-glow--blue" /><div className="hierarchy-glow hierarchy-glow--lime" />{step > 0 && <Confetti run={run} />}<div className="hierarchy-stage__label"><span><Network size={14}/> FINANCE / RECOGNITION ROUTE</span><span>SIMULATION 01 / 04</span></div><svg className="hierarchy-lines" viewBox="0 0 1000 680" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="hierarchy-path" x1="0" x2="0" y1="1" y2="0"><stop stopColor="#38d6ff"/><stop offset="1" stopColor="#e9fb6b"/></linearGradient></defs><path d="M500 565V470M500 470H200V390M500 470H400V390M500 470H600V390M500 470H800V390M500 340V265M500 215V140M500 90V45" fill="none" stroke="url(#hierarchy-path)" strokeWidth="2" strokeDasharray="7 9"/><path d="M500 565V45" fill="none" stroke="#e9fb6b" strokeWidth="3" opacity={step === 3 ? .85 : .08}/></svg><motion.div className="hierarchy-car" animate={step === 3 ? { top: ['80%', '60%', '48%', '31%', '11%'], left: ['50%', '50%', '50%', '50%', '50%'] } : carPosition} transition={step === 3 ? { duration: 3.2, times: [0, .27, .5, .75, 1], ease: 'easeInOut' } : { type: 'spring', stiffness: 90, damping: 16 }}><CarFront size={30}/><span>XP RUNNER</span></motion.div>{hierarchy.map(node => <TreeNode key={node.slot} node={node} step={step} />)}<div className="hierarchy-stage__rail"><span>VERIFIED ACTION</span><i /><span>DEALERSHIP MOMENTUM</span></div></section>
    <section className="hierarchy-controls"><div><p className="eyebrow">SIMULATION CONTROL</p><h2>{status[step]}</h2><p>Click through the sequence to demonstrate direct reward, squad recognition, then the animated leadership cascade. Every number here is illustrative only.</p></div><div><button className="button button--primary" disabled={step === 3} onClick={next}><Play size={15}/>{captions[step]}</button><button className="button button--ghost" onClick={reset}><RotateCcw size={15}/> Reset</button><small>NO LIVE XP · NO BACKEND WRITE</small></div></section>
    <aside className="hierarchy-explainer"><span><Sparkles size={17}/> WHY THIS XP?</span><div><strong>{step === 0 ? 'The rule is waiting for proof.' : step === 1 ? 'Direct work earns the strongest reward.' : step === 2 ? 'Teamwork is recognised, but proportionately.' : 'Leadership is rewarded for enablement, not for taking credit.'}</strong><p>{reasons[step]}</p></div><b>EXPLAINABLE REWARD LOGIC <ArrowUpRight size={14}/></b></aside>
  </main></PageMotion>;
}

const departments = [
  { slot: 'sales', name: 'Sales', task: 'Booking created', icon: Trophy }, { slot: 'finance', name: 'Finance', task: 'Credit approval', icon: BriefcaseBusiness }, { slot: 'accounts', name: 'Accounts', task: 'Invoice issued', icon: Building2 }, { slot: 'care', name: 'Customer Care', task: 'Insurance handoff', icon: UsersRound }, { slot: 'pdi', name: 'PDI', task: 'Vehicle ready', icon: CarFront },
];

export function AdminHierarchySimulation() {
  const [step, setStep] = useState(0); const [run, setRun] = useState(0); const labels = ['Start task relay', 'Award Finance contribution', 'Broadcast shared momentum', 'Relay complete'];
  return <section className="admin-hierarchy"><header><div><p className="eyebrow">ADMIN / ORGANISATION MOMENTUM MAP</p><h2>Watch a task become<br /><em>department momentum.</em></h2><p>A separate, presentation-only relay map. It demonstrates interconnected team recognition without touching operational records or real player scores.</p></div><span><Network size={24}/> SIMULATION</span></header><div className="admin-network"><div className="hierarchy-grid" />{step > 0 && <Confetti run={run} />}<svg viewBox="0 0 1000 460" preserveAspectRatio="none" aria-hidden="true"><path d="M130 290L350 155L500 250L650 155L870 290" fill="none" stroke="#3d5572" strokeWidth="2" strokeDasharray="7 8"/><path className="admin-network__signal" d="M130 290L350 155L500 250L650 155L870 290" fill="none" stroke="#e9fb6b" strokeWidth="3" pathLength="1" strokeDasharray="1" strokeDashoffset={step === 3 ? 0 : 1}/></svg><motion.div className="admin-network__car" animate={step === 3 ? { left: ['13%', '35%', '50%', '65%', '87%'] } : { left: step === 0 ? '13%' : step === 1 ? '35%' : '50%' }} transition={{ duration: step === 3 ? 3 : .55, ease: 'easeInOut' }}><CarFront size={27}/></motion.div>{departments.map((department, index) => { const Icon = department.icon; const active = step >= 2 && (index === 1 || step === 3); return <motion.article key={department.slot} className={`admin-department admin-department--${department.slot}${active ? ' is-active' : ''}`} animate={active ? { y: [0, -6, 0], scale: [1, 1.045, 1] } : { y: 0, scale: 1 }}><Icon size={22}/><strong>{department.name}</strong><small>{department.task}</small>{active && <b>{index === 1 ? '+30 XP signal' : '+10 shared signal'}</b>}</motion.article>; })}</div><footer><div><p className="eyebrow">RELAY CONTROL</p><strong>{step === 0 ? 'A Finance approval is ready to route.' : step === 1 ? 'Finance receives direct simulated recognition.' : step === 2 ? 'Connected departments see the shared signal.' : 'The task has travelled across the organisation.'}</strong></div><div><button className="button button--primary" disabled={step === 3} onClick={() => { setStep(value => value + 1); setRun(value => value + 1); }}><Play size={15}/>{labels[step]}</button><button className="button button--ghost" onClick={() => { setStep(0); setRun(value => value + 1); }}><RotateCcw size={15}/> Reset</button></div></footer></section>;
}
