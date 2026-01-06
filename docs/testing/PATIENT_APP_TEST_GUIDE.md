# OncoLife Patient Application - Test Guide

## Overview

This document provides a complete testing guide for the OncoLife Patient Application. Use this to verify all implemented features are working correctly.

---

## Quick Reference

| Feature | API Endpoint | Status |
|---------|--------------|--------|
| User Registration | POST /api/v1/auth/signup | ✅ Implemented |
| User Login | POST /api/v1/auth/login | ✅ Implemented |
| Symptom Checker | WS /api/v1/chat/ws/{uuid} | ✅ Implemented |
| Patient Diary | GET/POST /api/v1/diary | ✅ Implemented |
| Questions to Doctor | GET/POST /api/v1/questions | ✅ Implemented |
| Chemo Dates | GET/POST /api/v1/chemo | ✅ Implemented |
| Profile Management | GET/PATCH /api/v1/profile | ✅ Implemented |
| Education Content | GET /api/v1/education/tab | ✅ Implemented |

---

## Test Scenarios

### 1. Patient Onboarding Flow

#### 1.1 New Patient Registration (Fax-Initiated)

**Prerequisites:** Patient referral fax received from clinic

**Expected Flow:**
```
Fax Received → OCR Processing → Patient Account Created → Welcome Email Sent
```

**What to Test:**
1. Verify welcome email received at patient's email
2. Email contains:
   - Username (email address)
   - Temporary password
   - Login link
3. Temporary password works for first login

**API Test:**
```bash
# Check onboarding status
GET /api/v1/onboarding/status?patient_id={uuid}

Expected Response:
{
  "status": "pending_first_login",
  "email_sent": true,
  "sms_sent": true
}
```

---

#### 1.2 First Login - Mandatory Setup

**Screen Flow:**
```
Login Screen → Password Reset → Acknowledgement → Terms & Privacy → Reminder Preferences → Dashboard
```

**Step 1: Login with Temporary Password**
- Enter email from welcome email
- Enter temporary password
- Click "Login"
- **Expected:** Redirect to "Set New Password" screen

**Step 2: Set New Password**
- Enter new password (min 8 chars, 1 uppercase, 1 number, 1 special)
- Confirm password
- Click "Update Password"
- **Expected:** Redirect to Acknowledgement screen

**Step 3: Acknowledgement Screen**
- Read the acknowledgement text:
  > "I understand this tool does not replace my care team or emergency services."
- Check the acknowledgement checkbox
- Click "Continue"
- **Expected:** Redirect to Terms & Privacy screen

**Step 4: Terms & Privacy**
- View Terms & Conditions
- View Privacy Policy (HIPAA notice)
- Check both acceptance checkboxes
- Click "Accept & Continue"
- **Expected:** Redirect to Reminder Preferences screen

**Step 5: Reminder Preferences**
- See pre-filled phone/email (from referral)
- Edit if needed
- Select reminder method: Email or SMS
- Select reminder time
- Click "Save Preferences"
- **Expected:** Redirect to Main Dashboard/Chat screen

**API Tests:**
```bash
# Complete acknowledgement
POST /api/v1/onboarding/complete/acknowledgement
{ "acknowledged": true }

# Accept terms
POST /api/v1/onboarding/complete/terms
{ "terms_accepted": true, "privacy_accepted": true }

# Set reminders
POST /api/v1/onboarding/complete/reminders
{ "method": "email", "time": "09:00" }
```

---

### 2. Symptom Checker (Daily Check-In) - NEW 6-PHASE FLOW

#### 2.1 Start New Session

**NEW Screen Flow (6 Phases):**
```
Dashboard → Medical Disclaimer → Emergency Check → Grouped Symptom Selection → Ruby Chat → Summary
```

**What to Test:**

**Phase 1: Medical Disclaimer Screen**
- Click "Start Daily Check-In"
- **Expected:** Disclaimer screen displays:
  ```
  IMPORTANT MEDICAL DISCLAIMER:
  This system is an automated symptom checker. It is NOT a substitute 
  for professional medical advice, diagnosis, or treatment.
  
  If you believe you are having a medical emergency, call 911 immediately.
  
  [I Understand - Start Triage]
  ```
- Click "I Understand - Start Triage" button
- **Expected:** Moves to Emergency Check screen

**Phase 2: Emergency Check Screen (Urgent Safety Check)**
- System displays: "Before we assess your symptoms, we need to rule out immediate emergencies."
- **Emergency symptoms shown** (multi-select):
  - ⚠️ Trouble breathing or shortness of breath
  - ⚠️ Chest pain
  - ⚠️ Uncontrolled bleeding OR Blood in stool/urine
  - ⚠️ Fainting or Syncope
  - ⚠️ Confusion or Altered Mental Status
