"""
Constants for the Symptom Checker module.
Defines triage levels, input types, symptom categories, and groupings.
"""
from enum import Enum


class TriageLevel(str, Enum):
    """Triage action levels from most to least urgent."""
    CALL_911 = "call_911"           # Emergency - Call 911 immediately
    URGENT = "urgent"               # Urgent - Contact care team immediately
    NOTIFY_CARE_TEAM = "notify_care_team"  # Alert - Care team will be notified
    NONE = "none"                   # Monitor - Follow up at next appointment


class InputType(str, Enum):
    """Types of user input expected for questions."""
    YES_NO = "yes_no"
    TEXT = "text"
    NUMBER = "number"
    CHOICE = "choice"           # Single select
    MULTISELECT = "multiselect" # Multiple select
    BUTTON = "button"           # Single action button
    CONFIRM = "confirm"         # Confirmation with checkbox


class SymptomCategory(str, Enum):
    """Categories of symptoms."""
    EMERGENCY = "emergency"
    DIGESTIVE = "digestive"
    PAIN_NERVE = "pain_nerve"
    SYSTEMIC = "systemic"
    SKIN_EXTERNAL = "skin_external"
    COMMON = "common"
    OTHER = "other"


class ConversationPhase(str, Enum):
    """Phases of the symptom checker conversation."""
    DISCLAIMER = "disclaimer"                    # NEW: Medical disclaimer
    EMERGENCY_CHECK = "emergency_check"          # NEW: Urgent safety check
    SYMPTOM_SELECTION = "symptom_selection"      # Grouped symptom selection
    SCREENING = "screening"                      # Per-symptom questions
    FOLLOW_UP = "follow_up"                      # Follow-up questions
    SUMMARY = "summary"                          # NEW: Session summary
    COMPLETED = "completed"                      # Final state
    EMERGENCY = "emergency"                      # Emergency path
    BRANCHED = "branched"                        # Branched to another symptom


# =============================================================================
# SYMPTOM GROUPINGS (User-Friendly Categories)
# =============================================================================

# Emergency symptoms shown in Urgent Safety Check screen
EMERGENCY_SYMPTOMS = [
    {"id": "URG-101", "name": "Trouble Breathing", "icon": "🫁"},
    {"id": "URG-102", "name": "Chest Pain", "icon": "💔"},
    {"id": "URG-103", "name": "Bleeding / Bruising", "icon": "🩸"},
    {"id": "URG-107", "name": "Fainting / Syncope", "icon": "😵"},
    {"id": "URG-108", "name": "Confusion / Altered Mental Status", "icon": "🧠"},
]

# Grouped symptoms for main symptom selection screen
# IDs must match symptom_definitions.py
SYMPTOM_GROUPS = {
    "digestive": {
        "name": "Digestive Health",
        "icon": "🍽️",
        "symptoms": [
            {"id": "NAU-203", "name": "Nausea"},
            {"id": "VOM-204", "name": "Vomiting"},
            {"id": "DIA-205", "name": "Diarrhea"},
            {"id": "CON-210", "name": "Constipation"},
            {"id": "APP-209", "name": "No Appetite"},
            {"id": "MSO-208", "name": "Mouth Sores"},
            {"id": "DEH-201", "name": "Dehydration"},
        ]
    },
    "pain_nerve": {
        "name": "Pain & Nerve",
        "icon": "⚡",
        "symptoms": [
            {"id": "PAI-213", "name": "Pain / General Aches"},
            {"id": "NEU-216", "name": "Neuropathy (Numbness/Tingling)"},
            {"id": "HEA-210", "name": "Headache"},
            {"id": "ABD-211", "name": "Abdominal Pain"},
            {"id": "JMP-212", "name": "Joint / Muscle Pain"},
            {"id": "LEG-208", "name": "Leg / Calf Pain"},
            {"id": "URG-114", "name": "Port Site Pain"},
        ]
    },
    "systemic": {
        "name": "Systemic & Infection",
        "icon": "🌡️",
        "symptoms": [
            {"id": "FEV-202", "name": "Fever"},
            {"id": "FAT-206", "name": "Fatigue / Weakness"},
            {"id": "COU-215", "name": "Cough"},
            {"id": "URI-211", "name": "Urinary Problems"},
        ]
    },
    "skin_external": {
        "name": "Skin & External",
        "icon": "🩹",
        "symptoms": [
            {"id": "SKI-212", "name": "Skin Rash / Redness"},
            {"id": "SWE-214", "name": "Swelling"},
            {"id": "EYE-207", "name": "Eye Complaints"},
        ]
    }
}


# =============================================================================
# MEDICAL DISCLAIMER
# =============================================================================

MEDICAL_DISCLAIMER = """⚠️ IMPORTANT MEDICAL DISCLAIMER

This system is an automated symptom checker. It is NOT a substitute for professional medical advice, diagnosis, or treatment.

• This tool helps you report symptoms to your care team
• It does not provide medical diagnoses
• Always follow your doctor's instructions

**If you believe you are having a medical emergency, call 911 immediately.**"""


