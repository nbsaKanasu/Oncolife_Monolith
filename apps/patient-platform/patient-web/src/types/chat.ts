export interface Message {
  id: number;
  chat_uuid: string;
  sender: 'user' | 'assistant';
  message_type: 
    | 'text' 
    | 'button_response' 
    | 'multi_select_response' 
    | 'single-select' 
    | 'multi-select' 
    | 'button_prompt' 
    | 'feeling-select' 
    | 'feeling_response'
    | 'symptom-select'  // New: Symptom checker selection
    | 'yes_no'          // New: Yes/No questions
    | 'choice'          // New: Single choice
    | 'multiselect'     // New: Multi-select
    | 'number'          // New: Number input
    | 'triage_result';  // New: Triage result display
  content: string;
  structured_data?: {
    options?: string[];
    options_data?: Array<{ label: string; value: any; category?: string }>;
    selected_options?: string[];
    max_selections?: number;
    frontend_type?: string;
    triage_level?: 'call_911' | 'notify_care_team' | 'none';
    is_complete?: boolean;
  };
  created_at: string;
}

export interface ChatSession {
  chat_uuid: string;
  conversation_state: string;
  messages: Message[];
  is_new_session: boolean;
  symptom_list: string[];  // Add symptom list from backend
}

export type ResponseType = 'text' | 'button_prompt' | 'multi_select' | 'button_response' | 'multi_select_response' | 'feeling-select' | 'feeling_response'; 