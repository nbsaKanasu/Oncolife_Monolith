import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { MessageCircle, LibraryBig, Notebook, Grid3X3, LogOut, ChevronRight, ChevronLeft, LayoutDashboard, ShieldUser, Users, Menu, X, ChevronDown, BookOpen, FileText, StickyNote, GraduationCap, User } from 'lucide-react';
import logo from '../../assets/logo.png';
import { useNavigate, useLocation } from 'react-router-dom';
import { SESSION_START_KEY } from '../SessionTimeout/SessionTimeoutManager';
// import { useUser } from '../../contexts/UserContext'; // Each app provides its own UserContext
import { useUserType } from '../../contexts/UserTypeContext';
// import { useLogout } from '../../restful/login';

const Sidebar = styled.nav<{ isExpanded: boolean }>`
  height: 100vh;
  width: ${props => props.isExpanded ? '18rem' : '5rem'};
  background: linear-gradient(to bottom, #f8fafc, #ffffff);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  border-right: 1px solid rgba(226, 232, 240, 0.6);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease-out;
  
  @media (max-width: 767px) {
    display: none;
  }
`;

const Header = styled.div<{ isExpanded: boolean }>`
  display: flex;
  align-items: center;
  justify-content: ${props => props.isExpanded ? 'space-between' : 'center'};
  padding: 1.5rem ${props => props.isExpanded ? '1.5rem' : '1rem'};
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  flex-shrink: 0;
`;

const LogoIcon = styled.div`
  width: 2rem;
  height: 2rem;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border-radius: 0.5rem;
  margin-right: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const LogoInner = styled.div`
  width: 1rem;
  height: 1rem;
  background: white;
  border-radius: 0.125rem;
