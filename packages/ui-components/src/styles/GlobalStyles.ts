/**
 * OncoLife Global Styles
 * 
 * Includes:
 * - CSS Reset
 * - Source Sans Pro font import
 * - Base typography
 * - Animation keyframes
 * - Utility classes
 * - Dark mode support
 * - Responsive helpers
 */

import { createGlobalStyle } from 'styled-components';
import styled from 'styled-components';
import { sharedTokens } from './theme';

// =============================================================================
// GLOBAL STYLES
// =============================================================================

export const GlobalStyles = createGlobalStyle`
  /* Source Sans Pro Font Import */
  @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&display=swap');

  /* CSS Reset */
  *, *::before, *::after {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  /* Root Variables */
  :root {
    /* Severity Colors */
    --severity-emergency: ${sharedTokens.severity.emergency};
    --severity-urgent: ${sharedTokens.severity.urgent};
    --severity-moderate: ${sharedTokens.severity.moderate};
    --severity-mild: ${sharedTokens.severity.mild};
    
    /* Light Mode Gray Scale */
    --gray-50: ${sharedTokens.grayLight[50]};
    --gray-100: ${sharedTokens.grayLight[100]};
    --gray-200: ${sharedTokens.grayLight[200]};
    --gray-300: ${sharedTokens.grayLight[300]};
    --gray-400: ${sharedTokens.grayLight[400]};
    --gray-500: ${sharedTokens.grayLight[500]};
    --gray-600: ${sharedTokens.grayLight[600]};
    --gray-700: ${sharedTokens.grayLight[700]};
    --gray-800: ${sharedTokens.grayLight[800]};
    --gray-900: ${sharedTokens.grayLight[900]};
    
    /* Shadows */
    --shadow-sm: ${sharedTokens.shadows.sm};
    --shadow-md: ${sharedTokens.shadows.md};
    --shadow-lg: ${sharedTokens.shadows.lg};
    --shadow-xl: ${sharedTokens.shadows.xl};
    
    /* Border Radius */
    --radius-xs: ${sharedTokens.borderRadius.xs}px;
    --radius-sm: ${sharedTokens.borderRadius.sm}px;
    --radius-md: ${sharedTokens.borderRadius.md}px;
    --radius-lg: ${sharedTokens.borderRadius.lg}px;
    --radius-xl: ${sharedTokens.borderRadius.xl}px;
    --radius-full: ${sharedTokens.borderRadius.full}px;
    
    /* Transitions */
    --transition-fast: ${sharedTokens.transitions.fast};
    --transition-normal: ${sharedTokens.transitions.normal};
    --transition-slow: ${sharedTokens.transitions.slow};
    --transition-page-enter: ${sharedTokens.transitions.pageEnter};
    --transition-page-exit: ${sharedTokens.transitions.pageExit};
    
    /* Safe Areas (for mobile notch/home indicator) */
    --safe-area-inset-top: env(safe-area-inset-top, 0px);
    --safe-area-inset-bottom: env(safe-area-inset-bottom, 0px);
    --safe-area-inset-left: env(safe-area-inset-left, 0px);
    --safe-area-inset-right: env(safe-area-inset-right, 0px);
  }

  /* Dark Mode Variables */
  [data-theme="dark"] {
    --gray-50: ${sharedTokens.grayDark[50]};
    --gray-100: ${sharedTokens.grayDark[100]};
    --gray-200: ${sharedTokens.grayDark[200]};
    --gray-300: ${sharedTokens.grayDark[300]};
    --gray-400: ${sharedTokens.grayDark[400]};
    --gray-500: ${sharedTokens.grayDark[500]};
    --gray-600: ${sharedTokens.grayDark[600]};
    --gray-700: ${sharedTokens.grayDark[700]};
    --gray-800: ${sharedTokens.grayDark[800]};
    --gray-900: ${sharedTokens.grayDark[900]};
    
    --shadow-sm: ${sharedTokens.shadowsDark.sm};
    --shadow-md: ${sharedTokens.shadowsDark.md};
    --shadow-lg: ${sharedTokens.shadowsDark.lg};
    --shadow-xl: ${sharedTokens.shadowsDark.xl};
  }

  /* ==========================================================================
     ANIMATION KEYFRAMES
     ========================================================================== */

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

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

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(100%);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }

  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  @keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }

  /* ==========================================================================
     ANIMATION UTILITY CLASSES
     ========================================================================== */

  .animate-fadeIn {
    animation: fadeIn var(--transition-page-enter) forwards;
  }

  .animate-fadeInUp {
    animation: fadeInUp var(--transition-page-enter) forwards;
  }

  .animate-fadeInDown {
    animation: fadeInDown var(--transition-page-enter) forwards;
  }

  .animate-slideInLeft {
    animation: slideInLeft var(--transition-page-enter) forwards;
  }

  .animate-slideInRight {
    animation: slideInRight var(--transition-page-enter) forwards;
  }

  .animate-scaleIn {
    animation: scaleIn var(--transition-page-enter) forwards;
  }

  .animate-slideUp {
    animation: slideUp var(--transition-page-enter) forwards;
  }

  .animate-pulse {
    animation: pulse 2s infinite;
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }

  .animate-bounce {
    animation: bounce 1s infinite;
  }

  /* Staggered children animations */
  .animate-stagger > * {
    opacity: 0;
    animation: fadeInUp var(--transition-page-enter) forwards;
  }

  .animate-stagger > *:nth-child(1) { animation-delay: 0ms; }
  .animate-stagger > *:nth-child(2) { animation-delay: 50ms; }
  .animate-stagger > *:nth-child(3) { animation-delay: 100ms; }
  .animate-stagger > *:nth-child(4) { animation-delay: 150ms; }
  .animate-stagger > *:nth-child(5) { animation-delay: 200ms; }
  .animate-stagger > *:nth-child(6) { animation-delay: 250ms; }
  .animate-stagger > *:nth-child(7) { animation-delay: 300ms; }
  .animate-stagger > *:nth-child(8) { animation-delay: 350ms; }

  /* Page transition container */
  .page-transition-enter {
    opacity: 0;
    transform: translateY(10px);
  }

  .page-transition-enter-active {
    opacity: 1;
    transform: translateY(0);
    transition: opacity var(--transition-page-enter), transform var(--transition-page-enter);
  }

  .page-transition-exit {
    opacity: 1;
  }

  .page-transition-exit-active {
    opacity: 0;
    transition: opacity var(--transition-page-exit);
  }

  /* ==========================================================================
     BASE STYLES
     ========================================================================== */

  html {
    font-size: 16px;
    scroll-behavior: smooth;
    height: 100%;
    -webkit-text-size-adjust: 100%;
    -webkit-tap-highlight-color: transparent;
  }

  body {
    margin: 0;
    font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.6;
    color: var(--gray-800);
    background-color: var(--gray-50);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    height: 100%;
    overflow-x: hidden;
    transition: background-color var(--transition-normal), color var(--transition-normal);
  }

  #root {
    height: 100%;
    min-height: 100vh;
  }

  /* Typography */
  h1, h2, h3, h4, h5, h6 {
    font-family: 'Source Sans Pro', sans-serif;
    font-weight: 600;
    line-height: 1.3;
    margin-bottom: 0.5em;
    color: var(--gray-900);
    transition: color var(--transition-normal);
  }

  h1 { font-size: 2rem; font-weight: 700; }
  h2 { font-size: 1.5rem; }
  h3 { font-size: 1.25rem; }
  h4 { font-size: 1.125rem; }
  h5 { font-size: 1rem; }
  h6 { font-size: 0.875rem; }

  p {
    margin-bottom: 1rem;
    color: var(--gray-700);
    transition: color var(--transition-normal);
  }

  a {
    color: inherit;
    text-decoration: none;
    transition: color var(--transition-fast);
  }

  /* Interactive Elements */
  button, input, select, textarea {
    font-family: inherit;
    font-size: inherit;
  }

  button {
    cursor: pointer;
    border: none;
    outline: none;
    background: transparent;
    transition: all var(--transition-fast);
  }

  /* Touch-friendly targets */
  button, a, input, select, textarea, [role="button"] {
    min-height: 44px;
    
    @media (min-width: 900px) {
      min-height: 36px;
    }
  }

  /* Images */
  img, svg {
    max-width: 100%;
    height: auto;
    display: block;
  }

  /* Lists */
  ul, ol {
    list-style: none;
  }

  /* Tables */
  table {
    border-collapse: collapse;
    width: 100%;
  }

  /* Focus Styles (Accessibility) */
  :focus-visible {
    outline: 2px solid ${sharedTokens.status.info};
    outline-offset: 2px;
  }

  /* Selection */
  ::selection {
    background-color: rgba(0, 137, 123, 0.2);
    color: inherit;
  }

  [data-theme="dark"] ::selection {
    background-color: rgba(77, 182, 172, 0.3);
  }

  /* Scrollbar Styling */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    background: var(--gray-100);
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb {
    background: var(--gray-300);
    border-radius: 4px;
    
    &:hover {
      background: var(--gray-400);
    }
  }

  /* ==========================================================================
     UTILITY CLASSES
     ========================================================================== */

  .visually-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  .truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* Responsive Visibility */
  .hide-mobile {
    @media (max-width: 599px) {
      display: none !important;
    }
  }

  .hide-tablet {
    @media (min-width: 600px) and (max-width: 899px) {
      display: none !important;
    }
  }

  .hide-desktop {
    @media (min-width: 900px) {
      display: none !important;
    }
  }

  .show-mobile-only {
    @media (min-width: 600px) {
      display: none !important;
    }
  }

  .show-tablet-up {
    @media (max-width: 599px) {
      display: none !important;
    }
  }

  .show-desktop-only {
    @media (max-width: 899px) {
      display: none !important;
    }
  }

  /* Skeleton Loading */
  .skeleton {
    background: linear-gradient(
      90deg,
      var(--gray-200) 25%,
      var(--gray-100) 50%,
      var(--gray-200) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: var(--radius-sm);
  }

  /* Reduced Motion */
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
`;

