"""
Constants for the Symptom Checker module.
Defines triage levels, input types, and symptom categories.
"""
from enum import Enum


class TriageLevel(str, Enum):
    """Triage action levels from most to least urgent."""
    CALL_911 = "call_911"           # Emergency - Call 911 immediately
    NOTIFY_CARE_TEAM = "notify_care_team"  # Alert - Care team will be notified
    NONE = "none"                   # Monitor - Follow up at next appointment


class InputType(str, Enum):
    """Types of user input expected for questions."""
    YES_NO = "yes_no"
    TEXT = "text"
    NUMBER = "number"
    CHOICE = "choice"           # Single select
    MULTISELECT = "multiselect" # Multiple select


class SymptomCategory(str, Enum):
    """Categories of symptoms."""
    EMERGENCY = "emergency"
    COMMON = "common"
    OTHER = "other"


class ConversationPhase(str, Enum):
    """Phases of the symptom checker conversation."""
    GREETING = "greeting"
    SYMPTOM_SELECTION = "symptom_selection"
    SCREENING = "screening"
    FOLLOW_UP = "follow_up"
    COMPLETED = "completed"
    EMERGENCY = "emergency"
    BRANCHED = "branched"


# Standard Options
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



