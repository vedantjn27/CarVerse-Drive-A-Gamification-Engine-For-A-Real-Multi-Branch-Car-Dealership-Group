import { Navigate } from 'react-router-dom';
import type { PropsWithChildren } from 'react';
import { useAuth } from '../auth/AuthContext';
export function RequireAdmin({ children }: PropsWithChildren) { return useAuth().session?.role === 'ADMIN' ? <>{children}</> : <Navigate to="/app" replace />; }
