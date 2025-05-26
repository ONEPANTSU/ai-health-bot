CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT NOT NULL UNIQUE,
    username TEXT,
    full_name TEXT,
    registered_at TIMESTAMP DEFAULT now(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS patient_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id),
    questionnaire_id UUID REFERENCES questionnaires(id),
    answers JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    gpt_response TEXT,
    s3_files TEXT[],
    summary TEXT
);

CREATE TABLE IF NOT EXISTS questionnaires (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT now()
);