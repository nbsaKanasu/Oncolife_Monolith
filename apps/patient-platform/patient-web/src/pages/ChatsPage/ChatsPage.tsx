import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { MessageBubble } from '../../components/chat/MessageBubble';
import { MessageInput } from '../../components/chat/MessageInput';
import { ThinkingBubble } from '../../components/chat/ThinkingBubble';
import { CalendarModal } from '../../components/chat/CalendarModal';
import { NewConversationModal } from '../../components/chat/NewConversationModal';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useSymptomList } from '../../hooks/useSymptomList';
import { chatService } from '../../services/chatService';
import { getTodayInUserTimezone } from '@oncolife/shared-utils';
import type { ChatSession, Message } from '../../types/chat';
import '../../components/chat/Chat.css';
import { API_CONFIG } from '../../config/api';
import { getAuthHeaders } from '../../utils/authUtils';

const ChatsPage: React.FC = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [chatSession, setChatSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [isCalendarModalOpen, setIsCalendarModalOpen] = useState(false);
  const [isNewConversationModalOpen, setIsNewConversationModalOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Use the symptom list hook for localStorage management
  const { 
    symptomList, 
    updateSymptomList, 
    addSymptoms, 
    resetSymptomList 
  } = useSymptomList();

  const handleNewMessage = useCallback((wsMessage: any) => {
    console.log('Received WebSocket message:', wsMessage);
    console.log('[DEBUG] Raw WebSocket message type:', wsMessage.type);
    console.log('[DEBUG] Raw WebSocket message data:', {
      id: wsMessage.id,
      message_type: wsMessage.message_type,
      content: wsMessage.content,
      structured_data: wsMessage.structured_data
    });

    setMessages(prevMessages => {
      console.log('[DEBUG] Processing WebSocket message, current messages count:', prevMessages.length);
      
      if (wsMessage.type === 'message_chunk') {
        console.log('Processing message chunk:', wsMessage);
        setIsThinking(false);
        const messageIndex = prevMessages.findIndex(m => m.id === wsMessage.message_id);
        if (messageIndex !== -1) {
          const updatedMessages = [...prevMessages];
          updatedMessages[messageIndex].content += wsMessage.content;
          console.log('[DEBUG] Updated existing message at index:', messageIndex);
          return updatedMessages;
        } else {
          const newMessage: Message = {
            id: wsMessage.message_id,
            chat_uuid: chatSession?.chat_uuid || '',
            sender: 'assistant',
            message_type: 'text',
            content: wsMessage.content,
            created_at: new Date().toISOString(),
          };
          console.log('[DEBUG] Created new message from chunk:', newMessage);
          return [...prevMessages, newMessage];
        }
      } else if (wsMessage.type === 'message_end') {
        console.log('Processing message end:', wsMessage);
        setIsThinking(false);
        return prevMessages;
      } else if (wsMessage.id) {
        console.log('Processing complete message:', wsMessage);
        setIsThinking(false);
        
        // Check if this is a final summary message (indicates conversation completion)
        if (wsMessage.content && wsMessage.content.includes('Thank you for completing this chat!')) {
          // Update the chat session state to COMPLETED
          setChatSession(prev => prev ? { ...prev, conversation_state: 'COMPLETED' } : null);
        }
        
        // Check for new symptoms in the LLM response
        if (wsMessage.content && typeof wsMessage.content === 'string') {
          try {
            // Try to parse the content as JSON to extract new_symptoms
            const contentStr = wsMessage.content.trim();
            if (contentStr.startsWith('{') && contentStr.endsWith('}')) {
              const parsedContent = JSON.parse(contentStr);
              if (parsedContent.new_symptoms && Array.isArray(parsedContent.new_symptoms)) {
                console.log('New symptoms detected from LLM:', parsedContent.new_symptoms);
                // Add new symptoms to localStorage
                addSymptoms(parsedContent.new_symptoms);
              }
            }
          } catch (error) {
            // Content is not JSON, continue normally
            console.log('Message content is not JSON, processing as normal text');
          }
        }
        
        console.log('[DEBUG] Returning updated messages, removing temp message with id -1');
        return [...prevMessages.filter(m => m.id !== -1 && m.id !== wsMessage.id), wsMessage];
      }
      console.log('No matching message type, returning previous messages');
      return prevMessages;
    });
  }, [chatSession, addSymptoms]);

  const { isConnected, sendMessage, connectionError } = useWebSocket(
    chatSession?.chat_uuid || null,
    handleNewMessage
  );

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadTodaySession = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await chatService.getTodaySession();
      const sessionData = response.data;
      
      if (!sessionData) {
        throw new Error('No session data returned');
      }
      
      setChatSession(sessionData);
      setMessages(Array.isArray(sessionData.messages) ? sessionData.messages : []);
      
      if (sessionData.symptom_list && Array.isArray(sessionData.symptom_list)) {
        console.log('Loading symptom list from backend:', sessionData.symptom_list);
        updateSymptomList(sessionData.symptom_list);
      } else {
        console.log('No symptom list from backend, resetting to empty');
        resetSymptomList();
      }
      
      setLoading(false);
    } catch (error: any) {
      // If auth failed (expired/invalid), force logout and redirect to login silently
      const status = error?.response?.status;
      if (status === 401 || status === 403) {
        setLoading(true); // keep loading screen while redirecting
        try { logout(); } catch {}
        navigate('/login', { replace: true });
        return;
      }
      setError('Failed to load chat session');
      console.error('Failed to load chat session:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTodaySession();
  }, []);

  // Helper function to check if current conversation is finished
  const isConversationFinished = () => {
    const state = chatSession?.conversation_state?.toString().toUpperCase();
    return state === 'COMPLETED' || state === 'EMERGENCY';
  };

  // Handle new conversation button click with confirmation if needed
  const handleNewConversationClick = () => {
    // If no current session or conversation is finished, start new conversation directly
    if (!chatSession || isConversationFinished()) {
      handleStartNewConversation();
    } else {
      // Show confirmation modal for unfinished conversation
      setIsNewConversationModalOpen(true);
    }
  };

  // Start new conversation (called after confirmation or directly)
  const handleStartNewConversation = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Reset symptom list in localStorage for new conversation
      resetSymptomList();
      
      const sessionData = await chatService.startNewSession();
      setChatSession(sessionData);
      setMessages(Array.isArray(sessionData.messages) ? sessionData.messages : []);
      
      // Ensure symptom list is empty for new conversation
      if (sessionData.symptom_list && Array.isArray(sessionData.symptom_list)) {
        updateSymptomList(sessionData.symptom_list);
      }
    } catch (error) {
      setError('Failed to start a new chat session');
      console.error('Failed to start a new chat session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = (content: string) => {
    if (!chatSession) return;
    const userMessage: Message = {
      id: -1,
      chat_uuid: chatSession.chat_uuid,
      sender: 'user',
      message_type: 'text',
      content: content,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    if (isConnected) {
      setIsThinking(true);
      sendMessage(content, 'text');
    }
  };

  const handleButtonClick = async (option: string) => {
    if (!chatSession) return;
    
    console.log('[CHEMO DEBUG] Button clicked:', option);
    console.log('[CHEMO DEBUG] Current messages:', messages);
    
    // Handle special chemo date responses
    if (option === "I had it recently, but didn't record it") {
      setIsCalendarModalOpen(true);
      return;
    }

    if (option === "Yes") {
      console.log('[CHEMO DEBUG] Yes button clicked, checking for chemotherapy question...');
      
      // Check if this is the first question about chemotherapy by looking at the assistant's message
      // Find the most recent assistant message that asks about chemotherapy
      const assistantMessage = messages
        .filter(msg => msg.sender === 'assistant')
        .reverse()
        .find(msg => msg.content.toLowerCase().includes('did you get chemotherapy'));
      
      console.log('[CHEMO DEBUG] Found assistant message:', assistantMessage);
      
      if (assistantMessage) {
        // Fire-and-forget chemo date logging - don't block the conversation
        (async () => {
          try {
            console.log('[CHEMO DEBUG] Attempting to log chemotherapy date for today');
            // Get today's date in user's timezone
            const todayInUserTz = getTodayInUserTimezone();
            console.log('[CHEMO DEBUG] Today in user timezone:', todayInUserTz.toISOString().split('T')[0]);
            
            const chemoResult = await chatService.logChemoDate(todayInUserTz);
            console.log('[CHEMO DEBUG] Successfully logged chemotherapy date for today:', chemoResult);
          } catch (error) {
            console.error('[CHEMO DEBUG] Failed to log chemotherapy date:', error);
            // Don't block the conversation - just log the error
          }
        })();
      } else {
        console.log('[CHEMO DEBUG] No chemotherapy question found in recent messages');
        console.log('[CHEMO DEBUG] All assistant messages:', messages.filter(msg => msg.sender === 'assistant').map(msg => msg.content));
      }
    }

    // Regular message handling
    const userMessage: Message = {
      id: -1,
      chat_uuid: chatSession.chat_uuid,
      sender: 'user',
      message_type: 'button_response',
      content: option,
      created_at: new Date().toISOString(),
    };
    
    console.log('[DEBUG] Adding user message to UI:', userMessage);
    setMessages(prev => [...prev, userMessage]);
    
    if (isConnected) {
      console.log('[DEBUG] WebSocket connected, sending message:', option);
      console.log('[DEBUG] Setting isThinking to true');
      setIsThinking(true);
      const sendResult = sendMessage(option, 'button_response');
      console.log('[DEBUG] sendMessage result:', sendResult);
    } else {
      console.log('[DEBUG] WebSocket not connected, cannot send message');
    }
  };

  const handleMultiSelectSubmit = (selections: string[]) => {
    if (!chatSession) return;
    
    // Filter out "None" selection and store symptoms in localStorage
    const validSelections = selections.filter(s => s.toLowerCase() !== 'none');
    if (validSelections.length > 0) {
      console.log('Storing selected symptoms:', validSelections);
      updateSymptomList(validSelections);
    } else {
      console.log('No valid symptoms selected, resetting symptom list');
      resetSymptomList();
    }
    
    const formattedSelections = selections.join(', ');
    const userMessage: Message = {
      id: -1,
      chat_uuid: chatSession.chat_uuid,
      sender: 'user',
      message_type: 'multi_select_response',
      content: formattedSelections,
      created_at: new Date().toISOString(),
    };
    
    setMessages(prev => {
        const newMessages = [...prev];
        let latestAssistantMsgIndex = -1;
        for (let i = newMessages.length - 1; i >= 0; i--) {
            if (newMessages[i].sender === 'assistant') {
                latestAssistantMsgIndex = i;
                break;
            }
        }
        
        if (latestAssistantMsgIndex > -1) {
            newMessages[latestAssistantMsgIndex] = {
                ...newMessages[latestAssistantMsgIndex],
                structured_data: {
                    ...newMessages[latestAssistantMsgIndex].structured_data,
                    selected_options: selections
                }
            };
        }
        return [...newMessages, userMessage];
    });

    if (isConnected) {
      setIsThinking(true);
      sendMessage(formattedSelections, 'multi_select_response');
    }
  };

  const handleFeelingSelect = (feeling: string) => {
    if (!chatSession) return;
    // Optimistically add the user's feeling selection as a message
    const userMessage: Message = {
      id: -1,
      chat_uuid: chatSession.chat_uuid,
      sender: 'user',
      message_type: 'feeling_response',
      content: feeling,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    // Persist overall feeling to backend
    fetch(`${API_CONFIG.BASE_URL}/chat/${chatSession.chat_uuid}/feeling`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ feeling })
    }).catch(() => {});

    // Send the feeling to the backend via WS to continue flow
    if (isConnected) {
      setIsThinking(true);
      sendMessage(feeling, 'feeling_response');
    }
  };

  const handleCalendarDateSelect = async (selectedDate: Date) => {
    if (!chatSession) return;
    // Format the date for display in user's timezone
    const dateString = selectedDate.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });

    // Optimistically add the message so the UI updates immediately
    const userMessage: Message = {
      id: -1,
      chat_uuid: chatSession.chat_uuid,
      sender: 'user',
      message_type: 'button_response',
      content: `Yes, I got chemotherapy on ${dateString}`,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    if (isConnected) {
      setIsThinking(true);
      sendMessage(`Yes, I got chemotherapy on ${dateString}`, 'button_response');
    }

    // Fire-and-forget the API persistence (log errors but don't block the UI)
    try {
      await chatService.logChemoDate(selectedDate);
      console.log('Logged chemotherapy date:', selectedDate);
    } catch (error) {
      console.error('Failed to log chemotherapy date:', error);
    }
  };

  const shouldShowTextInput = () => {
    // Never show input if the conversation is over
    const state = chatSession?.conversation_state?.toString().toUpperCase();
    if (state === 'COMPLETED' || state === 'EMERGENCY') {
      return false;
    }
    
    if (!messages || messages.length === 0) return true;
    const lastMessage = messages[messages.length - 1];
    if (isThinking) return false;
    if (lastMessage.sender === 'user') return false;
    // Hide for any message type that expects a button/interactive response
    if (['single-select', 'multi-select', 'feeling-select'].includes(lastMessage.message_type)) {
      return false;
    }
    return lastMessage.message_type === 'text';
  };

  const shouldShowInteractiveElements = (message: Message, index: number): boolean => {
    console.log('[DEBUG] shouldShowInteractiveElements called with:', {
      index,
      message_sender: message.sender,
      message_type: message.message_type,
      content: message.content,
      structured_data: message.structured_data,
      total_messages: messages.length
    });
    
    // Only show interactive elements if this is an assistant message
    if (message.sender !== 'assistant') {
      console.log('[DEBUG] Not assistant message, returning false');
      return false;
    }
    
    // Check if there's a user message after this assistant message
    for (let i = index + 1; i < messages.length; i++) {
      if (messages[i].sender === 'user') {
        console.log('[DEBUG] User already responded at index', i, 'not showing buttons');
        return false; // User has already responded, don't show buttons
      }
    }
    
    // This is the latest assistant message with no user response
    const shouldShow = true;
    console.log('[DEBUG] Should show interactive elements:', shouldShow, 'for message at index', index);
    return shouldShow;
  };

  
  if (loading) return <div className="loading">Loading chat...</div>;

  if (error) {
    return (
      <div className="error">
        <p>Error: {error}</p>
        <button onClick={loadTodaySession}>Retry</button>
      </div>
    );
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="header-spacer"></div>
        <div className="chat-title">Chat with Ruby</div>
        <button onClick={handleNewConversationClick} className="new-conversation-button">
          <span className="new-conversation-icon">+</span>
          New Conversation
        </button>
      </div>

      {/* Full-page overlay while connecting (blocks interactions) */}
      {!isConnected && !connectionError && (
        <div className="page-overlay" aria-live="polite" aria-busy="true" role="status">
          <div className="overlay-spinner" />
          <span>Connecting to chat...</span>
        </div>
      )}
      
      {!isConnected && (
        connectionError ? (
          <div className="connection-error-banner">
            <span>⚠️ {connectionError}</span>
            <button onClick={() => window.location.reload()} className="retry-button">Retry</button>
          </div>
        ) : (
          <div className="connection-loading-inline" aria-live="polite">
            <div className="spinner" aria-label="Connecting" />
            <span>Connecting to chat...</span>
          </div>
        )
      )}
      
      <div className="messages-container">
        {messages.map((message, index) => (
          <MessageBubble
            key={`${message.id}-${message.content.length}`}
            message={message}
            onButtonClick={handleButtonClick}
            onMultiSelectSubmit={handleMultiSelectSubmit}
            onFeelingSelect={handleFeelingSelect}
            shouldShowInteractiveElements={shouldShowInteractiveElements(message, index)}
          />
        ))}
        {isThinking && <ThinkingBubble />}
        <div ref={messagesEndRef} />
      </div>
      
      <MessageInput 
        onSendMessage={handleSendMessage}
        disabled={!isConnected || isThinking}
        shouldShow={shouldShowTextInput()}
      />

      {/* Calendar Modal for selecting chemo dates */}
      <CalendarModal
        isOpen={isCalendarModalOpen}
        onClose={() => setIsCalendarModalOpen(false)}
        onDateSelect={handleCalendarDateSelect}
      />

      {/* New Conversation Confirmation Modal */}
      <NewConversationModal
        isOpen={isNewConversationModalOpen}
        onClose={() => setIsNewConversationModalOpen(false)}
        onConfirm={handleStartNewConversation}
      />
    </div>
  );
};
  
export default ChatsPage;