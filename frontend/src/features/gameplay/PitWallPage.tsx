import { motion } from 'framer-motion';
import { CarFront, CheckCircle2, CircleDot, Flag, Gauge, Handshake, Play, ShieldCheck, Sparkles, Target, Trophy } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth/AuthContext';
import { AchievementCinematic, awardNextCosmetic } from '../enhancements/GameEnhancements';
import { completeDemoAction, completeRoleWork, demoCheckIn, getActiveBookings, getBoard, getBosses, getProfile, getQuests, getServerStatus, getWorkstation } from '../dashboard/dashboardApi';
import './pit-wall.css';

const focusKey = (id: string) => `carverse.focus-mission.${id}`;
const rallyKey = (id: string) => `carverse.rally.${id}`;
const nextOwner: Record<string, string> = { BOOKING_CREATED:'SALES', DOCUMENT_SET_COMPLETED:'SALES', DISCOUNT_APPROVED:'FINANCE', FINANCE_APPROVED:'ACCOUNTS', INVOICE_APPROVED:'ACCOUNTS', GATEPASS_ISSUED:'CUSTOMER CARE', INSURANCE_APPROVED:'RTO / REGN TEAM', RTO_REGISTRATION_COMPLETED:'PDI', PDI_COMPLETED:'PDI', DISPATCHED:'SALES' };

