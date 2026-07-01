import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

# 1) Setup Path to find Library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Library.db_utils import DB_UTILS
from Library.CV_generation import CV_GENERATION

# 2) Page Config
st.set_page_config(page_title="📄 PDF Generator", layout="wide")

# 3) Initialize DB & CV Gen via Session State
if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
schema = db.schema
engine = db.get_engine()

if 'cv_gen' not in st.session_state:
    st.session_state.cv_gen = CV_GENERATION(db.working_folder, {"DB_URL": os.getenv("DB_POSTGRESQL")})

cv_gen = st.session_state.cv_gen

# 4) Navigation
st.page_link("concept_filing.py", label="🏠 Volver al panel principal")
st.write("---")

st.title("📄 Generate Application Documents")

# --- DATA FETCHING ---
@st.cache_data
def fetch_available_options():
    query = f"""
    WITH base_query AS (
        SELECT 
            fact_app.application_id,
            'Resume' AS category,
            dc.company_name,
            fact_app.job_name,
            dl."language",
            fact_app.status,
            djc.category_name, 
            dimf.file_name,
            dimf.file_hash,
            dimf.active_status,
            dimf.file_type,
            fact_app.created_at 
        FROM "{schema}".fact_application fact_app 
        JOIN "{schema}".dim_company dc ON dc.company_id = fact_app.company_id
        JOIN "{schema}".dim_language dl ON dl.lang_id = fact_app.lang_id 
        LEFT JOIN "{schema}".dim_job_category djc ON djc.job_cat_id = fact_app.job_cat_id 
        JOIN "{schema}".dim_resume_details drd ON drd.application_id = fact_app.application_id  
        LEFT JOIN "{schema}".dim_file dimf ON dimf.file_id = drd.file_id 
        
        UNION ALL
        
        SELECT 
            fact_app.application_id,
            'Cover Letter' AS category,
            dc.company_name,
            fact_app.job_name,
            dl."language",
            fact_app.status,
            djc.category_name, 
            dimf.file_name,
            dimf.file_hash,
            dimf.active_status,
            dimf.file_type,
            fact_app.created_at
        FROM "{schema}".fact_application fact_app 
        JOIN "{schema}".dim_company dc ON dc.company_id = fact_app.company_id
        JOIN "{schema}".dim_language dl ON dl.lang_id = fact_app.lang_id 
        LEFT JOIN "{schema}".dim_job_category djc ON djc.job_cat_id = fact_app.job_cat_id 
        JOIN "{schema}".dim_cover_letter dcletter ON dcletter.application_id = fact_app.application_id  
        LEFT JOIN "{schema}".dim_file dimf ON dimf.file_id = dcletter.file_id 
    )
    SELECT * FROM base_query WHERE active_status = TRUE;
    """
    return pd.read_sql(query, engine)

try:
    df_options = fetch_available_options()
except Exception as e:
    st.error(f"Error fetching data: {e}")
    df_options = pd.DataFrame()

if df_options.empty:
    st.info("No active files/applications ready for generation. Please check milestones and templates.")
