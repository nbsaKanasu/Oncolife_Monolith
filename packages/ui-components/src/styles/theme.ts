/**
 * OncoLife Design System - Theme Foundation
 * 
 * Brand: HealthAI
 * Application: OncoLife
 * Patient: "OncoLife - Ruby: Compassionate Care, Intelligent Triage"
 * Doctor: "OncoLife"
 * 
 * Supports: Light Mode + Dark Mode
 */

import { createTheme, ThemeOptions, responsiveFontSizes, PaletteMode } from '@mui/material/styles';

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
  // Triage / Severity Colors (consistent across both apps and modes)
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
  
  // Light Mode Gray Scale
  grayLight: {
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
  
  // Dark Mode Gray Scale
  grayDark: {
    50: '#0F172A',
    100: '#1E293B',
    200: '#334155',
    300: '#475569',
    400: '#64748B',
    500: '#94A3B8',
    600: '#CBD5E1',
    700: '#E2E8F0',
    800: '#F1F5F9',
    900: '#F8FAFC',
  },
  
  // Shadows
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
  
  // Dark Mode Shadows
  shadowsDark: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.3)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.6), 0 10px 10px -5px rgba(0, 0, 0, 0.3)',
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
  
  // Transitions
  transitions: {
    fast: '0.15s ease',
    normal: '0.25s ease',
    slow: '0.35s ease',
    pageEnter: '0.4s cubic-bezier(0.4, 0, 0.2, 1)',
    pageExit: '0.3s cubic-bezier(0.4, 0, 1, 1)',
  },
};

// =============================================================================
// PATIENT THEME COLORS
// =============================================================================

export const patientColors = {
  light: {
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
      default: '#F5F7FA',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1E293B',
      secondary: '#64748B',
      disabled: '#94A3B8',
    },
  },
  dark: {
    primary: {
      main: '#4DB6AC',      // Lighter teal for dark mode
      light: '#80CBC4',
      dark: '#00897B',
      contrastText: '#0F172A',
    },
    secondary: {
      main: '#B388FF',      // Lighter lavender
      light: '#E1BEE7',
      dark: '#7E57C2',
      contrastText: '#0F172A',
    },
    background: {
      default: '#0F172A',   // Deep navy
      paper: '#1E293B',
    },
    text: {
      primary: '#F1F5F9',
      secondary: '#94A3B8',
      disabled: '#64748B',
    },
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

// =============================================================================
// DOCTOR THEME COLORS
// =============================================================================

export const doctorColors = {
  light: {
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
      default: '#F8FAFC',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#0F172A',
      secondary: '#475569',
      disabled: '#94A3B8',
    },
  },
  dark: {
    primary: {
      main: '#3B82F6',      // Brighter blue for dark mode
      light: '#60A5FA',
      dark: '#2563EB',
      contrastText: '#0F172A',
    },
    secondary: {
      main: '#60A5FA',
      light: '#93C5FD',
      dark: '#3B82F6',
      contrastText: '#0F172A',
    },
    background: {
      default: '#0F172A',   // Deep navy
      paper: '#1E293B',
    },
    text: {
      primary: '#F1F5F9',
      secondary: '#94A3B8',
      disabled: '#64748B',
    },
  },
  // Dashboard accent colors
  accent: {
    teal: '#0D9488',
    indigo: '#4F46E5',
    amber: '#D97706',
  },
};

// =============================================================================
// THEME FACTORY FUNCTIONS
// =============================================================================

const createPatientThemeOptions = (mode: PaletteMode): ThemeOptions => {
  const colors = mode === 'dark' ? patientColors.dark : patientColors.light;
  const gray = mode === 'dark' ? sharedTokens.grayDark : sharedTokens.grayLight;
  
  return {
    breakpoints,
    typography,
    palette: {
      mode,
      primary: colors.primary,
      secondary: colors.secondary,
      background: colors.background,
      text: colors.text,
      success: { main: sharedTokens.severity.mild },
      warning: { main: sharedTokens.severity.moderate },
      error: { main: sharedTokens.severity.emergency },
      info: { main: sharedTokens.status.info },
      grey: gray,
    },
    shape: {
      borderRadius: sharedTokens.borderRadius.sm,
    },
    spacing: sharedTokens.spacing,
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: colors.background.default,
            transition: 'background-color 0.3s ease, color 0.3s ease',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: sharedTokens.borderRadius.md,
            padding: '10px 24px',
            fontWeight: 600,
            minHeight: 44,
            transition: `all ${sharedTokens.transitions.normal}`,
            '@media (max-width:600px)': {
              minHeight: 48,
              padding: '12px 24px',
            },
          },
          contained: {
            boxShadow: mode === 'dark' ? sharedTokens.shadowsDark.sm : sharedTokens.shadows.sm,
            '&:hover': {
              boxShadow: mode === 'dark' ? sharedTokens.shadowsDark.md : sharedTokens.shadows.md,
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: sharedTokens.borderRadius.lg,
            boxShadow: mode === 'dark' ? sharedTokens.shadowsDark.md : sharedTokens.shadows.md,
            transition: `all ${sharedTokens.transitions.normal}`,
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: sharedTokens.borderRadius.sm,
              transition: `all ${sharedTokens.transitions.fast}`,
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
            backgroundColor: colors.background.paper,
          },
        },
      },
      MuiBottomNavigation: {
        styleOverrides: {
          root: {
            height: 64,
            backgroundColor: colors.background.paper,
            borderTop: `1px solid ${gray[200]}`,
          },
        },
      },
      MuiBottomNavigationAction: {
        styleOverrides: {
          root: {
            minWidth: 64,
            padding: '8px 12px',
            '&.Mui-selected': {
              color: colors.primary.main,
            },
          },
        },
      },
    },
  };
};

