-- Missing extension tables required by sync_fact_to_tracker() trigger on fact_application.
-- Safe to re-run: uses IF NOT EXISTS.

SET search_path TO consulting_tracker, public;

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
    CONSTRAINT dim_resume_details_user_id_fkey FOREIGN KEY (user_id) REFERENCES neon_auth."user" (id) ON DELETE CASCADE,
    CONSTRAINT dim_resume_details_application_id_fkey FOREIGN KEY (application_id) REFERENCES consulting_tracker.fact_application(application_id) ON DELETE CASCADE,
    CONSTRAINT dim_resume_details_file_id_fkey FOREIGN KEY (file_id) REFERENCES consulting_tracker.dim_file(file_id)
);

CREATE TABLE IF NOT EXISTS consulting_tracker.dim_cover_letter (
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
