/**
 * OncoLife Ruby - Notes/Diary Page Styles
 * Responsive, themed design for patient diary entries
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

export const NotesPageContainer = styled.div`
  flex: 1;
  background-color: ${colors.background};
  display: flex;
  flex-direction: row;
  overflow: hidden;
  height: calc(100vh - 64px);
  
  @media (max-width: 768px) {
    flex-direction: column;
    height: auto;
    min-height: calc(100vh - 120px);
  }
`;

export const NotesSidebarContainer = styled.div`
  width: 320px;
  background: ${colors.paper};
  border-right: 1px solid ${colors.border};
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  @media (max-width: 992px) {
    width: 280px;
  }
  
  @media (max-width: 768px) {
    width: 100%;
    max-height: 300px;
    border-right: none;
    border-bottom: 1px solid ${colors.border};
  }
`;

export const SidebarHeader = styled.div`
  padding: 16px;
  border-bottom: 1px solid ${colors.border};
  background: linear-gradient(135deg, ${colors.primary}05 0%, ${colors.secondary}05 100%);
`;

export const SidebarTitle = styled.h3`
  font-size: 1rem;
  font-weight: 600;
  color: ${colors.text};
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

export const SearchInput = styled.div`
  display: flex;
  align-items: center;
  background: ${colors.background};
  border-radius: 10px;
  padding: 10px 14px;
  border: 1px solid ${colors.border};
  transition: all 0.2s ease;
  
  &:focus-within {
    border-color: ${colors.primary};
    background: ${colors.paper};
    box-shadow: 0 0 0 3px ${colors.primary}15;
  }
  
  svg {
    color: ${colors.textSecondary};
    margin-right: 10px;
    flex-shrink: 0;
  }
  
  input {
    border: none;
    outline: none;
    background: transparent;
    font-size: 0.875rem;
    color: ${colors.text};
    width: 100%;
    
    &::placeholder {
      color: ${colors.textSecondary};
    }
  }
`;

export const DateNavigation = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid ${colors.border};
  background: ${colors.paper};
`;

export const NavButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: ${colors.background};
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: ${colors.textSecondary};
  
  &:hover {
    background: ${colors.primary}15;
    color: ${colors.primary};
  }
  
  svg {
    width: 16px;
    height: 16px;
  }
`;

export const CurrentMonth = styled.span`
  font-size: 0.9375rem;
  font-weight: 600;
  color: ${colors.text};
  min-width: 120px;
  text-align: center;
`;

export const NotesListContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  
  @media (max-width: 768px) {
    max-height: 200px;
  }
`;

export const NoteItemCard = styled.div<{ $isSelected?: boolean }>`
  padding: 14px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 6px;
  background: ${props => props.$isSelected ? `${colors.primary}10` : 'transparent'};
  border: 2px solid ${props => props.$isSelected ? colors.primary : 'transparent'};
  
  &:hover {
    background: ${props => props.$isSelected ? `${colors.primary}15` : colors.background};
  }
`;

export const NoteItemTitle = styled.h4`
  font-size: 0.9375rem;
  font-weight: 600;
  color: ${colors.text};
  margin: 0 0 4px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

export const NoteItemDate = styled.span`
  font-size: 0.75rem;
  color: ${colors.textSecondary};
  display: flex;
  align-items: center;
  gap: 4px;
`;

export const NoteItemPreview = styled.p`
  font-size: 0.8125rem;
  color: ${colors.textSecondary};
  margin: 6px 0 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

export const AddNoteButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: calc(100% - 16px);
  margin: 8px;
  padding: 12px;
  background: linear-gradient(135deg, ${colors.primary} 0%, ${colors.primaryDark} 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px ${colors.primary}40;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px ${colors.primary}50;
  }
`;

export const NoteEditorContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  background: ${colors.paper};
  overflow: hidden;
  
  @media (max-width: 768px) {
    min-height: 400px;
  }
`;

export const EditorHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid ${colors.border};
  background: linear-gradient(135deg, ${colors.primary}05 0%, ${colors.secondary}05 100%);
  
  @media (max-width: 576px) {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
`;

export const EditorTitle = styled.input`
  font-size: 1.25rem;
  font-weight: 600;
  color: ${colors.text};
  border: none;
  outline: none;
  background: transparent;
  flex: 1;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
  
  &:focus {
    background: ${colors.paper};
    box-shadow: 0 0 0 2px ${colors.primary}30;
  }
  
  &::placeholder {
    color: ${colors.textSecondary};
  }
`;

export const EditorActions = styled.div`
  display: flex;
  gap: 8px;
  
  @media (max-width: 576px) {
    width: 100%;
    justify-content: flex-end;
  }
`;

export const ActionButton = styled.button<{ $variant?: 'primary' | 'danger' | 'default' }>`
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  ${props => {
    switch (props.$variant) {
      case 'primary':
        return `
          background: ${colors.primary};
          color: white;
          border: none;
          
          &:hover {
            background: ${colors.primaryDark};
          }
        `;
      case 'danger':
        return `
          background: transparent;
          color: #DC2626;
          border: 1px solid #DC262630;
          
          &:hover {
            background: #DC262610;
          }
        `;
      default:
        return `
          background: transparent;
          color: ${colors.textSecondary};
          border: 1px solid ${colors.border};
          
          &:hover {
            background: ${colors.background};
          }
        `;
    }
  }}
  
  svg {
    width: 16px;
    height: 16px;
  }
`;

export const EditorContent = styled.div`
  flex: 1;
  padding: 20px;
  overflow-y: auto;
`;

export const EditorTextarea = styled.textarea`
  width: 100%;
  height: 100%;
  min-height: 300px;
  border: none;
  outline: none;
  background: transparent;
  font-size: 1rem;
  line-height: 1.7;
  color: ${colors.text};
  resize: none;
  font-family: 'Source Sans Pro', sans-serif;
  
  &::placeholder {
    color: ${colors.textSecondary};
  }
`;

export const EmptyEditorState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: ${colors.textSecondary};
  text-align: center;
  padding: 40px;
  
  .icon {
    font-size: 3rem;
    margin-bottom: 16px;
  }
  
  h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: ${colors.text};
    margin: 0 0 8px 0;
  }
  
  p {
    font-size: 0.9375rem;
    margin: 0;
    max-width: 300px;
  }
`;
