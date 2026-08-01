-- ==========================================
-- Career Manager — complete schema (PostgreSQL 17 / Neon)
-- ==========================================
-- Single source of truth: sequences, tables, indexes, functions, RLS, triggers.
-- user_id stores the Cognito user pool subject (sub). Neon Auth FKs intentionally omitted.
-- user_id stores the Cognito user pool subject (sub). Neon Auth FKs intentionally omitted.
--
-- Greenfield install (destroys all data in consulting_tracker):
--   Uncomment the DROP/CREATE SCHEMA lines below, then run this file.
--
-- Existing database: do NOT re-run this whole file — it uses CREATE without
-- IF NOT EXISTS. Add missing objects manually or restore from backup first.
-- ==========================================

-- DROP SCHEMA IF EXISTS consulting_tracker CASCADE;
-- CREATE SCHEMA consulting_tracker AUTHORIZATION neondb_owner;

	SET search_path TO consulting_tracker, public;

-- ==========================================
-- 1. EXPLICIT SEQUENCES
-- ==========================================
CREATE SEQUENCE IF NOT EXISTS consulting_tracker.seq_dim_company INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
CREATE SEQUENCE IF NOT EXISTS consulting_tracker.seq_dim_ctype INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
CREATE SEQUENCE IF NOT EXISTS consulting_tracker.seq_dim_file INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
CREATE SEQUENCE IF NOT EXISTS consulting_tracker.seq_dim_job_category INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
CREATE SEQUENCE IF NOT EXISTS consulting_tracker.seq_dim_language INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
CREATE SEQUENCE IF NOT EXISTS consulting_tracker.seq_fact_application INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
CREATE SEQUENCE IF NOT EXISTS consulting_tracker.seq_dim_attachment
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS consulting_tracker.seq_fact_pdf
	START WITH 1
	INCREMENT BY 1
	NO MINVALUE
	NO MAXVALUE
	CACHE 1;

CREATE SEQUENCE IF NOT EXISTS consulting_tracker.seq_web_list
	START WITH 1
	INCREMENT BY 1
	NO MINVALUE
	NO MAXVALUE
	CACHE 1;

-- ==========================================
-- 2. TABLES & CONSTRAINTS (dependency order)
-- ==========================================

-- 2.1 COMPANY TYPES (scoped per user)
CREATE TABLE IF NOT EXISTS consulting_tracker.dim_ctype (
	user_id uuid NOT NULL,
	ctype_id int4 DEFAULT nextval('consulting_tracker.seq_dim_ctype'::regclass) NOT NULL,
	type_name varchar(100) NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_ctype_pkey PRIMARY KEY (ctype_id)
);

-- 2.2 JOB CATEGORY (scoped per user)
CREATE TABLE IF NOT EXISTS consulting_tracker.dim_job_category (
	user_id uuid NOT NULL,
	job_cat_id int4 DEFAULT nextval('consulting_tracker.seq_dim_job_category'::regclass) NOT NULL,
	category_name varchar(255) NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_job_category_pkey PRIMARY KEY (job_cat_id)
);

-- 2.3 LANGUAGES (scoped per user)
CREATE TABLE IF NOT EXISTS consulting_tracker.dim_language (
	user_id uuid NOT NULL,
	lang_id int4 DEFAULT nextval('consulting_tracker.seq_dim_language'::regclass) NOT NULL,
	"language" varchar(100) NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_language_pkey PRIMARY KEY (lang_id)
);


-- 2.4 COMPANIES (scoped per user)
CREATE TABLE IF NOT EXISTS consulting_tracker.dim_company (
	user_id uuid NOT NULL,
	company_id int4 DEFAULT nextval('consulting_tracker.seq_dim_company'::regclass) NOT NULL,
	ctype_id int4 NULL,
	company_name varchar(255) NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_company_pkey PRIMARY KEY (company_id),
	CONSTRAINT dim_company_ctype_id_fkey FOREIGN KEY (ctype_id) REFERENCES consulting_tracker.dim_ctype(ctype_id)
);

-- 2.5 FILES / TEMPLATES (scoped per user)
CREATE TABLE IF NOT EXISTS consulting_tracker.dim_file (
	user_id uuid NOT NULL,
	file_id int4 DEFAULT nextval('consulting_tracker.seq_dim_file'::regclass) NOT NULL,
	lang_id int4 NULL,
	file_name varchar(255) NOT NULL,
	file_hash char(32) NOT NULL,
	file_type varchar(50) NOT NULL,
	active_status bool DEFAULT true NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_file_file_type_check CHECK (((file_type)::text = ANY (ARRAY[('cover letter'::character varying)::text, ('cv'::character varying)::text]))),
	CONSTRAINT dim_file_pkey PRIMARY KEY (file_id),
	CONSTRAINT dim_file_lang_id_fkey FOREIGN KEY (lang_id) REFERENCES consulting_tracker.dim_language(lang_id)
);



