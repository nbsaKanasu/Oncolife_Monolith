/**
 * OncoLife Design System - Theme Foundation
 * 
 * Brand: HealthAI
 * Application: OncoLife
 * Patient: "OncoLife - Ruby: Compassionate Care, Intelligent Triage"
 * Doctor: "OncoLife"
 */

import { createTheme, ThemeOptions, responsiveFontSizes } from '@mui/material/styles';

// =============================================================================
// RESPONSIVE BREAKPOINTS
// =============================================================================

export const breakpoints = {
  values: {
    xs: 0,      // Mobile (portrait)
    sm: 600,    // Mobile (landscape) / Small tablet
    md: 900,    // Tablet
    lg: 1200,   // Desktop
    xl: 1536,   // Large desktop
  },
};

// =============================================================================
// TYPOGRAPHY - Source Sans Pro
// =============================================================================

const typography = {
  fontFamily: "'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  h1: {
    fontSize: '2rem',
    fontWeight: 700,
    lineHeight: 1.2,
    letterSpacing: '-0.02em',
    '@media (min-width:600px)': {
      fontSize: '2.25rem',
    },
    '@media (min-width:900px)': {
      fontSize: '2.5rem',
    },
  },
  h2: {
    fontSize: '1.5rem',
    fontWeight: 600,
    lineHeight: 1.3,
    letterSpacing: '-0.01em',
    '@media (min-width:600px)': {
      fontSize: '1.75rem',
    },
    '@media (min-width:900px)': {
      fontSize: '2rem',
    },
  },
  h3: {
    fontSize: '1.25rem',
    fontWeight: 600,
    lineHeight: 1.4,
    '@media (min-width:900px)': {
      fontSize: '1.5rem',
    },
  },
  h4: {
    fontSize: '1.125rem',
    fontWeight: 600,
    lineHeight: 1.4,
  },
  h5: {
    fontSize: '1rem',
    fontWeight: 600,
    lineHeight: 1.5,
  },
  h6: {
    fontSize: '0.875rem',
    fontWeight: 600,
    lineHeight: 1.5,
  },
  body1: {
    fontSize: '1rem',
    lineHeight: 1.6,
  },
  body2: {
    fontSize: '0.875rem',
    lineHeight: 1.5,
  },
  button: {
    textTransform: 'none' as const,
    fontWeight: 600,
  },
  caption: {
    fontSize: '0.75rem',
    lineHeight: 1.5,
  },
};

// =============================================================================
// SHARED DESIGN TOKENS
// =============================================================================

export const sharedTokens = {
  // Triage / Severity Colors (consistent across both apps)
  severity: {
    emergency: '#DC2626',    // Red - Call 911
    urgent: '#EA580C',       // Orange - Severe
    moderate: '#F59E0B',     // Amber - Moderate
    mild: '#22C55E',         // Green - Mild/OK
  },
  
  // Status Colors
  status: {
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
  },
  
  // Neutral Gray Scale
  gray: {
    50: '#F8FAFC',
    100: '#F1F5F9',
    200: '#E2E8F0',
    300: '#CBD5E1',
    400: '#94A3B8',
    500: '#64748B',
    600: '#475569',
    700: '#334155',
    800: '#1E293B',
    900: '#0F172A',
  },
  
  // Shadows
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
  
  // Border Radius
  borderRadius: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
    full: 9999,
  },
  
  // Spacing Scale
  spacing: 8, // Base spacing unit (8px)
};

// =============================================================================
// PATIENT THEME - "OncoLife - Ruby"
// Healing Teal + Soft Lavender - Calming, Compassionate, Trustworthy
// =============================================================================

export const patientColors = {
  primary: {
    main: '#00897B',      // Healing Teal
    light: '#4DB6AC',
    dark: '#00695C',
    contrastText: '#FFFFFF',
  },
  secondary: {
    main: '#7E57C2',      // Soft Lavender/Purple
    light: '#B388FF',
    dark: '#5E35B1',
    contrastText: '#FFFFFF',
  },
  background: {
    default: '#F5F7FA',   // Light gray-blue (easy on eyes)
    paper: '#FFFFFF',
  },
  text: {
    primary: '#1E293B',
    secondary: '#64748B',
    disabled: '#94A3B8',
  },
  // Ruby Chat Colors
  ruby: {
    primary: '#00897B',
    light: '#4DB6AC',
    bubble: '#FFFFFF',
    border: '#B2DFDB',
  },
  // Patient Message Colors
  patient: {
    primary: '#7E57C2',
    bubble: '#7E57C2',
    text: '#FFFFFF',
  },
};

