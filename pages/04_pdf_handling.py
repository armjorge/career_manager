import streamlit as st
import pandas as pd
import os
import sys
import io
from datetime import datetime
import pandas as pd

# 1) Setup Path to find Library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Library.db_utils import DB_UTILS
from Library.CV_generation import CV_GENERATION

# 2) Page Config
st.set_page_config(page_title="📝 PDF uploading", layout="wide")
# 3) Initialize DB via Session State
if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
schema = db.schema
conn = db.get_db_connection()
working_folder = db.working_folder

mongo_db = db.mongo_db_connexion()
try:
    df_full = pd.read_sql(f'SELECT * FROM "{schema}".applications ORDER BY created_at DESC;', conn)
except Exception:
    df_full = pd.DataFrame()

# 3) Initialize DB via Session State
if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
conn = db.get_db_connection()
mongo_collection = db.mongo_db_connexion()

# Fetch SQL Data
try:
    df_full = pd.read_sql(f'SELECT * FROM "{db.schema}".applications ORDER BY created_at DESC;', conn)
except Exception:
    df_full = pd.DataFrame()

st.title("📝 Application Document Manager")

if not df_full.empty:
    # Ensure it is sorted (already handled by your SQL ORDER BY, but good to verify)
    df_full = df_full.sort_values("created_at", ascending=False)

    # Create a friendly display label: "Company - Job (ID)"
    df_full["display_label"] = (
        df_full["company_name"] + " - " + df_full["job"] + 
        " (#" + df_full["application_id"].astype(str) + ")"
    )

    # 2. Create the selectbox using the display label
    # We use format_func to show the label while the widget technically holds the whole row or the ID
    selected_label = st.selectbox(
        "Select Application",
        options=df_full["display_label"].tolist(),
        index=0
    )

    # 3. Retrieve the actual ID from the selected label
    # We filter the dataframe to get the correct record
    app_data = df_full[df_full["display_label"] == selected_label].iloc[0]
    app_id = app_data["application_id"]

    st.divider() 
    # --- MONGO LOGIC: Sync/Initialize Document ---
    # We use update_one with upsert=True to create if it doesn't exist
    mongo_collection.update_one(
        {"application_id": str(app_id)},
        {"$setOnInsert": {
            "job": app_data["job"],
            "company_type": app_data["company_type"],
            "pdf_job_description": None,
            "pdf_cv_sent": None,
            "pdf_cover_letter": None,
            "url_link": ""
        }},
        upsert=True
    )

    # Fetch current state from Mongo
    current_doc = mongo_collection.find_one({"application_id": str(app_id)})

    # --- UI: File Uploading & Fields ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Document Uploads")
        
        # Dictionary to map labels to keys
        files_to_upload = {
            "Descripción del puesto": "pdf_job_description",
            "CV Enviado": "pdf_cv_sent",
            "Cover Letter Enviada": "pdf_cover_letter"
        }
        for label, key in files_to_upload.items():
                # 1. Check if file exists in the MongoDB document
                file_data = current_doc.get(key)
                status = "✅ Subido" if file_data else "❌ Pendiente"
                
                st.write(f"**{label}:** {status}")

                # 2. Layout for Upload and Download buttons
                btn_col1, btn_col2 = st.columns([3, 1])
                
                with btn_col1:
                    uploaded_file = st.file_uploader(
                        f"Subir/Reemplazar {label}", 
                        type="pdf", 
                        key=f"up_{key}_{app_id}",
                        label_visibility="collapsed" # Keeps UI clean
                    )
                
                with btn_col2:
                    # 3. Only show download button if the data actually exists in Mongo
                    if file_data:
                        st.download_button(
                            label="💾",
                            data=file_data,
                            file_name=f"{label}_{app_id}.pdf",
                            mime="application/pdf",
                            key=f"dl_{key}_{app_id}"
                        )

                # 4. Save logic (your existing code)
                if uploaded_file:
                    file_bytes = uploaded_file.read()
                    mongo_collection.update_one(
                        {"application_id": str(app_id)},
                        {"$set": {key: file_bytes}}
                    )
                    st.rerun() # Refresh to update the "status" and show the download button


    with col2:
        st.subheader("External Links")
        
        # Get existing URL from Mongo
        existing_url = current_doc.get("url_link", "")
        
        # 1. Show a clickable link if it exists
        if existing_url:
            st.markdown(f"🔗 **Current Link:** [{existing_url}]({existing_url})")
        else:
            st.info("No URL saved for this application.")

        # 2. Text input for editing (defaults to the existing URL)
        url_input = st.text_input(
            "Edit Job URL Link", 
            value=existing_url, 
            placeholder="https://example.com/job-post",
            key=f"url_in_{app_id}"
        )
        
        # 3. Save button logic
        if st.button("Save Changes"):
            if url_input != existing_url:
                mongo_collection.update_one(
                    {"application_id": str(app_id)},
                    {"$set": {"url_link": url_input}}
                )
                st.toast("URL updated successfully!")
                st.rerun() # Refresh to update the clickable link at the top
            else:
                st.write("No changes detected.")

else:
    st.warning("No applications found in the SQL database.")