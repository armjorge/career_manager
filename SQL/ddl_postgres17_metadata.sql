-- -------------------------------------------------------------
-- Entity: dim_language
-- -------------------------------------------------------------
COMMENT ON TABLE consulting_tracker.dim_language IS 'Lookup table storing spoken/written languages utilized across application assets.';
COMMENT ON COLUMN consulting_tracker.dim_language.lang_id IS 'Unique identifier for the language of the application or file. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.dim_language.language IS 'Name of the language used (e.g., English, Spanish). [Filtered Name]';
COMMENT ON COLUMN consulting_tracker.dim_language.created_at IS 'Timestamp indicating when the record was created. [Time Dimension]';

-- -------------------------------------------------------------
-- Entity: dim_ctype
-- -------------------------------------------------------------
COMMENT ON TABLE consulting_tracker.dim_ctype IS 'Lookup dimension classifying the core operational domain or vertical of a target organization.';
COMMENT ON COLUMN consulting_tracker.dim_ctype.ctype_id IS 'Unique identifier for the company type/sector. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.dim_ctype.type_name IS 'Descriptive name of the company type or industry sector. [Filtered Name]';
COMMENT ON COLUMN consulting_tracker.dim_ctype.created_at IS 'Timestamp indicating when the record was created. [Time Dimension]';

-- -------------------------------------------------------------
-- Entity: dim_job_category
-- -------------------------------------------------------------
COMMENT ON TABLE consulting_tracker.dim_job_category IS 'Lookup table for categorizing job roles into functional areas (e.g., Data Science, Engineering).';
COMMENT ON COLUMN consulting_tracker.dim_job_category.job_cat_id IS 'Unique identifier for the job category. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.dim_job_category.category_name IS 'Descriptive name of the job role category. [Filtered Name]';
COMMENT ON COLUMN consulting_tracker.dim_job_category.created_at IS 'Timestamp indicating when the record was created. [Time Dimension]';

-- -------------------------------------------------------------
-- Entity: dim_company
-- -------------------------------------------------------------
COMMENT ON TABLE consulting_tracker.dim_company IS 'Dimension table storing target organizations and their associated industry types.';
COMMENT ON COLUMN consulting_tracker.dim_company.company_id IS 'Unique identifier for the target company. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.dim_company.ctype_id IS 'Unique identifier for the company type/sector. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.dim_company.company_name IS 'Official name of the target organization. [Filtered Name]';
COMMENT ON COLUMN consulting_tracker.dim_company.created_at IS 'Timestamp indicating when the record was created. [Time Dimension]';

-- -------------------------------------------------------------
-- Entity: dim_file
-- -------------------------------------------------------------
COMMENT ON TABLE consulting_tracker.dim_file IS 'Dimension table tracking physical files, their hashes, and validity status for resume and cover letter management.';
COMMENT ON COLUMN consulting_tracker.dim_file.file_id IS 'Unique identifier for the physical or digital file record. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.dim_file.lang_id IS 'Unique identifier for the language of the application or file. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.dim_file.file_name IS 'The original name of the file on disk. [Filtered Name]';
COMMENT ON COLUMN consulting_tracker.dim_file.file_hash IS 'Unique MD5/SHA hash of the file content for deduplication. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_file.file_type IS 'Categorization of the file (e.g., resume, cover letter). [Filtered Name]';
COMMENT ON COLUMN consulting_tracker.dim_file.active_status IS 'Boolean flag indicating if the record is currently active or valid. [Fact]';
COMMENT ON COLUMN consulting_tracker.dim_file.created_at IS 'Timestamp indicating when the record was created. [Time Dimension]';

-- -------------------------------------------------------------
-- Entity: fact_application
-- -------------------------------------------------------------
COMMENT ON TABLE consulting_tracker.fact_application IS 'Core Fact table capturing the intersection and initialization of a professional consulting application stream.';
COMMENT ON COLUMN consulting_tracker.fact_application.application_id IS 'Unique identifier for the job application process. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.fact_application.company_id IS 'Unique identifier for the target company. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.fact_application.job_name IS 'The specific title of the position applied for. [Filtered Name]';
COMMENT ON COLUMN consulting_tracker.fact_application.lang_id IS 'Unique identifier for the language of the application or file. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.fact_application.status IS 'Current state of the application lifecycle (e.g., open, closed). [Fact]';
COMMENT ON COLUMN consulting_tracker.fact_application.job_cat_id IS 'Unique identifier for the job category. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.fact_application.created_at IS 'Timestamp indicating when the record was created. [Time Dimension]';

