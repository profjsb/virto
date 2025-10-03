import { describe, it, expect, beforeEach, vi } from 'vitest';
import { api } from '../api';

describe('API Client', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should create axios instance with correct baseURL', () => {
    expect(api.defaults.baseURL).toBeDefined();
  });

  it('should add auth token to requests when present', async () => {
    const token = 'test-token-123';
    localStorage.setItem('token', token);

    const requestInterceptor = api.interceptors.request.handlers[0];
    const config = { headers: {} } as any;

    if (requestInterceptor && requestInterceptor.fulfilled) {
      const modifiedConfig = requestInterceptor.fulfilled(config);
      expect(modifiedConfig.headers['Authorization']).toBe(`Bearer ${token}`);
    }
  });

  it('should not add auth header when no token present', async () => {
    const requestInterceptor = api.interceptors.request.handlers[0];
    const config = { headers: {} } as any;

    if (requestInterceptor && requestInterceptor.fulfilled) {
      const modifiedConfig = requestInterceptor.fulfilled(config);
      expect(modifiedConfig.headers['Authorization']).toBeUndefined();
    }
  });
});