-- 2.6 WEB LIST (scoped per user — must precede fact_application for FK reference)
CREATE TABLE IF NOT EXISTS consulting_tracker.fact_web_list (
	user_id uuid NOT NULL,
	site_id int4 DEFAULT nextval('consulting_tracker.seq_web_list'::regclass) NOT NULL,
	address text NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	last_modification timestamptz,
	CONSTRAINT fact_web_list_pkey PRIMARY KEY (site_id)
);

-- 2.7 APPLICATIONS (core fact — scoped per user)
CREATE TABLE IF NOT EXISTS consulting_tracker.fact_application (
	user_id uuid NOT NULL,
	application_id int4 DEFAULT nextval('consulting_tracker.seq_fact_application'::regclass) NOT NULL,
	company_id int4 NULL,
	job_name varchar(255) NOT NULL,
	lang_id int4 NULL,
	status varchar(20) NOT NULL,
	job_cat_id int4 NULL,
	site_id int4 NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT fact_application_pkey PRIMARY KEY (application_id),
	CONSTRAINT fact_application_status_check CHECK (((status)::text = ANY (ARRAY[('closed'::character varying)::text, ('open'::character varying)::text]))),
	CONSTRAINT fact_application_company_id_fkey FOREIGN KEY (company_id) REFERENCES consulting_tracker.dim_company(company_id),
	CONSTRAINT fact_application_dim_job_category_fk FOREIGN KEY (job_cat_id) REFERENCES consulting_tracker.dim_job_category(job_cat_id) ON DELETE SET NULL ON UPDATE CASCADE,
	CONSTRAINT fact_application_lang_id_fkey FOREIGN KEY (lang_id) REFERENCES consulting_tracker.dim_language(lang_id),
	CONSTRAINT fact_application_site_id_fkey FOREIGN KEY (site_id) REFERENCES consulting_tracker.fact_web_list(site_id) ON DELETE SET NULL
);

-- Backfill: add site_id to existing fact_application tables
ALTER TABLE consulting_tracker.fact_application
    ADD COLUMN IF NOT EXISTS site_id int4 NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'consulting_tracker'
          AND table_name = 'fact_application'
          AND constraint_name = 'fact_application_site_id_fkey'
    ) THEN
        ALTER TABLE consulting_tracker.fact_application
            ADD CONSTRAINT fact_application_site_id_fkey
            FOREIGN KEY (site_id) REFERENCES consulting_tracker.fact_web_list(site_id)
            ON DELETE SET NULL;
    END IF;
END $$;


-- 2.8 TRACKER (1:1 per application — contact + sent-file paths)
CREATE TABLE IF NOT EXISTS consulting_tracker.dim_tracker (
	application_id int4 NOT NULL,
	user_id uuid NOT NULL,
	contact_name varchar(255) NULL,
	contact_email varchar(255) NULL,
	position_url text NULL,
	resume text NULL,
	cover_letter text NULL,
	position_pdf text NULL,
	CONSTRAINT dim_tracker_pkey PRIMARY KEY (application_id),
	CONSTRAINT dim_tracker_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id) ON DELETE CASCADE
);

-- 2.9 RESUME DETAILS (1:1 per application — CV text blocks + template link)
CREATE TABLE IF NOT EXISTS consulting_tracker.dim_resume_details (
	application_id int4 NOT NULL,
	user_id uuid NOT NULL,
	ed1 text NULL,
	ed2 text NULL,
	ed3 text NULL,
	ex1 text NULL,
	ex2 text NULL,
	ex3 text NULL,
	skills text NULL,
	interests text NULL,
	file_id int4 NULL,
	CONSTRAINT dim_resume_details_pkey PRIMARY KEY (application_id),
	CONSTRAINT dim_resume_details_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id) ON DELETE CASCADE,
	CONSTRAINT dim_resume_details_file_id_fkey FOREIGN KEY (file_id) REFERENCES consulting_tracker.dim_file(file_id)
);

-- 2.10 COVER LETTER (1:1 per application — letter text + template link)
CREATE TABLE IF NOT EXISTS consulting_tracker.dim_cover_letter (
	application_id int4 NOT NULL,
	user_id uuid NOT NULL,
	header text NULL,
	body text NULL,
	"close" text NULL,
	file_id int4 NULL,
	CONSTRAINT dim_cover_letter_pkey PRIMARY KEY (application_id),
	CONSTRAINT dim_cover_letter_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id) ON DELETE CASCADE,
	CONSTRAINT dim_cover_letter_file_id_fkey FOREIGN KEY (file_id) REFERENCES consulting_tracker.dim_file(file_id)
);

-- 2.11 DOCUMENT GENERATION LOG (Word/PDF generator runs)
CREATE TABLE IF NOT EXISTS consulting_tracker.fact_pdf_generator (
	pdf_id int4 DEFAULT nextval('consulting_tracker.seq_fact_pdf'::regclass) NOT NULL,
	user_id uuid NOT NULL,
	application_id int4 NOT NULL,
	file_hash char(32) NOT NULL,
	file_name varchar(255) NULL,
	output_file varchar(255) DEFAULT 'output_file.docx'::character varying NOT NULL,
	pdf_success bool DEFAULT true NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT fact_pdf_generator_pkey PRIMARY KEY (pdf_id),
	CONSTRAINT fact_pdf_generator_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id) ON DELETE CASCADE
);
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
    CONSTRAINT dim_attachment_application_id_fkey
        FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id) ON DELETE CASCADE,
    CONSTRAINT dim_attachment_type_check
        CHECK (attachment_type IN ('job_description', 'resume_submitted', 'cover_letter_submitted'))
);


