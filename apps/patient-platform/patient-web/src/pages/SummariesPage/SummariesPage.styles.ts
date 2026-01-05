/**
 * OncoLife Ruby - Summaries Page Styles
 * Responsive, themed design for symptom check-in summaries
 */

import styled from "styled-components";

// Theme colors (Patient)
const colors = {
  primary: '#00897B',
  primaryLight: '#4DB6AC',
  primaryDark: '#00695C',
  secondary: '#7E57C2',
  background: '#F5F7FA',
  paper: '#FFFFFF',
  text: '#1E293B',
  textSecondary: '#64748B',
  border: '#E2E8F0',
};

export const Container = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100%;
  background-color: ${colors.background};
`;

export const Header = styled.div`
  display: flex;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, ${colors.primary} 0%, ${colors.primaryDark} 100%);
  color: white;
  
  @media (max-width: 576px) {
    padding: 16px;
  }
`;

export const Title = styled.h1`
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  margin: 0;
  
  @media (max-width: 576px) {
    font-size: 1.25rem;
  }
`;

export const Content = styled.div`
  display: flex;
  flex-direction: column;
  padding: 24px;
  flex: 1;
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
  
  @media (max-width: 768px) {
    padding: 16px;
  }
`;

export const PageHeader = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
  
  @media (min-width: 768px) {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
`;

export const PageTitle = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  color: ${colors.text};
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  
  @media (max-width: 576px) {
    font-size: 1.125rem;
  }
`;

export const NavigationContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  
  .btn-primary {
    background: ${colors.primary};
    border-color: ${colors.primary};
    font-weight: 600;
    font-size: 0.875rem;
    padding: 8px 16px;
    border-radius: 8px;
    transition: all 0.2s ease;
    
    &:hover {
      background: ${colors.primaryDark};
      border-color: ${colors.primaryDark};
      transform: translateY(-1px);
    }
  }
`;

export const DateNavigationGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  background: ${colors.paper};
  padding: 6px;
  border-radius: 12px;
  border: 1px solid ${colors.border};
`;

export const NavigationButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: ${colors.textSecondary};
  
  &:hover {
    background: ${colors.background};
    color: ${colors.primary};
  }
  
  svg {
    width: 18px;
    height: 18px;
  }
`;

export const DatePickerContainer = styled.div`
  display: flex;
  align-items: center;
  
  .MuiTextField-root {
    min-width: 160px;
  }
  
  .MuiInputBase-root {
    background-color: transparent;
    border-radius: 8px;
    font-size: 0.9375rem;
    
    fieldset {
      border: none;
    }
  }
`;

export const CurrentDateDisplay = styled.span`
  color: ${colors.text};
  font-weight: 600;
  font-size: 0.9375rem;
  padding: 0 8px;
  min-width: 120px;
  text-align: center;
`;

export const DateDisplayButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  height: 36px;
  min-width: 160px;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: ${colors.text};
  font-weight: 600;
  font-size: 0.9375rem;
  
  &:hover {
    background: ${colors.background};
    color: ${colors.primary};
  }
  
  svg {
    width: 16px;
    height: 16px;
    color: ${colors.textSecondary};
  }
`;

export const LoadingContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  gap: 16px;
  
  span {
    color: ${colors.textSecondary};
    font-size: 0.9375rem;
  }
`;

export const ErrorContainer = styled.div`
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 20px;
  color: #991B1B;
  display: flex;
  align-items: center;
  gap: 12px;
`;

export const EmptyState = styled.div`
  text-align: center;
  padding: 64px 24px;
  background: ${colors.paper};
  border-radius: 16px;
  border: 2px dashed ${colors.border};
  
  .empty-icon {
    font-size: 3rem;
    margin-bottom: 16px;
  }
  
  h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: ${colors.text};
    margin: 0 0 8px 0;
  }
  
  p {
    font-size: 0.9375rem;
    color: ${colors.textSecondary};
    margin: 0;
    max-width: 400px;
    margin: 0 auto;
  }
`;

// Summary Card Styles
export const SummaryCard = styled.div`
  background: ${colors.paper};
  border-radius: 14px;
  border: 1px solid ${colors.border};
  overflow: hidden;
  transition: all 0.2s ease;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
    border-color: ${colors.primary}50;
  }
`;

export const SummaryCardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: linear-gradient(135deg, ${colors.primary}08 0%, ${colors.secondary}08 100%);
  border-bottom: 1px solid ${colors.border};
`;

export const SummaryDate = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: ${colors.text};
  font-size: 0.9375rem;
  
  svg {
    color: ${colors.primary};
  }
`;

export const SummaryBadge = styled.span<{ $severity?: 'mild' | 'moderate' | 'severe' | 'urgent' }>`
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  
  ${props => {
    switch (props.$severity) {
      case 'urgent':
        return `
          background: #DC262615;
          color: #DC2626;
          border: 1px solid #DC262630;
        `;
      case 'severe':
        return `
          background: #EA580C15;
          color: #EA580C;
          border: 1px solid #EA580C30;
        `;
      case 'moderate':
        return `
          background: #F59E0B15;
          color: #D97706;
          border: 1px solid #F59E0B30;
        `;
      default:
        return `
          background: #10B98115;
          color: #059669;
          border: 1px solid #10B98130;
        `;
    }
  }}
`;

export const SummaryCardContent = styled.div`
  padding: 16px 20px;
`;

export const SummarySymptoms = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
`;

export const SymptomTag = styled.span`
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  background: ${colors.background};
  color: ${colors.text};
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
`;

export const SummaryText = styled.p`
  font-size: 0.875rem;
  color: ${colors.textSecondary};
  margin: 0;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

export const ViewDetailsLink = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 12px 20px;
  border-top: 1px solid ${colors.border};
  color: ${colors.primary};
  font-size: 0.8125rem;
  font-weight: 600;
  
  svg {
    margin-left: 4px;
    transition: transform 0.2s;
  }
  
  &:hover svg {
    transform: translateX(4px);
  }
`;

export const SummaryGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;
