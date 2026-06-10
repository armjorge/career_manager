-- ==========================================
-- Initialize Schema Environment
-- ==========================================
-- DROP SCHEMA IF EXISTS consulting_tracker CASCADE;
CREATE SCHEMA consulting_tracker AUTHORIZATION neondb_owner;

-- Force the session to use our schema for un-prefixed commands
SET search_path TO consulting_tracker, public;

-- ==========================================
-- 1. EXPLICIT SEQUENCES (With BigInt Max values)
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
-- ==========================================
-- 2. TRIGGER FUNCTIONS (Compiled Early)
-- ==========================================
CREATE OR REPLACE FUNCTION consulting_tracker.sync_fact_to_tracker()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
-- 1. Populate the master tracker extension
    INSERT INTO consulting_tracker.dim_tracker (application_id)
    VALUES (NEW.application_id);

-- 2. Populate the granular CV text snapshot dimension
    INSERT INTO consulting_tracker.dim_resume_details (application_id)
    VALUES (NEW.application_id); 
    -- Note: Your DDL requires job_name to be NOT NULL, so we stage a placeholder string!
    
    -- 3. Populate the cover letter workspace dimension
    INSERT INTO consulting_tracker.dim_cover_letter (application_id)
    VALUES (NEW.application_id);
    
    -- Finalize the transactional handshake

    RETURN NEW; 
END;
$function$;

-- ==========================================
-- 3. TABLES & CONSTRAINTS
-- ==========================================

CREATE TABLE consulting_tracker.dim_ctype (
	ctype_id int4 DEFAULT nextval('consulting_tracker.seq_dim_ctype'::regclass) NOT NULL,
	type_name varchar(100) NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_ctype_pkey PRIMARY KEY (ctype_id)
);
CREATE UNIQUE INDEX uq_type_name_lower ON consulting_tracker.dim_ctype USING btree (lower((type_name)::text));

CREATE TABLE consulting_tracker.dim_job_category (
	job_cat_id int4 DEFAULT nextval('consulting_tracker.seq_dim_job_category'::regclass) NOT NULL,
	category_name varchar(255) NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_job_category_pkey PRIMARY KEY (job_cat_id)
);

CREATE TABLE consulting_tracker.dim_language (
	lang_id int4 DEFAULT nextval('consulting_tracker.seq_dim_language'::regclass) NOT NULL,
	"language" varchar(100) NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_language_pkey PRIMARY KEY (lang_id)
);
CREATE UNIQUE INDEX uq_dim_language_lower ON consulting_tracker.dim_language USING btree (lower((language)::text));

CREATE TABLE consulting_tracker.dim_company (
	company_id int4 DEFAULT nextval('consulting_tracker.seq_dim_company'::regclass) NOT NULL,
	ctype_id int4 NULL,
	company_name varchar(255) NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT dim_company_pkey PRIMARY KEY (company_id),
	CONSTRAINT dim_company_ctype_id_fkey FOREIGN KEY (ctype_id) REFERENCES consulting_tracker.dim_ctype(ctype_id)
);

CREATE TABLE consulting_tracker.dim_file (
	file_id int4 DEFAULT nextval('consulting_tracker.seq_dim_file'::regclass) NOT NULL,
	lang_id int4 NULL,
	file_name varchar(255) NOT NULL,
	file_hash char(32) NOT NULL,
	file_type varchar(50) NOT NULL,
	active_status bool DEFAULT true NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL
	CONSTRAINT dim_file_file_type_check CHECK (((file_type)::text = ANY (ARRAY[('cover letter'::character varying)::text, ('cv'::character varying)::text]))),
	CONSTRAINT dim_file_pkey PRIMARY KEY (file_id),
	CONSTRAINT dim_file_lang_id_fkey FOREIGN KEY (lang_id) REFERENCES consulting_tracker.dim_language(lang_id),
	CONSTRAINT dim_file_hash UNIQUE (file_hash)
);



CREATE TABLE consulting_tracker.fact_application (
	application_id int4 DEFAULT nextval('consulting_tracker.seq_fact_application'::regclass) NOT NULL,
	company_id int4 NULL,
	job_name varchar(255) NOT NULL,
	lang_id int4 NULL,
	status varchar(20) NOT NULL,
	job_cat_id int4 NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT fact_application_pkey PRIMARY KEY (application_id),
	CONSTRAINT fact_application_status_check CHECK (((status)::text = ANY (ARRAY[('closed'::character varying)::text, ('open'::character varying)::text]))),
	CONSTRAINT fact_application_company_id_fkey FOREIGN KEY (company_id) REFERENCES consulting_tracker.dim_company(company_id),
	CONSTRAINT fact_application_dim_job_category_fk FOREIGN KEY (job_cat_id) REFERENCES consulting_tracker.dim_job_category(job_cat_id) ON DELETE SET NULL ON UPDATE CASCADE,
	CONSTRAINT fact_application_lang_id_fkey FOREIGN KEY (lang_id) REFERENCES consulting_tracker.dim_language(lang_id)
);
CREATE TABLE consulting_tracker.fact_pdf_generator (
    pdf_id integer DEFAULT nextval('consulting_tracker.seq_fact_pdf'::regclass) NOT NULL,
    application_id integer NOT NULL,
    active_status boolean NOT NULL,
    file_hash character(64) NOT NULL,
    file_name character varying(255),
    output_file character varying(255) DEFAULT 'output_file.docx'::character varying NOT NULL,
    job_status boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fact_job_pkey PRIMARY KEY (application_id, file_hash, job_status, created_at),
    CONSTRAINT fact_job_application_id_fkey FOREIGN KEY (application_id) 
        REFERENCES consulting_tracker.fact_application(application_id) ON DELETE CASCADE
);


CREATE TABLE consulting_tracker.dim_resume_details (
	application_id int4 NOT NULL,
	ed1 text NULL, ed2 text NULL, ed3 text NULL,
	ex1 text NULL, ex2 text NULL, ex3 text NULL,
	skills text NULL, interests text NULL,
	file_id int4 NULL,
	CONSTRAINT dim_resume_details_pkey PRIMARY KEY (application_id),
	CONSTRAINT dim_resume_details_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id),
	CONSTRAINT dim_resume_details_file_id_fkey FOREIGN KEY (file_id) REFERENCES consulting_tracker.dim_file(file_id)
);

CREATE TABLE consulting_tracker.dim_cover_letter (
	application_id int4 NOT NULL,
	header text NULL, 
	body text NULL,
	close text NULL, 
	file_id int4 NULL,		
	CONSTRAINT dim_cover_letter_pkey PRIMARY KEY (application_id),
	CONSTRAINT dim_cover_letter_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id),
	CONSTRAINT dim_cover_letter_file_id_fkey FOREIGN KEY (file_id) REFERENCES consulting_tracker.dim_file(file_id)
);

CREATE TABLE consulting_tracker.dim_tracker (
	application_id int4 NOT NULL,
	contact_name varchar(255) NULL,
	contact_email varchar(255) NULL,
	position_url text NULL,
	resume text NULL,
	cover_letter text NULL,
	position_pdf text NULL,
	CONSTRAINT dim_tracker_pkey PRIMARY KEY (application_id),
	CONSTRAINT dim_tracker_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id)
);


-- ==========================================
-- 4. TRIGGERS (Placed after table exists)
-- ==========================================
CREATE TRIGGER trg_after_application_insert 
    AFTER INSERT ON consulting_tracker.fact_application 
    FOR EACH ROW EXECUTE FUNCTION consulting_tracker.sync_fact_to_tracker();