- **Test Path A - Emergency selected:**
  - Select any emergency symptom
  - Click "Continue"
  - **Expected:** Immediate emergency escalation path (Call 911 screen)
- **Test Path B - No emergencies:**
  - Click "None of these - Continue"
  - **Expected:** Proceeds to Grouped Symptom Selection

**Phase 3: Grouped Symptom Selection**
- System displays symptom categories in groups:
  - **Digestive Health:** Nausea, Vomiting, Diarrhea, Constipation, No Appetite, Mouth Sores
  - **Pain & Nerve:** Pain, Neuropathy (Numbness/Tingling)
  - **Systemic & Infection:** Fever, Bleeding or Bruising, Fatigue, Cough, Urinary Problems
  - **Skin & External:** Skin Rash, Swelling, Eye Complaints
- Select one or more symptoms (multi-select)
- Click "Continue"
- **Expected:** Ruby Chat interface begins

**Phase 4: Ruby Chat (Per-Symptom Questions)**
- **Expected:** Ruby introduces herself:
  ```
  "Hello! I am Ruby, your automated triage assistant. 
  I'm here to help assess your symptoms."
  ```
- For each selected symptom, answer screening questions in WhatsApp-like chat style:

**Example: Fever**
- Ruby: "Do you have a fever?" → Select (Yes/No)
- Ruby: "What is your temperature?" → Enter number or select range
- Ruby: "How long have you had the fever?" → Select option
- Ruby: "Any other symptoms with the fever?" → Multi-select

**Expected Behavior:**
- WhatsApp-style chat bubbles (Ruby on left, Patient on right)
- Questions appear one at a time
- Selected options clearly shown as patient's response
- Ruby avatar visible on her messages
- Smooth scrolling to new messages
- Progress through all selected symptoms

**Phase 5: Triage Result**
After all questions answered:
- **Green (Mild):** "Your symptoms are mild. Continue monitoring."
- **Yellow (Moderate):** "Monitor closely. Contact care team if worsening."
- **Orange (Severe):** "Contact your care team today."
- **Red (Urgent/Emergency):** "Seek immediate medical attention. Call 911."

**Phase 6: Summary Screen**
- System displays complete summary of session
- **Action Buttons available:**
  - 📥 **Download Summary** - Save as PDF
  - 📓 **Save to Diary** - Creates diary entry
  - 🔄 **Report Another Symptom** - Return to symptom selection
  - ✅ **Done** - Complete session
- Education content appears below summary:
  - Symptom-specific tips (4-6 bullets)
  - "Read More" links to PDFs
  - Care Team Handout link
  - Mandatory disclaimer text

**API Tests:**
```bash
# Get/Create today's session
GET /api/v1/chat/session/today

# WebSocket connection
WS /api/v1/chat/ws/{chat_uuid}

# Send message
{
  "content": "fever",
  "message_type": "multi_select_response"
}
```

---

#### 2.2 Emergency Triage (Call 911)

**Trigger Conditions:**
- Temperature > 103°F with chills
- Severe bleeding
- Difficulty breathing
- Chest pain
- Confusion/altered consciousness

**Expected Screen:**
```
⚠️ EMERGENCY

Based on your symptoms, you should seek immediate medical attention.

🚨 CALL 911 or go to the nearest emergency room.

Your care team has been notified.

[Call 911 Button]
[I Understand Button]
```

**What to Verify:**
1. Red/emergency styling is prominent
2. 911 button is functional
3. Care team notification logged
4. Cannot continue regular flow until acknowledged

---

### 3. Patient Diary

#### 3.1 View Diary Entries

**Screen Flow:**
```
Dashboard → "My Diary" → Calendar/List View → Entry Details
```

**What to Test:**
- Calendar shows dates with entries highlighted
- Click date to see entries for that day
- Auto-generated entries from symptom checker visible
- Manual entries visible
- Entries marked for doctor show indicator

**API Test:**
```bash
GET /api/v1/diary?timezone=America/Los_Angeles

Expected Response:
{
  "entries": [
    {
      "id": 1,
      "entry_uuid": "uuid",
      "created_at": "2026-01-04T10:30:00Z",
      "title": "Symptom Check - January 04, 2026",
      "diary_entry": "Daily Check-in Summary...",
      "marked_for_doctor": true
    }
  ]
}
```

---

#### 3.2 Create Manual Diary Entry

**Screen Flow:**
```
My Diary → "Add Entry" → Entry Form → Save
```

**What to Test:**
1. Click "Add Entry" button
2. Enter optional title
3. Enter diary text (required)
4. Toggle "Share with Doctor" (optional)
5. Click "Save"
6. **Expected:** Entry appears in list

