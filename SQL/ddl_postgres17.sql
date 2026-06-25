	-- ==========================================
	-- Initialize Schema Environment
	-- ==========================================
	-- DROP SCHEMA IF EXISTS consulting_tracker CASCADE;
	-- CREATE SCHEMA consulting_tracker AUTHORIZATION neondb_owner;
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

	CREATE SEQUENCE consulting_tracker.seq_web_list
		START WITH 1
		INCREMENT BY 1
		NO MINVALUE
		NO MAXVALUE
		CACHE 1;


	-- ==========================================
	-- 2. MULTI-TENANT TRIGGER FUNCTIONS
	-- ==========================================
	CREATE OR REPLACE FUNCTION consulting_tracker.sync_fact_to_tracker()
	RETURNS trigger
	LANGUAGE plpgsql
	AS $function$
	BEGIN
		-- 1. Populate the master tracker extension with the tenant ID
		INSERT INTO consulting_tracker.dim_tracker (application_id, user_id)
		VALUES (NEW.application_id, NEW.user_id);

		-- 2. Populate the granular CV text snapshot dimension with the tenant ID
		INSERT INTO consulting_tracker.dim_resume_details (application_id, user_id)
		VALUES (NEW.application_id, NEW.user_id); 
		
		-- 3. Populate the cover letter workspace dimension with the tenant ID
		INSERT INTO consulting_tracker.dim_cover_letter (application_id, user_id)
		VALUES (NEW.application_id, NEW.user_id);
		
		-- Handshake complete
		RETURN NEW; 
	END;
	$function$;

	-- ==========================================
	-- 3. TABLES & CONSTRAINTS
	-- ==========================================
	-- 1. COMPANY TYPES (Scoped per user)
	CREATE TABLE consulting_tracker.dim_ctype (
		user_id uuid NOT NULL,
		ctype_id int4 DEFAULT nextval('consulting_tracker.seq_dim_ctype'::regclass) NOT NULL,
		type_name varchar(100) NOT NULL,
		created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
		CONSTRAINT dim_ctype_pkey PRIMARY KEY (ctype_id),
		CONSTRAINT dim_company_user_id FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE
	);
	-- FIX: Unique constraint now allows multiple users to have the same type_name
	CREATE UNIQUE INDEX uq_type_name_lower_per_user ON consulting_tracker.dim_ctype (user_id, lower((type_name)::text));

	-- 2. JOB CATEGORY (Scoped per user)
	CREATE TABLE consulting_tracker.dim_job_category (
		user_id uuid NOT NULL,
		job_cat_id int4 DEFAULT nextval('consulting_tracker.seq_dim_job_category'::regclass) NOT NULL,
		category_name varchar(255) NOT NULL,
		created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
		CONSTRAINT dim_job_category_pkey PRIMARY KEY (job_cat_id),
		CONSTRAINT dim_job_cat_user_id FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE
	);
	CREATE UNIQUE INDEX uq_job_cat_lower_per_user ON consulting_tracker.dim_job_category (user_id, lower((category_name)::text));

	-- 3. LANGUAGES (Scoped per user)
	CREATE TABLE consulting_tracker.dim_language (
		user_id uuid NOT NULL,
		lang_id int4 DEFAULT nextval('consulting_tracker.seq_dim_language'::regclass) NOT NULL,
		"language" varchar(100) NOT NULL,
		created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
		CONSTRAINT dim_language_pkey PRIMARY KEY (lang_id),
		CONSTRAINT dim_lang_user_id FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE
	);
	CREATE UNIQUE INDEX uq_dim_language_lower_per_user ON consulting_tracker.dim_language (user_id, lower((language)::text));

	-- 4. COMPANIES (Scoped per user)
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

	-- 5. FILES (Scoped per user)
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
	-- FIX: Unique hash per user so different users can upload identical template copies
	CREATE UNIQUE INDEX uq_dim_file_hash_per_user ON consulting_tracker.dim_file (user_id, file_hash);

	-- 6. APPLICATIONS (Directly bound to the user)
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

	-- 7. WEB LIST (Scoped per user)
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
	-- 9. Dim tracker (Scoped per user)
	CREATE TABLE consulting_tracker.dim_tracker (
		application_id int4 NOT NULL,
		user_id uuid NOT NULL, -- Added for Neon Auth Multi-tenancy
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


	-- ==========================================
	-- 4. ROW LEVEL SECURITY (Placed AFTER tables are created)
	-- ==========================================
	ALTER TABLE consulting_tracker.fact_application ENABLE ROW LEVEL SECURITY;

	-- Clear policy if it exists to allow re-running scripts cleanly
	DROP POLICY IF EXISTS user_isolation_policy ON consulting_tracker.fact_application;
	CREATE POLICY user_isolation_policy ON consulting_tracker.fact_application
		FOR ALL USING (user_id = auth.user_id());

	-- ==========================================
	-- 5. TRIGGERS
	-- ==========================================
	DROP TRIGGER IF EXISTS trg_after_application_insert ON consulting_tracker.fact_application;

	CREATE TRIGGER trg_after_application_insert 
		AFTER INSERT ON consulting_tracker.fact_application 
		FOR EACH ROW EXECUTE FUNCTION consulting_tracker.sync_fact_to_tracker();