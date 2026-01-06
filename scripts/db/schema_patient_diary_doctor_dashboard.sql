-- =============================================================================
-- OncoLife Database Schema - Patient Diary & Doctor Dashboard
-- =============================================================================
-- Run this script to add new tables for:
-- 1. Patient Questions ("Questions to Ask Doctor")
-- 2. Symptom Time Series (analytics)
-- 3. Treatment Events (timeline overlays)
-- 4. Physician Reports (weekly reports)
-- 5. Audit Logs (HIPAA compliance)
--
-- Execute against the appropriate database:
-- - Patient tables: Run against oncolife_patient database
-- - Doctor tables: Run against oncolife_doctor database
-- =============================================================================

-- =============================================================================
-- PATIENT DATABASE TABLES (oncolife_patient)
-- =============================================================================

-- Patient Questions - "Questions to Ask Doctor" feature
CREATE TABLE IF NOT EXISTS patient_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_uuid UUID NOT NULL,
    question_text TEXT NOT NULL,
    share_with_physician BOOLEAN DEFAULT false NOT NULL,
    is_answered BOOLEAN DEFAULT false NOT NULL,
    category VARCHAR(50) DEFAULT 'other',
    is_deleted BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for patient_questions
CREATE INDEX IF NOT EXISTS ix_patient_questions_patient 
    ON patient_questions(patient_uuid);
CREATE INDEX IF NOT EXISTS ix_patient_questions_shared 
    ON patient_questions(share_with_physician);
CREATE INDEX IF NOT EXISTS ix_patient_questions_created 
    ON patient_questions(created_at DESC);

-- Add comment
COMMENT ON TABLE patient_questions IS 'Patient questions to ask their doctor (opt-in sharing)';


-- =============================================================================
-- DOCTOR DATABASE TABLES (oncolife_doctor)
-- =============================================================================

-- Symptom Time Series - Powers timeline charts and analytics
CREATE TABLE IF NOT EXISTS symptom_time_series (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL,
    symptom_id VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('mild', 'moderate', 'severe', 'urgent')),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    source_session_id UUID,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance-critical indexes
CREATE INDEX IF NOT EXISTS idx_symptom_patient_time 
    ON symptom_time_series(patient_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_symptom_severity 
    ON symptom_time_series(severity);

COMMENT ON TABLE symptom_time_series IS 'Time-series symptom data for clinical analytics';


-- Treatment Events - Timeline overlays for chemo correlation
CREATE TABLE IF NOT EXISTS treatment_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL CHECK (
        event_type IN ('chemo_start', 'chemo_end', 'cycle_start', 'cycle_end', 'regimen_change')
    ),
    event_date DATE NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for timeline queries
CREATE INDEX IF NOT EXISTS idx_treatment_patient_date 
    ON treatment_events(patient_id, event_date);

COMMENT ON TABLE treatment_events IS 'Treatment events for timeline overlays';


-- Physician Reports - Weekly report metadata
CREATE TABLE IF NOT EXISTS physician_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    physician_id UUID NOT NULL,
    report_week_start DATE NOT NULL,
    report_week_end DATE NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    report_s3_path TEXT NOT NULL,
    patient_count INTEGER,
    alert_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for report retrieval
CREATE INDEX IF NOT EXISTS idx_report_physician_week 
    ON physician_reports(physician_id, report_week_start);

COMMENT ON TABLE physician_reports IS 'Weekly physician report metadata';


-- Audit Logs - HIPAA compliance tracking
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    user_role VARCHAR(50) NOT NULL CHECK (user_role IN ('physician', 'staff', 'admin')),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    ip_address VARCHAR(50),
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_audit_user_time 
    ON audit_logs(user_id, accessed_at);
CREATE INDEX IF NOT EXISTS idx_audit_entity 
    ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_action 
    ON audit_logs(action);

COMMENT ON TABLE audit_logs IS 'HIPAA-compliant access audit logs';


-- =============================================================================
-- DATA MIGRATION - Populate symptom_time_series from existing conversations
-- =============================================================================

-- Run this to backfill symptom time series data from existing conversations
-- Note: This is a one-time migration; new data will be populated automatically

-- INSERT INTO symptom_time_series (patient_id, symptom_id, severity, recorded_at, source_session_id)
-- SELECT 
--     c.patient_uuid,
--     unnest(c.symptom_list) as symptom_id,
--     COALESCE(
--         CASE 
--             WHEN c.conversation_state = 'EMERGENCY' THEN 'urgent'
--             ELSE 'moderate'
--         END, 
--         'moderate'
--     ) as severity,
--     c.created_at as recorded_at,
--     c.uuid as source_session_id
-- FROM conversations c
-- WHERE c.symptom_list IS NOT NULL
-- AND array_length(c.symptom_list, 1) > 0
-- ON CONFLICT DO NOTHING;


-- =============================================================================
-- GRANT PERMISSIONS (adjust as needed for your environment)
-- =============================================================================

-- Grant permissions to application user
-- GRANT SELECT, INSERT, UPDATE ON patient_questions TO oncolife_app;
-- GRANT SELECT, INSERT ON symptom_time_series TO oncolife_app;
-- GRANT SELECT, INSERT ON treatment_events TO oncolife_app;
-- GRANT SELECT, INSERT ON physician_reports TO oncolife_app;
-- GRANT INSERT ON audit_logs TO oncolife_app;  -- No SELECT for security


-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Run these queries to verify tables were created:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
-- \dt+ patient_questions
-- \dt+ symptom_time_series
-- \dt+ treatment_events
-- \dt+ physician_reports
-- \dt+ audit_logs



