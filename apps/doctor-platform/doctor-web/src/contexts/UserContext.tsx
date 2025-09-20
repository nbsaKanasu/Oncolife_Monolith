import React, { createContext, useContext } from 'react';
import type { ReactNode } from 'react';

export interface ProfileData {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

interface UserContextType {
  profile: ProfileData | null;
  isLoading: boolean;
  error: string | null;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const useUser = () => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

interface UserProviderProps {
  children: ReactNode;
}

export const UserProvider: React.FC<UserProviderProps> = ({ children }) => {
  // Mock profile data that matches Navigation component expectations
  const profile: ProfileData = {
    first_name: 'Dr. John',
    last_name: 'Smith',
    email: 'dr.john.smith@clinic.com',
    id: 'doctor-1'
  };
  const isLoading = false;
  const error = null;

  const value: UserContextType = {
    profile,
    isLoading,
    error,
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
};
