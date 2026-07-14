import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Gauge, RefreshCw } from 'lucide-react';
import type { PropsWithChildren } from 'react';
import { healthCheck } from './authApi';

export function ReadinessGate({ children }: PropsWithChildren) {
  const readiness = useQuery({ queryKey: ['health'], queryFn: healthCheck, retry: 4, retryDelay: attempt => Math.min(1_000 * 2 ** attempt, 12_000), refetchInterval: query => query.state.status === 'success' ? false : 8_000 });
  if (readiness.isSuccess) return <>{children}</>;
  return <main className="readiness"><motion.div initial={{ opacity: 0, scale: .95 }} animate={{ opacity: 1, scale: 1 }} className="readiness-card"><span className="readiness-orbit"><Gauge size={27} /></span><p className="eyebrow">PREPARING THE GRID</p><h1>Warming up<br />CarVerse Drive.</h1><p>The dealership data is being readied for your session. This can take a moment after the service wakes up.</p>{readiness.isError && <button className="button button--primary" onClick={() => void readiness.refetch()}><RefreshCw size={15} /> Try again</button>}<span className="readiness-status">{readiness.isError ? 'CONNECTION RETRY NEEDED' : 'VERIFYING BACKEND READINESS'}</span></motion.div></main>;
}
