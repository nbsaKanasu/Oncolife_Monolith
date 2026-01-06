import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../utils/apiClient';
import { API_CONFIG } from '../config/api';

export interface PatientSummary {
  id: string;
  patientName: string;
  dateOfBirth: string;
  mrn: string;
  symptoms: string;
  summary: string;
  lastUpdated: string;
  status: 'active' | 'inactive' | 'pending';
  priority: 'high' | 'medium' | 'low';
}

// ===== New Types for Dashboard API =====

export interface PatientRanking {
  patient_uuid: string;
  first_name: string;
  last_name: string;
  email_address: string;
  last_checkin: string;
  max_severity: string;
  has_escalation: boolean;
  severity_badge: 'mild' | 'moderate' | 'severe' | 'urgent';
}

export interface DashboardLanding {
  patients: PatientRanking[];
  total_patients: number;
  period_days: number;
}

export interface SymptomDataPoint {
  date: string;
  severity: string;
  severity_numeric: number;
}

export interface TreatmentEvent {
  event_type: string;
  event_date: string;
  metadata: Record<string, unknown>;
}

export interface PatientTimeline {
  patient_uuid: string;
  period_days: number;
  symptom_series: Record<string, SymptomDataPoint[]>;
  treatment_events: TreatmentEvent[];
}

export interface SharedQuestion {
  id: string;
  question_text: string;
  category: string;
  is_answered: boolean;
  created_at: string;
}

export interface WeeklyReportSummary {
  report_id: string;
  physician_id: string;
  report_week_start: string;
  report_week_end: string;
  generated_at: string;
  total_patients: number;
  escalation_count: number;
  s3_path?: string;
}

export interface WeeklyReportData {
  report_week_start: string;
  report_week_end: string;
  physician_id: string;
  patients: Array<{
    patient_uuid: string;
    first_name: string;
    last_name: string;
    max_severity: string;
    escalation_count: number;
    symptom_data: SymptomDataPoint[];
    shared_questions: SharedQuestion[];
  }>;
  summary_stats: {
    total_patients: number;
    total_escalations: number;
    severity_breakdown: Record<string, number>;
  };
}

export interface DashboardResponse {
  data: PatientSummary[];
  total: number;
  page: number;
  totalPages: number;
}

// Mock data for development
const mockPatientSummaries: PatientSummary[] = [
  {
    id: '1',
    patientName: 'John Doe',
    dateOfBirth: 'January 1, 2001',
    mrn: 'A123456',
    symptoms: 'Fatigue, weight loss, localized pain',
    summary: 'The patient is a diagnosed case of breast cancer, currently under chemotherapy treatment. Presenting symptoms included fatigue, weight loss, and localized pain in the right breast area.',
    lastUpdated: 'April 19, 2025',
    status: 'active',
    priority: 'high'
  },
  {
    id: '2',
    patientName: 'Jane Smith',
    dateOfBirth: 'March 15, 1985',
    mrn: 'B789012',
    symptoms: 'Chest pain, shortness of breath',
    summary: 'Patient diagnosed with lung cancer, currently receiving radiotherapy. Experiencing chest pain and shortness of breath.',
    lastUpdated: 'April 18, 2025',
    status: 'active',
    priority: 'medium'
  },
  {
    id: '3',
    patientName: 'Robert Johnson',
    dateOfBirth: 'July 22, 1978',
    mrn: 'C345678',
    symptoms: 'Abdominal discomfort, changes in bowel habits',
    summary: 'Colon cancer diagnosis, post-surgical follow-up. Monitoring for any recurrence signs.',
    lastUpdated: 'April 17, 2025',
    status: 'active',
    priority: 'low'
  },
  {
    id: '4',
    patientName: 'Sarah Wilson',
    dateOfBirth: 'November 8, 1992',
    mrn: 'D901234',
    symptoms: 'Headaches, vision changes',
    summary: 'Brain tumor case, currently under observation. Regular monitoring of neurological symptoms.',
    lastUpdated: 'April 16, 2025',
    status: 'pending',
    priority: 'high'
  },
  {
    id: '5',
    patientName: 'Michael Brown',
    dateOfBirth: 'September 12, 1965',
    mrn: 'E567890',
    symptoms: 'Bone pain, fractures',
    summary: 'Multiple myeloma diagnosis, receiving targeted therapy. Managing bone pain and monitoring for fractures.',
    lastUpdated: 'April 15, 2025',
    status: 'active',
    priority: 'medium'
  },
  {
    id: '6',
    patientName: 'Emily Davis',
    dateOfBirth: 'February 28, 1989',
    mrn: 'F123789',
    symptoms: 'Skin lesions, itching',
    summary: 'Melanoma case, post-excision monitoring. Regular skin checks and follow-up appointments.',
    lastUpdated: 'April 14, 2025',
    status: 'active',
    priority: 'low'
  },
  {
    id: '7',
    patientName: 'David Miller',
    dateOfBirth: 'May 10, 1972',
    mrn: 'G456123',
    symptoms: 'Back pain, weakness in legs',
    summary: 'Spinal cord tumor, post-operative care. Physical therapy ongoing for mobility improvement.',
    lastUpdated: 'April 13, 2025',
    status: 'active',
    priority: 'medium'
  },
  {
    id: '8',
    patientName: 'Lisa Anderson',
    dateOfBirth: 'December 3, 1983',
    mrn: 'H789456',
    symptoms: 'Irregular periods, pelvic pain',
    summary: 'Ovarian cancer diagnosis, chemotherapy treatment. Monitoring for treatment response and side effects.',
    lastUpdated: 'April 12, 2025',
    status: 'active',
    priority: 'high'
  }
];

