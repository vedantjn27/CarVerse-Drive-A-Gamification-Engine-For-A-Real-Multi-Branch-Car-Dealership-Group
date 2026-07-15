import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, DatabaseZap, ShieldCheck, SlidersHorizontal } from 'lucide-react';
import { useState } from 'react';
import { PageMotion } from '../../shared/PageMotion';
import { useAuth } from '../auth/AuthContext';
import { getAnomalies, reingest, resolveAnomaly, tuneRule } from '../dashboard/dashboardApi';
import { AnomalyExplanation } from '../enhancements/AiPanels';
import { AdminHierarchySimulation } from '../simulation/HierarchySimulator';

const events = ['BOOKING_CREATED', 'DOCUMENT_SET_COMPLETED', 'DISCOUNT_APPROVED', 'FINANCE_APPROVED', 'INVOICE_APPROVED', 'GATEPASS_ISSUED', 'INSURANCE_APPROVED', 'RTO_REGISTRATION_COMPLETED', 'PDI_COMPLETED', 'DISPATCHED', 'VEHICLE_DELIVERED', 'FAST_DELIVERY_BONUS', 'CLEAN_BOOKING_BONUS', 'CROSS_DEPT_ASSIST', 'ESCALATION_RESOLVED', 'CANCELLATION_SAVE', 'DAILY_LOGIN_STREAK', 'FOLLOW_UP_LOGGED'];

export function AdminPage() {
  const token = useAuth().session!.accessToken;
  const client = useQueryClient();
  const [event, setEvent] = useState(events[0]);
  const [xp, setXp] = useState('20');
  const [note, setNote] = useState<Record<number, string>>({});
  const [explain, setExplain] = useState<number | null>(null);
  const anomalies = useQuery({ queryKey: ['anomalies', 'open'], queryFn: () => getAnomalies(token) });
  const resolve = useMutation({ mutationFn: ({ id, text }: { id: number; text: string }) => resolveAnomaly(token, id, text), onSuccess: () => void client.invalidateQueries({ queryKey: ['anomalies'] }) });
  const rebuild = useMutation({ mutationFn: () => reingest(token), onSuccess: () => void client.invalidateQueries() });
  const rule = useMutation({ mutationFn: () => tuneRule(token, event, Number(xp)), onSuccess: () => void client.invalidateQueries() });
  const confirmRebuild = () => window.confirm('Rebuild all ephemeral live data from the supplied CSVs?') && rebuild.mutate();
  const confirmRule = () => window.confirm(`Apply ${xp} base XP to ${event} and rebuild?`) && rule.mutate();

  return <PageMotion><header className="page-title"><p className="eyebrow">ADMIN / HUMAN REVIEW REQUIRED</p><h1>Control the <em>grid.</em></h1><p>These actions affect the current disposable demo instance. Anomaly flags never apply automatic penalties.</p></header>
    <AdminHierarchySimulation />
    <section className="admin-grid"><article className="dash-card"><div className="card-heading"><span><DatabaseZap size={17} /> FULL DATA REBUILD</span></div><p>Reingest the supplied CSVs and regenerate deterministic scores, quests, battles, awards, and anomalies.</p><button className="button button--primary" onClick={confirmRebuild} disabled={rebuild.isPending}>{rebuild.isPending ? 'Rebuilding…' : 'Reingest & rebuild'}</button>{rebuild.data && <small>Completed: {Object.entries(rebuild.data).map(([key, value]) => `${key} ${value}`).join(' · ')}</small>}</article>
      <article className="dash-card"><div className="card-heading"><span><SlidersHorizontal size={17} /> BASE-XP TUNING</span></div><p>Only canonical base XP is configurable. Caps, cooldowns, and anti-gaming rules remain protected.</p><select value={event} onChange={entry => setEvent(entry.target.value)}>{events.map(item => <option key={item}>{item}</option>)}</select><input type="number" min="0" max="500" value={xp} onChange={entry => setXp(entry.target.value)} /><button className="button button--primary" onClick={confirmRule} disabled={rule.isPending || !xp}>Apply base XP</button></article></section>
    <section className="dash-card anomaly-card"><div className="card-heading"><span><AlertTriangle size={17} /> OPEN ANOMALY REVIEW</span><span>{anomalies.data?.reviews.length ?? 0} open</span></div>{anomalies.data?.reviews.map(item => <article className="anomaly" key={item.id}><div><strong>{item.metric.replace(/_/g, ' ')}</strong><span>{item.user_id} · {item.department} · z-score {item.z_score.toFixed(2)}</span><p>{item.explanation}</p><button className="text-link" onClick={() => setExplain(item.id)}>AI triage explanation</button>{explain === item.id && <AnomalyExplanation id={item.id} onClose={() => setExplain(null)} />}</div><div><textarea value={note[item.id] ?? ''} onChange={entry => setNote(old => ({ ...old, [item.id]: entry.target.value }))} placeholder="Human resolution note" /><button className="button button--ghost" disabled={!note[item.id]?.trim() || resolve.isPending} onClick={() => resolve.mutate({ id: item.id, text: note[item.id] })}><ShieldCheck size={14} /> Resolve</button></div></article>) ?? <p>Loading review queue…</p>}</section>
  </PageMotion>;
}
