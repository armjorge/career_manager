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
# Ruta base del proyecto (carpeta raíz del repo)
BASE_PATH = Path(__file__).resolve().parent.parent

ENV_MAIN_PATH_KEY = "MAIN_PATH"
ENV_DB_URL_KEY = "DB_URL"

IS_RENDER = os.getenv("RENDER") == "true"

working_folder: Path | None = None
db_url: str | None = None

if IS_RENDER:
    # === MODO CLOUD (Render) ===
    # Usamos una carpeta local dentro del repo como MAIN_PATH
    working_folder = BASE_PATH / "temp_files"
    working_folder.mkdir(parents=True, exist_ok=True)

    # Opcional: inyectar MAIN_PATH en os.environ para mantener compatibilidad
    os.environ[ENV_MAIN_PATH_KEY] = str(working_folder)

    # DB_URL viene de las variables de entorno configuradas en Render
    db_url = os.getenv(ENV_DB_URL_KEY)
    if not db_url:
        st.error("❌ La variable de entorno DB_URL no está configurada en Render.")
        st.stop()

else:
    # === MODO LOCAL ===
    env_file = BASE_PATH / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)

        main_path_str = os.getenv(ENV_MAIN_PATH_KEY)
        db_url = os.getenv(ENV_DB_URL_KEY)

        if not main_path_str:
            st.error("❌ MAIN_PATH no está definido en el archivo .env.")
            st.stop()

        working_folder = Path(main_path_str)
        working_folder.mkdir(parents=True, exist_ok=True)

        if not db_url:
            st.error("❌ DB_URL no está definido en el archivo .env.")
            st.stop()
    else:
        st.error("❌ No se encontró el archivo .env en la raíz del proyecto.")
        st.stop()

# Rutas que usa tu lógica actual (sin cambiar el resto del código)
output_path = working_folder / "Output CVs"
output_path.mkdir(parents=True, exist_ok=True)

templates_path = working_folder / "CV Templates"
templates_path.mkdir(parents=True, exist_ok=True)


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
