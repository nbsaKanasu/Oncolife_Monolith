const express = require('express');
const router = express.Router();
const { api } = require('../utils/api.helpers');
const { apiClient } = require('../config/axios.config');

// Helper function to get cookie configuration based on environment
const getCookieConfig = () => {
  const isProduction = process.env.NODE_ENV === 'production';
  return {
    httpOnly: true,
    secure: isProduction, // HTTPS required in production
    // Use 'none' in production so cookies are sent on cross-site XHR with credentials
    sameSite: isProduction ? 'none' : 'lax',
    maxAge: 60 * 60 * 1000, // 1 hour (matches Cognito default)
    domain: undefined // Let browser handle domain
  };
};

router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      console.warn('[LOGIN] Missing credentials');
      return res.status(400).json({
        success: false,
        message: 'Email and password are required',
        error: 'MISSING_CREDENTIALS'
      });
    }

    const backendBase = apiClient?.defaults?.baseURL || '<unknown>';
    console.log(`[LOGIN] Incoming login for ${email} -> POST ${backendBase}/auth/login`);

    const response = await api.post('/auth/login', {
      email,
      password
    });

    console.log(`[LOGIN] Upstream response for ${email}: success=${response.success} status=${response.status}`);

    if (!response.success) {
      console.error('[LOGIN] Upstream error details:', response.error?.details || response.error?.message);
      return res.status(response.status).json({
        success: false,
        message: response.error.message,
        error: response.error.code === 401 ? 'INVALID_CREDENTIALS' : 'AUTHENTICATION_FAILED'
      });
    }

    const { valid, message, user_status, session, tokens } = response.data;

    if (valid) {
      if (user_status === 'CONFIRMED') {
        console.log(`[LOGIN] Successful login for ${email}`);
        
        // Set HTTP-only cookies in production
        if (process.env.NODE_ENV === 'production' && tokens?.access_token) {
          const cookieConfig = getCookieConfig();
          res.cookie('authToken', tokens.access_token, cookieConfig);
          if (tokens.refresh_token) {
            res.cookie('refreshToken', tokens.refresh_token, {
              ...cookieConfig,
              maxAge: 30 * 24 * 60 * 60 * 1000 // 30 days for refresh token
            });
          }
          console.log(`[LOGIN] Set HTTP-only cookies for ${email}`);
        }
        
        return res.status(200).json({
          success: true,
          message: 'Login successful',
          data: { user_status, message, tokens }
        });
      } else if (user_status === 'FORCE_CHANGE_PASSWORD') {
        console.log(`[LOGIN] Password change required for ${email}`);
        
        // Set session cookie for password change flow
        if (process.env.NODE_ENV === 'production' && session) {
          const cookieConfig = getCookieConfig();
          res.cookie('sessionToken', session, {
            ...cookieConfig,
            maxAge: 10 * 60 * 1000 // 10 minutes for session token
          });
          console.log(`[LOGIN] Set session cookie for ${email}`);
        }
        
        return res.status(200).json({
          success: true,
          message: 'Password change required',
          data: { user_status, message, session, requiresPasswordChange: true }
        });
      } else if (user_status === 'CHALLENGE_REQUIRED') {
        console.log(`[LOGIN] Challenge required for ${email}`);
        return res.status(200).json({
          success: true,
          message: 'Additional authentication required',
          data: { user_status, message, session, requiresChallenge: true }
        });
      }
    } else {
      console.warn(`[LOGIN] Invalid credentials for ${email}`);
      return res.status(401).json({
        success: false,
        message: message || 'Invalid email or password',
        error: 'INVALID_CREDENTIALS'
      });
    }

  } catch (error) {
    const backendBase = apiClient?.defaults?.baseURL || '<unknown>';
    console.error(`[LOGIN] Endpoint error (backend=${backendBase}):`, error?.response?.data || error.message);
    return res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: 'INTERNAL_ERROR'
    });
  }
});

router.post('/complete-new-password', async (req, res) => {
  try {
    const { email, new_password } = req.body;
    // Prefer explicit session in body; fall back to cookie in production
    const session = req.body?.session || (process.env.NODE_ENV === 'production' ? req.cookies?.sessionToken : undefined);

    if (!email || !new_password || !session) {
      console.warn('[LOGIN] Missing fields for complete-new-password');
      return res.status(400).json({
        success: false,
        message: 'Email, new password, and session are required',
        error: 'MISSING_FIELDS'
      });
    }

    const backendBase = apiClient?.defaults?.baseURL || '<unknown>';
    console.log(`[LOGIN] complete-new-password for ${email} -> POST ${backendBase}/auth/complete-new-password`);

    const response = await api.post('/auth/complete-new-password', {
      email,
      new_password,
      session
    });

    if (!response.success) {
      console.error('[LOGIN] Upstream error details (complete-new-password):', response.error?.details || response.error?.message);
      return res.status(response.status).json({
        success: false,
        message: response.error.message,
        error: response.error.code === 400 ? 'INVALID_REQUEST' : 'PASSWORD_CHANGE_FAILED'
      });
    }

    const { message, tokens } = response.data;

    // Set HTTP-only cookies in production after successful password change
    if (process.env.NODE_ENV === 'production' && tokens?.access_token) {
      const cookieConfig = getCookieConfig();
      res.cookie('authToken', tokens.access_token, cookieConfig);
      if (tokens.refresh_token) {
        res.cookie('refreshToken', tokens.refresh_token, {
          ...cookieConfig,
          maxAge: 30 * 24 * 60 * 60 * 1000 // 30 days for refresh token
        });
      }
      // Clear session cookie
      res.clearCookie('sessionToken');
      console.log(`[LOGIN] Set auth cookies and cleared session cookie for ${email}`);
    }

    console.log(`[LOGIN] complete-new-password success for ${email}`);
    return res.status(200).json({ success: true, message: 'Password changed successfully', data: { message, tokens } });
  } catch (error) {
    console.error('[LOGIN] complete-new-password endpoint error:', error?.response?.data || error.message);
    return res.status(500).json({ success: false, message: 'Internal server error', error: 'INTERNAL_ERROR' });
  }
});

