import React, { useState } from 'react';
import { Form } from 'react-bootstrap';
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
  const [isLoading, setIsLoading] = useState(false);

  // Get the location the user was trying to access before being redirected to login
  const from = location.state?.from?.pathname || '/chat';

  const handleLogin = async () => {
    setError(null);
    setIsLoading(true);
    try {
      const result = await authenticateLogin(email, password);
      
      if (result?.data?.requiresPasswordChange) {
        navigate('/reset-password');
      } else if (result?.data?.user_status === 'CONFIRMED') {
        // Navigate back to the page the user was trying to access, or chat as default
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
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLoading) {
      handleLogin();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) {
      e.preventDefault();
      handleLogin();
    }
  };

  return (
    <Card>
      <Title>Welcome to OncoLife! </Title>
      <Subtitle>Please enter your details to sign in to your account</Subtitle>
      {error && <div style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}
      <StyledForm onSubmit={handleSubmit}>
        <Form.Group className="mb-3" controlId="formEmail">
          <Form.Label>Email</Form.Label>
          <StyledInputGroup>
            <InputIcon>
              <Mail size={20} />
            </InputIcon>
            <StyledInput
              type="email"
              placeholder="Your Email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
          </StyledInputGroup>
        </Form.Group>
        <InputPassword
          value={password}
          onChange={(value) => !isLoading && setPassword(value)}
          className="mb-1"
          label="Password"
          placeholder="Password"
          onKeyDown={handleKeyDown}
        />
        <ForgotPassword onClick={() => navigate('/forgot-password', { state: { email } })}>Forgot Password?</ForgotPassword>
        <StyledButton variant="primary" type="submit" disabled={isLoading}>
          {isLoading ? (
            <>
              <span className="login-spinner" />
              Signing In...
            </>
          ) : (
            'Sign In'
          )}
        </StyledButton>
      </StyledForm>
    </Card>
  );
};

export default Login; 