**API Test:**
```bash
POST /api/v1/diary
{
  "title": "Feeling better today",
  "diary_entry": "Nausea has subsided. Eating better.",
  "marked_for_doctor": false
}
```

---

#### 3.3 Auto-Generated Diary Entry

**What to Test:**
After completing a symptom checker session:
1. Navigate to "My Diary"
2. **Expected:** New entry automatically created with:
   - Title: "Symptom Check - [Date]"
   - Content: Summary of symptoms reported
   - Severity levels listed
   - Triage outcome noted
   - Marked for doctor if escalation occurred

---

### 4. Questions to Ask Doctor

#### 4.1 View Questions

**Screen Flow:**
```
Dashboard → "Questions for Doctor" → Question List
```

**What to Test:**
- See list of all questions (private and shared)
- Private questions show lock icon
- Shared questions show "Shared" badge
- Answered questions show checkmark

---

#### 4.2 Create Question

**Screen Flow:**
```
Questions → "Add Question" → Question Form → Save
```

**What to Test:**
1. Click "Add Question"
2. Enter question text (required)
3. Select category: Symptom, Medication, Treatment, Other
4. Toggle "Share with Doctor" 
5. Click "Save"
6. **Expected:** Question appears in list

**API Test:**
```bash
POST /api/v1/questions
{
  "question_text": "Should I take my anti-nausea medication with food?",
  "category": "medication",
  "share_with_physician": true
}
```

---

#### 4.3 Share/Unshare Question

**What to Test:**
1. Find an existing question
2. Click "Share" toggle
3. **Expected:** Question status changes
4. Shared questions visible to physician

**API Test:**
```bash
POST /api/v1/questions/{question_id}/share?share=true
```

---

### 5. Chemotherapy Dates

#### 5.1 View Chemo Schedule

**Screen Flow:**
```
Dashboard → "My Treatment" → Chemo Calendar
```

**What to Test:**
- Calendar shows upcoming chemo dates
- Past chemo dates marked differently
- Click date for details

---

#### 5.2 Log Chemo Date

**Screen Flow:**
```
My Treatment → "Log Chemo" → Date Picker → Save
```

**What to Test:**
1. Click "Log Chemo Date"
2. Select date from calendar
3. Click "Save"
4. **Expected:** Date appears on calendar

**API Test:**
```bash
POST /api/v1/chemo/log
{
  "chemo_date": "2026-01-15"
}

GET /api/v1/chemo/history
```

---

### 6. Profile Management

#### 6.1 View Profile

**Screen Flow:**
```
Dashboard → Profile Icon → Profile Screen
```

**What to Test:**
- Name displayed correctly
- Email displayed
- Phone number displayed
- Disease type displayed
- Treatment type displayed

---

#### 6.2 Update Reminder Preferences

**Screen Flow:**
```
Profile → "Reminder Settings" → Edit Form → Save
```

**What to Test:**
1. Navigate to Profile
2. Click "Reminder Settings"
3. Change reminder method (Email/SMS)
4. Change reminder time
5. Click "Save"
6. **Expected:** Settings updated

**API Test:**
```bash
PATCH /api/v1/profile/config
{
  "reminder_method": "sms",
  "reminder_time": "08:00"
}
```

---

### 7. Education Tab

#### 7.1 View Education Library

**Screen Flow:**
```
Dashboard → "Education" → Education Library
```

**What to Test:**
- Default view: Last 7 days of symptoms
- Section: "My Current Symptoms"
- Section: "Common Chemotherapy Symptoms"
- Section: "Care Team Handouts"
- Each item shows title and brief description
- PDF links work (open in new tab/viewer)

---

#### 7.2 Search Education

**What to Test:**
1. Use search bar
2. Enter symptom name (e.g., "nausea")
3. **Expected:** Relevant education content displayed
4. Click on result to view details

**API Test:**
```bash
GET /api/v1/education/search?q=nausea
```

---

### 8. Conversation History

#### 8.1 View Past Sessions

**Screen Flow:**
```
Dashboard → "History" → Session List → Session Detail
```

**What to Test:**
- List shows all past symptom checker sessions
- Each session shows:
  - Date/time
  - Symptoms reported
  - Triage outcome (color-coded)
- Click session to see full conversation

**API Test:**
```bash
GET /api/v1/summaries/2026/1
```

---

## Error Handling Tests

### Network Errors
- Turn off WiFi during symptom checker
- **Expected:** "Connection lost. Your progress is saved." message
- Reconnect and continue from where left off

### Session Timeout
- Leave app idle for 30+ minutes
- Try to perform action
- **Expected:** Redirect to login screen

