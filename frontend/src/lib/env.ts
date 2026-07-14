const apiBase = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const env = {
  apiBase: apiBase.replace(/\/$/, ''),
  wsBase: (import.meta.env.VITE_WS_BASE_URL ?? apiBase.replace(/^http/, 'ws')).replace(/\/$/, ''),
};
