import os
import streamlit as st
import yaml
from dotenv import load_dotenv
import platform
import subprocess


def open_folder(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(['open', path])
    else:
        st.error("Unsupported OS for opening folder.")
# Configuración de rutas y carga de variables de entorno
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
env_file = os.path.join(BASE_PATH, ".env")

folder_name = "MAIN_PATH"
db_key = "DB_URL"

working_folder = None
data_access = {}

if os.path.exists(env_file):
    load_dotenv(dotenv_path=env_file)
    working_folder = os.getenv(folder_name)
    db_url = os.getenv(db_key)
else:
    st.error("❌ No se encontró el archivo .env en la raíz del proyecto.")
    st.stop()
output_path = os.path.join(working_folder, "Output CVs")
os.makedirs(output_path, exist_ok=True)
templates_path = os.path.join(working_folder, "CV Templates")

yaml_path = os.path.join(BASE_PATH, "config", "config.yml")
with open(yaml_path, "r") as f:
    yaml_data = yaml.safe_load(f) or {}

# Inyectar el DB_URL que sacamos del .env
yaml_data["DB_URL"] = db_url
data_access = yaml_data
st.set_page_config(page_title="Resumen aplicaciones", layout="wide")



# 🔙 Link a Home
st.page_link(
    "concept_filing.py",
    label="🏠 Volver al panel principal",
)
st.write("---")


if st.button("Generar el esquema SQL"):
    st.write("Iniciando el generador de esquema SQL...")
    from Library.SQL_management import CSV_TO_SQL
    CSV_TO_SQL(working_folder, data_access).csv_to_sql_process()

if st.button("Generar CVs desde PostgreSQL"):
    from Library.CV_generation import CV_GENERATION
    CV_GENERATION(working_folder, data_access).postgre_to_docx()



if st.button("Abrir folder de CVs y cartas"):
    open_folder(output_path)
