import { createContext, useCallback, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react';

export type UserRole = 'AGENT' | 'MANAGER' | 'ADMIN';

export interface Session {
  accessToken: string;
  employeeId: string;
  role: UserRole;
  expiresAt: number;
}

interface AuthContextValue {
  session: Session | null;
  saveSession: (session: Session) => void;
  clearSession: () => void;
}

const STORAGE_KEY = 'carverse.session';
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredSession(): Session | null {
  try {
    const parsed = JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? 'null') as Session | null;
    return parsed && parsed.expiresAt > Date.now() ? parsed : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, setSession] = useState<Session | null>(readStoredSession);
  const saveSession = useCallback((next: Session) => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setSession(next);
  }, []);
  const clearSession = useCallback(() => {
    sessionStorage.removeItem(STORAGE_KEY);
    setSession(null);
  }, []);
  useEffect(() => { window.addEventListener('carverse:unauthorized', clearSession); return () => window.removeEventListener('carverse:unauthorized', clearSession); }, [clearSession]);
  const value = useMemo(() => ({ session, saveSession, clearSession }), [session, saveSession, clearSession]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used within AuthProvider');
  return value;
}