// =============================================================================
// STYLED COMPONENTS (Layout Helpers)
// =============================================================================

export const Background = styled.div`
  min-height: 100vh;
  width: 100%;
  background: url('/src/assets/background.png') no-repeat center center fixed;
  background-size: cover;
  padding: 10px 20px;
  
  @media (max-width: 600px) {
    padding: 8px 12px;
  }
`;

export const WrapperStyle = styled.div`
  border: 5px solid white;
  border-radius: 30px;
  height: calc(100vh - 20px);
  display: flex;
  flex-direction: column;
  position: relative;
  
  @media (max-width: 600px) {
    border-width: 3px;
    border-radius: 20px;
    height: calc(100vh - 16px);
  }
`;

export const Container = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  height: 100vh;
  min-height: 0;
  background-color: var(--gray-50);
  transition: background-color var(--transition-normal);
`;

export const Header = styled.header`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background-color: #FFFFFF;
  border-bottom: 1px solid var(--gray-200);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
  
  [data-theme="dark"] & {
    background-color: var(--gray-100);
    border-color: var(--gray-200);
  }
  
  @media (min-width: 900px) {
    padding: 1.25rem 2rem;
  }
`;

export const Title = styled.h1`
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--gray-900);
  margin: 0;
  letter-spacing: -0.5px;
  
  @media (min-width: 900px) {
    font-size: 2rem;
  }
