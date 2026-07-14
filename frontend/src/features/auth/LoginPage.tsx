import { useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ArrowLeft, ArrowRight, KeyRound, LoaderCircle, ShieldCheck } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { ApiError } from '../../lib/api';
import { FormulaCar } from '../marketing/FormulaCar';
import { useAuth } from './AuthContext';
import { login } from './authApi';

export function LoginPage() {
  const { session, saveSession } = useAuth();
  const navigate = useNavigate();
  const [employeeId, setEmployeeId] = useState('');
  const [otp, setOtp] = useState('');
  const [error, setError] = useState<string | null>(null);
  const mutation = useMutation({ mutationFn: () => login(employeeId.trim(), otp.trim()), onSuccess: result => { saveSession({ accessToken: result.access_token, employeeId: result.employee_id, role: result.role, expiresAt: Date.now() + result.expires_in_seconds * 1000 }); navigate('/app'); }, onError: cause => setError(cause instanceof ApiError && cause.status === 401 ? 'Invalid employee ID or OTP.' : 'Unable to sign in right now. Please try again.') });
  if (session) return <Navigate to="/app" replace />;
  function submit(event: FormEvent) { event.preventDefault(); setError(null); if (!employeeId.trim() || !otp.trim()) { setError('Enter both your employee ID and OTP.'); return; } mutation.mutate(); }
  return <main className="login-page"><section className="login-visual"><Link to="/" className="brand"><span className="brand-mark">CV</span><span>CARVERSE<span className="brand-dot">.</span></span></Link><div className="login-race"><div className="login-line" /><FormulaCar /><span>ACCESSING THE GRID</span></div><div className="login-quote"><p>“Every verified milestone<br />moves the <em>whole team</em>.”</p><span>CARVERSE DRIVE / SECURE ACCESS</span></div></section><section className="login-panel"><Link className="back-link" to="/"><ArrowLeft size={15} /> Back to CarVerse</Link><motion.div initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} className="login-card"><span className="feature-icon"><KeyRound size={20} /></span><p className="eyebrow">TEAM MEMBER ACCESS</p><h1>Enter the<br /><em>grid.</em></h1><p className="login-copy">Use your dealership employee credentials to continue to your performance command centre.</p><form onSubmit={submit} noValidate><label>Employee ID<input value={employeeId} onChange={event => setEmployeeId(event.target.value)} autoComplete="username" maxLength={32} placeholder="e.g. BAA6879" disabled={mutation.isPending} /></label><label>OTP / PIN<input value={otp} onChange={event => setOtp(event.target.value)} autoComplete="current-password" inputMode="numeric" maxLength={32} type="password" placeholder="Your secure OTP" disabled={mutation.isPending} /></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="button button--primary login-submit" disabled={mutation.isPending}>{mutation.isPending ? <LoaderCircle className="spin" size={17} /> : <>Enter command centre <ArrowRight size={17} /></>}</button></form><p className="login-security"><ShieldCheck size={14} /> Session is secured for this browser tab only.</p></motion.div></section></main>;
}