const fetchPatientSummaries = async (
  page: number = 1, 
  search: string = '', 
  filter: string = 'all'
): Promise<DashboardResponse> => {
  // For now, return mock data
  // In production, this would be:
  // const response = await apiClient.get<DashboardResponse>(
  //   `${API_CONFIG.ENDPOINTS.DASHBOARD}/patients?page=${page}&search=${search}&filter=${filter}`
  // );
  // return response.data;
  
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 300));
  
  let filteredData = mockPatientSummaries;
  
  // Apply search filter
  if (search) {
    filteredData = filteredData.filter(patient => 
      patient.patientName.toLowerCase().includes(search.toLowerCase()) ||
      patient.mrn.toLowerCase().includes(search.toLowerCase())
    );
  }
  
  // Apply status filter
  if (filter && filter !== 'all') {
    filteredData = filteredData.filter(patient => patient.status === filter);
  }
  
  const itemsPerPage = 4;
  const startIndex = (page - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedData = filteredData.slice(startIndex, endIndex);
  
  return {
    data: paginatedData,
    total: filteredData.length,
    page,
    totalPages: Math.ceil(filteredData.length / itemsPerPage)
  };
};

export const usePatientSummaries = (
  page: number = 1, 
  search: string = '', 
  filter: string = 'all'
) => {
  return useQuery({
    queryKey: ['patientSummaries', page, search, filter],
    queryFn: () => fetchPatientSummaries(page, search, filter),
  });
};

// Fetch individual patient details
const fetchPatientDetails = async (patientId: string): Promise<PatientSummary> => {
  // For now, return mock data
  // In production, this would be:
  // const response = await apiClient.get<PatientSummary>(
  //   `${API_CONFIG.ENDPOINTS.DASHBOARD}/patients/${patientId}`
  // );
  // return response.data;
  
  await new Promise(resolve => setTimeout(resolve, 200));
  
  const patient = mockPatientSummaries.find(p => p.id === patientId);
  if (!patient) {
    throw new Error('Patient not found');
  }
  
  return patient;
};

export const usePatientDetails = (patientId: string) => {
  return useQuery({
    queryKey: ['patientDetails', patientId],
    queryFn: () => fetchPatientDetails(patientId),
    enabled: !!patientId,
  });
};

// ===== Real API Functions for Dashboard =====

// Fetch dashboard landing (ranked patient list)
const fetchDashboardLanding = async (days: number = 7): Promise<DashboardLanding> => {
  try {
    const response = await apiClient.get(
      `${API_CONFIG.ENDPOINTS.DASHBOARD.LANDING}?days=${days}`
    );
    return response.data;
  } catch {
    // Fallback to mock data if API not ready
    return {
      patients: mockPatientSummaries.map(p => ({
        patient_uuid: p.id,
        first_name: p.patientName.split(' ')[0],
        last_name: p.patientName.split(' ')[1] || '',
        email_address: `${p.patientName.toLowerCase().replace(' ', '.')}@example.com`,
        last_checkin: p.lastUpdated,
        max_severity: p.priority === 'high' ? 'severe' : p.priority === 'medium' ? 'moderate' : 'mild',
        has_escalation: p.priority === 'high',
        severity_badge: p.priority === 'high' ? 'severe' : p.priority === 'medium' ? 'moderate' : 'mild' as 'mild' | 'moderate' | 'severe' | 'urgent',
      })),
      total_patients: mockPatientSummaries.length,
      period_days: days,
    };
  }
};

