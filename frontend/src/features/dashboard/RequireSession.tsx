import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export function RequireSession() { return useAuth().session ? <Outlet /> : <Navigate to="/login" replace />; }