### Invalid Inputs
- Try empty diary entry → "Entry cannot be empty"
- Try invalid date for chemo → "Please select a valid date"
- Try weak password → Password requirements shown

---

## UI/UX Tests

### Dark Mode Testing

**What to Test:**

**Toggle Location:**
- Desktop/Tablet: Sidebar → Bottom (pill toggle with "Light Mode/Dark Mode" label)
- Mobile: Top header bar (moon/sun icon)

**Dark Mode Activation:**
1. Click dark mode toggle
2. **Expected:**
   - Background changes to deep navy (#0F172A)
   - Text becomes light gray (#F1F5F9)
   - Primary color shifts to lighter teal (#4DB6AC)
   - Cards/Paper backgrounds become slate (#1E293B)
   - Smooth 0.3s transition animation

**Persistence Test:**
1. Toggle to dark mode
2. Close browser tab
3. Reopen app
4. **Expected:** Dark mode persists (stored in localStorage)

**System Preference Test:**
1. Set OS to dark mode
2. Open OncoLife (first time or clear localStorage)
3. **Expected:** App automatically uses dark mode

### Responsive Design Testing

**Mobile (< 600px):**
- [ ] Bottom navigation bar visible (5 main icons: Chat, Summaries, Diary, Questions, Education)
- [ ] Profile accessible via header avatar/hamburger menu
- [ ] Full-width buttons
- [ ] Chat bubbles properly sized
- [ ] No horizontal scroll

**Tablet (600px - 900px):**
- [ ] Sidebar navigation visible with all 6 items
- [ ] Content area adjusts width
- [ ] Cards stack appropriately

**Desktop (> 900px):**
- [ ] Full sidebar with labels (Symptom Check, Summaries, Diary, Questions, Education, Profile)
- [ ] Dark mode toggle visible in sidebar
- [ ] Spacious content area
- [ ] Hover states work properly

### Navigation Items (All Screen Sizes)

| Icon | Label | Route | Purpose |
|------|-------|-------|---------|
| 💬 | Symptom Check | /chat | Daily symptom checker |
| 📄 | Summaries | /summaries | Past triage summaries |
| 📖 | Diary | /notes | Personal diary/notes |
| ❓ | Questions | /questions | Questions for doctor |
| 📚 | Education | /education | Learning resources |
| 👤 | Profile | /profile | Account settings |

### Symptom Chat UX Testing

**WhatsApp-Style Chat:**
- [ ] Ruby's messages appear on left with avatar
- [ ] Patient's messages appear on right (purple bubble)
- [ ] Smooth scroll to new messages
- [ ] Interactive options are touch-friendly (48px minimum)
- [ ] Selected options show confirmation
- [ ] Emergency symptoms highlighted in red

**Summary Screen:**
- [ ] Triage result color matches severity
- [ ] Action buttons all functional
- [ ] Education content displays correctly
- [ ] Disclaimer always visible

---

## Accessibility Tests

- [ ] Screen reader announces all buttons
- [ ] Text size can be increased
- [ ] Color contrast meets WCAG 2.1 AA (light AND dark mode)
- [ ] Touch targets are 44x44px minimum (48px on mobile)
- [ ] Form labels are associated with inputs
- [ ] Focus states visible for keyboard navigation
- [ ] Reduced motion preference respected

---

## Test Data Checklist

### Before Testing:
- [ ] Test patient account created
- [ ] At least 3 past symptom sessions exist
- [ ] At least 2 diary entries exist
- [ ] At least 1 chemo date logged
- [ ] At least 2 questions created (1 shared, 1 private)

### Test Accounts:
```
Patient 1 (New): newpatient@test.com / TempPass123!
Patient 2 (Active): activepatient@test.com / TestPass123!
```

---

## Bug Reporting Template

```
**Bug Title:** [Short description]

**Environment:**
- Device: [iPhone 13 / Android / Chrome Desktop]
- OS Version: [iOS 17 / Android 14 / Windows 11]
- App Version: [1.0.0]

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Result:**


**Actual Result:**


**Screenshots/Video:**
[Attach if available]

**Severity:** [Critical / High / Medium / Low]
```

---

## Test Sign-Off

| Test Area | Tester | Date | Pass/Fail |
|-----------|--------|------|-----------|
| Onboarding Flow | | | |
| Symptom Checker | | | |
| Patient Diary | | | |
| Questions | | | |
| Chemo Dates | | | |
| Profile | | | |
| Education | | | |
| History | | | |

---

*Last Updated: January 2026*
*Version: 2.0 - Updated for new 6-phase symptom checker UX, dark mode, and responsive design*

