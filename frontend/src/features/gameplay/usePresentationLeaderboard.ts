import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import type { Leaderboard } from '../../types/api';
import { getBoard } from '../dashboard/dashboardApi';

type BoardKind = 'individual' | 'branch' | 'department';
const key = (employeeId: string, sessionId: number, kind: BoardKind) => `carverse.presentation-board.${employeeId}.${sessionId}.${kind}`;

function stored(employeeId: string, sessionId: number, kind: BoardKind) {
  try { return JSON.parse(sessionStorage.getItem(key(employeeId, sessionId, kind)) ?? 'null') as Leaderboard | null; } catch { return null; }
}

/** A stable per-login display snapshot for presentation-only experiences. */
export function usePresentationLeaderboard(token: string, employeeId: string, sessionId: number, kind: BoardKind) {
  const [snapshot, setSnapshot] = useState<Leaderboard | null>(() => stored(employeeId, sessionId, kind));
  const query = useQuery({ queryKey: ['presentation-board-source', kind], queryFn: () => getBoard(token, kind, 'week') });
  useEffect(() => {
    if (snapshot || !query.data) return;
    sessionStorage.setItem(key(employeeId, sessionId, kind), JSON.stringify(query.data));
    setSnapshot(query.data);
  }, [employeeId, kind, query.data, sessionId, snapshot]);
  return { ...query, data: snapshot ?? query.data };
}
