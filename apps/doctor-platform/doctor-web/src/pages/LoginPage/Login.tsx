import React, { useState } from 'react';
import { Mail } from 'lucide-react';
import { Card, Title, Subtitle, InputPassword } from '@oncolife/ui-components';
import {
  StyledForm,
  ForgotPassword,
  StyledInputGroup,
  StyledInput,
  InputIcon,
  StyledButton
} from './LoginPage.styles';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { authenticateLogin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState<string | null>(null);

  // Get the location the user was trying to access before being redirected to login
  const from = location.state?.from?.pathname || '/dashboard';

  const handleLogin = async () => {
    setError(null);
    try {
      const result = await authenticateLogin(email, password);
      
      if (result?.data?.requiresPasswordChange || result?.data?.user_status === 'FORCE_CHANGE_PASSWORD') {
        // Navigate to reset password page for doctors with temporary passwords
        navigate('/reset-password');
      } else if (result?.data?.user_status === 'CONFIRMED') {
        // Navigate back to the page the user was trying to access, or dashboard as default
        navigate(from, { replace: true });
      }
    } catch (err: any) {
      let message = 'Login failed';
        if (err.message === 'AUTHENTICATION_FAILED') {
          message = 'Failed Authentication';
        } else if (err.message === 'INVALID_CREDENTIALS') {
          message = 'Invalid Credentials';
        } else {
          message = 'Failed Authentication';
        }
      setError(message);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleLogin();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleLogin();
    }
  };

  return (
    <Card>
      <Title>Welcome to OncoLife AI Doctor Portal</Title>
      <Subtitle>Please enter your credentials to access the doctor dashboard</Subtitle>
      {error && <div style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}
      <StyledForm onSubmit={handleSubmit}>
        <div className="mb-3">
          <label>Email</label>
          <StyledInputGroup>
            <InputIcon>
              <Mail size={20} />
            </InputIcon>
            <StyledInput
              type="email"
              placeholder="Doctor Email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </StyledInputGroup>
        </div>
        <InputPassword
          value={password}
          onChange={setPassword}
          className="mb-1"
          label="Password"
          placeholder="Password"
          onKeyDown={handleKeyDown}
        />
        <ForgotPassword onClick={() => navigate('/forgot-password', { state: { email } })}>Forgot Password?</ForgotPassword>
        <StyledButton variant="primary" type="submit">
          Sign In
        </StyledButton>
      </StyledForm>
    </Card>
  );
};

export default Login;
