import React, { useState } from 'react';
import { CircularProgress } from '@mui/material';
import { Button } from 'react-bootstrap';
import { 
  PageHeader, 
  PageTitle, 
  NavigationContainer,
  DateNavigationGroup,
  NavigationButton,
  LoadingContainer,
  ErrorContainer,
} from './SummariesPage.styles';
import { DatePicker as SharedDatePicker, Container, Header, Title, Content } from '@oncolife/ui-components';
import { useSummaries, type Summary } from '../../services/summaries';
import { SummaryGrid } from './components';
import dayjs, { Dayjs } from 'dayjs';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const SummariesPage: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());
  const navigate = useNavigate();
  
  const { data, isLoading, error } = useSummaries(
    selectedDate.year(), 
    selectedDate.month() + 1
  );

  const handleDateChange = (newDate: Dayjs | null) => {
    if (newDate) {
      setSelectedDate(newDate);
    }
  };

  const goToPreviousMonth = () => {
    setSelectedDate(selectedDate.subtract(1, 'month'));
  };

  const goToNextMonth = () => {
    setSelectedDate(selectedDate.add(1, 'month'));
  };

  const goToToday = () => {
    setSelectedDate(dayjs());
  };

  const handleViewDetails = (summaryId: string) => {
    navigate(`/summaries/${summaryId}`);
  };


  return (
    <Container>
      <Header>
        <Title>Summaries</Title>
      </Header>
      
      <Content>
        <PageHeader>
          <PageTitle>
            Monthly Summaries
          </PageTitle>
          
          <NavigationContainer>
            <DateNavigationGroup>
              <NavigationButton onClick={goToPreviousMonth}>
                <ChevronLeft />
              </NavigationButton>
              
              <SharedDatePicker
                value={selectedDate}
                onChange={handleDateChange}
              />
              
              <NavigationButton onClick={goToNextMonth}>
                <ChevronRight />
              </NavigationButton>
            </DateNavigationGroup>
            
            <Button 
              variant="primary" 
              onClick={goToToday}
              size="sm"
            >
              Today
            </Button>
          </NavigationContainer>
        </PageHeader>

        {error && (
          <ErrorContainer>
            <strong>Error:</strong> {error.message || 'Failed to load summaries'}
          </ErrorContainer>
        )}

        {isLoading ? (
          <LoadingContainer>
            <CircularProgress size={48} />
          </LoadingContainer>
        ) : (
          <SummaryGrid 
            summaries={data || { data: [] }} 
            onViewDetails={handleViewDetails} 
          />
        )}
      </Content>
    </Container>
  );
};

export default SummariesPage; 