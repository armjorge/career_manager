-- DROP SCHEMA consulting_tracker;

CREATE SCHEMA consulting_tracker AUTHORIZATION neondb_owner;

-- DROP SEQUENCE consulting_tracker.dim_company_company_id_seq;

CREATE SEQUENCE consulting_tracker.dim_company_company_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE consulting_tracker.dim_company_company_id_seq1;

CREATE SEQUENCE consulting_tracker.dim_company_company_id_seq1
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE consulting_tracker.dim_ctype_ctype_id_seq;

CREATE SEQUENCE consulting_tracker.dim_ctype_ctype_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE consulting_tracker.dim_ctype_ctype_id_seq1;

CREATE SEQUENCE consulting_tracker.dim_ctype_ctype_id_seq1
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE consulting_tracker.dim_file_file_id_seq;

CREATE SEQUENCE consulting_tracker.dim_file_file_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE consulting_tracker.dim_file_file_id_seq1;

CREATE SEQUENCE consulting_tracker.dim_file_file_id_seq1
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE consulting_tracker.dim_language_lang_id_seq;

CREATE SEQUENCE consulting_tracker.dim_language_lang_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE consulting_tracker.dim_language_lang_id_seq1;

CREATE SEQUENCE consulting_tracker.dim_language_lang_id_seq1
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE consulting_tracker.fact_application_application_id_seq;

CREATE SEQUENCE consulting_tracker.fact_application_application_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE consulting_tracker.fact_application_application_id_seq1;

CREATE SEQUENCE consulting_tracker.fact_application_application_id_seq1
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;-- consulting_tracker.dim_ctype definition

-- Drop table

-- DROP TABLE consulting_tracker.dim_ctype;

CREATE TABLE consulting_tracker.dim_ctype (
	ctype_id serial4 NOT NULL,
	type_name varchar(100) NOT NULL,
	CONSTRAINT dim_ctype_pkey PRIMARY KEY (ctype_id)
);
CREATE UNIQUE INDEX uq_type_name_lower ON consulting_tracker.dim_ctype USING btree (lower((type_name)::text));


-- consulting_tracker.dim_language definition

-- Drop table

-- DROP TABLE consulting_tracker.dim_language;

CREATE TABLE consulting_tracker.dim_language (
	lang_id serial4 NOT NULL,
	"language" varchar(100) NOT NULL,
	CONSTRAINT dim_language_pkey PRIMARY KEY (lang_id)
);
CREATE UNIQUE INDEX uq_dim_language_lower ON consulting_tracker.dim_language USING btree (lower((language)::text));


-- consulting_tracker.dim_company definition

-- Drop table

-- DROP TABLE consulting_tracker.dim_company;

CREATE TABLE consulting_tracker.dim_company (
	company_id serial4 NOT NULL,
	ctype_id int4 NULL,
	company_name varchar(255) NOT NULL,
	CONSTRAINT dim_company_pkey PRIMARY KEY (company_id),
	CONSTRAINT dim_company_ctype_id_fkey FOREIGN KEY (ctype_id) REFERENCES consulting_tracker.dim_ctype(ctype_id)
);


-- consulting_tracker.dim_file definition

-- Drop table

-- DROP TABLE consulting_tracker.dim_file;

CREATE TABLE consulting_tracker.dim_file (
	file_id serial4 NOT NULL,
	lang_id int4 NULL,
	file_name varchar(255) NOT NULL,
	file_type varchar(50) NOT NULL,
	active_status bool DEFAULT true NOT NULL,
	CONSTRAINT dim_file_file_type_check CHECK (((file_type)::text = ANY (ARRAY[('cover letter'::character varying)::text, ('cv'::character varying)::text]))),
	CONSTRAINT dim_file_pkey PRIMARY KEY (file_id),
	CONSTRAINT dim_file_lang_id_fkey FOREIGN KEY (lang_id) REFERENCES consulting_tracker.dim_language(lang_id)
);


-- consulting_tracker.fact_application definition

-- Drop table

-- DROP TABLE consulting_tracker.fact_application;

CREATE TABLE consulting_tracker.fact_application (
	application_id serial4 NOT NULL,
	company_id int4 NULL,
	lang_id int4 NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	status varchar(20) NOT NULL,
	CONSTRAINT fact_application_pkey PRIMARY KEY (application_id),
	CONSTRAINT fact_application_status_check CHECK (((status)::text = ANY (ARRAY[('closed'::character varying)::text, ('open'::character varying)::text]))),
	CONSTRAINT fact_application_company_id_fkey FOREIGN KEY (company_id) REFERENCES consulting_tracker.dim_company(company_id),
	CONSTRAINT fact_application_lang_id_fkey FOREIGN KEY (lang_id) REFERENCES consulting_tracker.dim_language(lang_id)
);
-- DROP FUNCTION consulting_tracker.sync_fact_to_tracker();

CREATE OR REPLACE FUNCTION consulting_tracker.sync_fact_to_tracker()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- NEW holds the data row currently being inserted into fact_application
    INSERT INTO consulting_tracker.dim_tracker (application_id)
    VALUES (NEW.application_id);
    
    -- In an AFTER trigger, we just return the row to finalize the process
    RETURN NEW; 
END;
$function$
;

-- Table Triggers

CREATE TRIGGER trg_after_application_insert AFTER
INSERT
    ON
    consulting_tracker.fact_application FOR EACH ROW EXECUTE FUNCTION sync_fact_to_tracker();


-- consulting_tracker.dim_resume_details definition

-- Drop table

-- DROP TABLE consulting_tracker.dim_resume_details;

CREATE TABLE consulting_tracker.dim_resume_details (
	application_id int4 NOT NULL,
	job_name varchar(255) NOT NULL,
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
	CONSTRAINT dim_resume_details_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id),
	CONSTRAINT dim_resume_details_file_id_fkey FOREIGN KEY (file_id) REFERENCES consulting_tracker.dim_file(file_id)
);


-- consulting_tracker.dim_tracker definition

-- Drop table

-- DROP TABLE consulting_tracker.dim_tracker;

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