`;

const LogoText = styled.h1`
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(to right, #1e293b, #475569);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
`;

const Logo = styled.img`
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  object-fit: cover;
  flex-shrink: 0;
  margin-right: 0.75rem;
`;

const ExpandToggleButton = styled.button`
  width: 2rem;
  height: 2rem;
  border: none;
  background: none;
  border-radius: 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease-out;
  
  &:hover {
    background: rgba(59, 130, 246, 0.1);
    transform: scale(1.1);
  }
  
  &:active {
    transform: scale(1.05);
  }
`;

const UserProfileContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'isExpanded'
})<{ isExpanded: boolean }>`
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  justify-content: ${props => (props.isExpanded ? 'flex-start' : 'center')};
  transition: background 0.2s;
  &:hover {
    background: #f3f4f6;
  }
`;

const AvatarInitials = styled.div`
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: linear-gradient(135deg, #7aa5ff 0%, #8f79d1 100%); /* slightly lighter */
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
`;

const UserInfo = styled.div`
  margin-left: 0.75rem;
  transition: all 0.3s;
`;

const UserHello = styled.p`
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
`;

const UserName = styled.p`
  font-weight: 500;
  color: #1f2937;
  margin: 0;
`;

const MenuSection = styled.nav`
  flex: 1;
  padding: 1rem 1rem 1.5rem 1rem;
  overflow-y: auto;
`;

const MenuTitle = styled.h3`
  font-size: 0.875rem;
  font-weight: 500;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 1rem 1rem;
`;

const MenuList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const MenuButton = styled.button<{ isActive?: boolean; isExpanded?: boolean }>`
  position: relative;
  display: flex;
  align-items: center;
  justify-content: ${props => props.isExpanded ? 'flex-start' : 'center'};
  width: 100%;
  padding: ${props => props.isExpanded ? '1rem' : '0.75rem'};
  background: ${props => props.isActive 
    ? 'linear-gradient(to right, #eff6ff, rgba(239, 246, 255, 0.8), #eef2ff)' 
    : 'none'};
  border: none;
  border-radius: 1rem;
  color: ${props => props.isActive ? '#1d4ed8' : '#475569'};
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease-out;
  box-shadow: ${props => props.isActive ? '0 10px 25px -5px rgba(59, 130, 246, 0.1), 0 8px 10px -6px rgba(59, 130, 246, 0.1)' : 'none'};
  
  &:hover {
    background: ${props => props.isActive 
      ? 'linear-gradient(to right, #eff6ff, rgba(239, 246, 255, 0.8), #eef2ff)' 
      : 'linear-gradient(to right, #f8fafc, rgba(248, 250, 252, 0.5))'};
    color: ${props => props.isActive ? '#1d4ed8' : '#1e293b'};
    box-shadow: ${props => props.isActive 
      ? '0 10px 25px -5px rgba(59, 130, 246, 0.1), 0 8px 10px -6px rgba(59, 130, 246, 0.1)' 
      : '0 6px 20px -6px rgba(148, 163, 184, 0.3)'};
  }
  
  &:focus {
    outline: none;
    box-shadow: 0 0 0 2px #3b82f6, 0 0 0 4px rgba(59, 130, 246, 0.1);
  }
`;

const MenuIconWrapper = styled.span<{ isExpanded?: boolean }>`
  margin-right: ${props => props.isExpanded ? '1rem' : '0'};
  flex-shrink: 0;
  transition: transform 0.2s ease-out;
  
  ${MenuButton}:hover & {
    transform: scale(1.1);
  }
`;

const MenuLabel = styled.span`
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const FooterSection = styled.div`
  padding: 1rem;
  padding-bottom: 1rem;
`;

const FooterStatus = styled.div`
  background: linear-gradient(to right, #eff6ff, #eef2ff);
  border-radius: 0.75rem;
  padding: 1rem;
  border: 1px solid rgba(59, 130, 246, 0.3);
`;

const StatusIndicator = styled.div`
  width: 0.5rem;
  height: 0.5rem;
  background: #4ade80;
  border-radius: 50%;
  margin-right: 0.5rem;
  animation: pulse 2s infinite;
  
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
`;

const StatusText = styled.span`
  font-size: 0.75rem;
  color: #475569;
  display: flex;
  align-items: center;
`;

const LogoutButton = styled.button<{ isExpanded?: boolean }>`
  display: flex;
  align-items: center;
  justify-content: ${props => props.isExpanded ? 'flex-start' : 'center'};
  width: 100%;
  padding: ${props => props.isExpanded ? '1rem' : '0.75rem'};
  background: none;
  border: none;
  border-radius: 1rem;
  color: #ef4444;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease-out;
  
  &:hover {
    background: linear-gradient(to right, #fef2f2, rgba(254, 242, 242, 0.8));
    box-shadow: 0 6px 20px -6px rgba(239, 68, 68, 0.3);
  }
  
  &:focus {
    outline: none;
    box-shadow: 0 0 0 2px #ef4444, 0 0 0 4px rgba(239, 68, 68, 0.1);
  }
`;

const ProfileSection = styled.div<{ isExpanded: boolean }>`
  padding: 1.5rem;
  border-bottom: 1px solid rgba(226, 232, 240, 0.3);
  margin-bottom: 0.5rem;
`;

const ProfileContainer = styled.div<{ isExpanded: boolean; isClickable?: boolean }>`
  display: flex;
  align-items: center;
  gap: ${props => props.isExpanded ? '0.75rem' : '0'};
  padding: ${props => props.isExpanded ? '0.75rem' : '0.75rem'};
  border-radius: 12px;
  background: transparent;
  cursor: ${props => props.isClickable ? 'pointer' : 'default'};
  transition: all 0.3s ease;
  justify-content: ${props => props.isExpanded ? 'flex-start' : 'center'};

  &:hover {
    background: ${props => props.isClickable ? 'rgba(59, 130, 246, 0.08)' : 'transparent'};
    transform: ${props => props.isClickable ? 'translateY(-1px)' : 'none'};
  }
`;

const Avatar = styled.div`
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
`;

const ProfileInfo = styled.div<{ isExpanded: boolean }>`
  display: ${props => props.isExpanded ? 'flex' : 'none'};
  flex-direction: column;
  min-width: 0;
  flex: 1;
`;

const ProfileGreeting = styled.div`
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
  line-height: 1;
  margin-bottom: 0.125rem;
`;

const ProfileName = styled.div`
  font-size: 0.875rem;
  color: #1e293b;
  font-weight: 600;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const LogoutSection = styled.div`
  padding: 0 1rem 1rem 1rem;
  border-top: 1px solid rgba(226, 232, 240, 0.5);
  margin-top: auto;
`;

// Mobile Navigation Styles
const MobileNavContainer = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  
  @media (min-width: 768px) {
    display: none;
  }
`;

const MobileHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  height: 4rem;
`;

// Export mobile nav height for other components to use
export const MOBILE_NAV_HEIGHT = '4rem';

// Utility component to add proper spacing for mobile navigation
export const MobileNavSpacer = styled.div`
  @media (max-width: 767px) {
    height: ${MOBILE_NAV_HEIGHT};
    width: 100%;
    flex-shrink: 0;
  }
`;

// Wrapper for page content that accounts for mobile navigation
export const PageContentWrapper = styled.div`
  @media (max-width: 767px) {
    padding-top: ${MOBILE_NAV_HEIGHT};
  }
`;

const MobileLogo = styled.div`
  display: flex;
  align-items: center;
`;

const MobileLogoText = styled.span`
  font-size: 1.2rem;
  font-weight: 600;
  color: #2563eb;
  margin-left: 0.5rem;
`;

const MobileMenuButton = styled.button`
  padding: 0.75rem;
  border: none;
  background: none;
  border-radius: 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  min-width: 2.75rem;
  min-height: 2.75rem;
  
  &:hover {
    background: #f3f4f6;
  }
  
  &:active {
    background: #e5e7eb;
  }
  
  @media (hover: none) {
    &:hover {
      background: none;
    }
  }
`;

const BreadcrumbContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'isOpen'
})<{ isOpen: boolean }>`
  background: #f8fafc;
  border-top: 1px solid #e5e7eb;
  padding: 0.75rem 1rem;
  display: ${props => props.isOpen ? 'block' : 'none'};
  max-height: ${props => props.isOpen ? '400px' : '0'};
  overflow-y: auto;
  transition: all 0.3s ease-in-out;
`;

const BreadcrumbItem = styled.button`
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 1rem;
  margin-bottom: 0.5rem;
  border: none;
  background: #fff;
  border-radius: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  min-height: 3.5rem;
  
  &:hover {
    background: #f1f5f9;
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  }
  
  &:active {
    transform: translateY(0);
    background: #e2e8f0;
  }
  
  @media (hover: none) {
    &:hover {
      transform: none;
      background: #fff;
    }
  }
`;

const BreadcrumbItemContent = styled.div`
  display: flex;
  align-items: center;
`;

const BreadcrumbIcon = styled.span`
  color: #4b5563;
  margin-right: 0.75rem;
  display: flex;
  align-items: center;
`;

const BreadcrumbLabel = styled.span`
  color: #374151;
  font-weight: 500;
  font-size: 1rem;
`;

const BreadcrumbChevron = styled.span`
  color: #9ca3af;
  display: flex;
  align-items: center;
`;

const MobileUserSection = styled.div`
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
  background: #fff;
`;

const MobileUserProfile = styled.div`
  display: flex;
  align-items: center;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 0.75rem;
  margin-bottom: 1rem;
  cursor: pointer;
  transition: background 0.2s;
  min-height: 4rem;
  
  &:hover {
    background: #f1f5f9;
  }
  
  &:active {
    background: #e2e8f0;
  }
  
  @media (hover: none) {
    &:hover {
      background: #f8fafc;
    }
  }
`;

const MobileUserInfo = styled.div`
  margin-left: 0.75rem;
`;

const MobileUserHello = styled.p`
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
`;

const MobileUserName = styled.p`
  font-weight: 500;
  color: #1f2937;
  margin: 0;
`;

const MobileLogoutButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 1rem;
  border: none;
  background: #fef2f2;
  color: #ef4444;
  border-radius: 0.75rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  min-height: 3.5rem;
  font-size: 1rem;
  
  &:hover {
    background: #fee2e2;
    color: #dc2626;
  }
  
  &:active {
    background: #fecaca;
  }
  
  @media (hover: none) {
    &:hover {
      background: #fef2f2;
      color: #ef4444;
    }
  }
`;

const MobileOverlay = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'isOpen'
})<{ isOpen: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: ${props => props.isOpen ? 'block' : 'none'};
  opacity: ${props => props.isOpen ? 1 : 0};
  transition: opacity 0.3s ease-in-out;
`;

interface MenuItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  href: string;
}

interface ProfileData {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

interface NavigationProps {
  userType: 'patient' | 'doctor';
  profile?: ProfileData | null;
}

interface UserProfileProps {
  isExpanded: boolean;
  onClick?: () => void;
  profile?: ProfileData | null;
}

const UserProfile: React.FC<UserProfileProps> = ({ isExpanded, onClick, profile }) => {
  let displayName = 'User';
  let initials = 'U';
  if (profile) {
    displayName = profile.first_name + (profile.last_name ? ' ' + profile.last_name : '');
    const first = profile.first_name?.[0] || '';
    const last = profile.last_name?.[0] || '';
    initials = (first + last).toUpperCase() || 'U';
  }
  return (
    <UserProfileContainer isExpanded={isExpanded} onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
      <AvatarInitials>{initials}</AvatarInitials>
      {isExpanded && (
        <UserInfo>
          <UserHello>Hello</UserHello>
          <UserName>{displayName}</UserName>
        </UserInfo>
      )}
    </UserProfileContainer>
  );
};

interface MenuItemProps {
  item: MenuItem;
  onClick: (href: string) => void;
  isExpanded: boolean;
}

const MenuItemComponent: React.FC<MenuItemProps> = ({ item, onClick, isExpanded }) => {
  const location = useLocation();
  const isActive = location.pathname === item.href;
  
  return (
    <MenuButton onClick={() => onClick(item.href)} isActive={isActive} isExpanded={isExpanded} title={!isExpanded ? item.label : ''}>
      <MenuIconWrapper isExpanded={isExpanded}>{item.icon}</MenuIconWrapper>
      {isExpanded && <MenuLabel>{item.label}</MenuLabel>}
    </MenuButton>
  );
};



// Extract menu content to a function for reuse
const SidebarContent: React.FC<{
  isExpanded: boolean;
  onMenuClick: (href: string) => void;
  onLogout: () => void;
  onToggleExpand: () => void;
  onProfileClick: () => void;
  userType: 'patient' | 'doctor';
  profile?: ProfileData | null;
}> = ({ isExpanded, onMenuClick, onLogout, onToggleExpand, onProfileClick, userType, profile }) => {
  
  // Define menu items based on user type
  const menuItems: MenuItem[] = userType === 'patient' 
    ? [
        { id: '1', label: 'Chat', icon: <MessageCircle size={20} />, href: '/chat' },
        { id: '2', label: 'Summaries', icon: <FileText size={20} />, href: '/summaries' },
        { id: '3', label: 'Notes', icon: <StickyNote size={20} />, href: '/notes' },
        { id: '4', label: 'Education', icon: <GraduationCap size={20} />, href: '/education' },
        { id: '5', label: 'Profile', icon: <User size={20} />, href: '/profile' },
      ]
    : [
        { id: '1', label: 'Dashboard', icon: <LayoutDashboard size={20} />, href: '/dashboard' },
        { id: '2', label: 'Patients', icon: <Users size={20} />, href: '/patients' },
        { id: '3', label: 'Staff', icon: <ShieldUser size={20} />, href: '/staff' },
      ];

  return (
    <>
      <Header isExpanded={isExpanded}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Logo src={logo} alt="OncoLife AI Logo" />
          {isExpanded && <LogoText>OncoLife AI</LogoText>}
        </div>
        <ExpandToggleButton onClick={onToggleExpand} aria-label={isExpanded ? 'Collapse menu' : 'Expand menu'}>
          {isExpanded ? (
            <ChevronLeft size={16} style={{ color: '#3b82f6' }} />
          ) : (
            <ChevronRight size={16} style={{ color: '#3b82f6' }} />
          )}
        </ExpandToggleButton>
      </Header>
      
      <ProfileSection isExpanded={isExpanded}>
        <ProfileContainer 
          isExpanded={isExpanded} 
          isClickable={userType === 'patient'}
          onClick={userType === 'patient' ? onProfileClick : undefined}
          title={!isExpanded ? (userType === 'patient' ? 'View Profile' : '') : ''}
        >
          <Avatar>
            {profile ? 
              ((profile.first_name?.[0] || '') + (profile.last_name?.[0] || '')).toUpperCase() || 'U'
              : 'U'
            }
          </Avatar>
          <ProfileInfo isExpanded={isExpanded}>
            <ProfileGreeting>Hello</ProfileGreeting>
            <ProfileName>
              {profile ? 
                (profile.first_name + (profile.last_name ? ' ' + profile.last_name : ''))
                : 'User'
              }
            </ProfileName>
          </ProfileInfo>
        </ProfileContainer>
      </ProfileSection>
      
      <MenuSection>
        <MenuList>
          {menuItems.map((item) => (
            <MenuItemComponent 
              key={item.id} 
              item={item} 
              onClick={onMenuClick}
              isExpanded={isExpanded}
            />
          ))}
        </MenuList>
      </MenuSection>
      
      <LogoutSection>
        <LogoutButton onClick={onLogout} isExpanded={isExpanded} title={!isExpanded ? 'Log out' : ''}>
          <MenuIconWrapper isExpanded={isExpanded}>
            <LogOut size={20} />
          </MenuIconWrapper>
          {isExpanded && <MenuLabel>Log out</MenuLabel>}
        </LogoutButton>
      </LogoutSection>

    </>
  );
};

// Mobile Navigation Component
const MobileNavigation: React.FC<{
  userType: 'patient' | 'doctor';
  profile?: ProfileData | null;
  onMenuClick: (href: string) => void;
  onLogout: () => void;
  onProfileClick: () => void;
}> = ({ userType, profile, onMenuClick, onLogout, onProfileClick }) => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  // Define menu items based on user type
  const menuItems: MenuItem[] = userType === 'patient' 
    ? [
        { id: '1', label: 'Chat', icon: <MessageCircle size={20} />, href: '/chat' },
        { id: '2', label: 'Summaries', icon: <FileText size={20} />, href: '/summaries' },
        { id: '3', label: 'Notes', icon: <StickyNote size={20} />, href: '/notes' },
        { id: '4', label: 'Education', icon: <GraduationCap size={20} />, href: '/education' },
        { id: '5', label: 'Profile', icon: <User size={20} />, href: '/profile' },
      ]
    : [
        { id: '1', label: 'Dashboard', icon: <LayoutDashboard size={20} />, href: '/dashboard' },
        { id: '2', label: 'Patients', icon: <Users size={20} />, href: '/patients' },
        { id: '3', label: 'Staff', icon: <ShieldUser size={20} />, href: '/staff' },
      ];



  // Close menu when clicking outside or navigating
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (isOpen && !target.closest('[data-mobile-nav]')) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Close menu on route change
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  const handleMenuItemClick = (href: string) => {
    onMenuClick(href);
    setIsOpen(false);
  };

  const handleLogoutClick = () => {
    onLogout();
    setIsOpen(false);
  };

  const handleProfileClick = () => {
    // Only handle profile click for patients
    if (userType === 'patient') {
      onProfileClick();
      setIsOpen(false);
    }
  };

  // User display info
  let displayName = 'User';
  let initials = 'U';
  if (profile) {
    displayName = profile.first_name + (profile.last_name ? ' ' + profile.last_name : '');
    const first = profile.first_name?.[0] || '';
    const last = profile.last_name?.[0] || '';
    initials = (first + last).toUpperCase() || 'U';
  }

  return (
    <>
      <MobileOverlay isOpen={isOpen} onClick={() => setIsOpen(false)} />
      <MobileNavContainer data-mobile-nav>
        <MobileHeader>
          <MobileLogo>
            <Logo src={logo} alt="Company Logo" />
            <MobileLogoText>Oncolife AI</MobileLogoText>
          </MobileLogo>
          <MobileMenuButton 
            onClick={() => setIsOpen(!isOpen)}
            aria-label={isOpen ? 'Close menu' : 'Open menu'}
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </MobileMenuButton>
        </MobileHeader>

        <BreadcrumbContainer isOpen={isOpen}>
          {/* Navigation items */}
          {menuItems.map((item) => (
            <BreadcrumbItem 
              key={item.id}
              onClick={() => handleMenuItemClick(item.href)}
            >
              <BreadcrumbItemContent>
                <BreadcrumbIcon>{item.icon}</BreadcrumbIcon>
                <BreadcrumbLabel>{item.label}</BreadcrumbLabel>
              </BreadcrumbItemContent>
              <BreadcrumbChevron>
                <ChevronRight size={16} />
              </BreadcrumbChevron>
            </BreadcrumbItem>
          ))}

          {/* User section */}
          <MobileUserSection>
            <MobileUserProfile 
              onClick={userType === 'patient' ? handleProfileClick : undefined}
              style={{ cursor: userType === 'patient' ? 'pointer' : 'default' }}
            >
              <AvatarInitials>{initials}</AvatarInitials>
              <MobileUserInfo>
                <MobileUserHello>Hello</MobileUserHello>
                <MobileUserName>{displayName}</MobileUserName>
              </MobileUserInfo>
            </MobileUserProfile>
            
            <MobileLogoutButton onClick={handleLogoutClick}>
              <LogOut size={20} style={{ marginRight: '0.5rem' }} />
              Log out
            </MobileLogoutButton>
          </MobileUserSection>
        </BreadcrumbContainer>
      </MobileNavContainer>
    </>
  );
};

const Navigation: React.FC<NavigationProps> = ({ userType, profile }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const navigate = useNavigate();

  const handleMenuItemClick = (href: string) => {
    navigate(href);
  };

  const handleLogout = () => {
    // useLogout();
    localStorage.removeItem('authToken');
    sessionStorage.removeItem(SESSION_START_KEY);
    navigate('/login');
  };

  const handleProfileClick = () => {
    // Only navigate to profile for patients
    if (userType === 'patient') {
      navigate('/profile');
    }
    // For doctors, do nothing - just show the name
  };

  return (
    <>
      {/* Mobile Navigation - visible on small screens */}
      <MobileNavigation
        userType={userType}
        profile={profile}
        onMenuClick={handleMenuItemClick}
        onLogout={handleLogout}
        onProfileClick={handleProfileClick}
      />

      {/* Desktop Sidebar - visible on medium screens and up */}
      <Sidebar isExpanded={isExpanded}>
        <SidebarContent
          isExpanded={isExpanded}
          onMenuClick={handleMenuItemClick}
          onLogout={handleLogout}
          onToggleExpand={() => setIsExpanded((prev) => !prev)}
          onProfileClick={handleProfileClick}
          userType={userType}
          profile={profile}
        />
      </Sidebar>
    </>
  );
};

export default Navigation;