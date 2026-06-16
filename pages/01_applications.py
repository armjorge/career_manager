import streamlit as st
import pandas as pd
import os
import sys
import io
from datetime import datetime

# 1) Setup Path to find Library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Library.db_utils import DB_UTILS
from Library.CV_generation import CV_GENERATION

# 2) Page Config
st.set_page_config(page_title="📝 Applications & Tracking", layout="wide")

# 3) Initialize DB via Session State
if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
schema = db.schema
engine = db.get_engine()
working_folder = db.working_folder

# 4) Layout & Navigation
st.page_link("concept_filing.py", label="🏠 Volver al panel principal")
st.write("---")

log_box = st.empty()
def ui_log(msg: str, level: str = "info"):
    if level == "success": log_box.success(msg)
    elif level == "warning": log_box.warning(msg)
    elif level == "error": log_box.error(msg)
    else: log_box.info(msg)        

st.title("📝 Applications & Tracking Management")

PK = "application_id"

def get_or_create_id(table, column, value, id_column):
    if not value or not value.strip(): return None
    # Check exists
    query_check = f'SELECT {id_column} FROM "{schema}"."{table}" WHERE LOWER("{column}") = LOWER(%s);'
    conn = db.get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query_check, (value.strip(),))
            row = cur.fetchone()
            if row:
                return row[0]
            # Insert
            query_ins = f'INSERT INTO "{schema}"."{table}" ("{column}") VALUES (%s) RETURNING {id_column};'
            cur.execute(query_ins, (value.strip(),))
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
    except Exception as e:
        conn.rollback()
        st.error(f"Error in get_or_create_id for {table}: {e}")
        return None
    finally:
        conn.close()

# --- FETCH SHARED DATA ---
df_companies = pd.read_sql(f'SELECT company_id, company_name FROM "{schema}".dim_company ORDER BY company_name;', engine)
company_dict = dict(zip(df_companies['company_name'], df_companies['company_id']))

df_langs = pd.read_sql(f'SELECT lang_id, language FROM "{schema}".dim_language ORDER BY language;', engine)
lang_dict = dict(zip(df_langs['language'], df_langs['lang_id']))

df_cats = pd.read_sql(f'SELECT job_cat_id, category_name FROM "{schema}".dim_job_category ORDER BY category_name;', engine)
cat_dict = dict(zip(df_cats['category_name'], df_cats['job_cat_id']))

status_opts = ["open", "closed"]

# Create Tabs for Milestones
tab1, tab2 = st.tabs(["📋 Milestone 1: Applications & Resume", "📍 Milestone 2: Tracking Details"])

# ==============================================================================
# TAB 1: APPLICATIONS & RESUME
# ==============================================================================
with tab1:
    st.header("📋 Applications & Resume Management")
    
    # Fetch Data for Tab 1
    query_apps = f"""
        SELECT 
            fa.application_id, fa.job_name, c.company_name, l.language, fa.status, 
            jc.category_name, fa.created_at, fa.company_id, fa.lang_id, fa.job_cat_id,
            rd.ex1, rd.ex2, rd.ex3, rd.ed1, rd.ed2, rd.ed3, rd.skills
        FROM "{schema}".fact_application fa
        LEFT JOIN "{schema}".dim_company c ON fa.company_id = c.company_id
        LEFT JOIN "{schema}".dim_language l ON fa.lang_id = l.lang_id
        LEFT JOIN "{schema}".dim_job_category jc ON fa.job_cat_id = jc.job_cat_id
        LEFT JOIN "{schema}".dim_resume_details rd ON fa.application_id = rd.application_id
        ORDER BY fa.created_at DESC;
    """
    try:
        df_apps = pd.read_sql(query_apps, engine)
    except Exception as e:
        st.error(f"Error loading applications: {e}")
        df_apps = pd.DataFrame()

    if not df_apps.empty:
        cols_show = ["job_name", "company_name", "language", "status", "category_name", "created_at"]
        st.dataframe(df_apps[cols_show], use_container_width=True, height=300)
    else:
        st.info("No applications found.")

    st.subheader("➕ Add or Edit Application")
    
    selected_pk_app = None
    original_app = {}
    if not df_apps.empty:
        options = df_apps.copy()
        options["label"] = options["job_name"].fillna("") + " | " + options["company_name"].fillna("") + " | " + options["created_at"].astype(str)
        label_list = options["label"].tolist()
        pk_by_label = dict(zip(options["label"], options[PK]))
        selected_label = st.selectbox("Select existing application to edit (optional):", [""] + label_list, key="sel_app")
        if selected_label:
            selected_pk_app = pk_by_label[selected_label]
            original_app = df_apps[df_apps[PK] == selected_pk_app].iloc[0].to_dict()

    with st.form("form_milestone_1", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            curr_comp = original_app.get("company_name", "")
            comp_opts = sorted(list(company_dict.keys()))
            comp_val = st.selectbox("Company (Mandatory)", options=comp_opts, index=comp_opts.index(curr_comp) if curr_comp in comp_opts else 0)
            job_val = st.text_input("Job Position (Mandatory)", value=original_app.get("job_name", "") or "")
            curr_stat = original_app.get("status", "open")
            stat_val = st.selectbox("Status", options=status_opts, index=status_opts.index(curr_stat) if curr_stat in status_opts else 0)
        
        with col2:
            curr_l = original_app.get("language", "")
            l_opts = ["➕ Add New..."] + sorted(list(lang_dict.keys()))
            l_val = st.selectbox("Language", options=l_opts, index=l_opts.index(curr_l) if curr_l in l_opts else 0)
            new_l_input = st.text_input("New Language (if needed)", value="")
            curr_c = original_app.get("category_name", "")
            c_opts = ["➕ Add New..."] + sorted(list(cat_dict.keys()))
            c_val = st.selectbox("Job Category", options=c_opts, index=c_opts.index(curr_c) if curr_c in c_opts else 0)
            new_c_input = st.text_input("New Category (if needed)", value="")

        st.write("---")
        c1, c2 = st.columns(2)
        btn_update = c1.form_submit_button("💾 Save Changes (Milestone 1)")
        btn_insert = c2.form_submit_button("➕ Create New Application")

    # DB Logic for Tab 1
    if btn_update or btn_insert:
        cid = company_dict.get(comp_val)
        lid = get_or_create_id("dim_language", "language", new_l_input, "lang_id") if l_val == "➕ Add New..." else lang_dict.get(l_val)
        jcid = get_or_create_id("dim_job_category", "category_name", new_c_input, "job_cat_id") if c_val == "➕ Add New..." else cat_dict.get(c_val)
        
        if not cid or not job_val:
            st.error("Company and Job Name are required.")
        else:
            conn = db.get_db_connection()
            try:
                with conn.cursor() as cur:
                    if btn_insert:
                        cur.execute(f'INSERT INTO "{schema}".fact_application (company_id, job_name, lang_id, status, job_cat_id) VALUES (%s, %s, %s, %s, %s) RETURNING application_id;', (cid, job_val, lid, stat_val, jcid))
                        app_id = cur.fetchone()[0]
                    else:
                        cur.execute(f'UPDATE "{schema}".fact_application SET company_id=%s, job_name=%s, lang_id=%s, status=%s, job_cat_id=%s WHERE application_id=%s;', (cid, job_val, lid, stat_val, jcid, selected_pk_app))
                        app_id = selected_pk_app
                    
                conn.commit()
                st.success("Success! ✅")
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"DB Error: {e}")
            finally:
                conn.close()

