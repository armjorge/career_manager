import streamlit as st
import pandas as pd
import os
import sys
import io
from datetime import datetime

# 1) Setup Path to find Library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Library.db_utils import DB_UTILS

# 2) Page Config
st.set_page_config(page_title="📄 Milestones: Resume & Cover Letters", layout="wide")

# 3) Initialize DB via Session State
if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
schema = db.schema
engine = db.get_engine()

# 4) Layout & Navigation
st.page_link("concept_filing.py", label="🏠 Volver al panel principal")
st.write("---")

st.title("📄 Application Milestones")

# --- SHARED DATA FETCHING ---
def fetch_active_files():
    query = f"""
        SELECT file_id, file_name 
        FROM "{schema}".dim_file 
        WHERE active_status = True 
        ORDER BY created_at DESC;
    """
    return pd.read_sql(query, engine)

df_files = fetch_active_files()
file_options = dict(zip(df_files['file_name'], df_files['file_id']))
file_list = [""] + sorted(list(file_options.keys()))

# Create Tabs
tab1, tab2 = st.tabs(["📝 Milestone: Resume Details", "✉️ Milestone: Cover Letter"])

# ==============================================================================
# TAB 1: RESUME DETAILS
# ==============================================================================
with tab1:
    st.header("📝 Resume Details Management")
    
    query_resume_master = f"""
        SELECT 
            dc.company_name,
            fa.job_name,
            dl."language",
            fa.status,
            djc.category_name,
            drd.ed1, drd.ed2, drd.ed3, 
            drd.ex1, drd.ex2, drd.ex3,
            drd.skills, drd.interests, 
            dimf.file_name,
            fa.application_id,
            fa.created_at
        FROM "{schema}".fact_application fa
        JOIN "{schema}".dim_tracker dt ON dt.application_id = fa.application_id 
        JOIN "{schema}".dim_company dc ON dc.company_id = fa.company_id
        JOIN "{schema}".dim_language dl ON dl.lang_id = fa.lang_id 
        LEFT JOIN "{schema}".dim_job_category djc ON djc.job_cat_id = fa.job_cat_id 
        JOIN "{schema}".dim_resume_details drd ON drd.application_id = fa.application_id  
        LEFT JOIN "{schema}".dim_file dimf ON dimf.file_id = drd.file_id 
        ORDER BY fa.created_at DESC;
    """
    
    try:
        df_resume = pd.read_sql(query_resume_master, engine)
    except Exception as e:
        st.error(f"Error loading resume details: {e}")
        df_resume = pd.DataFrame()

    if not df_resume.empty:
        cols_view_r = [
            "company_name", "job_name", "language", "status", "category_name", 
            "ed1", "ed2", "ed3", "ex1", "ex2", "ex3", "skills", "interests", "file_name"
        ]
        st.dataframe(df_resume[cols_view_r], use_container_width=True, height=250)
    else:
        st.info("No applications found for resume filling.")

    st.subheader("✏️ Fill/Update Resume Details")
    
    selected_pk_r = None
    original_r = {}
    if not df_resume.empty:
        df_resume["label"] = df_resume["job_name"].fillna("") + " | " + df_resume["company_name"].fillna("") + " | " + df_resume["created_at"].astype(str)
        label_list_r = df_resume["label"].tolist()
        pk_by_label_r = dict(zip(df_resume["label"], df_resume["application_id"]))
        selected_label_r = st.selectbox("Select application for Resume:", [""] + label_list_r, key="sel_res")
        
        if selected_label_r:
            selected_pk_r = pk_by_label_r[selected_label_r]
            original_r = df_resume[df_resume["application_id"] == selected_pk_r].iloc[0].to_dict()

    with st.form("resume_form"):
        col1, col2 = st.columns(2)
        with col1:
            ed1 = st.text_area("Education 1", value=original_r.get("ed1", "") or "", height=100)
            ed2 = st.text_area("Education 2", value=original_r.get("ed2", "") or "", height=100)
            ed3 = st.text_area("Education 3", value=original_r.get("ed3", "") or "", height=100)
            interests = st.text_area("Interests", value=original_r.get("interests", "") or "", height=100)
        with col2:
            ex1 = st.text_area("Experience 1", value=original_r.get("ex1", "") or "", height=100)
            ex2 = st.text_area("Experience 2", value=original_r.get("ex2", "") or "", height=100)
            ex3 = st.text_area("Experience 3", value=original_r.get("ex3", "") or "", height=100)
            skills = st.text_area("Skills", value=original_r.get("skills", "") or "", height=100)
        
        curr_file_r = original_r.get("file_name", "")
        selected_file_r = st.selectbox("Associated File (Template)", options=file_list, 
                                       index=file_list.index(curr_file_r) if curr_file_r in file_list else 0,
                                       key="file_res")

        submit_r = st.form_submit_button("💾 Save Resume Details")

    if submit_r:
        if not selected_pk_r:
            st.error("Please select an application.")
        else:
            fid = file_options.get(selected_file_r)
            conn = db.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = f"""
                        UPDATE "{schema}".dim_resume_details 
                        SET ed1=%s, ed2=%s, ed3=%s, ex1=%s, ex2=%s, ex3=%s, skills=%s, interests=%s, file_id=%s
                        WHERE application_id=%s;
                    """
                    cur.execute(query, (ed1, ed2, ed3, ex1, ex2, ex3, skills, interests, fid, selected_pk_r))
                conn.commit()
                st.success("Resume details updated! ✅")
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"Database error: {e}")
            finally:
                conn.close()

