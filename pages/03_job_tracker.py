import streamlit as st
import pandas as pd
import os
import sys

# 1) Setup Path to find Library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Library.db_utils import DB_UTILS

# 2) Page Config
st.set_page_config(page_title="📌 Job Tracker", layout="wide")

# 3) Initialize DB via Session State
if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
schema = db.schema
conn = db.get_db_connection()
engine = db.get_engine()

# 4) Navigation
st.page_link("concept_filing.py", label="🏠 Volver al panel principal")
st.write("---")

st.title("📌 Job tracker")

# === Load job_tracker table ===
try:
    jt_df = pd.read_sql(
        f'''
        SELECT
            application_id,
            company,
            contact_person,
            reach_out_day,
            stage,
            "type",
            position,
            posting_url,
            message,
            next_stage_deadline
        FROM "{schema}".job_tracker
        ORDER BY company, position;
        ''',
        engine
    )
except Exception as e:
    st.error(f"❌ Error al cargar job_tracker: {e}")
    st.stop()

if jt_df.empty:
    st.warning("⚠️ No hay registros en job_tracker. Crea aplicaciones primero.")
    st.stop()

# === Display current records ===
st.subheader("📋 Registros actuales")
display_cols = [
    "company", "contact_person", "reach_out_day", 
    "stage", "type", "position", "posting_url", 
    "message", "next_stage_deadline"
]
st.dataframe(jt_df[display_cols], use_container_width=True)

st.markdown("---")
st.markdown("### ✏️ Editar un registro")

# === Selector company – position ===
labels = [f"{row.company} — {row.position}" for _, row in jt_df.iterrows()]
indices = list(range(len(labels)))

selected_index = st.selectbox(
    "Selecciona la company–position a editar:",
    indices,
    format_func=lambda i: labels[i],
)

selected_row = jt_df.iloc[selected_index]

# Read-only fields for context
col_left, col_right = st.columns(2)
col_left.text_input("Company", value=selected_row["company"], disabled=True)
col_right.text_input("Position", value=selected_row["position"], disabled=True)

# Helper to handle NULLs
def safe_str(value):
    return str(value) if pd.notna(value) else ""

# === Edit form ===
with st.form("job_tracker_edit_form"):
    c1, c2 = st.columns(2)
    contact_person = c1.text_input("Contact person", value=safe_str(selected_row["contact_person"]))
    reach_out_day_str = c2.text_input("Reach out day (YYYY-MM-DD)", value=safe_str(selected_row["reach_out_day"]))
    
    c3, c4 = st.columns(2)
    stage = c3.text_input("Stage", value=safe_str(selected_row["stage"]))
    type_field = c4.text_input("Type", value=safe_str(selected_row["type"]))
    
    posting_url = st.text_input("Posting URL", value=safe_str(selected_row["posting_url"]))
    message = st.text_area("Message", value=safe_str(selected_row["message"]), height=150)
    next_stage_deadline_str = st.text_input("Next stage deadline (YYYY-MM-DD)", value=safe_str(selected_row["next_stage_deadline"]))

    submitted_jt = st.form_submit_button("💾 Guardar cambios")

if submitted_jt:
    try:
        conn = db.get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                f'''
                UPDATE "{schema}".job_tracker
                SET
                    contact_person      = %s,
                    reach_out_day       = %s,
                    stage               = %s,
                    "type"              = %s,
                    posting_url         = %s,
                    message             = %s,
                    next_stage_deadline = %s
                WHERE application_id = %s;
                ''',
                (
                    contact_person or None,
                    reach_out_day_str or None,
                    stage or None,
                    type_field or None,
                    posting_url or None,
                    message or None,
                    next_stage_deadline_str or None,
                    int(selected_row["application_id"]),
                ),
            )
            conn.commit()
            conn.close()

        st.success("✅ Registro actualizado correctamente.")
        st.rerun() # Refresh table and selection

    except Exception as e:
        conn.rollback()
        st.error(f"❌ Error al actualizar el registro: {e}")