# ==============================================================================
# TAB 2: TRACKING DETAILS
# ==============================================================================
with tab2:
    st.header("📍 Tracking Details Management")
    
    query_tracking = f"""
        SELECT 
            dc.company_name, fact_app.job_name, dl."language", fact_app.status, djc.category_name,
            dtrack.application_id, dtrack.contact_name, dtrack.contact_email, dtrack.position_url, fact_app.created_at
        FROM "{schema}".fact_application fact_app 
        JOIN "{schema}".dim_tracker dtrack ON dtrack.application_id = fact_app.application_id 
        JOIN "{schema}".dim_company dc ON dc.company_id = fact_app.company_id
        JOIN "{schema}".dim_language dl ON dl.lang_id = fact_app.lang_id 
        LEFT JOIN "{schema}".dim_job_category djc ON djc.job_cat_id = fact_app.job_cat_id 
        ORDER BY fact_app.created_at DESC;
    """
    try:
        df_track = pd.read_sql(query_tracking, engine)
    except Exception as e:
        st.error(f"Error loading tracking: {e}")
        df_track = pd.DataFrame()

    if not df_track.empty:
        cols_show_t = ["company_name", "job_name", "language", "status", "category_name", "contact_name", "contact_email", "position_url"]
        st.dataframe(df_track[cols_show_t], use_container_width=True, height=300)
    else:
        st.info("No tracking records found.")

    st.subheader("📝 Update Tracking Details")
    
    selected_pk_track = None
    original_track = {}
    if not df_track.empty:
        options_t = df_track.copy()
        options_t["label"] = options_t["job_name"].fillna("") + " | " + options_t["company_name"].fillna("") + " | " + options_t["created_at"].astype(str)
        label_list_t = options_t["label"].tolist()
        pk_by_label_t = dict(zip(options_t["label"], options_t[PK]))
        selected_label_t = st.selectbox("Select application to update tracking:", [""] + label_list_t, key="sel_track")
        if selected_label_t:
            selected_pk_track = pk_by_label_t[selected_label_t]
            original_track = df_track[df_track[PK] == selected_pk_track].iloc[0].to_dict()

    with st.form("form_milestone_2", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            c_name = st.text_input("Contact Name", value=original_track.get("contact_name", "") or "")
            c_email = st.text_input("Contact Email", value=original_track.get("contact_email", "") or "")
        with c2:
            p_url = st.text_input("Position URL", value=original_track.get("position_url", "") or "")
        
        btn_save_track = st.form_submit_button("💾 Save Tracking Details (Milestone 2)")

    if btn_save_track:
        if not selected_pk_track:
            st.error("Please select a record from the list.")
        else:
            conn = db.get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(f'UPDATE "{schema}".dim_tracker SET contact_name=%s, contact_email=%s, position_url=%s WHERE application_id=%s;', (c_name, c_email, p_url, selected_pk_track))
                conn.commit()
                st.success("Tracking Updated! ✅")
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"DB Error: {e}")
            finally:
                conn.close()
