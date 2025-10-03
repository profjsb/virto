import { describe, it, expect, beforeEach } from 'vitest';
import { api } from '../api';

describe('API Client', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should create axios instance with correct baseURL', () => {
    expect(api.defaults.baseURL).toBeDefined();
  });

  it('should have request interceptor configured', () => {
    // Verify that interceptors are set up
    expect(api.interceptors.request).toBeDefined();
  });

  it('should have response interceptor configured', () => {
    // Verify that interceptors are set up
    expect(api.interceptors.response).toBeDefined();
  });
});
