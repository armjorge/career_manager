# Importar librerías
import streamlit as st
from dotenv import load_dotenv
from Library.db_utils import DB_UTILS
from pathlib import Path

# Cargar variables de entorno
BASE_PATH = Path(__file__).resolve().parent
env_file = BASE_PATH / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)


st.set_page_config(page_title="Administrador de carrera · Panel principal", layout="centered")

st.title("🚀 Administrador de Carrera · Panel principal")
st.write("Selecciona una sección para continuar:")

st.page_link(
    "pages/00_companies.py",
    label="Empresas",
    icon="🏢",
)

st.page_link(
    "pages/01_applications.py",
    label="Aplicaciones",
    icon="🗃️",
)

st.page_link(
    "pages/02_pdf_letters_resumes.py",
    label="Cartas y CV",
    icon="✉️",
)

st.page_link(
    "pages/03_pdf_generator.py",
    label="Generador de Archivos",
    icon="📈",
)

st.page_link(
    "pages/04_pdf_handling.py",
    label="Cargar PDF's",
    icon="📄",
)