-- ==========================================
-- Migration: dim_attachment
-- Tracks uploaded PDFs (job description, CV submitted, cover letter submitted)
-- per fact_application. Files are stored in S3; this table holds the metadata.
-- ==========================================

SET search_path TO consulting_tracker, public;

-- Sequence
CREATE SEQUENCE IF NOT EXISTS consulting_tracker.seq_dim_attachment
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

-- Table
CREATE TABLE IF NOT EXISTS consulting_tracker.dim_attachment (
    attachment_id    int4 DEFAULT nextval('consulting_tracker.seq_dim_attachment'::regclass) NOT NULL,
    application_id   int4 NOT NULL,
    user_id          uuid NOT NULL,
    attachment_type  varchar(30) NOT NULL,
    -- S3 metadata (NULL until a file is uploaded)
    s3_key           text NULL,
    file_name        varchar(255) NULL,
    file_hash        char(32) NULL,
    file_size_bytes  int8 NULL,
    uploaded_at      timestamptz NULL,
    -- Audit columns following existing schema conventions
    load_date        date DEFAULT CURRENT_DATE NOT NULL,
    created_at       timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT dim_attachment_pkey PRIMARY KEY (attachment_id),
    CONSTRAINT dim_attachment_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE,
    CONSTRAINT dim_attachment_application_id_fkey
        FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id) ON DELETE CASCADE,
    CONSTRAINT dim_attachment_type_check
        CHECK (attachment_type IN ('job_description', 'resume_submitted', 'cover_letter_submitted'))
);

-- One row per (application, type) — enforces the 3-slot model
CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_attachment_app_type
    ON consulting_tracker.dim_attachment (application_id, attachment_type);

-- Fast lookup by user + application
CREATE INDEX IF NOT EXISTS idx_dim_attachment_user_app
    ON consulting_tracker.dim_attachment (user_id, application_id);

-- ==========================================
-- Update trigger function to auto-create the three attachment slots
-- ==========================================
CREATE OR REPLACE FUNCTION consulting_tracker.sync_fact_to_tracker()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    -- 1. Master tracker row
    INSERT INTO consulting_tracker.dim_tracker (application_id, user_id)
    VALUES (NEW.application_id, NEW.user_id);

    -- 2. Empty CV text blocks row
    INSERT INTO consulting_tracker.dim_resume_details (application_id, user_id)
    VALUES (NEW.application_id, NEW.user_id);

    -- 3. Empty cover letter row
    INSERT INTO consulting_tracker.dim_cover_letter (application_id, user_id)
    VALUES (NEW.application_id, NEW.user_id);

    -- 4. Three attachment slots (job description, CV submitted, cover letter submitted)
    INSERT INTO consulting_tracker.dim_attachment (application_id, user_id, attachment_type)
    VALUES
        (NEW.application_id, NEW.user_id, 'job_description'),
        (NEW.application_id, NEW.user_id, 'resume_submitted'),
        (NEW.application_id, NEW.user_id, 'cover_letter_submitted');

    RETURN NEW;
END;
$function$;

-- Back-fill existing applications that have no attachment rows yet
INSERT INTO consulting_tracker.dim_attachment (application_id, user_id, attachment_type)
SELECT fa.application_id, fa.user_id, t.attachment_type
FROM consulting_tracker.fact_application fa
CROSS JOIN (VALUES
    ('job_description'),
    ('resume_submitted'),
    ('cover_letter_submitted')
) AS t(attachment_type)
WHERE NOT EXISTS (
    SELECT 1
    FROM consulting_tracker.dim_attachment da
    WHERE da.application_id = fa.application_id
      AND da.attachment_type = t.attachment_type
);
