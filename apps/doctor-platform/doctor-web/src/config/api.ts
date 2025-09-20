const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

export const API_CONFIG = {
  BASE_URL,
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/login',
      SIGNUP: '/signup',
      COMPLETE_NEW_PASSWORD: '/complete-new-password',
      FORGOT_PASSWORD: '/forgot-password',
      RESET_PASSWORD: '/reset-password',
      LOGOUT: '/logout'
    },
    DASHBOARD: '/dashboard',
    PATIENT_DASHBOARD: '/patient-dashboard',
    PATIENTS: {
      LIST: '/patients',
      CREATE: '/patients',
      UPDATE: '/patients',
      DELETE: '/patients'
    },
    STAFF: {
      LIST: '/staff',
      CREATE: '/staff',
      UPDATE: '/staff',
      DELETE: '/staff'
    }
  }
};
