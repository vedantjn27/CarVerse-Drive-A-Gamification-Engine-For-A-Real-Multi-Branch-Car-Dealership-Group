/**
 * Local development stays self-contained. Production builds use the deployed
 * Render API unless Vercel supplies an explicit VITE_API_BASE_URL override.
 * WebSocket URLs are derived from the selected HTTP origin, so HTTPS becomes
 * secure WSS automatically.
 */
const LOCAL_API_BASE = 'http://localhost:8000';
const PRODUCTION_API_BASE = 'https://carverse-drive-a-gamification-engine-for.onrender.com';
const configuredApiBase = import.meta.env.VITE_API_BASE_URL?.trim();
const apiBase = configuredApiBase || (import.meta.env.PROD ? PRODUCTION_API_BASE : LOCAL_API_BASE);
const configuredWsBase = import.meta.env.VITE_WS_BASE_URL?.trim();

export const env = {
  apiBase: apiBase.replace(/\/$/, ''),
  wsBase: (configuredWsBase || apiBase.replace(/^http/, 'ws')).replace(/\/$/, ''),
};
