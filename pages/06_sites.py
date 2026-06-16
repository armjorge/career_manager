import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

# 1) Setup Path to find Library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Library.db_utils import DB_UTILS

# 2) Page Config
st.set_page_config(page_title="🌐 Website Repository", layout="wide")

# 3) Initialize DB via Session State
if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
schema = db.schema
engine = db.get_engine()

# 4) Navigation
st.page_link("concept_filing.py", label="🏠 Volver al panel principal")
st.write("---")

st.title("🌐 Website Repository")

# 5) UI Layout
col_list, col_add = st.columns([2, 1])

with col_add:
    st.subheader("➕ Add New Website")
    with st.form("add_site_form", clear_on_submit=True):
        new_address = st.text_input("Website Address (e.g. www.linkedin.com)")
        submit_button = st.form_submit_button("Add Website")
        
        if submit_button:
            if new_address:
                # Check if it exists
                if db.record_exists("fact_web_list", "address", new_address):
                    st.warning(f"⚠️ '{new_address}' already exists.")
                else:
                    if db.insert_record("fact_web_list", {"address": new_address}):
                        st.success(f"✅ '{new_address}' added.")
                        st.rerun()
            else:
                st.error("⚠️ Address cannot be empty.")

with col_list:
    st.subheader("📋 Registered Websites")
    
    # Query data
    query = f"""
        SELECT address, created_at
        FROM "{schema}".fact_web_list
        ORDER BY COALESCE(last_modification, created_at) DESC;
    """
    try:
        df_sites = pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        df_sites = pd.DataFrame()
    
    if not df_sites.empty:
        # We use data_editor to allow editing the address
        # Note: In Streamlit, changes are applied when the user clicks outside or presses Enter.
        edited_df = st.data_editor(
            df_sites,
            column_config={
                "site_id": st.column_config.NumberColumn("ID", disabled=True),
                "address": st.column_config.LinkColumn("Website Address", required=True),
                "created_at": st.column_config.DatetimeColumn("Created At", disabled=True),
                "last_modification": st.column_config.DatetimeColumn("Last Modification", disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            key="sites_editor"
        )
        
        # Check for changes in st.session_state.sites_editor
        if "sites_editor" in st.session_state:
            changes = st.session_state.sites_editor.get("edited_rows", {})
            if changes:
                success_count = 0
                for index_str, row_changes in changes.items():
                    idx = int(index_str)
                    site_id = df_sites.iloc[idx]["site_id"]
                    if "address" in row_changes:
                        new_addr = row_changes["address"]
                        if new_addr:
                            if db.update_record("fact_web_list", {"address": new_addr}, "site_id", site_id):
                                success_count += 1
                        else:
                            st.error(f"⚠️ Address for ID {site_id} cannot be empty.")
                
                if success_count > 0:
                    st.success(f"✅ Updated {success_count} record(s).")
                    st.rerun()
    else:
        st.info("No websites registered yet.")
