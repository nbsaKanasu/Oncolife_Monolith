import React, { useMemo, useState } from 'react';
import type { Message } from '../../types/chat';

interface MultiSelectMessageProps {
  message: Message;
  onSubmitSelections: (selections: string[]) => void;
}

export const MultiSelectMessage: React.FC<MultiSelectMessageProps> = ({ 
  message, 
  onSubmitSelections 
}) => {
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);

  // Ensure Bruising and Bleeding are separate options; split any legacy combined label
  const optionsWithFallback = useMemo(() => {
    const baseOptions = [...(message.structured_data?.options || [])];
    const isInitialSymptomPrompt = (message.content || '').toLowerCase().includes("please select any symptoms you're experiencing today");
    if (!isInitialSymptomPrompt) return baseOptions;

    const normalized: string[] = [];
    baseOptions.forEach((o) => {
      const lower = o.toLowerCase();
      if (['bruising / bleeding', 'bruising/bleeding', 'bruising or bleeding'].includes(lower)) {
        normalized.push('Bruising', 'Bleeding');
      } else {
        normalized.push(o);
      }
    });

    // De-duplicate while preserving order
    const seen = new Set<string>();
    const deduped = normalized.filter(o => {
      const key = o.toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    return deduped;
  }, [message]);

  const maxSelections = message.structured_data?.max_selections || optionsWithFallback.length || 0;

  const toggleOption = (option: string) => {
    setSelectedOptions(prev => {
      if (prev.includes(option)) {
        return prev.filter(item => item !== option);
      } else if (prev.length < maxSelections) {
        return [...prev, option];
      }
      return prev;
    });
  };

  const handleSubmit = () => {
    if (selectedOptions.length > 0) {
      onSubmitSelections(selectedOptions);
    }
  };

  return (
    <div className="multi-select-options">
      {optionsWithFallback.map((option, index) => (
        <label
          key={index}
          className={`multi-select-item ${selectedOptions.includes(option) ? 'selected' : ''}`}
          htmlFor={`checkbox-${index}`}
        >
          <input
            id={`checkbox-${index}`}
            type="checkbox"
            checked={selectedOptions.includes(option)}
            onChange={() => toggleOption(option)}
          />
          <span>{option}</span>
        </label>
      ))}
      <button
        className="multi-select-submit"
        onClick={handleSubmit}
        disabled={selectedOptions.length === 0}
      >
        Submit ({selectedOptions.length} selected)
      </button>
    </div>
  );
}; 