-- ==========================================
-- Career Manager — complete schema (PostgreSQL 17 / Neon)
-- ==========================================
-- Single source of truth: sequences, tables, indexes, functions, RLS, triggers.
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
CREATE SEQUENCE consulting_tracker.seq_dim_company INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
CREATE SEQUENCE consulting_tracker.seq_dim_ctype INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
CREATE SEQUENCE consulting_tracker.seq_dim_file INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
CREATE SEQUENCE consulting_tracker.seq_dim_job_category INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
CREATE SEQUENCE consulting_tracker.seq_dim_language INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
CREATE SEQUENCE consulting_tracker.seq_fact_application INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;

CREATE SEQUENCE consulting_tracker.seq_fact_pdf
	START WITH 1
	INCREMENT BY 1
	NO MINVALUE
	NO MAXVALUE
	CACHE 1;

CREATE SEQUENCE consulting_tracker.seq_web_list
	START WITH 1
	INCREMENT BY 1
	NO MINVALUE
	NO MAXVALUE
	CACHE 1;

-- ==========================================
-- 2. TABLES & CONSTRAINTS (dependency order)
-- ==========================================

-- 2.1 COMPANY TYPES (scoped per user)
CREATE TABLE consulting_tracker.dim_ctype (
	user_id uuid NOT NULL,
	ctype_id int4 DEFAULT nextval('consulting_tracker.seq_dim_ctype'::regclass) NOT NULL,
	type_name varchar(100) NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_ctype_pkey PRIMARY KEY (ctype_id),
	CONSTRAINT dim_company_user_id FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX uq_type_name_lower_per_user ON consulting_tracker.dim_ctype (user_id, lower((type_name)::text));

-- 2.2 JOB CATEGORY (scoped per user)
CREATE TABLE consulting_tracker.dim_job_category (
	user_id uuid NOT NULL,
	job_cat_id int4 DEFAULT nextval('consulting_tracker.seq_dim_job_category'::regclass) NOT NULL,
	category_name varchar(255) NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_job_category_pkey PRIMARY KEY (job_cat_id),
	CONSTRAINT dim_job_cat_user_id FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX uq_job_cat_lower_per_user ON consulting_tracker.dim_job_category (user_id, lower((category_name)::text));

-- 2.3 LANGUAGES (scoped per user)
CREATE TABLE consulting_tracker.dim_language (
	user_id uuid NOT NULL,
	lang_id int4 DEFAULT nextval('consulting_tracker.seq_dim_language'::regclass) NOT NULL,
	"language" varchar(100) NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_language_pkey PRIMARY KEY (lang_id),
	CONSTRAINT dim_lang_user_id FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX uq_dim_language_lower_per_user ON consulting_tracker.dim_language (user_id, lower((language)::text));

-- 2.4 COMPANIES (scoped per user)
CREATE TABLE consulting_tracker.dim_company (
	user_id uuid NOT NULL,
	company_id int4 DEFAULT nextval('consulting_tracker.seq_dim_company'::regclass) NOT NULL,
	ctype_id int4 NULL,
	company_name varchar(255) NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_company_pkey PRIMARY KEY (company_id),
	CONSTRAINT dim_company_user_id FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE,
	CONSTRAINT dim_company_ctype_id_fkey FOREIGN KEY (ctype_id) REFERENCES consulting_tracker.dim_ctype(ctype_id)
);

-- 2.5 FILES / TEMPLATES (scoped per user)
CREATE TABLE consulting_tracker.dim_file (
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
	CONSTRAINT dim_file_user_id FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE,
	CONSTRAINT dim_file_lang_id_fkey FOREIGN KEY (lang_id) REFERENCES consulting_tracker.dim_language(lang_id)
);
CREATE UNIQUE INDEX uq_dim_file_hash_per_user ON consulting_tracker.dim_file (user_id, file_hash);

-- 2.6 APPLICATIONS (core fact — scoped per user)
CREATE TABLE consulting_tracker.fact_application (
	user_id uuid NOT NULL,
	application_id int4 DEFAULT nextval('consulting_tracker.seq_fact_application'::regclass) NOT NULL,
	company_id int4 NULL,
	job_name varchar(255) NOT NULL,
	lang_id int4 NULL,
	status varchar(20) NOT NULL,
	job_cat_id int4 NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT fact_application_pkey PRIMARY KEY (application_id),
	CONSTRAINT fact_app_user_id FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE,
	CONSTRAINT fact_application_status_check CHECK (((status)::text = ANY (ARRAY[('closed'::character varying)::text, ('open'::character varying)::text]))),
	CONSTRAINT fact_application_company_id_fkey FOREIGN KEY (company_id) REFERENCES consulting_tracker.dim_company(company_id),
	CONSTRAINT fact_application_dim_job_category_fk FOREIGN KEY (job_cat_id) REFERENCES consulting_tracker.dim_job_category(job_cat_id) ON DELETE SET NULL ON UPDATE CASCADE,
	CONSTRAINT fact_application_lang_id_fkey FOREIGN KEY (lang_id) REFERENCES consulting_tracker.dim_language(lang_id)
);

-- 2.7 WEB LIST (scoped per user)
CREATE TABLE consulting_tracker.fact_web_list (
	user_id uuid NOT NULL,
	site_id int4 DEFAULT nextval('consulting_tracker.seq_web_list'::regclass) NOT NULL,
	address text NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	last_modification timestamptz,
	CONSTRAINT fact_web_list_pkey PRIMARY KEY (site_id),
	CONSTRAINT fact_web_user_id FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX uq_fact_web_list_per_user ON consulting_tracker.fact_web_list (user_id, lower((address)::text));

-- 2.8 TRACKER (1:1 per application — contact + sent-file paths)
CREATE TABLE consulting_tracker.dim_tracker (
	application_id int4 NOT NULL,
	user_id uuid NOT NULL,
	contact_name varchar(255) NULL,
	contact_email varchar(255) NULL,
	position_url text NULL,
	resume text NULL,
	cover_letter text NULL,
	position_pdf text NULL,
	CONSTRAINT dim_tracker_pkey PRIMARY KEY (application_id),
	CONSTRAINT dim_tracker_user_id_fkey FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE,
	CONSTRAINT dim_tracker_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id) ON DELETE CASCADE
);

-- 2.9 RESUME DETAILS (1:1 per application — CV text blocks + template link)
CREATE TABLE consulting_tracker.dim_resume_details (
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
	CONSTRAINT dim_resume_details_user_id_fkey FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE,
	CONSTRAINT dim_resume_details_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id) ON DELETE CASCADE,
	CONSTRAINT dim_resume_details_file_id_fkey FOREIGN KEY (file_id) REFERENCES consulting_tracker.dim_file(file_id)
);

-- 2.10 COVER LETTER (1:1 per application — letter text + template link)
CREATE TABLE consulting_tracker.dim_cover_letter (
	application_id int4 NOT NULL,
	user_id uuid NOT NULL,
	header text NULL,
	body text NULL,
	"close" text NULL,
	file_id int4 NULL,
	CONSTRAINT dim_cover_letter_pkey PRIMARY KEY (application_id),
	CONSTRAINT dim_cover_letter_user_id_fkey FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE,
	CONSTRAINT dim_cover_letter_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id) ON DELETE CASCADE,
	CONSTRAINT dim_cover_letter_file_id_fkey FOREIGN KEY (file_id) REFERENCES consulting_tracker.dim_file(file_id)
);

-- 2.11 DOCUMENT GENERATION LOG (Word/PDF generator runs)
CREATE TABLE consulting_tracker.fact_pdf_generator (
	pdf_id int4 DEFAULT nextval('consulting_tracker.seq_fact_pdf'::regclass) NOT NULL,
	user_id uuid NOT NULL,
	application_id int4 NOT NULL,
	file_hash char(32) NOT NULL,
	file_name varchar(255) NULL,
	output_file varchar(255) DEFAULT 'output_file.docx'::character varying NOT NULL,
	pdf_success bool DEFAULT true NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT fact_pdf_generator_pkey PRIMARY KEY (pdf_id),
	CONSTRAINT fact_pdf_generator_user_id_fkey FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE,
	CONSTRAINT fact_pdf_generator_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id) ON DELETE CASCADE
);

