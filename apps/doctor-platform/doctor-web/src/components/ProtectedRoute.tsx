import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * ProtectedRoute component that provides route-level authentication protection.
 * This is a security-first approach that prevents unauthorized access at the routing level,
 * rather than relying solely on API-level protection.
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // While loading, don't render anything to avoid flash of protected content
  if (isLoading) {
    return null; // or a loading spinner if preferred
  }

  // If not authenticated, redirect to login immediately
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If authenticated, render the protected content
  return <>{children}</>;
};

export default ProtectedRoute;
