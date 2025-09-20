import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { useLogin, useCompleteNewPassword } from '../services/login';
import type { CompleteNewPasswordResponse, LoginResponse } from '../services/login';
import { SESSION_START_KEY } from '@oncolife/ui-components';
import { useQueryClient } from '@tanstack/react-query';
import { fetchProfile } from '../services/profile';
import { shouldUseLocalStorage } from '../utils/authUtils';
import { PATIENT_STORAGE_KEYS } from '../utils/storageKeys';

interface User {
  email: string;
  name?: string;
  role?: string;
  userType: 'patient';
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  userType: 'patient';
  isAuthenticated: boolean;
  isLoading: boolean;
  isPasswordChangeRequired: boolean;
  authenticateLogin: (email: string, password: string) => Promise<LoginResponse>;
  logout: () => void;
  completeNewPassword: (email: string, newPassword: string,) => Promise<CompleteNewPasswordResponse>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

// Storage keys are now imported from tokenCleanup utility

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    shouldUseLocalStorage() ? localStorage.getItem(PATIENT_STORAGE_KEYS.authToken) : null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isPasswordChangeRequired, setIsPasswordChangeRequired] = useState(false);
  const [isAuthenticatedViaApi, setIsAuthenticatedViaApi] = useState(false);
  const loginMutation = useLogin();
  const completeNewPasswordMutation = useCompleteNewPassword();
  const queryClient = useQueryClient();

  // In development, check localStorage; in production, validate via API calls
  const isAuthenticated = shouldUseLocalStorage() ? !!token : isAuthenticatedViaApi;

  useEffect(() => {
    const initializeAuth = async () => {
      if (shouldUseLocalStorage()) {
        // Development: Check localStorage
        const storedToken = localStorage.getItem(PATIENT_STORAGE_KEYS.authToken);
        if (storedToken) {
          // TODO: Verify token with backend
          setToken(storedToken);
        }
      }
      
      // Always try to prefetch profile (works in both dev and prod)
      // This will validate authentication via API call
      try {
        await queryClient.fetchQuery({ queryKey: ['profile'], queryFn: fetchProfile });
        // If profile fetch succeeds, user is authenticated
        setIsAuthenticatedViaApi(true);
      } catch (error) {
        // If profile fetch fails, user is not authenticated
        setIsAuthenticatedViaApi(false);
        if (shouldUseLocalStorage()) {
          setToken(null);
        }
      }
      
      setIsLoading(false);
    };

    initializeAuth();
  }, [queryClient]);

  const authenticateLogin = async (email: string, password: string) => {
    try {
      const result = await loginMutation.mutateAsync({ email, password });
      
      if (result.success) {
        setUser({email: email, userType: 'patient'});
        
        // Update token state based on environment
        if (shouldUseLocalStorage()) {
          // Set token directly from response data
          if (result.data?.session) {
            setToken(result.data.session);
          } else if (result.data?.tokens?.access_token) {
            setToken(result.data.tokens.access_token);
          } else {
            // Fallback: check localStorage after a brief delay
            setTimeout(() => {
              const stored = localStorage.getItem(PATIENT_STORAGE_KEYS.authToken);
              if (stored) setToken(stored);
            }, 100);
          }
        } else {
          // In production, we don't track token state (handled by cookies)
          setIsAuthenticatedViaApi(true);
        }
        
        sessionStorage.setItem(SESSION_START_KEY, Date.now().toString());
        if (result.data?.requiresPasswordChange) {
          setIsPasswordChangeRequired(true);
        }
        // Refresh and prefetch profile immediately so the sidebar shows name/initials
        await queryClient.invalidateQueries({ queryKey: ['profile'] });
        try {
          await queryClient.fetchQuery({ queryKey: ['profile'], queryFn: fetchProfile });
        } catch {}
        return result;
      } else {
        // Include error code in thrown error for UI to parse
        throw new Error(result.error);
      }
    } catch (error: any) {
      // If error from backend, try to include error code
      if (error?.message) {
        throw error;
      }
      throw new Error('Login failed');
    }
  };

  const completeNewPassword = async (email: string, newPassword: string) => {
    try {
      const result = await completeNewPasswordMutation.mutateAsync({ email, newPassword });
      return result;
    } catch (error) {
      throw new Error('New password reset failed');
    }
  };

  const logout = () => {
    // Always clear localStorage (for development and backward compatibility)
    localStorage.removeItem(PATIENT_STORAGE_KEYS.authToken);
    localStorage.removeItem(PATIENT_STORAGE_KEYS.refreshToken);
    sessionStorage.removeItem(SESSION_START_KEY);
    setToken(null);
    setUser(null);
    setIsAuthenticatedViaApi(false);
    queryClient.removeQueries({ queryKey: ['profile'] });
    // In production, cookies are cleared by the server via the logout endpoint
  };

  const value: AuthContextType = {
    user,
    token,
    userType: 'patient',
    isAuthenticated,
    isPasswordChangeRequired,
    isLoading,
    authenticateLogin,
    completeNewPassword,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 