# ==============================================================================
# TAB 2: COVER LETTERS
# ==============================================================================
with tab2:
    st.header("✉️ Cover Letter Management")
    
    query_cover_master = f"""
        SELECT 
            dc.company_name,
            fa.job_name,
            dl."language",
            fa.status,
            djc.category_name,
            dcletter."header",
            dcletter."body", 
            dcletter."close", 
            dimf.file_name,
            fa.application_id,
            fa.created_at
        FROM "{schema}".fact_application fa
        JOIN "{schema}".dim_tracker dt ON dt.application_id = fa.application_id 
        JOIN "{schema}".dim_company dc ON dc.company_id = fa.company_id
        JOIN "{schema}".dim_language dl ON dl.lang_id = fa.lang_id 
        LEFT JOIN "{schema}".dim_job_category djc ON djc.job_cat_id = fa.job_cat_id 
        JOIN "{schema}".dim_cover_letter dcletter ON dcletter.application_id = fa.application_id  
        LEFT JOIN "{schema}".dim_file dimf ON dimf.file_id = dcletter.file_id 
        ORDER BY fa.created_at DESC;
    """
    
    try:
        df_cover = pd.read_sql(query_cover_master, engine)
    except Exception as e:
        st.error(f"Error loading cover letters: {e}")
        df_cover = pd.DataFrame()

    if not df_cover.empty:
        cols_view_c = [
            "company_name", "job_name", "language", "status", "category_name", 
            "header", "body", "close", "file_name"
        ]
        st.dataframe(df_cover[cols_view_c], use_container_width=True, height=250)
    else:
        st.info("No applications found for cover letter filling.")

    st.subheader("✏️ Fill/Update Cover Letter")
    
    selected_pk_c = None
    original_c = {}
    if not df_cover.empty:
        df_cover["label"] = df_cover["job_name"].fillna("") + " | " + df_cover["company_name"].fillna("") + " | " + df_cover["created_at"].astype(str)
        label_list_c = df_cover["label"].tolist()
        pk_by_label_c = dict(zip(df_cover["label"], df_cover["application_id"]))
        selected_label_c = st.selectbox("Select application for Cover Letter:", [""] + label_list_c, key="sel_cov")
        
        if selected_label_c:
            selected_pk_c = pk_by_label_c[selected_label_c]
            original_c = df_cover[df_cover["application_id"] == selected_pk_c].iloc[0].to_dict()

    with st.form("cover_form"):
        header_text = st.text_area("Header", value=original_c.get("header", "") or "", height=100)
        body_text = st.text_area("Body", value=original_c.get("body", "") or "", height=250)
        close_text = st.text_area("Close", value=original_c.get("close", "") or "", height=100)
        
        curr_file_c = original_c.get("file_name", "")
        selected_file_c = st.selectbox("Associated File (Template)", options=file_list, 
                                       index=file_list.index(curr_file_c) if curr_file_c in file_list else 0,
                                       key="file_cov")

        submit_c = st.form_submit_button("💾 Save Cover Letter")

    if submit_c:
        if not selected_pk_c:
            st.error("Please select an application.")
        else:
            fid = file_options.get(selected_file_c)
            conn = db.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = f"""
                        UPDATE "{schema}".dim_cover_letter 
                        SET header=%s, body=%s, close=%s, file_id=%s
                        WHERE application_id=%s;
                    """
                    cur.execute(query, (header_text, body_text, close_text, fid, selected_pk_c))
                conn.commit()
                st.success("Cover letter updated! ✅")
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"Database error: {e}")
            finally:
                conn.close()