EMERGENCY_CHECK_MESSAGE = """🚨 Urgent Safety Check

Before we assess your symptoms, we need to rule out immediate emergencies.

Please select any of the following that you are **currently experiencing**:"""


RUBY_GREETING = """Hello! I am **Ruby**, your automated triage assistant. 👋

I'm here to help assess your symptoms and share the information with your care team.

I'll ask you a few questions about each symptom you selected. Take your time - there's no rush."""


# =============================================================================
# STANDARD OPTIONS
# =============================================================================

ORAL_INTAKE_OPTIONS = [
    {"label": "I have a reduced appetite but can still eat and drink", "value": "reduced"},
    {"label": "I have had difficulty keeping food or fluids down", "value": "difficulty"},
    {"label": "I can barely eat or drink anything", "value": "barely"},
    {"label": "I have not been able to eat or drink in the last 24 hours", "value": "none"},
    {"label": "I can eat and drink normally", "value": "normal"}
]

ORAL_INTAKE_OPTIONS_12H = [
    {"label": "I have a reduced appetite but can still eat and drink", "value": "reduced"},
    {"label": "I have had difficulty keeping food or fluids down", "value": "difficulty"},
    {"label": "I can barely eat or drink anything", "value": "barely"},
    {"label": "I have not been able to eat or drink in the last 12 hours", "value": "none"},
    {"label": "I can eat and drink normally", "value": "normal"}
]

DEHYDRATION_SIGNS_OPTIONS = [
    {"label": "Dark urine", "value": "dark_urine"},
    {"label": "Reduced urination for over 12 hours", "value": "less_urine"},
    {"label": "Constantly feeling thirsty", "value": "thirsty"},
    {"label": "Feeling lightheaded", "value": "lightheaded"},
    {"label": "I know my Heart Rate/Blood Pressure", "value": "vitals_known"},
    {"label": "None of the above", "value": "none"}
]

SEVERITY_OPTIONS = [
    {"label": "Mild", "value": "mild"},
    {"label": "Moderate", "value": "mod"},
    {"label": "Severe", "value": "sev"}
]

DURATION_OPTIONS_SHORT = [
    {"label": "Less than 24 hours", "value": "<24h"},
    {"label": "1-2 days", "value": "1-2d"},
    {"label": "3-7 days", "value": "3-7d"},
    {"label": "More than a week", "value": ">1w"},
    {"label": "More than 3 weeks", "value": ">3w"}
]

DURATION_OPTIONS_NAUSEA = [
    {"label": "Less than 24 hours", "value": "<24h"},
    {"label": "24 hours", "value": "24h"},
    {"label": "2-3 days", "value": "2-3d"},
    {"label": "More than 3 days", "value": ">3d"}
]

# Medication Options
MEDS_NAUSEA = [
    {"label": "Compazine (prochlorperazine) 5 mg every 6 hours", "value": "compazine"},
    {"label": "Zofran (ondansetron) 8 mg every 8 hours", "value": "zofran"},
    {"label": "Olanzapine 5 mg daily", "value": "olanzapine"},
    {"label": "Other", "value": "other"},
    {"label": "None", "value": "none"}
]

MEDS_DIARRHEA = [
    {"label": "Imodium (loperamide) 4 mg then 2 mg after each loose stool", "value": "imodium"},
    {"label": "Lomotil (diphenoxylate/atropine) 1-2 tablets up to 4 times daily", "value": "lomotil"},
    {"label": "Other", "value": "other"},
    {"label": "None", "value": "none"}
]

MEDS_CONSTIPATION = [
    {"label": "Miralax 17g once daily", "value": "miralax_qd"},
    {"label": "Miralax 17g twice daily", "value": "miralax_bid"},
    {"label": "Senna 8.6mg", "value": "senna"},
    {"label": "Bisacodyl (Dulcolax)", "value": "bisacodyl"},
    {"label": "Docusate (Colace)", "value": "docusate"},
    {"label": "Other", "value": "other"},
    {"label": "None", "value": "none"}
]

MEDS_NEUROPATHY = [
    {"label": "Gabapentin", "value": "gabapentin"},
    {"label": "Duloxetine (Cymbalta)", "value": "duloxetine"},
    {"label": "Pregabalin (Lyrica)", "value": "pregabalin"},
    {"label": "Other", "value": "other"},
    {"label": "None", "value": "none"}
]

MEDS_COUGH = [
    {"label": "Robitussin (dextromethorphan) 10-20 mg every 4 hours", "value": "robitussin_10_20"},
    {"label": "Robitussin (dextromethorphan) 30 mg every 6-8 hours", "value": "robitussin_30"},
    {"label": "Other", "value": "other"},
    {"label": "None", "value": "none"}
]


# =============================================================================
# SUMMARY OPTIONS
# =============================================================================

SUMMARY_ACTIONS = [
    {"label": "📥 Download Summary", "value": "download", "icon": "download"},
    {"label": "📔 Save to My Diary", "value": "save_diary", "icon": "diary"},
    {"label": "🔄 Report Another Symptom", "value": "report_another", "icon": "repeat"},
    {"label": "✅ Done for Today", "value": "done", "icon": "check"},
]
