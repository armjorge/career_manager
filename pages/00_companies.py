import streamlit as st
import pandas as pd
import os
import sys

if 'db' in st.session_state:
   del st.session_state['db']
# 1) Setup Path to find Library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Library.db_utils import DB_UTILS

# 2) Page Config
st.set_page_config(page_title="Basic Info (Languages, Companies)", layout="wide")

# 🔙 Link to Home
st.page_link("concept_filing.py", label="🏠 Volver al panel principal")
st.write("---")

# 3) Initialize DB
# FORCE REFRESH for debugging - you can remove this later
if 'db' in st.session_state:
    del st.session_state['db']

if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
schema = db.schema
engine = db.get_engine()

# --- Debug Info ---
with st.expander("🛠️ Connection Debug"):
    st.write(f"**Schema:** `{schema}`")
    st.write(f"**Engine URL (Host):** `{engine.url.host}`")
    st.write(f"**Engine URL (DB):** `{engine.url.database}`")

# 4) UI Content
st.title("🏢 Management: Companies, Types & Languages")

col1, col2, col3 = st.columns(3)

# === 📂 Section: Company Types (dim_ctype) ===
with col1:
    st.subheader("📂 Company Types")
    # Removed try/except to see real errors
    df_types = pd.read_sql(f'SELECT type_name FROM "{schema}".dim_ctype ORDER BY type_name;', engine)
    st.dataframe(df_types, use_container_width=True, height=250)

    with st.expander("➕ Add New Type"):
        new_type = st.text_input("Type Name", key="new_type_input")
        if st.button("Add Type"):
            if new_type:
                if db.record_exists("dim_ctype", "type_name", new_type):
                    st.warning(f"⚠️ '{new_type}' already exists.")
                else:
                    if db.insert_record("dim_ctype", {"type_name": new_type}):
                        st.success(f"✅ '{new_type}' added.")
                        st.rerun()
            else:
                st.warning("⚠️ Field cannot be empty.")

# === 🌐 Section: Languages (dim_language) ===
with col2:
    st.subheader("🌐 Languages")
    # Removed try/except to see real errors
    df_langs = pd.read_sql(f'SELECT language FROM "{schema}".dim_language ORDER BY language;', engine)
    st.dataframe(df_langs, use_container_width=True, height=250)

    with st.expander("➕ Add New Language"):
        new_lang = st.text_input("Language", key="new_lang_input")
        if st.button("Add Language"):
            if new_lang:
                if db.record_exists("dim_language", "language", new_lang):
                    st.warning(f"⚠️ '{new_lang}' already exists.")
                else:
                    if db.insert_record("dim_language", {"language": new_lang}):
                        st.success(f"✅ '{new_lang}' added.")
                        st.rerun()
            else:
                st.warning("⚠️ Field cannot be empty.")

# === 🏢 Section: Companies (dim_company) ===
with col3:
    st.subheader("🏢 Companies")
    # Removed try/except to see real errors
    query_companies = f"""
        SELECT c.company_name, t.type_name as industry
        FROM "{schema}".dim_company c
        LEFT JOIN "{schema}".dim_ctype t ON c.ctype_id = t.ctype_id
        ORDER BY c.company_name;
    """
    df_companies = pd.read_sql(query_companies, engine)
    st.dataframe(df_companies, use_container_width=True, height=250)

    with st.expander("➕ Add New Company"):
        new_company_name = st.text_input("Company Name", key="new_company_input")
        
        # Fetch types for selectbox
        df_types_list = pd.read_sql(f'SELECT ctype_id, type_name FROM "{schema}".dim_ctype ORDER BY type_name;', engine)
        type_options = dict(zip(df_types_list['type_name'], df_types_list['ctype_id']))

        selected_type_name = st.selectbox("Industry / Type", options=list(type_options.keys()))

        if st.button("Add Company"):
            if new_company_name and selected_type_name:
                if db.record_exists("dim_company", "company_name", new_company_name):
                    st.warning(f"⚠️ '{new_company_name}' already exists.")
                else:
                    ctype_id = type_options[selected_type_name]
                    if db.insert_record("dim_company", {"company_name": new_company_name, "ctype_id": ctype_id}):
                        st.success(f"✅ '{new_company_name}' added.")
                        st.rerun()
            else:
                st.warning("⚠️ Both fields are required.")
