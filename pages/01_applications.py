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
st.set_page_config(page_title="📝 Applications", layout="wide")

# 3) Initialize DB via Session State
if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
schema = db.schema
conn = db.get_db_connection()
working_folder = db.working_folder

# 4) Layout & Navigation
st.page_link("concept_filing.py", label="🏠 Volver al panel principal")
st.write("---")

# Helper for logging in this view
log_box = st.empty()
def ui_log(msg: str, level: str = "info"):
    if level == "success":
        log_box.success(msg)
    elif level == "warning":
        log_box.warning(msg)
    elif level == "error":
        log_box.error(msg)
    else:
        log_box.info(msg)        

st.title("📝 Applications")

PK = "application_id"
cols_show = ["job", "company_type", "lang", "status", "company_name", "created_at"]

# === Load FULL table ===
try:
    df_full = pd.read_sql(f'''
        SELECT *
        FROM "{schema}".applications
        ORDER BY created_at DESC;
    ''', conn)
except Exception:
    df_full = pd.DataFrame()

# === Display & Export ===
if not df_full.empty:
    show_cols = [c for c in cols_show if c in df_full.columns]
    st.dataframe(df_full[show_cols], use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_full[show_cols].to_excel(writer, index=False, sheet_name="applications")

    st.download_button(
        label="⬇️ Exportar a Excel (vista)",
        data=buffer.getvalue(),
        file_name=f"applications_{datetime.now():%Y%m%d_%H%M}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.info("No hay registros para mostrar/exportar.")

st.markdown("### ➕ Agregar o Editar Application")

# === Selector Logic ===
selected_pk = None
original = {}

if not df_full.empty and PK in df_full.columns:
    options = df_full[[PK, "job", "company_name", "created_at"]].copy()
    options["label"] = (
        options["job"].fillna("").astype(str)
        + " | " + options["company_name"].fillna("").astype(str)
        + " | " + options["created_at"].astype(str)
    )

    label_list = options["label"].tolist()
    pk_by_label = dict(zip(options["label"], options[PK]))

    selected_label = st.selectbox(
        "Selecciona una aplicación existente (opcional para editar):",
        [""] + label_list
    )

    if selected_label:
        selected_pk = pk_by_label[selected_label]
        original_row = df_full[df_full[PK] == selected_pk].iloc[0]
        original = original_row.to_dict()
else:
    st.warning(f"No encontré columna '{PK}'.")

# === Helper: normalize values ===
def _norm(v):
    return "" if v is None else v

# === Fetch Options for Selectboxes ===
try:
    lang_opts = pd.read_sql(f'SELECT lang FROM "{schema}".languages ORDER BY lang;', conn)["lang"].dropna().astype(str).tolist()
except: lang_opts = []

try:
    company_opts = pd.read_sql(f'SELECT company_name FROM "{schema}".companies ORDER BY company_name;', conn)["company_name"].dropna().astype(str).tolist()
except: company_opts = []

status_opts = ["applied", "interviewing", "offered", "rejected"]

# === Form ===
with st.form("applications_form", clear_on_submit=False):
    job_val = st.text_input("Job position", value=original.get("job", "") or "")
    
    # Language
    default_lang = (original.get("lang") or "")
    if default_lang and default_lang not in lang_opts: lang_opts = [default_lang] + lang_opts
    lang_val = st.selectbox("Language", options=lang_opts, index=lang_opts.index(default_lang) if default_lang in lang_opts else 0)

    # Company
    default_company = (original.get("company_name") or "")
    if default_company and default_company not in company_opts: company_opts = [default_company] + company_opts
    company_name_val = st.selectbox("Company name", options=company_opts, index=company_opts.index(default_company) if default_company in company_opts else 0)

    # Company Type (Filtered)
    try:
        company_type_opts = pd.read_sql(f'SELECT company_type FROM "{schema}".companies WHERE company_name = %(cn)s ORDER BY company_type;', 
                                        conn, params={"cn": company_name_val})["company_type"].dropna().astype(str).tolist()
    except: company_type_opts = []
    
    default_ct = (original.get("company_type") or "")
    if default_ct and default_ct not in company_type_opts: company_type_opts = [default_ct] + company_type_opts
    company_type_val = st.selectbox("Company type", options=company_type_opts if company_type_opts else [""], index=company_type_opts.index(default_ct) if default_ct in company_type_opts else 0)

    status_val = st.selectbox("Status", options=status_opts, index=status_opts.index(original.get("status")) if original.get("status") in status_opts else 0)

    # Long Text Fields
    education1_val = st.text_area("Education 1", value=original.get("education1", "") or "", height=90)
    experience1_val = st.text_area("Experience 1", value=original.get("experience1", "") or "", height=120)
    skills_val = st.text_area("Skills", value=original.get("skills", "") or "", height=120)
    # ... (other text areas follow the same pattern)

    new_values = {
        "job": job_val, "lang": lang_val, "company_name": company_name_val,
        "company_type": company_type_val, "status": status_val,
        "education1": education1_val, "experience1": experience1_val, "skills": skills_val
        # add other fields as needed
    }

    col_a, col_b = st.columns(2)
    submit_update = col_a.form_submit_button("💾 Guardar cambios")
    submit_insert = col_b.form_submit_button("➕ Crear nueva aplicación")

# === Database Actions ===
if submit_update and selected_pk:
    changed = {k: v for k, v in new_values.items() if _norm(v) != _norm(original.get(k))}
    if changed:
        set_clause = ", ".join([f'"{k}" = %({k})s' for k in changed.keys()])
        params = {**changed, PK: selected_pk}
        with conn.cursor() as cur:
            cur.execute(f'UPDATE "{schema}".applications SET {set_clause} WHERE "{PK}" = %({PK})s;', params)
        conn.commit()
        st.success("Actualizado ✅")
        st.rerun()

if submit_insert:
    cols_sql = ", ".join([f'"{c}"' for c in new_values.keys()])
    placeholders = ", ".join([f"%({c})s" for c in new_values.keys()])
    with conn.cursor() as cur:
        cur.execute(f'INSERT INTO "{schema}".applications ({cols_sql}) VALUES ({placeholders});', new_values)
    conn.commit()
    st.success("Creada ✅")
    st.rerun()

# === CV Generation (Using Shared Paths) ===
# Note: gen requires data_access which we can add to DB_UTILS or handle here
gen = CV_GENERATION(working_folder, {"DB_URL": os.getenv("DB_POSTGRESQL")}) 

if st.button("📄 Generar CV para este registro", disabled=(selected_pk is None)):
    df_cv = df_full[df_full[PK] == selected_pk].copy()
    if not df_cv.empty:
        gen.postgre_to_docx("cv", df_cv, ui_log=ui_log)
        ui_log("Proceso ejecutado ✅", "success")

col1, col2 = st.columns(2)
if col1.button("📁 Abre plantillas"): gen.open_folder(db.templates_path)
if col2.button("📁 Abre resultados"): gen.open_folder(db.output_path)