`;

export const Content = styled.main`
  display: flex;
  flex-direction: column;
  padding: 1rem;
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  overflow-y: auto;
  
  @media (min-width: 600px) {
    padding: 1.5rem;
  }
  
  @media (min-width: 900px) {
    padding: 2rem;
  }
`;

export const PageHeader = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--gray-200);
  animation: fadeInDown var(--transition-page-enter) forwards;
  
  @media (min-width: 600px) {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 2rem;
  }
`;

export const PageTitle = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  
  @media (min-width: 900px) {
    font-size: 1.5rem;
    gap: 1rem;
  }
`;

export const Logo = styled.img`
  width: 40px;
  height: 40px;
  
  @media (min-width: 900px) {
    width: 56px;
    height: 56px;
  }
`;

interface CardProps {
  width?: string;
}

export const Card = styled.div<CardProps>`
  background: rgba(255, 255, 255, 0.95);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: 1.25rem;
  max-width: ${(props) => props.width || '100%'};
  width: 100%;
  display: flex;
  flex-direction: column;
  animation: scaleIn var(--transition-page-enter) forwards;
  transition: all var(--transition-normal);
  
  [data-theme="dark"] & {
    background: rgba(30, 41, 59, 0.95);
  }
  
  @media (min-width: 600px) {
    padding: 1.5rem;
    max-width: ${(props) => props.width || '490px'};
  }
`;

export const Subtitle = styled.p`
  font-size: 0.875rem;
  color: var(--gray-600);
  margin-bottom: 1.5rem;
  text-align: center;
  
  @media (min-width: 600px) {
    font-size: 1rem;
  }
`;

// =============================================================================
// RESPONSIVE GRID
// =============================================================================

export const Grid = styled.div<{ columns?: number; gap?: string }>`
  display: grid;
  grid-template-columns: 1fr;
  gap: ${props => props.gap || '1rem'};
  
  @media (min-width: 600px) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (min-width: 900px) {
    grid-template-columns: repeat(${props => props.columns || 3}, 1fr);
  }
`;

// =============================================================================
// FLEX UTILITIES
// =============================================================================

export const Flex = styled.div<{
  direction?: 'row' | 'column';
  align?: string;
  justify?: string;
  gap?: string;
  wrap?: boolean;
}>`
  display: flex;
  flex-direction: ${props => props.direction || 'row'};
  align-items: ${props => props.align || 'stretch'};
  justify-content: ${props => props.justify || 'flex-start'};
  gap: ${props => props.gap || '0'};
  flex-wrap: ${props => props.wrap ? 'wrap' : 'nowrap'};
`;

export const Stack = styled(Flex)`
  flex-direction: column;
`;

export const Row = styled(Flex)`
  flex-direction: row;
`;

// =============================================================================
// ANIMATED PAGE WRAPPER
// =============================================================================

export const AnimatedPage = styled.div<{ delay?: number }>`
  animation: fadeInUp var(--transition-page-enter) forwards;
  animation-delay: ${props => props.delay || 0}ms;
  opacity: 0;
`;

export const StaggeredList = styled.div`
  & > * {
    opacity: 0;
    animation: fadeInUp var(--transition-page-enter) forwards;
  }
  
  & > *:nth-child(1) { animation-delay: 0ms; }
  & > *:nth-child(2) { animation-delay: 50ms; }
  & > *:nth-child(3) { animation-delay: 100ms; }
  & > *:nth-child(4) { animation-delay: 150ms; }
  & > *:nth-child(5) { animation-delay: 200ms; }
  & > *:nth-child(6) { animation-delay: 250ms; }
`;
