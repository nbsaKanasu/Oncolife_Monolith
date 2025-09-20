import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { GlobalStyles, SessionTimeoutManager } from '@oncolife/ui-components';
import { AuthProvider } from './contexts/AuthContext';
import { UserProvider } from './contexts/UserContext';
import { UserTypeProvider } from './contexts/UserTypeContext';
import { useAuth } from './contexts/AuthContext';
import { PATIENT_STORAGE_KEYS } from './utils/storageKeys';

// Shared login from ui-components
import LoginPage from './pages/LoginPage';
import ResetPassword from './pages/LoginPage/ResetPassword';
import ForgotPassword from './pages/LoginPage/ForgotPassword';
import Acknowledgement from './pages/LoginPage/Acknowledgement';

// Patient-specific pages
import SignUpPage from './pages/SignUpPage';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import ChatsPage from './pages/ChatsPage';
import { SummariesPage, SummariesDetailsPage } from './pages/SummariesPage';
import NotesPage from './pages/NotesPage';
import EducationPage from './pages/EducationPage';
import ProfilePage from './pages/ProfilePage';

function RootRedirect() {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return null;
  }
  
  return <Navigate to={isAuthenticated ? '/chat' : '/login'} />;
}

function App() {
  return (
    <UserTypeProvider>
      <AuthProvider>
        <UserProvider>
          <GlobalStyles />
          <BrowserRouter>
            <SessionTimeoutManager authTokenKey={PATIENT_STORAGE_KEYS.authToken} />
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route path="/acknowledgement" element={<Acknowledgement />} />
              <Route path="/signup" element={<SignUpPage />} />
              <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                <Route path="/chat" element={<ChatsPage />} />
                <Route path="/summaries" element={<SummariesPage />} />
                <Route path="/summaries/:id" element={<SummariesDetailsPage />} />
                <Route path="/notes" element={<NotesPage />} />
                <Route path="/education" element={<EducationPage />} />
                <Route path="/profile" element={<ProfilePage />} />
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