export function PitWallPage() {
  const { session } = useAuth();
  const token = session!.accessToken;
  const [focus, setFocus] = useState(() => localStorage.getItem(focusKey(session!.employeeId)) ?? '');
  const [rally, setRally] = useState(() => localStorage.getItem(rallyKey(session!.employeeId)) === 'true');
  const [replaying, setReplaying] = useState(false);
  const [celebration, setCelebration] = useState('');
  const [artifact, setArtifact] = useState<string | null>(null);
  const client = useQueryClient();
  const profile = useQuery({ queryKey:['profile'], queryFn:()=>getProfile(token) });
  const quests = useQuery({ queryKey:['quests'], queryFn:()=>getQuests(token) });
  const bookings = useQuery({ queryKey:['pitBookings', profile.data?.department], queryFn:()=>getActiveBookings(token, profile.data?.department ?? undefined), enabled: !!profile.data?.department });
  const bosses = useQuery({ queryKey:['bosses'], queryFn:()=>getBosses(token) });
  const league = useQuery({ queryKey:['pitLeague'], queryFn:()=>getBoard(token,'individual','week') });
  const workstation = useQuery({ queryKey:['workstation'], queryFn:()=>getWorkstation(token) });
  const server = useQuery({ queryKey:['server-status'], queryFn:getServerStatus, refetchInterval:15_000 });
  const mission = useMemo(() => quests.data?.quests.find(item => item.code === focus) ?? quests.data?.quests.find(item => !item.claimed), [focus, quests.data]);
  const pitStop = bookings.data?.entries.find(item => nextOwner[item.current_stage] === profile.data?.department);
  const boss = bosses.data?.battles.find(item => item.department === profile.data?.department) ?? bosses.data?.battles[0];
  const rank = profile.data?.all_time_rank;
  const ahead = league.data?.entries.find(item => Number(item.rank) === Number(rank ?? 0) - 1);
  const setMission = (code: string) => { setFocus(code); localStorage.setItem(focusKey(session!.employeeId), code); };
  const joinRally = () => { setRally(true); localStorage.setItem(rallyKey(session!.employeeId),'true'); };
  useEffect(()=>{const marker=server.data?.process_started_at;if(!marker)return;const key=`carverse.rally.server.${session!.employeeId}`;const prior=localStorage.getItem(key);if(prior&&prior!==marker){setRally(false);localStorage.removeItem(rallyKey(session!.employeeId))}localStorage.setItem(key,marker)},[server.data?.process_started_at,session]);
  const celebrate = (title: string) => { const next = awardNextCosmetic(session!.employeeId); setArtifact(next); setCelebration(title); void client.invalidateQueries(); };
  const complete = useMutation({ mutationFn: () => completeDemoAction(token, pitStop!.location_code, pitStop!.enquiry_no), onSuccess: result => celebrate(`+${result.points} XP · ${result.canonical_event.replace(/_/g, ' ')}`) });
  const checkIn = useMutation({ mutationFn: () => demoCheckIn(token), onSuccess: result => celebrate(`+${result.points} XP · Daily shift check-in`) });
  const roleWork = useMutation({ mutationFn: () => completeRoleWork(token), onSuccess: result => celebrate(`+${result.points} XP · ${result.title}`) });
  useEffect(() => { if (!replaying) return; const timer = window.setTimeout(() => { setReplaying(false); setCelebration('Verified race replay complete'); }, 1700); return () => window.clearTimeout(timer); }, [replaying]);

  return <main className="app-page pit-page">
    <header className="pit-header"><div><p className="eyebrow">PLAYER MODE / VERIFIED WORK ONLY</p><h1>Own your <em>next move.</em></h1><p>Your clicks set focus and reveal the playbook. XP, rank, and rewards move only when the dealership data verifies real work.</p></div><div className="shift-chip"><Gauge size={17}/><span>SHIFT BRIEFING</span><strong>Level {profile.data?.level ?? '—'}</strong></div></header>
    <section className="pit-brief-grid">
      <article className="pit-card pit-card--lead"><span className="pit-label"><Target size={15}/> MY NEXT MOVE</span><h2>{mission?.title ?? 'Choose a focus mission'}</h2><p>{mission ? `${mission.progress}/${mission.target_count} verified actions. ${mission.description}` : 'Pick an eligible mission. Selecting it never grants XP.'}</p><div className="pit-progress"><span style={{width:`${Math.min(100,(mission?.progress ?? 0)/Math.max(1,mission?.target_count ?? 1)*100)}%`}}/></div><div className="mission-pills">{quests.data?.quests.filter(item=>!item.claimed).slice(0,3).map(item=><button key={item.code} className={item.code===mission?.code?'active':''} onClick={()=>setMission(item.code)}>{item.title}</button>)}</div></article>
      <article className="pit-card"><span className="pit-label"><CarFront size={15}/> PIT STOP</span><h2>{workstation.data?.mode === 'OPERATIONS' ? workstation.data.title : pitStop ? pitStop.enquiry_no : 'No action waiting for your team'}</h2><p>{workstation.data?.mode === 'OPERATIONS' ? workstation.data.description : pitStop ? `${pitStop.current_stage.replace(/_/g,' ')} · ${pitStop.progress_percent}% complete · ${pitStop.location_code}` : 'All active bookings are waiting for another department. Return when a verified handoff reaches your lane.'}</p>{workstation.data?.mode === 'OPERATIONS'?<><button className="button button--primary" onClick={()=>roleWork.mutate()} disabled={roleWork.isPending}>{roleWork.isPending?'Verifying…':'Complete department handoff'}</button>{roleWork.error&&<small className="pit-error">{roleWork.error.message}</small>}</>:pitStop&&<><Link className="button button--ghost" to={`/app/race?department=${encodeURIComponent(profile.data?.department ?? '')}&location=${encodeURIComponent(pitStop.location_code)}&enquiry=${encodeURIComponent(pitStop.enquiry_no)}`}>Open this race track <Flag size={14}/></Link><button className="button button--primary" onClick={()=>complete.mutate()} disabled={complete.isPending}>{complete.isPending?'Verifying…':'Complete next demo action'}</button>{complete.error&&<small className="pit-error">{complete.error.message}</small>}</>}</article>
      <article className="pit-card"><span className="pit-label"><Trophy size={15}/> NEAR MISS</span><h2>{ahead ? `Catch ${String(ahead.name ?? ahead.user_id)}` : 'Hold your position'}</h2><p>{ahead ? 'A verified milestone can change the weekly grid. No clicks change standings.' : 'Your league position is calculated from verified events.'}</p><Link className="text-link" to="/app/leagues">View live league →</Link></article>
    </section>
    <section className="pit-card daily-checkin"><span className="pit-label"><CheckCircle2 size={15}/> ALL-DEPARTMENT SHIFT CHECK-IN</span><h2>Start the shift, protect the streak.</h2><p>Every active employee can demonstrate one capped daily check-in. It earns only the existing 2-XP daily-login rule; meaningful score comes from verified booking milestones.</p><button className="button button--ghost" onClick={()=>checkIn.mutate()} disabled={checkIn.isPending}>{checkIn.isPending?'Checking in…':'Record daily check-in'}</button>{checkIn.error&&<small className="pit-error">{checkIn.error.message}</small>}</section>
    <section className="pit-main-grid">
      <article className="pit-card race-replay-card"><span className="pit-label"><Play size={15}/> REAL-DATA SHIFT REPLAY</span><h2>Watch the verified chain.</h2><p>The car pauses at every department handoff before reaching delivery, making the shared workflow easy to narrate.</p><div className={`replay-track ${replaying?'is-replaying':''}`}><motion.div className="replay-car" animate={{left:replaying?['4%','25%','47%','68%','90%']:'4%'}} transition={{duration:4.8,times:[0,.2,.45,.7,1],ease:'easeInOut'}}><CarFront size={27}/></motion.div><span>SALES</span><span>FINANCE</span><span>ACCOUNTS</span><span>PDI</span><span>DELIVERY</span></div><button className="button button--primary" onClick={()=>setReplaying(true)} disabled={replaying}>{replaying?'Replaying verified events…':'Run shift replay'}</button></article>
      <article className="pit-card rally-card"><span className="pit-label"><Handshake size={15}/> TEAM RALLY</span><h2>{boss?.title ?? 'Department challenge'}</h2><p>{boss ? `${boss.progress}/${boss.target_count} verified milestones · ${boss.remaining} remaining.` : 'Team targets load from verified department activity.'}</p>{rally?<span className="rally-joined"><CheckCircle2 size={15}/> Rally joined — your verified contribution will count.</span>:<button className="button button--primary" onClick={joinRally}>Join the rally</button>}<small><ShieldCheck size={13}/> Joining changes no score; verified work does.</small></article>
    </section>
    <section className="pit-card garage-unlocks"><span className="pit-label"><Sparkles size={15}/> GARAGE & REPUTATION</span><h2>Unlock cosmetics through real milestones.</h2><div>{['First verified booking','Five clean handoffs','Department boss contributor','Delivery champion'].map((title,index)=><article key={title} className={Number(profile.data?.milestone_awards ?? 0)>index?'unlocked':''}><CircleDot size={17}/><strong>{title}</strong><small>{Number(profile.data?.milestone_awards ?? 0)>index?'Unlocked from verified performance':'Keep moving real bookings forward'}</small></article>)}</div></section>
    <section className="pit-card demo-story"><span className="pit-label"><Flag size={15}/> JUDGE DEMO STORYLINE</span><ol><li>Choose a mission and open a real pit stop.</li><li>Run the verified booking replay.</li><li>Show the resulting mission, boss battle, garage, and league impact.</li><li>Claim a completed mission reward from the Missions page.</li></ol></section>
    <AchievementCinematic title={celebration} artifact={artifact} open={!!celebration} onClose={()=>{setCelebration('');setArtifact(null)}}/>
  </main>;
}