const patientThemeOptions: ThemeOptions = {
  breakpoints,
  typography,
  palette: {
    mode: 'light',
    primary: patientColors.primary,
    secondary: patientColors.secondary,
    background: patientColors.background,
    text: patientColors.text,
    success: { main: sharedTokens.severity.mild },
    warning: { main: sharedTokens.severity.moderate },
    error: { main: sharedTokens.severity.emergency },
    info: { main: sharedTokens.status.info },
    grey: sharedTokens.gray,
  },
  shape: {
    borderRadius: sharedTokens.borderRadius.sm,
  },
  spacing: sharedTokens.spacing,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: patientColors.background.default,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: sharedTokens.borderRadius.md,
          padding: '10px 24px',
          fontWeight: 600,
          minHeight: 44, // Touch-friendly
          '@media (max-width:600px)': {
            minHeight: 48, // Larger on mobile
            padding: '12px 24px',
          },
        },
        contained: {
          boxShadow: sharedTokens.shadows.sm,
          '&:hover': {
            boxShadow: sharedTokens.shadows.md,
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: sharedTokens.borderRadius.lg,
          boxShadow: sharedTokens.shadows.md,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: sharedTokens.borderRadius.sm,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: sharedTokens.borderRadius.md,
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRadius: 0,
        },
      },
    },
    MuiBottomNavigation: {
      styleOverrides: {
        root: {
          height: 64,
          backgroundColor: '#FFFFFF',
          borderTop: `1px solid ${sharedTokens.gray[200]}`,
        },
      },
    },
    MuiBottomNavigationAction: {
      styleOverrides: {
        root: {
          minWidth: 64,
          padding: '8px 12px',
          '&.Mui-selected': {
            color: patientColors.primary.main,
          },
        },
      },
    },
  },
};

export const patientTheme = responsiveFontSizes(createTheme(patientThemeOptions));

// =============================================================================
// DOCTOR THEME - "OncoLife"
// Clinical Navy + Medical Blue - Professional, Authoritative, Clinical
// =============================================================================

export const doctorColors = {
  primary: {
    main: '#1E3A5F',      // Clinical Navy
    light: '#2E5077',
    dark: '#0F2942',
    contrastText: '#FFFFFF',
  },
  secondary: {
    main: '#2563EB',      // Medical Blue
    light: '#3B82F6',
    dark: '#1D4ED8',
    contrastText: '#FFFFFF',
  },
  background: {
    default: '#F8FAFC',   // Clean clinical white-gray
    paper: '#FFFFFF',
  },
  text: {
    primary: '#0F172A',
    secondary: '#475569',
    disabled: '#94A3B8',
  },
  // Dashboard accent colors
  accent: {
    teal: '#0D9488',
    indigo: '#4F46E5',
    amber: '#D97706',
  },
};

const doctorThemeOptions: ThemeOptions = {
  breakpoints,
  typography,
  palette: {
    mode: 'light',
    primary: doctorColors.primary,
    secondary: doctorColors.secondary,
    background: doctorColors.background,
    text: doctorColors.text,
    success: { main: sharedTokens.severity.mild },
    warning: { main: sharedTokens.severity.moderate },
    error: { main: sharedTokens.severity.emergency },
    info: { main: sharedTokens.status.info },
    grey: sharedTokens.gray,
  },
  shape: {
    borderRadius: sharedTokens.borderRadius.sm,
  },
  spacing: sharedTokens.spacing,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: doctorColors.background.default,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: sharedTokens.borderRadius.sm,
          padding: '8px 20px',
          fontWeight: 600,
          minHeight: 40,
          '@media (max-width:600px)': {
            minHeight: 44,
          },
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: sharedTokens.shadows.sm,
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: sharedTokens.borderRadius.md,
          boxShadow: sharedTokens.shadows.sm,
          border: `1px solid ${sharedTokens.gray[200]}`,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 600,
          backgroundColor: sharedTokens.gray[50],
          color: sharedTokens.gray[700],
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:nth-of-type(even)': {
            backgroundColor: sharedTokens.gray[50],
          },
          '&:hover': {
            backgroundColor: sharedTokens.gray[100],
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: sharedTokens.borderRadius.xs,
          fontWeight: 600,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#FFFFFF',
          color: doctorColors.text.primary,
          boxShadow: sharedTokens.shadows.sm,
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: doctorColors.primary.main,
          color: '#FFFFFF',
        },
      },
    },
  },
};

export const doctorTheme = responsiveFontSizes(createTheme(doctorThemeOptions));

// =============================================================================
// SEVERITY BADGE HELPERS
// =============================================================================

export const getSeverityColor = (level: 'emergency' | 'urgent' | 'moderate' | 'mild') => {
  return sharedTokens.severity[level];
};

export const getSeverityLabel = (level: 'emergency' | 'urgent' | 'moderate' | 'mild') => {
  const labels = {
    emergency: 'Emergency',
    urgent: 'Urgent',
    moderate: 'Moderate',
    mild: 'Mild',
  };
  return labels[level];
};

// =============================================================================
// EXPORTS
// =============================================================================

// Legacy theme export for backward compatibility
export const theme = {
  colors: {
    primary: patientColors.primary.main,
    secondary: sharedTokens.gray[500],
    success: sharedTokens.severity.mild,
    danger: sharedTokens.severity.emergency,
    warning: sharedTokens.severity.moderate,
    info: sharedTokens.status.info,
    light: sharedTokens.gray[100],
    dark: sharedTokens.gray[800],
    white: '#ffffff',
    gray: sharedTokens.gray,
  },
  fonts: {
    body: typography.fontFamily,
    heading: typography.fontFamily,
  },
  fontSizes: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
  },
  borderRadius: sharedTokens.borderRadius,
};

export type Theme = typeof theme;
