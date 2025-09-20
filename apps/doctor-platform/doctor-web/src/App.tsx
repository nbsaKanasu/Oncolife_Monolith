import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { GlobalStyles, SessionTimeoutManager } from '@oncolife/ui-components';
import { AuthProvider } from './contexts/AuthContext';
import { UserProvider } from './contexts/UserContext';
import { UserTypeProvider } from './contexts/UserTypeContext';
import { useAuth } from './contexts/AuthContext';
import { DOCTOR_STORAGE_KEYS } from './utils/storageKeys';

// Doctor-specific pages
import LoginPage from './pages/LoginPage';
import SignUpPage from './pages/SignUpPage';
import ForgotPassword from './pages/LoginPage/ForgotPassword';
import ResetPassword from './pages/LoginPage/ResetPassword';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardPage from './pages/Dashboard/DashboardPage';
import DashboardDetailsPage from './pages/Dashboard/DashboardDetailsPage';
import PatientsPage from './pages/Patients/PatientsPage';
import StaffPage from './pages/Staff/StaffPage';

function RootRedirect() {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return null;
  }
  
  return <Navigate to={isAuthenticated ? '/dashboard' : '/login'} />;
}

function App() {
  return (
    <UserTypeProvider userType="doctor">
      <AuthProvider>
        <UserProvider>
          <GlobalStyles />
          <BrowserRouter>
            <SessionTimeoutManager authTokenKey={DOCTOR_STORAGE_KEYS.authToken} />
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignUpPage />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/dashboard/:patientId" element={<DashboardDetailsPage />} />
                <Route path="/patients" element={<PatientsPage />} />
                <Route path="/staff" element={<StaffPage />} />
              </Route>
              <Route path="/" element={<RootRedirect />} />
            </Routes>
          </BrowserRouter>
        </UserProvider>
      </AuthProvider>
    </UserTypeProvider>
  );
}

export default App;