import { useQuery } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { getUserStats } from '../dashboard/dashboardApi';
export function UserDrilldown({ userId, close }: { userId:string; close:()=>void }) { const token=useAuth().session!.accessToken; const user=useQuery({queryKey:['userStats',userId],queryFn:()=>getUserStats(token,userId)}); return <div className="drilldown" role="dialog" aria-modal="true"><button onClick={close} aria-label="Close profile"><X/></button><p className="eyebrow">PLAYER PROFILE</p><h2>{user.data?.name??'Loading player'}</h2><p>{user.data?.designation} · {user.data?.department}</p><div><strong>{user.data?.total_xp??'—'} XP</strong><strong>Level {user.data?.level??'—'}</strong><strong>{user.data?.reputation??'—'}/100 reputation</strong></div></div> }