const createDoctorThemeOptions = (mode: PaletteMode): ThemeOptions => {
  const colors = mode === 'dark' ? doctorColors.dark : doctorColors.light;
  const gray = mode === 'dark' ? sharedTokens.grayDark : sharedTokens.grayLight;
  
  return {
    breakpoints,
    typography,
    palette: {
      mode,
      primary: colors.primary,
      secondary: colors.secondary,
      background: colors.background,
      text: colors.text,
      success: { main: sharedTokens.severity.mild },
      warning: { main: sharedTokens.severity.moderate },
      error: { main: sharedTokens.severity.emergency },
      info: { main: sharedTokens.status.info },
      grey: gray,
    },
    shape: {
      borderRadius: sharedTokens.borderRadius.sm,
    },
    spacing: sharedTokens.spacing,
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: colors.background.default,
            transition: 'background-color 0.3s ease, color 0.3s ease',
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
            transition: `all ${sharedTokens.transitions.normal}`,
            '@media (max-width:600px)': {
              minHeight: 44,
            },
          },
          contained: {
            boxShadow: 'none',
            '&:hover': {
              boxShadow: mode === 'dark' ? sharedTokens.shadowsDark.sm : sharedTokens.shadows.sm,
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: sharedTokens.borderRadius.md,
            boxShadow: mode === 'dark' ? sharedTokens.shadowsDark.sm : sharedTokens.shadows.sm,
            border: `1px solid ${gray[200]}`,
            transition: `all ${sharedTokens.transitions.normal}`,
          },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          head: {
            fontWeight: 600,
            backgroundColor: mode === 'dark' ? gray[100] : gray[50],
            color: mode === 'dark' ? gray[700] : gray[700],
          },
        },
      },
      MuiTableRow: {
        styleOverrides: {
          root: {
            transition: `background-color ${sharedTokens.transitions.fast}`,
            '&:nth-of-type(even)': {
              backgroundColor: mode === 'dark' ? gray[100] : gray[50],
            },
            '&:hover': {
              backgroundColor: mode === 'dark' ? gray[200] : gray[100],
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
            backgroundColor: colors.background.paper,
            color: colors.text.primary,
            boxShadow: mode === 'dark' ? sharedTokens.shadowsDark.sm : sharedTokens.shadows.sm,
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            backgroundColor: mode === 'dark' ? colors.background.paper : doctorColors.light.primary.main,
            color: mode === 'dark' ? colors.text.primary : '#FFFFFF',
          },
        },
      },
    },
  };
};

// =============================================================================
// THEME EXPORTS
// =============================================================================

// Light Mode Themes (default)
export const patientTheme = responsiveFontSizes(createTheme(createPatientThemeOptions('light')));
export const doctorTheme = responsiveFontSizes(createTheme(createDoctorThemeOptions('light')));

// Dark Mode Themes
export const patientThemeDark = responsiveFontSizes(createTheme(createPatientThemeOptions('dark')));
export const doctorThemeDark = responsiveFontSizes(createTheme(createDoctorThemeOptions('dark')));

// Theme Factory for dynamic switching
export const createPatientTheme = (mode: PaletteMode) => 
  responsiveFontSizes(createTheme(createPatientThemeOptions(mode)));

export const createDoctorTheme = (mode: PaletteMode) => 
  responsiveFontSizes(createTheme(createDoctorThemeOptions(mode)));

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
// ANIMATION KEYFRAMES (for CSS-in-JS)
// =============================================================================

export const animations = {
  fadeIn: `
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
  `,
  fadeInUp: `
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `,
  fadeInDown: `
    @keyframes fadeInDown {
      from {
        opacity: 0;
        transform: translateY(-20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `,
  slideInLeft: `
    @keyframes slideInLeft {
      from {
        opacity: 0;
        transform: translateX(-30px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }
  `,
  slideInRight: `
    @keyframes slideInRight {
      from {
        opacity: 0;
        transform: translateX(30px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }
  `,
  scaleIn: `
    @keyframes scaleIn {
      from {
        opacity: 0;
        transform: scale(0.95);
      }
      to {
        opacity: 1;
        transform: scale(1);
      }
    }
  `,
  pulse: `
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.6; }
    }
  `,
  shimmer: `
    @keyframes shimmer {
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }
  `,
};

// Animation class names for use in components
export const animationClasses = {
  fadeIn: 'animate-fadeIn',
  fadeInUp: 'animate-fadeInUp',
  fadeInDown: 'animate-fadeInDown',
  slideInLeft: 'animate-slideInLeft',
  slideInRight: 'animate-slideInRight',
  scaleIn: 'animate-scaleIn',
  staggerChild: 'animate-stagger-child',
};

// =============================================================================
// LEGACY EXPORTS (backward compatibility)
// =============================================================================

export const theme = {
  colors: {
    primary: patientColors.light.primary.main,
    secondary: sharedTokens.grayLight[500],
    success: sharedTokens.severity.mild,
    danger: sharedTokens.severity.emergency,
    warning: sharedTokens.severity.moderate,
    info: sharedTokens.status.info,
    light: sharedTokens.grayLight[100],
    dark: sharedTokens.grayLight[800],
    white: '#ffffff',
    gray: sharedTokens.grayLight,
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
  transitions: sharedTokens.transitions,
  animations,
};

export type Theme = typeof theme;