-- ==========================================
-- 3. INDEXES (multi-tenant access patterns)
-- ==========================================

-- dim_company
CREATE INDEX idx_dim_company_user_id ON consulting_tracker.dim_company (user_id, company_id);
CREATE INDEX idx_dim_company_ctype_id ON consulting_tracker.dim_company (ctype_id);

-- dim_file
CREATE INDEX idx_dim_file_user_id_type ON consulting_tracker.dim_file (user_id, file_type);
CREATE INDEX idx_dim_file_lang_id ON consulting_tracker.dim_file (lang_id);

-- fact_application
CREATE INDEX idx_fact_application_user_id_status ON consulting_tracker.fact_application (user_id, status);
CREATE INDEX idx_fact_application_company_id ON consulting_tracker.fact_application (company_id);
CREATE INDEX idx_fact_application_job_cat_id ON consulting_tracker.fact_application (job_cat_id);
CREATE INDEX idx_fact_application_lang_id ON consulting_tracker.fact_application (lang_id);

-- dim_tracker
CREATE INDEX idx_dim_tracker_user_id ON consulting_tracker.dim_tracker (user_id, application_id);

-- dim_resume_details / dim_cover_letter (Letters & CV + analytics)
CREATE INDEX idx_dim_resume_details_user_id ON consulting_tracker.dim_resume_details (user_id, application_id);
CREATE INDEX idx_dim_cover_letter_user_id ON consulting_tracker.dim_cover_letter (user_id, application_id);

