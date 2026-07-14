import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Radio } from 'lucide-react';
import { env } from '../../lib/env';
import { useAuth } from '../auth/AuthContext';
import { LevelUpWatcher } from '../enhancements/LevelUpWatcher';
interface FeedEvent { type:string; payload:Record<string,unknown> }
export function LiveFeed(){const {session}=useAuth();const client=useQueryClient();const [events,setEvents]=useState<FeedEvent[]>([]);const [connected,setConnected]=useState(false);useEffect(()=>{if(!session)return;let socket:WebSocket|undefined,closed=false;const connect=()=>{socket=new WebSocket(`${env.wsBase}/ws/leaderboard?token=${encodeURIComponent(session.accessToken)}`);socket.onopen=()=>setConnected(true);socket.onmessage=e=>{try{const message=JSON.parse(e.data) as FeedEvent;if(message.type!=='connected'){setEvents(old=>[message,...old].slice(0,4));void client.invalidateQueries()}}catch{/* ignore */}};socket.onclose=()=>{setConnected(false);if(!closed)window.setTimeout(connect,3000)}};connect();return()=>{closed=true;socket?.close()}},[session,client]);return <>{events.length>0&&<aside className="live-feed"><span><Radio size={13} className={connected?'live-icon':''}/> LIVE VERIFIED UPDATE</span>{events.map((event,i)=><p key={`${event.type}-${i}`}>{event.type.replace(/_/g,' ')}<small>{String(event.payload.canonical_event??event.payload.department??'Authoritative update')}</small></p>)}</aside>}<LevelUpWatcher/></>}
