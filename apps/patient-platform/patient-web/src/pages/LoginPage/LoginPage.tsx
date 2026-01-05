/**
 * OncoLife Ruby - Patient Login Page
 * "Compassionate Care, Intelligent Triage"
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import {
  LoginContainer,
  BrandPanel,
  BrandContent,
  LogoContainer,
  BrandTitle,
  BrandSubtitle,
  BrandTagline,
  LoginPanel,
  LoginCard,
  LoginTitle,
  LoginSubtitle,
  FormGroup,
  FormLabel,
  InputWrapper,
  InputIcon,
  StyledInput,
  PasswordToggle,
  ForgotPasswordLink,
  SubmitButton,
  ErrorMessage,
  SignUpLink,
  Footer,
} from './LoginPage.styles';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const { authenticateLogin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const result = await authenticateLogin(email, password);
      if (result?.data?.requiresPasswordChange) {
        navigate('/reset-password');
      } else if (result?.data?.user_status === 'CONFIRMED') {
        navigate('/chat');
      }
    } catch (err: any) {
      let message = 'Unable to sign in. Please try again.';
      if (err.message === 'AUTHENTICATION_FAILED' || err.message === 'INVALID_CREDENTIALS') {
        message = 'Invalid email or password. Please check your credentials.';
      }
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <LoginContainer>
      {/* Left Brand Panel */}
      <BrandPanel>
        <BrandContent>
          <LogoContainer>💎</LogoContainer>
          <BrandTitle>OncoLife</BrandTitle>
          <BrandSubtitle>Ruby</BrandSubtitle>
          <BrandTagline>"Compassionate Care, Intelligent Triage"</BrandTagline>
        </BrandContent>
      </BrandPanel>

      {/* Right Login Panel */}
      <LoginPanel>
        <LoginCard>
          <LoginTitle>Welcome Back 👋</LoginTitle>
          <LoginSubtitle>
            Sign in to access your personalized symptom tracker and care resources
          </LoginSubtitle>

          {error && (
            <ErrorMessage>
              <AlertCircle size={18} />
              {error}
            </ErrorMessage>
          )}

          <form onSubmit={handleSubmit}>
            <FormGroup>
              <FormLabel htmlFor="email">Email Address</FormLabel>
              <InputWrapper>
                <InputIcon>
                  <Mail size={20} />
                </InputIcon>
                <StyledInput
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyDown={handleKeyDown}
                  autoComplete="email"
                  required
                />
              </InputWrapper>
            </FormGroup>

            <FormGroup>
              <FormLabel htmlFor="password">Password</FormLabel>
              <InputWrapper>
                <InputIcon>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  </svg>
                </InputIcon>
                <StyledInput
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={handleKeyDown}
                  autoComplete="current-password"
                  required
                />
                <PasswordToggle
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </PasswordToggle>
              </InputWrapper>
            </FormGroup>

            <ForgotPasswordLink href="#">
              Forgot password?
            </ForgotPasswordLink>

            <SubmitButton type="submit" disabled={isLoading}>
              {isLoading ? 'Signing in...' : 'Sign In'}
            </SubmitButton>
          </form>

          <SignUpLink>
            Don't have an account?
            <Link to="/signup">Sign up</Link>
          </SignUpLink>

          <Footer>
            © 2025 HealthAI - OncoLife. All rights reserved.
          </Footer>
        </LoginCard>
      </LoginPanel>
    </LoginContainer>
  );
};

export default LoginPage;
