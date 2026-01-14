import streamlit as st
import pandas as pd
import datetime as dt
import os
import sys

# 1) Setup Path to find Library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Library.db_utils import DB_UTILS
from Library.CV_generation import CV_GENERATION

# 2) Page Config
st.set_page_config(page_title="📄 Cover Letters", layout="wide")

# 3) Initialize DB via Session State
if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
schema = db.schema
conn = db.get_db_connection()
working_folder = db.working_folder

# 4) Navigation
st.page_link("concept_filing.py", label="🏠 Volver al panel principal")
st.write("---")

# --- UI logger ---
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

st.title("📄 Cover Letters")

# === Load combinations from cover_letters ===
try:
    covers_df = pd.read_sql(
        f'''
        SELECT cover_id, job, lang, company_name, 
               header, address, date, body, "end", sign
        FROM "{schema}".cover_letters
        ORDER BY cover_id DESC;
        ''',
        conn
    )
except Exception as e:
    st.error(f"Error loading cover letters: {e}")
    covers_df = pd.DataFrame()

if covers_df.empty:
    st.warning("⚠️ No existen cover letters registradas. El trigger debería crear una por cada aplicación.")
    st.stop()

# Selector setup
combo_options = [
    f"{row.job} — {row.lang} — {row.company_name}" 
    for _, row in covers_df.iterrows()
]

if 'cover_letter_selected_index' not in st.session_state:
    st.session_state.cover_letter_selected_index = 0

selected_index = st.selectbox(
    "Selecciona una aplicación (Job — Language — Company):", 
    range(len(combo_options)),
    format_func=lambda i: combo_options[i],
    index=st.session_state.cover_letter_selected_index,
    key='cover_selector'
)
st.session_state.cover_letter_selected_index = selected_index

current = covers_df.iloc[selected_index]

# Status check
has_content = any([
    pd.notna(current.get("header")) and str(current.get("header")).strip(),
    pd.notna(current.get("body")) and str(current.get("body")).strip(),
])

if has_content:
    st.info("✏️ Carta existente: puedes editar los campos abajo.")
else:
    st.info("🆕 Nueva carta: llena los campos para crearla.")

# === Formulario ===
with st.form("cover_letter_form"):
    st.markdown("### 🧾 Información de la carta")

    default_date = dt.date.today()
    if pd.notna(current["date"]) and str(current["date"]).strip() != "":
        try:
            default_date = pd.to_datetime(current["date"]).date()
        except Exception:
            pass

    picked_date = st.date_input("Fecha de carta", value=default_date)
    header = st.text_area("Header", value=current["header"] if pd.notna(current["header"]) else "", height=100)
    address = st.text_area("Address", value=current["address"] if pd.notna(current["address"]) else "", height=80)
    body = st.text_area("Body", value=current["body"] if pd.notna(current["body"]) else "", height=250)
    end_text = st.text_area("End", value=current["end"] if pd.notna(current["end"]) else "", height=80)
    sign = st.text_area("Sign", value=current["sign"] if pd.notna(current["sign"]) else "", height=60)

    submitted = st.form_submit_button("💾 Guardar carta")

    if submitted:
        try:
            cover_id = int(current["cover_id"])
            with conn.cursor() as cur:
                cur.execute(
                    f'''
                    UPDATE "{schema}".cover_letters
                    SET header = %s, address = %s, date = %s, body = %s, "end" = %s, sign = %s
                    WHERE cover_id = %s;
                    ''',
                    (header, address, picked_date, body, end_text, sign, cover_id)
                )
            conn.commit()
            st.success("✅ Carta guardada correctamente.")
            st.rerun()
        except Exception as e:
            conn.rollback()
            st.error(f"❌ Error al guardar la carta: {e}")

# === Generar documento ===
st.markdown("---")
st.markdown("### 📝 Generar documento")

# Note: We pass DB_URL in the data_access dict if CV_GENERATION requires it
gen = CV_GENERATION(working_folder, {"DB_URL": os.getenv("DB_POSTGRESQL")})

if st.button("Crear Cover Letter"):
    try:
        # Get selected details from memory
        row = covers_df.iloc[selected_index]
        
        df_cl = pd.DataFrame([{
            "job": row["job"],
            "lang": row["lang"],
            "company_name": row["company_name"],
            "header": header, # Use current UI values
            "address": address,
            "date": picked_date,
            "body": body,
            "end": end_text,
            "sign": sign,
        }])

        ui_log("Iniciando generación de Cover Letter...", "info")
        gen.postgre_to_docx("coverletter", df_cl, ui_log=ui_log)
        ui_log("Cover Letter generada ✅", "success")

    except Exception as e:
        ui_log(f"Error generando Cover Letter: {e}", "error")

col1, col2 = st.columns(2)
if col1.button("📁 Abre plantillas"): 
    gen.open_folder(db.templates_path)
if col2.button("📁 Abre resultados"): 
    gen.open_folder(db.output_path)