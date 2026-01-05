/// <reference types="./types/assets" />

// =============================================================================
// THEMES (MUI)
// =============================================================================
export { 
  patientTheme, 
  doctorTheme,
  patientColors,
  doctorColors,
  sharedTokens,
  breakpoints,
  getSeverityColor,
  getSeverityLabel,
  theme, // Legacy theme for backward compatibility
} from './styles/theme';
export type { Theme } from './styles/theme';

// =============================================================================
// GLOBAL STYLES (Styled Components)
// =============================================================================
export { 
  GlobalStyles,
  Container, 
  Header, 
  Title, 
  Content, 
  PageHeader, 
  PageTitle,
  Card,
  Subtitle,
  Logo,
  Background,
  WrapperStyle,
  Grid,
  Flex,
  Stack,
  Row,
} from './styles/GlobalStyles';

// =============================================================================
// COMPONENTS
// =============================================================================

// Login components
export { default as InputPassword } from './components/Login/InputPassword';
export * from './components/Login/InputPassword.styles';
export { default as Login } from './pages/Login/Login';

// Navigation
export { default as Navigation } from './components/Navigation/Navigation';

// Date Picker
export { default as DatePicker } from './components/DatePicker';
export * from './components/DatePicker/DatePicker.styles';

// Session Management
export { default as SessionTimeoutManager, SESSION_START_KEY } from './components/SessionTimeout/SessionTimeoutManager';
export { default as SessionTimeoutModal } from './components/SessionTimeout/SessionTimeoutModal';

// Error Boundary
export { default as ErrorBoundary } from './components/ErrorBoundary';
