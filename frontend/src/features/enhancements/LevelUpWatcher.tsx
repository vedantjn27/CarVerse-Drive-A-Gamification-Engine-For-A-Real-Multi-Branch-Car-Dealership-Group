import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import { getProfile } from '../dashboard/dashboardApi';
import { AchievementCinematic } from './GameEnhancements';

export function LevelUpWatcher(){const {session}=useAuth();const [celebration,setCelebration]=useState('');const profile=useQuery({queryKey:['profile'],queryFn:()=>getProfile(session!.accessToken),enabled:!!session});useEffect(()=>{if(!profile.data)return;const key=`carverse.level.${session!.employeeId}`;const previous=Number(localStorage.getItem(key)??profile.data.level);if(profile.data.level>previous)setCelebration(`Level ${profile.data.level} unlocked · ${profile.data.title}`);localStorage.setItem(key,String(profile.data.level))},[profile.data,session]);return <AchievementCinematic title={celebration} artifact="Champion trophy" open={!!celebration} onClose={()=>setCelebration('')}/>}