-- ==========================================
-- 3. INDEXES (multi-tenant access patterns)
-- ==========================================
CREATE UNIQUE INDEX IF NOT EXISTS uq_type_name_lower_per_user ON consulting_tracker.dim_ctype (user_id, lower((type_name)::text));
CREATE UNIQUE INDEX IF NOT EXISTS uq_job_cat_lower_per_user ON consulting_tracker.dim_job_category (user_id, lower((category_name)::text));
CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_language_lower_per_user ON consulting_tracker.dim_language (user_id, lower((language)::text));
CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_file_hash_per_user ON consulting_tracker.dim_file (user_id, file_hash);
CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_web_list_per_user ON consulting_tracker.fact_web_list (user_id, lower((address)::text));
-- dim_company
CREATE INDEX IF NOT EXISTS idx_dim_company_user_id ON consulting_tracker.dim_company (user_id, company_id);
CREATE INDEX IF NOT EXISTS idx_dim_company_ctype_id ON consulting_tracker.dim_company (ctype_id);

-- dim_file
CREATE INDEX IF NOT EXISTS idx_dim_file_user_id_type ON consulting_tracker.dim_file (user_id, file_type);
CREATE INDEX IF NOT EXISTS idx_dim_file_lang_id ON consulting_tracker.dim_file (lang_id);

-- fact_application
CREATE INDEX IF NOT EXISTS idx_fact_application_user_id_status ON consulting_tracker.fact_application (user_id, status);
CREATE INDEX IF NOT EXISTS idx_fact_application_company_id ON consulting_tracker.fact_application (company_id);
CREATE INDEX IF NOT EXISTS idx_fact_application_job_cat_id ON consulting_tracker.fact_application (job_cat_id);
CREATE INDEX IF NOT EXISTS idx_fact_application_lang_id ON consulting_tracker.fact_application (lang_id);

-- dim_tracker
CREATE INDEX IF NOT EXISTS idx_dim_tracker_user_id ON consulting_tracker.dim_tracker (user_id, application_id);

-- dim_resume_details / dim_cover_letter (Letters & CV + analytics)
CREATE INDEX IF NOT EXISTS idx_dim_resume_details_user_id ON consulting_tracker.dim_resume_details (user_id, application_id);
CREATE INDEX IF NOT EXISTS idx_dim_cover_letter_user_id ON consulting_tracker.dim_cover_letter (user_id, application_id);

-- fact_pdf_generator (Generator page history)
CREATE INDEX IF NOT EXISTS idx_fact_pdf_generator_user_created ON consulting_tracker.fact_pdf_generator (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fact_pdf_generator_application ON consulting_tracker.fact_pdf_generator (user_id, application_id);

-- fact_application → fact_web_list
CREATE INDEX IF NOT EXISTS idx_fact_application_site_id ON consulting_tracker.fact_application (site_id);


-- One row per (application, type) — enforces the 3-slot model
CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_attachment_app_type
    ON consulting_tracker.dim_attachment (application_id, attachment_type);

-- Fast lookup by user + application
CREATE INDEX IF NOT EXISTS idx_dim_attachment_user_app
    ON consulting_tracker.dim_attachment (user_id, application_id);


-- ==========================================
-- 4. TRIGGER FUNCTIONS (after all target tables exist)
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

-- ==========================================
-- 5. ROW LEVEL SECURITY — not used
-- ==========================================
-- Multi-tenancy is enforced in FastAPI: every API query filters by user_id from the
-- Cognito JWT subject (sub claim). No FK to an auth user table is required.
--
-- RLS is intentionally omitted; this app uses Lambda + FastAPI ownership filters.

-- ==========================================
-- 6. TRIGGERS
-- ==========================================
DROP TRIGGER IF EXISTS trg_after_application_insert ON consulting_tracker.fact_application;

CREATE TRIGGER trg_after_application_insert
	AFTER INSERT ON consulting_tracker.fact_application
	FOR EACH ROW EXECUTE FUNCTION consulting_tracker.sync_fact_to_tracker();

-- ==========================================
-- 7. VIEWS
-- ==========================================

-- vw_web_list: fact_web_list with application usage counts, ordered by created_at DESC
CREATE OR REPLACE VIEW consulting_tracker.vw_web_list AS
SELECT
    fwl.site_id,
    fwl.user_id,
    fwl.address,
    fwl.created_at,
    fwl.last_modification,
    COUNT(fa.application_id) AS application_count
FROM consulting_tracker.fact_web_list fwl
LEFT JOIN consulting_tracker.fact_application fa
    ON fa.site_id = fwl.site_id AND fa.user_id = fwl.user_id
GROUP BY
    fwl.site_id,
    fwl.user_id,
    fwl.address,
    fwl.created_at,
    fwl.last_modification;
