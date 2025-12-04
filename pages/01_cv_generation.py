import os
import streamlit as st
import yaml
from dotenv import load_dotenv
import platform
import subprocess
from pathlib import Path


def open_folder(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(['open', path])
    else:
        st.error("Unsupported OS for opening folder.")
# Ruta base del proyecto (carpeta raíz del repo)
# Ruta base del proyecto (carpeta raíz del repo)
BASE_PATH = Path(__file__).resolve().parent.parent
env_file = BASE_PATH / ".env"

folder_name = "MAIN_PATH"
db_key = "DB_URL"

working_folder = None
db_url = None

if env_file.exists():
    # ===== MODO LOCAL (.env) =====
    load_dotenv(dotenv_path=env_file)

    main_path_str = os.getenv(folder_name)
    db_url = os.getenv(db_key)

    if not main_path_str:
        st.error("❌ MAIN_PATH no está definido en el archivo .env.")
        st.stop()

    working_folder = Path(main_path_str)
    working_folder.mkdir(parents=True, exist_ok=True)

    if not db_url:
        st.error("❌ DB_URL no está definido en el archivo .env.")
        st.stop()

else:
    # ===== MODO CLOUD / SIN .env (Render) =====
    main_path_str = os.getenv(folder_name)

    # Si no está definida MAIN_PATH en el entorno, usamos un default
    if not main_path_str:
        main_path_str = str(BASE_PATH / "temp_files")
        os.environ[folder_name] = main_path_str  # la inyectamos por si otro código la usa

    working_folder = Path(main_path_str)
    working_folder.mkdir(parents=True, exist_ok=True)

    db_url = os.getenv(db_key)
    if not db_url:
        st.error("❌ La variable de entorno DB_URL no está configurada.")
        st.stop()

# Rutas usadas en tu lógica
output_path = working_folder / "Output CVs"
output_path.mkdir(parents=True, exist_ok=True)


templates_path = working_folder / "CV Templates"
templates_path.mkdir(parents=True, exist_ok=True)

# Cargar configuración YAML
yaml_path = BASE_PATH / "config" / "config.yml"

with open(yaml_path, "r") as file:
    data_access = yaml.safe_load(file) or {}
data_access['DB_URL'] = db_url


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
