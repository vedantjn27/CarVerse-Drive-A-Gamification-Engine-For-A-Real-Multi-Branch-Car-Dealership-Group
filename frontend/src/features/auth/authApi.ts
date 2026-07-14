import { api } from '../../lib/api';
import type { HealthResponse, LoginResponse } from '../../types/api';

export const healthCheck = () => api<HealthResponse>('/health');
export const login = (employee_id: string, otp: string) => api<LoginResponse>('/api/v1/auth/login', { method: 'POST', body: JSON.stringify({ employee_id, otp }) });
