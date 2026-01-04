import React, { useState } from 'react';
import type { Message } from '../../types/chat';
import { formatTimeForDisplay } from '@oncolife/shared-utils';

interface SymptomMessageBubbleProps {
  message: Message;
  onOptionSelect?: (value: string | boolean) => void;
  onMultiSelectSubmit?: (values: string[]) => void;
  onSymptomSelect?: (symptomIds: string[]) => void;
  shouldShowInteractive?: boolean;
}

// Check icon SVG component
const CheckIcon: React.FC = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

// Ruby avatar component
const RubyAvatar: React.FC<{ mini?: boolean }> = ({ mini }) => (
  <div className={mini ? 'mini-avatar' : 'ruby-avatar'}>💎</div>
);

export const SymptomMessageBubble: React.FC<SymptomMessageBubbleProps> = ({
  message,
  onOptionSelect,
  onMultiSelectSubmit,
  onSymptomSelect,
  shouldShowInteractive = false,
}) => {
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);
  
  const isUser = message.sender === 'user';
  const frontendType = message.structured_data?.frontend_type || message.message_type;
  const options = message.structured_data?.options_data || 
                  message.structured_data?.options?.map((opt: string) => ({ label: opt, value: opt })) || 
                  [];

  // Handle single option selection (yes/no, choice)
  const handleOptionClick = (value: string | boolean) => {
    if (onOptionSelect) {
      onOptionSelect(value);
    }
  };

  // Handle multi-select toggle
  const handleMultiToggle = (value: string) => {
    setSelectedOptions(prev => {
      if (prev.includes(value)) {
        return prev.filter(v => v !== value);
      } else {
        return [...prev, value];
      }
    });
  };

  // Handle multi-select submit
  const handleMultiSubmit = () => {
    if (onMultiSelectSubmit && selectedOptions.length > 0) {
      onMultiSelectSubmit(selectedOptions);
      setSelectedOptions([]);
    }
  };

  // Handle symptom selection toggle
  const handleSymptomToggle = (symptomId: string) => {
    setSelectedSymptoms(prev => {
      if (prev.includes(symptomId)) {
        return prev.filter(s => s !== symptomId);
      } else {
        return [...prev, symptomId];
      }
    });
  };

  // Handle symptom selection submit
  const handleSymptomSubmit = () => {
    if (onSymptomSelect) {
      onSymptomSelect(selectedSymptoms.length > 0 ? selectedSymptoms : ['none']);
      setSelectedSymptoms([]);
    }
  };

  // Format message content with markdown-style bold
  const formatContent = (content: string) => {
    // Replace **text** with <strong>text</strong>
    const formatted = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    return { __html: formatted };
  };

  // Render triage result with special styling
  const renderTriageResult = () => {
    const triageLevel = message.structured_data?.triage_level;
    let triageClass = 'ok';
    let icon = '✅';
    
    if (triageLevel === 'call_911') {
      triageClass = 'emergency';
      icon = '🚨';
    } else if (triageLevel === 'notify_care_team') {
      triageClass = 'alert';
      icon = '⚠️';
    }

    return (
      <div className={`triage-result ${triageClass}`}>
        <div 
          className="message-content" 
          dangerouslySetInnerHTML={formatContent(message.content)}
        />
      </div>
    );
  };

  // Render symptom selector
  const renderSymptomSelector = () => {
    const optionsData = message.structured_data?.options_data || [];
    
    // Group by category
    const emergency = optionsData.filter((o: any) => o.category === 'emergency');
    const common = optionsData.filter((o: any) => o.category === 'common');
    const other = optionsData.filter((o: any) => o.category === 'other');
    const none = optionsData.filter((o: any) => o.category === 'none');

    return (
      <div className="symptom-selector">
        {emergency.length > 0 && (
          <div className="symptom-category">
            <div className="category-label emergency">🚨 Emergency Symptoms</div>
            <div className="symptom-grid">
              {emergency.map((opt: any) => (
                <button
                  key={opt.value}
                  className={`symptom-chip emergency ${selectedSymptoms.includes(opt.value) ? 'selected' : ''}`}
                  onClick={() => handleSymptomToggle(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {common.length > 0 && (
          <div className="symptom-category">
            <div className="category-label">Common Side Effects</div>
            <div className="symptom-grid">
              {common.map((opt: any) => (
                <button
                  key={opt.value}
                  className={`symptom-chip ${selectedSymptoms.includes(opt.value) ? 'selected' : ''}`}
                  onClick={() => handleSymptomToggle(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {other.length > 0 && (
          <div className="symptom-category">
            <div className="category-label">Other Symptoms</div>
            <div className="symptom-grid">
              {other.map((opt: any) => (
                <button
                  key={opt.value}
                  className={`symptom-chip ${selectedSymptoms.includes(opt.value) ? 'selected' : ''}`}
                  onClick={() => handleSymptomToggle(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {none.length > 0 && (
          <div className="symptom-category">
            <div className="symptom-grid">
              {none.map((opt: any) => (
                <button
                  key={opt.value}
                  className={`symptom-chip ${selectedSymptoms.includes(opt.value) ? 'selected' : ''}`}
                  onClick={() => handleSymptomToggle(opt.value)}
                >
                  ✨ {opt.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <button 
          className="multi-select-submit"
          onClick={handleSymptomSubmit}
          disabled={selectedSymptoms.length === 0}
        >
          Continue ({selectedSymptoms.length} selected)
        </button>
      </div>
    );
  };

  // Render interactive options based on type
  const renderInteractive = () => {
    if (!shouldShowInteractive || !options.length) return null;

    // Symptom selector
    if (frontendType === 'symptom-select' || frontendType === 'symptom_select') {
      return renderSymptomSelector();
    }

    // Yes/No or single choice
    if (frontendType === 'yes_no' || frontendType === 'single-select' || frontendType === 'choice') {
      return (
        <div className="message-options">
          {options.map((opt: any, index: number) => (
            <button
              key={index}
              className="option-btn"
              onClick={() => handleOptionClick(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>
      );
    }

    // Multi-select
    if (frontendType === 'multi-select' || frontendType === 'multiselect') {
      return (
        <div className="multi-select-container">
          {options.map((opt: any, index: number) => (
            <div
              key={index}
              className={`multi-option ${selectedOptions.includes(opt.value) ? 'selected' : ''}`}
              onClick={() => handleMultiToggle(opt.value)}
            >
              <div className="checkbox-custom">
                <CheckIcon />
              </div>
              <span className="multi-option-label">{opt.label}</span>
            </div>
          ))}
          <button 
            className="multi-select-submit"
            onClick={handleMultiSubmit}
            disabled={selectedOptions.length === 0}
          >
            Submit Selection
          </button>
        </div>
      );
    }

    return null;
  };

  // Check if this is a triage result
  const isTriageResult = message.structured_data?.is_complete === true;

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && (
        <div className="message-with-avatar">
          <RubyAvatar mini />
          <div>
            <div className="message-bubble">
              {isTriageResult ? (
                renderTriageResult()
              ) : (
                <div 
                  className="message-content"
                  dangerouslySetInnerHTML={formatContent(message.content)}
                />
              )}
              {renderInteractive()}
            </div>
            <div className="message-time">
              {formatTimeForDisplay(message.created_at)}
            </div>
          </div>
        </div>
      )}
      {isUser && (
        <>
          <div className="message-bubble">
            <div className="message-content">{message.content}</div>
          </div>
          <div className="message-time">
            {formatTimeForDisplay(message.created_at)}
          </div>
        </>
      )}
    </div>
  );
};



