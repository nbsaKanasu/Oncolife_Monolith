import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { useLogin, useCompleteNewPassword } from '../services/login';
import type { CompleteNewPasswordResponse, LoginResponse } from '../services/login';
import { SESSION_START_KEY } from '@oncolife/ui-components';
import { DOCTOR_STORAGE_KEYS } from '../utils/storageKeys';

interface User {
  email: string;
  name?: string;
  role?: string;
  userType: 'doctor';
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  userType: 'doctor';
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
  const [token, setToken] = useState<string | null>(localStorage.getItem(DOCTOR_STORAGE_KEYS.authToken));
  const [isLoading, setIsLoading] = useState(true);
  const [isPasswordChangeRequired, setIsPasswordChangeRequired] = useState(false);
  const loginMutation = useLogin();
  const completeNewPasswordMutation = useCompleteNewPassword();

  const isAuthenticated = !!token;

  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem(DOCTOR_STORAGE_KEYS.authToken);
      if (storedToken) {
        // TODO: Verify token with backend
        setToken(storedToken);
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const authenticateLogin = async (email: string, password: string) => {
    try {
      const result = await loginMutation.mutateAsync({ email, password });
      
      if (result.success) {
        setUser({email: email, userType: 'doctor'});
        
        // Update token state - set token directly from response data
        if (result.data?.session) {
          setToken(result.data.session);
        } else if (result.data?.tokens?.id_token) {
          setToken(result.data.tokens.id_token);
        } else {
          // Fallback: check localStorage after a brief delay
          setTimeout(() => {
            const stored = localStorage.getItem(DOCTOR_STORAGE_KEYS.authToken);
            if (stored) setToken(stored);
          }, 100);
        }
        
        sessionStorage.setItem(SESSION_START_KEY, Date.now().toString());
        if (result.data?.requiresPasswordChange) {
          setIsPasswordChangeRequired(true);
        }
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
    localStorage.removeItem(DOCTOR_STORAGE_KEYS.authToken);
    localStorage.removeItem(DOCTOR_STORAGE_KEYS.refreshToken);
    sessionStorage.removeItem(SESSION_START_KEY);
    setToken(null);
    setUser(null);
    setIsPasswordChangeRequired(false);
  };

  const value: AuthContextType = {
    user,
    token,
    userType: 'doctor',
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