-- fact_pdf_generator (Generator page history)
CREATE INDEX idx_fact_pdf_generator_user_created ON consulting_tracker.fact_pdf_generator (user_id, created_at DESC);
CREATE INDEX idx_fact_pdf_generator_application ON consulting_tracker.fact_pdf_generator (user_id, application_id);

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

	-- 2. Empty CV text blocks row (Milestone 3)
	INSERT INTO consulting_tracker.dim_resume_details (application_id, user_id)
	VALUES (NEW.application_id, NEW.user_id);

	-- 3. Empty cover letter row (Milestone 4)
	INSERT INTO consulting_tracker.dim_cover_letter (application_id, user_id)
	VALUES (NEW.application_id, NEW.user_id);

	RETURN NEW;
END;
$function$;

-- ==========================================
-- 5. ROW LEVEL SECURITY (optional)
-- ==========================================
-- neon_auth."user" stores accounts; RLS helpers live in schema auth (pg_session_jwt).
-- Career Manager FastAPI already scopes every query by user_id — RLS is only needed
-- if you also expose tables via the Neon Data API.
--
-- This block is safe on greenfield installs: it skips RLS when auth.uid() is absent.

DO $$
BEGIN
	BEGIN
		CREATE EXTENSION IF NOT EXISTS pg_session_jwt;
	EXCEPTION
		WHEN OTHERS THEN
			RAISE NOTICE 'pg_session_jwt not installed (%). RLS will be skipped.', SQLERRM;
	END;

	IF to_regprocedure('auth.uid()') IS NOT NULL THEN
		ALTER TABLE consulting_tracker.fact_application ENABLE ROW LEVEL SECURITY;

		DROP POLICY IF EXISTS user_isolation_policy ON consulting_tracker.fact_application;
		CREATE POLICY user_isolation_policy ON consulting_tracker.fact_application
			FOR ALL
			USING (user_id = auth.uid());

		RAISE NOTICE 'RLS enabled on fact_application (user_id = auth.uid()).';
	ELSE
		RAISE NOTICE 'auth.uid() not found — skipping RLS. FastAPI enforces user_id in API queries.';
	END IF;
END $$;

-- ==========================================
-- 6. TRIGGERS
-- ==========================================
DROP TRIGGER IF EXISTS trg_after_application_insert ON consulting_tracker.fact_application;

CREATE TRIGGER trg_after_application_insert
	AFTER INSERT ON consulting_tracker.fact_application
	FOR EACH ROW EXECUTE FUNCTION consulting_tracker.sync_fact_to_tracker();
