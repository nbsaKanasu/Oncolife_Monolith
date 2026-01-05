/**
 * OncoLife Physician Portal - Layout
 * 
 * Responsive layout with:
 * - Desktop: Sidebar navigation (dark theme)
 * - Mobile: Hamburger drawer
 */

import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useTheme, useMediaQuery } from '@mui/material';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Avatar from '@mui/material/Avatar';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Divider from '@mui/material/Divider';
import { 
  LayoutDashboard,
  Users,
  UserCog,
  Menu as MenuIcon,
  LogOut,
  X,
  Activity
} from 'lucide-react';
import { useUser } from '../contexts/UserContext';

// Sidebar width
const DRAWER_WIDTH = 260;

// Navigation items
const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { id: 'patients', label: 'Patients', icon: Users, path: '/patients' },
  { id: 'staff', label: 'Staff', icon: UserCog, path: '/staff' },
];

const Layout: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { profile } = useUser();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  // Get current nav item
  const currentNav = navItems.find(item => location.pathname.startsWith(item.path))?.id || 'dashboard';

  // Get user initials
  const getInitials = () => {
    if (profile) {
      const first = profile.first_name?.[0] || '';
      const last = profile.last_name?.[0] || '';
      return (first + last).toUpperCase() || 'DR';
    }
    return 'DR';
  };

  const getUserName = () => {
    if (profile) {
      return `Dr. ${profile.first_name || ''} ${profile.last_name || ''}`.trim() || 'Doctor';
    }
    return 'Doctor';
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    setMobileDrawerOpen(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    sessionStorage.clear();
    navigate('/login');
  };

  // Sidebar Content (Dark themed for doctor)
  const SidebarContent = () => (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%',
      bgcolor: theme.palette.primary.main,
      color: 'white',
    }}>
      {/* Logo Header */}
      <Box sx={{ 
        p: 2.5, 
        display: 'flex', 
        alignItems: 'center', 
        gap: 1.5,
        borderBottom: '1px solid rgba(255,255,255,0.1)',
      }}>
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: 2,
            bgcolor: 'rgba(255,255,255,0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
          }}
        >
          <Activity size={24} />
        </Box>
        <Box sx={{ flex: 1 }}>
          <Typography 
            variant="h6" 
            fontWeight={700}
            sx={{ lineHeight: 1.2, color: 'white' }}
          >
            OncoLife
          </Typography>
          <Typography 
            variant="caption"
            sx={{ 
              display: 'block', 
              lineHeight: 1.2,
              color: 'rgba(255,255,255,0.7)',
            }}
          >
            Physician Portal
          </Typography>
        </Box>
        {isMobile && (
          <IconButton 
            onClick={() => setMobileDrawerOpen(false)}
            sx={{ color: 'white' }}
          >
            <X size={20} />
          </IconButton>
        )}
      </Box>

      {/* User Profile Section */}
      <Box sx={{ 
        p: 2, 
        display: 'flex', 
        alignItems: 'center', 
        gap: 1.5,
        borderBottom: '1px solid rgba(255,255,255,0.1)',
      }}>
        <Avatar 
          sx={{ 
            bgcolor: theme.palette.secondary.main,
            width: 44,
            height: 44,
            fontWeight: 600,
          }}
        >
          {getInitials()}
        </Avatar>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography 
            variant="body2" 
            sx={{ color: 'rgba(255,255,255,0.7)' }}
          >
            Welcome
          </Typography>
          <Typography 
            variant="body1" 
            fontWeight={600}
            sx={{ 
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              color: 'white',
            }}
          >
            {getUserName()}
          </Typography>
        </Box>
      </Box>

      {/* Navigation Links */}
      <Box sx={{ flex: 1, py: 2, overflow: 'auto' }}>
        <Typography 
          variant="overline"
          sx={{ 
            px: 2, 
            mb: 1, 
            display: 'block',
            color: 'rgba(255,255,255,0.5)',
            fontSize: '0.7rem',
            letterSpacing: '0.1em',
          }}
        >
          Navigation
        </Typography>
        <List disablePadding>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentNav === item.id;
            return (
              <ListItem key={item.id} disablePadding>
                <ListItemButton
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    mx: 1,
                    borderRadius: 2,
                    bgcolor: isActive ? 'rgba(255,255,255,0.15)' : 'transparent',
                    color: 'white',
                    '&:hover': {
                      bgcolor: isActive 
                        ? 'rgba(255,255,255,0.2)' 
                        : 'rgba(255,255,255,0.08)',
                    },
                  }}
                >
                  <ListItemIcon sx={{ 
                    minWidth: 40,
                    color: isActive ? 'white' : 'rgba(255,255,255,0.7)',
                  }}>
                    <Icon size={22} />
                  </ListItemIcon>
                  <ListItemText 
                    primary={item.label}
                    primaryTypographyProps={{
                      fontWeight: isActive ? 600 : 500,
                      color: 'inherit',
                    }}
                  />
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
      </Box>

      {/* Logout */}
      <Box sx={{ borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <Box sx={{ p: 1 }}>
          <ListItemButton
            onClick={handleLogout}
            sx={{
              borderRadius: 2,
              color: '#FCA5A5',
              '&:hover': {
                bgcolor: 'rgba(239, 68, 68, 0.15)',
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 40, color: 'inherit' }}>
              <LogOut size={22} />
            </ListItemIcon>
            <ListItemText primary="Log out" />
          </ListItemButton>
        </Box>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Desktop Sidebar */}
      {!isMobile && (
        <Drawer
          variant="permanent"
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
              border: 'none',
            },
          }}
        >
          <SidebarContent />
        </Drawer>
      )}

      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        open={mobileDrawerOpen}
        onClose={() => setMobileDrawerOpen(false)}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            width: 280,
            boxSizing: 'border-box',
          },
        }}
      >
        <SidebarContent />
      </Drawer>

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          bgcolor: theme.palette.background.default,
        }}
      >
        {/* Mobile Header */}
        {isMobile && (
          <AppBar 
            position="sticky" 
            elevation={0}
            sx={{ 
              bgcolor: theme.palette.primary.main,
            }}
          >
            <Toolbar sx={{ minHeight: { xs: 56 } }}>
              <IconButton
                edge="start"
                onClick={() => setMobileDrawerOpen(true)}
                sx={{ mr: 2, color: 'white' }}
              >
                <MenuIcon />
              </IconButton>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Activity size={24} color="white" />
                <Typography variant="h6" fontWeight={700} color="white">
                  OncoLife
                </Typography>
              </Box>
              <Box sx={{ flexGrow: 1 }} />
              <Avatar 
                sx={{ 
                  width: 36, 
                  height: 36,
                  bgcolor: theme.palette.secondary.main,
                  fontSize: '0.875rem',
                  fontWeight: 600,
                }}
              >
                {getInitials()}
              </Avatar>
            </Toolbar>
          </AppBar>
        )}

        {/* Page Content */}
        <Box sx={{ flex: 1, overflow: 'auto' }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;
