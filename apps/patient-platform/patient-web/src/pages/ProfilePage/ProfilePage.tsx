import React, { useState, useEffect } from 'react';
import { CircularProgress } from '@mui/material';
import {
  ProfileContainer,
  ProfileHeader as ProfileHeaderStyled,
  ProfileTitle,
  ProfileContent,
  ProfileCard,
  LoadingContainer,
  ErrorContainer,
} from './ProfilePage.styles';
import { ProfileHeader, PersonalInformation } from './components';
import type { ProfileData, ProfileFormData } from './types';
import { useFetchProfile } from '../../services/profile';

const ProfilePage: React.FC = () => {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [formData, setFormData] = useState<ProfileFormData | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { data: profileData, isLoading: isProfileLoading } = useFetchProfile();

  useEffect(() => {
    if (profileData) {
      setProfile(profileData as ProfileData);
      setFormData(profileData as ProfileFormData);
    }
  }, [profileData]);

  const handleEditProfile = () => {
    setIsEditing(true);
  };

  const handleEditImage = () => {
    // TODO: Implement image upload functionality
    console.log('Edit image clicked');
  };

  const handleFieldChange = (field: keyof ProfileFormData, value: string) => {
    if (formData) {
      setFormData({
        ...formData,
        [field]: value,
      });
    }
  };

  const handleSave = async () => {
    try {
      // TODO: Implement API call to save profile data
      console.log('Saving profile data:', formData);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (profile && formData) {
        setProfile({
          ...profile,
          ...formData,
        });
      }
      
      setIsEditing(false);
    } catch (err) {
      setError('Failed to save profile data');
    }
  };

  const handleCancel = () => {
    if (profile) {
      setFormData({
        first_name: profile.first_name || '',
        last_name: profile.last_name || '',
        email_address: profile.email_address || '',
        phone_number: profile.phone_number || '',
        date_of_birth: profile.date_of_birth || '',
        chemotherapy_day: profile.chemotherapy_day || '',
        reminder_time: profile.reminder_time || '',
        doctor_name: profile.doctor_name || '',
        clinic_name: profile.clinic_name || '',
        // Treatment Info
        last_chemo_date: profile.last_chemo_date || '',
        next_physician_visit: profile.next_physician_visit || '',
        diagnosis: profile.diagnosis || '',
        treatment_type: profile.treatment_type || '',
        emergency_contact_name: profile.emergency_contact_name || '',
        emergency_contact_phone: profile.emergency_contact_phone || '',
      });
    }
    setIsEditing(false);
  };

  if (isProfileLoading) {
    return (
      <ProfileContainer>
        <ProfileHeaderStyled>
          <ProfileTitle>Profile</ProfileTitle>
        </ProfileHeaderStyled>
        <LoadingContainer>
          <CircularProgress size={48} />
        </LoadingContainer>
      </ProfileContainer>
    );
  }

  if (error) {
    return (
      <ProfileContainer>
        <ProfileHeaderStyled>
          <ProfileTitle>Profile</ProfileTitle>
        </ProfileHeaderStyled>
        <ProfileContent>
          <ErrorContainer>
            <strong>Error:</strong> {error}
          </ErrorContainer>
        </ProfileContent>
      </ProfileContainer>
    );
  }

  if (!profile || !formData) {
    return (
      <ProfileContainer>
        <ProfileHeaderStyled>
          <ProfileTitle>Profile</ProfileTitle>
        </ProfileHeaderStyled>
        <ProfileContent>
          <ErrorContainer>
            <strong>Error:</strong> No profile data available
          </ErrorContainer>
        </ProfileContent>
      </ProfileContainer>
    );
  }

  return (
    <ProfileContainer>
      <ProfileHeaderStyled>
        <ProfileTitle>Profile</ProfileTitle>
      </ProfileHeaderStyled>
      
      <ProfileContent>
        <ProfileCard>
          <ProfileHeader
            profile={profile}
            onEditProfile={handleEditProfile}
            onEditImage={handleEditImage}
          />
          
          <PersonalInformation
            formData={formData}
            isEditing={isEditing}
            onFieldChange={handleFieldChange}
            onSave={handleSave}
            onCancel={handleCancel}
          />
        </ProfileCard>
      </ProfileContent>
    </ProfileContainer>
  );
};

export default ProfilePage; 