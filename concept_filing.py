import streamlit as st

st.set_page_config(page_title="Carrier · Panel principal", layout="centered")

st.title("🚀 Carrier · Panel principal")
st.write("Selecciona una sección para continuar:")

st.page_link(
    "pages/00_db_handling.py",
    label="Administración de la base",
    icon="🗃️",
)

st.page_link(
    "pages/01_cv_generation.py",
    label="Generación de archivos",
    icon="📄",
)