export const useDashboardLanding = (days: number = 7) => {
  return useQuery({
    queryKey: ['dashboardLanding', days],
    queryFn: () => fetchDashboardLanding(days),
  });
};

// Fetch patient timeline data
const fetchPatientTimeline = async (
  patientUuid: string,
  days: number = 30
): Promise<PatientTimeline> => {
  try {
    const response = await apiClient.get(
      `${API_CONFIG.ENDPOINTS.DASHBOARD.PATIENT_TIMELINE(patientUuid)}?days=${days}`
    );
    return response.data;
  } catch {
    // Fallback mock data
    return {
      patient_uuid: patientUuid,
      period_days: days,
      symptom_series: {
        'nausea': [
          { date: '2025-01-01', severity: 'mild', severity_numeric: 1 },
          { date: '2025-01-02', severity: 'moderate', severity_numeric: 2 },
          { date: '2025-01-03', severity: 'mild', severity_numeric: 1 },
        ],
        'fatigue': [
          { date: '2025-01-01', severity: 'moderate', severity_numeric: 2 },
          { date: '2025-01-02', severity: 'severe', severity_numeric: 3 },
          { date: '2025-01-03', severity: 'moderate', severity_numeric: 2 },
        ],
      },
      treatment_events: [
        { event_type: 'chemo_start', event_date: '2024-12-16', metadata: { cycle: 1 } },
        { event_type: 'cycle_start', event_date: '2024-12-30', metadata: { cycle: 2 } },
      ],
    };
  }
};

export const usePatientTimeline = (patientUuid: string, days: number = 30) => {
  return useQuery({
    queryKey: ['patientTimeline', patientUuid, days],
    queryFn: () => fetchPatientTimeline(patientUuid, days),
    enabled: !!patientUuid,
  });
};

// Fetch patient's shared questions
const fetchPatientQuestions = async (patientUuid: string): Promise<SharedQuestion[]> => {
  try {
    const response = await apiClient.get(
      API_CONFIG.ENDPOINTS.DASHBOARD.PATIENT_QUESTIONS(patientUuid)
    );
    return response.data.questions || response.data;
  } catch {
    return [];
  }
};

export const usePatientQuestions = (patientUuid: string) => {
  return useQuery({
    queryKey: ['patientQuestions', patientUuid],
    queryFn: () => fetchPatientQuestions(patientUuid),
    enabled: !!patientUuid,
  });
};

// Fetch weekly reports list
const fetchReportsList = async (): Promise<WeeklyReportSummary[]> => {
  try {
    const response = await apiClient.get(API_CONFIG.ENDPOINTS.DASHBOARD.REPORTS_LIST);
    return response.data.reports || response.data;
  } catch {
    return [];
  }
};

export const useReportsList = () => {
  return useQuery({
    queryKey: ['reportsList'],
    queryFn: fetchReportsList,
  });
};

// Fetch weekly report data
const fetchWeeklyReportData = async (weekStart?: string): Promise<WeeklyReportData> => {
  try {
    const url = weekStart 
      ? `${API_CONFIG.ENDPOINTS.DASHBOARD.REPORTS_WEEKLY}?week_start=${weekStart}`
      : API_CONFIG.ENDPOINTS.DASHBOARD.REPORTS_WEEKLY;
    const response = await apiClient.get(url);
    return response.data;
  } catch {
    // Fallback mock data
    const now = new Date();
    const weekStartDate = new Date(now);
    weekStartDate.setDate(now.getDate() - now.getDay());
    const weekEndDate = new Date(weekStartDate);
    weekEndDate.setDate(weekStartDate.getDate() + 6);
    
    return {
      report_week_start: weekStartDate.toISOString().split('T')[0],
      report_week_end: weekEndDate.toISOString().split('T')[0],
      physician_id: 'mock-physician',
      patients: [],
      summary_stats: {
        total_patients: 0,
        total_escalations: 0,
        severity_breakdown: {},
      },
    };
  }
};

export const useWeeklyReportData = (weekStart?: string) => {
  return useQuery({
    queryKey: ['weeklyReport', weekStart],
    queryFn: () => fetchWeeklyReportData(weekStart),
  });
};

// Generate weekly report
const generateWeeklyReport = async (weekStart?: string): Promise<{ report_id: string }> => {
  const response = await apiClient.post(
    API_CONFIG.ENDPOINTS.DASHBOARD.REPORTS_GENERATE,
    { week_start: weekStart }
  );
  return response.data;
};

export const useGenerateReport = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: generateWeeklyReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reportsList'] });
      queryClient.invalidateQueries({ queryKey: ['weeklyReport'] });
    },
  });
};