-- -------------------------------------------------------------
-- Entity: fact_job
-- -------------------------------------------------------------
COMMENT ON TABLE consulting_tracker.fact_pdf_generator IS 'Transaction table tracking the status and output of automated document generation jobs.';
COMMENT ON COLUMN consulting_tracker.fact_pdf_generator.pdf_id IS 'Unique identifier for a specific execution job, such as PDF generation. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.fact_pdf_generator.application_id IS 'Unique identifier for the job application process. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.fact_pdf_generator.active_status IS 'Boolean flag indicating if the record is currently active or valid. [Fact]';
COMMENT ON COLUMN consulting_tracker.fact_pdf_generator.file_hash IS 'Unique MD5/SHA hash of the file content for deduplication. [Dimension]';
COMMENT ON COLUMN consulting_tracker.fact_pdf_generator.file_name IS 'The original name of the file on disk. [Filtered Name]';
COMMENT ON COLUMN consulting_tracker.fact_pdf_generator.output_file IS 'Path or name of the generated output document. [Dimension]';
COMMENT ON COLUMN consulting_tracker.fact_pdf_generator.pdf_success IS 'Outcome of the job execution (success/failure). [Fact]';
COMMENT ON COLUMN consulting_tracker.fact_pdf_generator.created_at IS 'Timestamp indicating when the record was created. [Time Dimension]';

-- -------------------------------------------------------------
-- Entity: dim_resume_details
-- -------------------------------------------------------------
COMMENT ON TABLE consulting_tracker.dim_resume_details IS '1:1 Extension dimension capturing the precise granular CV text blocks and experience snapshots.';
COMMENT ON COLUMN consulting_tracker.dim_resume_details.application_id IS 'Unique identifier for the job application process. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.dim_resume_details.ed1 IS 'Educational background text block for resume templates. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_resume_details.ed2 IS 'Educational background text block for resume templates. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_resume_details.ed3 IS 'Educational background text block for resume templates. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_resume_details.ex1 IS 'Professional experience text block for resume templates. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_resume_details.ex2 IS 'Professional experience text block for resume templates. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_resume_details.ex3 IS 'Professional experience text block for resume templates. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_resume_details.skills IS 'Technical or soft skills text block for resume templates. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_resume_details.interests IS 'Personal interests or hobbies text block for resume templates. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_resume_details.file_id IS 'Unique identifier for the physical or digital file record. [Dimension/PK]';

-- -------------------------------------------------------------
-- Entity: dim_cover_letter
-- -------------------------------------------------------------
COMMENT ON TABLE consulting_tracker.dim_cover_letter IS '1:1 Extension dimension capturing text content specifically drafted for cover letter generation.';
COMMENT ON COLUMN consulting_tracker.dim_cover_letter.application_id IS 'Unique identifier for the job application process. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.dim_cover_letter.header IS 'Header content for the cover letter template. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_cover_letter.body IS 'Main body content for the cover letter template. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_cover_letter.close IS 'Closing statement content for the cover letter template. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_cover_letter.file_id IS 'Unique identifier for the physical or digital file record. [Dimension/PK]';

-- -------------------------------------------------------------
-- Entity: dim_tracker
-- -------------------------------------------------------------
COMMENT ON TABLE consulting_tracker.dim_tracker IS '1:1 Extension dimension for tracking logistical details and contact information for each application.';
COMMENT ON COLUMN consulting_tracker.dim_tracker.application_id IS 'Unique identifier for the job application process. [Dimension/PK]';
COMMENT ON COLUMN consulting_tracker.dim_tracker.contact_name IS 'Name of the primary contact person for the application. [Filtered Name]';
COMMENT ON COLUMN consulting_tracker.dim_tracker.contact_email IS 'Email address of the primary contact person. [Filtered Name]';
COMMENT ON COLUMN consulting_tracker.dim_tracker.position_url IS 'URL link to the job posting or application portal. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_tracker.resume IS 'Path or reference to the generated resume file. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_tracker.cover_letter IS 'Path or reference to the generated cover letter file. [Dimension]';
COMMENT ON COLUMN consulting_tracker.dim_tracker.position_pdf IS 'Path or reference to the original job description PDF. [Dimension]';
