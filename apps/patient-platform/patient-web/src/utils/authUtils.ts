/**
 * Authentication utilities for handling environment-based auth
 */

import { PATIENT_STORAGE_KEYS } from './storageKeys';

// Helper to determine if we should use localStorage (dev) or rely on cookies (prod)
export const shouldUseLocalStorage = (): boolean => {
  return import.meta.env.DEV || import.meta.env.MODE === 'development';
};

// Helper to get auth headers based on environment
export const getAuthHeaders = (): Record<string, string> => {
  if (shouldUseLocalStorage()) {
    const token = localStorage.getItem(PATIENT_STORAGE_KEYS.authToken);
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }
  return {}; // No Authorization header in production (uses cookies)
};

// Helper to get auth token for WebSocket connections
export const getWebSocketToken = (): string | null => {
  if (shouldUseLocalStorage()) {
    return localStorage.getItem(PATIENT_STORAGE_KEYS.authToken);
  }
  // Try to read authToken cookie on the client as a best-effort (may be HTTP-only and thus inaccessible)
  try {
    const cookies = document.cookie || '';
    const match = cookies.match(/(?:^|;\s*)authToken=([^;]+)/);
    if (match && match[1]) {
      return decodeURIComponent(match[1]);
    }
  } catch {
    // ignore
  }
  // Fallback placeholder; proxy will inject Authorization from cookie
  return 'ws-cookie-auth';
};

// Helper to check if user is authenticated based on environment
export const isAuthenticated = (): boolean => {
  if (shouldUseLocalStorage()) {
    return !!localStorage.getItem(PATIENT_STORAGE_KEYS.authToken);
  }
  // In production, let API calls validate auth via cookies
  return true;
};