else:
    # --- UI COMPONENTS ---
    col_filters, col_actions = st.columns([1, 1])
    
    with col_filters:
        st.subheader("🔍 Selection")
        category_choice = st.radio("Choose Category:", ["Resume", "Cover Letter"], horizontal=True)
        
        filtered_df = df_options[df_options['category'] == category_choice].copy()
        
        if filtered_df.empty:
            st.warning(f"No active templates for {category_choice}.")
        else:
            filtered_df['display_label'] = filtered_df['company_name'].fillna("") + " | " + filtered_df['job_name'].fillna("") + " (" + filtered_df['language'].fillna("") + ")"
            selected_label = st.selectbox("Select Application:", filtered_df['display_label'].tolist())
            
            selected_row = filtered_df[filtered_df['display_label'] == selected_label].iloc[0]
            
            st.info(f"**Template:** {selected_row['file_name']}")
            
    with col_actions:
        st.subheader("⚙️ Configuration")
        prefix = st.text_input("Filename Prefix (optional):", placeholder="e.g. JACJ")
        
        # Proposed output name
        cat_suffix = "CV" if category_choice == "Resume" else "CLetter"
        # User requested company_name || ' ' || category_name || '.docx'
        # We'll use selected_row['category_name'] if available, else cat_suffix
        c_name = selected_row['category_name'] if pd.notnull(selected_row['category_name']) else cat_suffix
        proposed_base = f"{prefix} {selected_row['company_name']} {c_name}".strip()
        st.write(f"**Output filename proposal:** `{proposed_base}.docx`")
        
        if st.button("🚀 Generate Document", use_container_width=True):
            # --- GENERATION LOGIC ---
            aid = int(selected_row['application_id'])
            fhash = selected_row['file_hash']
            tname = selected_row['file_name']
            lang = selected_row['language']
            company = selected_row['company_name']
            
            # 1. Fetch Details for the placeholders
            table_details = "dim_resume_details" if category_choice == "Resume" else "dim_cover_letter"
            query_details = f"""
                SELECT t.*, fa.job_name as job, fa.created_at as date, dl.language as lang, dc.company_name
                FROM "{schema}".{table_details} t
                JOIN "{schema}".fact_application fa ON fa.application_id = t.application_id
                JOIN "{schema}".dim_language dl ON dl.lang_id = fa.lang_id
                JOIN "{schema}".dim_company dc ON dc.company_id = fa.company_id
                WHERE t.application_id = %s
            """
            df_details = pd.read_sql(query_details, engine, params=(aid,))
            
            if df_details.empty:
                st.error("Could not find record details in database.")
            else:
                # 2. Add extra fields like date_issued if needed (Cover Letter)
                if category_choice == "Cover Letter":
                    # Reuse logic from CV_generation.py but localized here for clarity
                    dt_date = pd.to_datetime(df_details["date"].values[0], errors="coerce")
                    if not pd.isna(dt_date):
                        day = int(dt_date.day)
                        month_num = int(dt_date.month)
                        year = int(dt_date.year)
                        months = {
                            'English': ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
                            'Spanish': ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
                            'French': ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octubre", "noviembre", "diciembre"]
                        }
                        date_issued = ""
                        if lang == 'English':
                            suffix = 'th'
                            if day in [1, 21, 31]: suffix = 'st'
                            elif day in [2, 22]: suffix = 'nd'
                            elif day in [3, 23]: suffix = 'rd'
                            date_issued = f"Mexico City, {months['English'][month_num-1]} {day}{suffix}, {year}"
                        elif lang == 'Spanish':
                            date_issued = f"Ciudad de México, {day} de {months['Spanish'][month_num-1].capitalize()} de {year}"
                        elif lang == 'French':
                            date_issued = f"Mexico, le {day} {months['French'][month_num-1].capitalize()} {year}"
                        df_details['date_issued'] = date_issued

                # 3. Filename Validation (Unique Name)
                output_folder = cv_gen.output_path
                final_name = f"{proposed_base}.docx"
                output_path = os.path.join(output_folder, final_name)
                
                counter = 1
                while os.path.exists(output_path):
                    final_name = f"{proposed_base}_{counter}.docx"
                    output_path = os.path.join(output_folder, final_name)
                    counter += 1
                
                # 4. Generate Word
                template_path = os.path.join(cv_gen.templates_path, tname)
                success = False
                try:
                    if not os.path.exists(template_path):
                        st.error(f"Template not found: {tname}")
                    else:
                        cv_gen.populate_document(template_path, df_details, output_path)
                        success = True
                        st.success(f"Document generated: **{final_name}**")
                        # Open folder
                        cv_gen.open_folder(output_folder)
                except Exception as e:
                    st.error(f"Generation failed: {e}")
                
                # 5. Log to fact_pdf_generator
                conn = db.get_db_connection()
                try:
                    with conn.cursor() as cur:
                        query_log = f"""
                            INSERT INTO "{schema}".fact_pdf_generator 
                            (application_id, file_hash, file_name, output_file, pdf_success, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        cur.execute(query_log, (aid, fhash, tname, final_name, success, datetime.now()))
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    st.warning(f"Logging failed: {e}")
                finally:
                    conn.close()

# --- RECENT GENERATIONS ---
st.write("---")
st.subheader("📜 Recent Generations")
try:
    df_recent = pd.read_sql(f"""
        SELECT application_id, output_file, pdf_success as success, created_at 
        FROM "{schema}".fact_pdf_generator 
        ORDER BY created_at DESC 
        LIMIT 10
    """, engine)
    if not df_recent.empty:
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No documents generated yet.")
except Exception as e:
    st.error(f"Could not load history: {e}")
