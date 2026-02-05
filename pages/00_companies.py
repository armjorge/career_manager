import streamlit as st
import pandas as pd
import os
import sys

# 1) Setup Path to find Library
# This allows the script inside 'pages/' to find 'Library/' in the root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Library.db_utils import DB_UTILS

# 2) Page Config
st.set_page_config(page_title="Companies & Business Types", layout="wide")

# 🔙 Link to Home (Optional, since Streamlit Sidebar has the menu)
st.page_link("concept_filing.py", label="🏠 Volver al panel principal")
st.write("---")

# 3) Initialize DB via Session State
if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
schema = db.schema
conn = db.get_db_connection()
engine = db.get_engine()

# 4) UI Content
st.title("🏢 Companies & Business Types")

col1, col2 = st.columns(2)

# === 🗂️ Sección: Company Types ===
with col1:
    st.subheader("📂 Company Types")

    try:
        df_types = pd.read_sql(
            f'SELECT type_business FROM "{schema}".company_types ORDER BY type_business;',
            engine
        )
    except Exception:
        df_types = pd.DataFrame()

    st.dataframe(df_types, use_container_width=True, height=250)

    st.markdown("### ➕ Agregar nuevo Company Type")
    new_type_business = st.text_input("Nuevo Type Business")

    if st.button("Agregar Company Type"):
        if new_type_business:
            try:
                conn = db.get_db_connection()
                with conn.cursor() as cur:
                    cur.execute(
                        f'INSERT INTO "{schema}".company_types (type_business) VALUES (%s) ON CONFLICT DO NOTHING;',
                        (new_type_business,)
                    )
                conn.commit()
                conn.close()
                st.success("✅ Tipo de negocio agregado correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al agregar tipo de negocio: {e}")
        else:
            st.warning("⚠️ El tipo de negocio no puede estar vacío.")


# === 🏢 Sección: Companies ===
with col2:
    st.subheader("🏢 Companies")

    try:
        df_companies = pd.read_sql(
            f'SELECT company_name, company_type, created_at FROM "{schema}".companies ORDER BY company_name;',
            conn
        )
    except Exception:
        df_companies = pd.DataFrame()

    st.dataframe(df_companies, use_container_width=True, height=250)

    st.markdown("### ➕ Agregar nueva Company")
    new_company_name = st.text_input("Nombre de la Company")

    # Load options for dropdown
    
    try:
        company_types_df = pd.read_sql(
            f'SELECT type_business FROM "{schema}".company_types ORDER BY type_business;',
            engine
        )
        company_type_options = company_types_df['type_business'].tolist()
    except Exception:
        company_type_options = []

    selected_company_type = st.selectbox("Tipo de negocio", options=company_type_options)

    if st.button("Agregar Company"):
        if new_company_name and selected_company_type:
            try:
                conn = db.get_db_connection()
                with conn.cursor() as cur:
                    cur.execute(
                        f'INSERT INTO "{schema}".companies (company_name, company_type) VALUES (%s, %s) ON CONFLICT DO NOTHING;',
                        (new_company_name, selected_company_type)
                    )
                conn.commit()
                conn.close()
                st.success("✅ Company agregada correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al agregar Company: {e}")
        else:
            st.warning("⚠️ Debes llenar ambos campos.")