router.post('/signup', async (req, res) => {
  try {
    const { emailAddress:email, firstName:first_name, lastName:last_name } = req.body;

    if (!email || !first_name || !last_name) {
      console.warn('[LOGIN] Missing fields for signup');
      return res.status(400).json({
        success: false,
        message: 'Email, first name, and last name are required',
        error: 'MISSING_FIELDS'
      });
    }

    const backendBase = apiClient?.defaults?.baseURL || '<unknown>';
    console.log(`[LOGIN] signup for ${email} -> POST ${backendBase}/auth/signup`);

    const response = await api.post('/auth/signup', { email, first_name, last_name });

    if (!response.success) {
      console.error('[LOGIN] Upstream error details (signup):', response.error?.details || response.error?.message);
      return res.status(response.status).json({
        success: false,
        message: response.error.message,
        error: response.error.code === 400 ? 'BAD_REQUEST' : 'SIGNUP_FAILED'
      });
    }

    const { message, email: userEmail, user_status } = response.data;

    console.log(`[LOGIN] signup success for ${email}`);
    return res.status(201).json({ success: true, message: 'User created successfully', data: { message, email: userEmail, user_status } });
  } catch (error) {
    console.error('Signup endpoint error:', error?.response?.data || error.message);
    return res.status(500).json({ success: false, message: 'Internal server error', error: 'INTERNAL_ERROR' });
  }
});

router.post('/forgot-password', async (req, res) => {
  try {
    const { email } = req.body;

    if (!email) {
      console.warn('[LOGIN] Missing email for forgot-password');
      return res.status(400).json({
        success: false,
        message: 'Email is required',
        error: 'MISSING_EMAIL'
      });
    }

    const backendBase = apiClient?.defaults?.baseURL || '<unknown>';
    console.log(`[LOGIN] forgot-password for ${email} -> POST ${backendBase}/auth/forgot-password`);

    const response = await api.post('/auth/forgot-password', { email });
    
    if (!response.success) {
      console.error('[LOGIN] Upstream error details (forgot-password):', response.error?.details || response.error?.message);
      return res.status(response.status).json({
        success: false,
        message: response.error.message,
        error: 'FORGOT_PASSWORD_FAILED'
      });
    }

    const { message, email: userEmail } = response.data;

    console.log(`[LOGIN] forgot-password success for ${email}`);
    return res.status(200).json({
      success: true,
      message: message || 'Password reset code sent successfully',
      data: { email: userEmail }
    });

  } catch (error) {
    console.error('[LOGIN] forgot-password endpoint error:', error?.response?.data || error.message);
    return res.status(500).json({ success: false, message: 'Internal server error', error: 'INTERNAL_ERROR' });
  }
});

router.post('/reset-password', async (req, res) => {
  try {
    const { email, confirmation_code, new_password } = req.body;

    if (!email || !confirmation_code || !new_password) {
      console.warn('[LOGIN] Missing fields for reset-password');
      return res.status(400).json({
        success: false,
        message: 'Email, confirmation code, and new password are required',
        error: 'MISSING_FIELDS'
      });
    }

    if (confirmation_code.length !== 6) {
      console.warn('[LOGIN] Invalid confirmation code length for reset-password');
      return res.status(400).json({
        success: false,
        message: 'Confirmation code must be 6 digits',
        error: 'INVALID_CODE_FORMAT'
      });
    }

    const backendBase = apiClient?.defaults?.baseURL || '<unknown>';
    console.log(`[LOGIN] reset-password for ${email} -> POST ${backendBase}/auth/reset-password`);

    const response = await api.post('/auth/reset-password', { 
      email, 
      confirmation_code, 
      new_password 
    });
    
    if (!response.success) {
      console.error('[LOGIN] Upstream error details (reset-password):', response.error?.details || response.error?.message);
      return res.status(response.status).json({
        success: false,
        message: response.error.message,
        error: 'RESET_PASSWORD_FAILED'
      });
    }

    const { message, email: userEmail } = response.data;

    console.log(`[LOGIN] reset-password success for ${email}`);
    return res.status(200).json({
      success: true,
      message: message || 'Password reset successfully',
      data: { email: userEmail }
    });

  } catch (error) {
    console.error('[LOGIN] reset-password endpoint error:', error?.response?.data || error.message);
    return res.status(500).json({ success: false, message: 'Internal server error', error: 'INTERNAL_ERROR' });
  }
});

router.post('/logout', async (req, res) => {
  try {
    console.log('[LOGIN] Logout request received');
    
    // Clear all auth cookies in production
    if (process.env.NODE_ENV === 'production') {
      res.clearCookie('authToken');
      res.clearCookie('refreshToken');
      res.clearCookie('sessionToken');
      console.log('[LOGIN] Cleared auth cookies');
    }
    
    // Call backend logout endpoint
    try {
      await api.post('/auth/logout');
      console.log('[LOGIN] Backend logout successful');
    } catch (error) {
      console.warn('[LOGIN] Backend logout failed (non-critical):', error?.response?.data || error.message);
    }
    
    return res.status(200).json({
      success: true,
      message: 'Logout successful'
    });
    
  } catch (error) {
    console.error('[LOGIN] Logout endpoint error:', error?.response?.data || error.message);
    return res.status(500).json({ 
      success: false, 
      message: 'Internal server error', 
      error: 'INTERNAL_ERROR' 
    });
  }
});

module.exports = router;
