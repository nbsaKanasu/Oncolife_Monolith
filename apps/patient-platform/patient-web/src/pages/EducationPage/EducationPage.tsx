/**
 * OncoLife Ruby - Education Page
 * Educational resources for cancer patients
 */

import React from 'react';
import { useTheme, useMediaQuery } from '@mui/material';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import styled from 'styled-components';
import { 
  BookOpen, 
  FileText, 
  Heart, 
  Pill, 
  Apple, 
  Activity,
  ChevronRight,
  Download
} from 'lucide-react';

// Theme colors
const colors = {
  primary: '#00897B',
  primaryLight: '#4DB6AC',
  secondary: '#7E57C2',
  background: '#F5F7FA',
  paper: '#FFFFFF',
  text: '#1E293B',
  textSecondary: '#64748B',
  border: '#E2E8F0',
};

const PageContainer = styled.div`
  min-height: 100%;
  background: ${colors.background};
`;

const PageHeader = styled.div`
  background: linear-gradient(135deg, ${colors.primary} 0%, #00695C 100%);
  padding: 24px;
  color: white;
  
  @media (max-width: 576px) {
    padding: 16px;
  }
`;

const HeaderContent = styled.div`
  max-width: 800px;
  margin: 0 auto;
`;

const PageTitle = styled.h1`
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
  
  @media (max-width: 576px) {
    font-size: 1.5rem;
  }
`;

const PageSubtitle = styled.p`
  font-size: 1rem;
  opacity: 0.9;
  margin: 0;
  
  @media (max-width: 576px) {
    font-size: 0.875rem;
  }
`;

const ContentArea = styled.div`
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
  
  @media (max-width: 576px) {
    padding: 16px;
  }
`;

const SectionTitle = styled.h2`
  font-size: 1.125rem;
  font-weight: 600;
  color: ${colors.text};
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ResourceGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 32px;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const ResourceCard = styled.div<{ $accentColor?: string }>`
  background: ${colors.paper};
  border-radius: 14px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid ${colors.border};
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: ${props => props.$accentColor || colors.primary};
  }
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    border-color: ${props => props.$accentColor || colors.primary}50;
  }
`;

const CardIcon = styled.div<{ $color?: string }>`
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: ${props => props.$color ? `${props.$color}15` : `${colors.primary}15`};
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  
  svg {
    color: ${props => props.$color || colors.primary};
  }
`;

const CardTitle = styled.h3`
  font-size: 1.0625rem;
  font-weight: 600;
  color: ${colors.text};
  margin: 0 0 6px 0;
`;

const CardDescription = styled.p`
  font-size: 0.875rem;
  color: ${colors.textSecondary};
  margin: 0;
  line-height: 1.5;
`;

const CardAction = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 16px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: ${colors.primary};
  
  svg {
    transition: transform 0.2s;
  }
  
  &:hover svg {
    transform: translateX(4px);
  }
`;

const QuickTip = styled.div`
  background: linear-gradient(135deg, ${colors.secondary}15 0%, ${colors.primary}15 100%);
  border-radius: 14px;
  padding: 20px;
  border: 1px solid ${colors.border};
  margin-bottom: 24px;
`;

const TipHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  
  h4 {
    font-size: 1rem;
    font-weight: 600;
    color: ${colors.text};
    margin: 0;
  }
`;

const TipContent = styled.p`
  font-size: 0.9375rem;
  color: ${colors.textSecondary};
  margin: 0;
  line-height: 1.6;
`;

const ComingSoonBadge = styled.span`
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  background: ${colors.secondary}15;
  color: ${colors.secondary};
  border-radius: 20px;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-left: auto;
`;

const resources = [
  {
    icon: Pill,
    title: 'Managing Side Effects',
    description: 'Learn about common chemotherapy side effects and strategies to manage them.',
    color: '#00897B',
  },
  {
    icon: Apple,
    title: 'Nutrition During Treatment',
    description: 'Dietary guidelines and tips for maintaining nutrition during cancer treatment.',
    color: '#10B981',
  },
  {
    icon: Heart,
    title: 'Emotional Wellness',
    description: 'Resources for emotional support and mental health during your cancer journey.',
    color: '#EC4899',
  },
  {
    icon: Activity,
    title: 'Staying Active',
    description: 'Safe exercise and physical activity recommendations during treatment.',
    color: '#F59E0B',
  },
];

const handouts = [
  {
    title: 'Care Team Contact Sheet',
    description: 'Important phone numbers and contacts for your care team.',
  },
  {
    title: 'Symptom Diary Template',
    description: 'Printable diary to track your symptoms between appointments.',
  },
  {
    title: 'Medication Schedule',
    description: 'Track your medications and when to take them.',
  },
];

const EducationPage: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <PageContainer>
      <PageHeader>
        <HeaderContent>
          <PageTitle>
            <BookOpen size={28} />
            Education Center
          </PageTitle>
          <PageSubtitle>
            Learn about your treatment and find helpful resources
          </PageSubtitle>
        </HeaderContent>
      </PageHeader>
      
      <ContentArea>
        {/* Quick Tip */}
        <QuickTip>
          <TipHeader>
            <span style={{ fontSize: '1.25rem' }}>💡</span>
            <h4>Tip of the Day</h4>
          </TipHeader>
          <TipContent>
            Staying hydrated is especially important during chemotherapy. Aim for 8-10 glasses
            of water daily, and keep a water bottle nearby as a reminder.
          </TipContent>
        </QuickTip>
        
        {/* Resource Categories */}
        <SectionTitle>
          <FileText size={20} color={colors.primary} />
          Learning Resources
        </SectionTitle>
        
        <ResourceGrid>
          {resources.map((resource, index) => {
            const Icon = resource.icon;
            return (
              <ResourceCard key={index} $accentColor={resource.color}>
                <CardIcon $color={resource.color}>
                  <Icon size={24} />
                </CardIcon>
                <CardTitle>{resource.title}</CardTitle>
                <CardDescription>{resource.description}</CardDescription>
                <CardAction>
                  Learn More <ChevronRight size={16} style={{ marginLeft: 4 }} />
                </CardAction>
              </ResourceCard>
            );
          })}
        </ResourceGrid>
        
        {/* Handouts Section */}
        <SectionTitle>
          <Download size={20} color={colors.primary} />
          Care Team Handouts
          <ComingSoonBadge>Coming Soon</ComingSoonBadge>
        </SectionTitle>
        
        <Box sx={{ mb: 4 }}>
          {handouts.map((handout, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                p: 2,
                mb: 1.5,
                bgcolor: colors.paper,
                borderRadius: 2,
                border: `1px solid ${colors.border}`,
                cursor: 'pointer',
                transition: 'all 0.2s',
                '&:hover': {
                  bgcolor: colors.background,
                  borderColor: colors.primary,
                },
              }}
            >
              <Box>
                <Typography variant="body1" fontWeight={600} color={colors.text}>
                  {handout.title}
                </Typography>
                <Typography variant="body2" color={colors.textSecondary}>
                  {handout.description}
                </Typography>
              </Box>
              <Download size={20} color={colors.textSecondary} />
            </Box>
          ))}
        </Box>
        
        {/* Footer Note */}
        <Box sx={{ 
          textAlign: 'center', 
          py: 4, 
          color: colors.textSecondary,
          fontSize: '0.8125rem',
        }}>
          <Typography variant="caption" color="textSecondary">
            📌 This information is for educational purposes only and does not replace 
            professional medical advice. Always consult your care team for personalized guidance.
          </Typography>
        </Box>
      </ContentArea>
    </PageContainer>
  );
};

export default EducationPage;
