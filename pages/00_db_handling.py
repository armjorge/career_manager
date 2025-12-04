import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from sqlalchemy import create_engine
from urllib.parse import urlparse
from dotenv import load_dotenv
import yaml
from pathlib import Path

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
# 1) Parse DB URL from self.data_access['sql_workflow']
sql_url = data_access['DB_URL']
parsed = urlparse(sql_url)
dbname = parsed.path.lstrip('/')
user = parsed.username
password = parsed.password
host = parsed.hostname
port = parsed.port

# 2) Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)

# 3) Streamlit UI
st.set_page_config(page_title="Resumen aplicaciones", layout="wide")
# 🔙 Link a Home
st.page_link(
    "concept_filing.py",
    label="🏠 Volver al panel principal",
)
st.write("---")
vista = st.sidebar.radio(
    "Seleccionar vista:",
    [
        "Companies",
        "Applications",
        "Cover Letters",
        "Job tracker"
    ]
)

schema = data_access['db_structure']['schema_name']    

if vista == "Companies":
    st.title("🏢 Companies & Business Types")

    col1, col2 = st.columns(2)

    # === 🗂️ Sección: Company Types ===
    with col1:
        st.subheader("📂 Company Types")

        # Mostrar registros actuales
        try:
            df_types = pd.read_sql(
                f'SELECT type_business FROM "{schema}".company_types ORDER BY type_business;',
                conn
            )
        except Exception:
            df_types = pd.DataFrame()

        st.dataframe(df_types, use_container_width=True, height=250)

        st.markdown("### ➕ Agregar nuevo Company Type")
        new_type_business = st.text_input("Nuevo Type Business")

        if st.button("Agregar Company Type"):
            if new_type_business:
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            f'''
                            INSERT INTO "{schema}".company_types (type_business)
                            VALUES (%s)
                            ON CONFLICT DO NOTHING;
                            ''',
                            (new_type_business,)
                        )
                        conn.commit()
                    st.success("✅ Tipo de negocio agregado correctamente.")
                except Exception as e:
                    st.error(f"❌ Error al agregar tipo de negocio: {e}")
            else:
                st.warning("⚠️ El tipo de negocio no puede estar vacío.")

    # === 🏢 Sección: Companies ===
    with col2:
        st.subheader("🏢 Companies")

        # Mostrar registros actuales
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

        # Cargar opciones de tipo de negocio
        try:
            company_types_df = pd.read_sql(
                f'SELECT type_business FROM "{schema}".company_types ORDER BY type_business;',
                conn
            )
            company_type_options = company_types_df['type_business'].tolist()
        except Exception:
            company_type_options = []

        selected_company_type = st.selectbox("Tipo de negocio", options=company_type_options)

        if st.button("Agregar Company"):
            if new_company_name and selected_company_type:
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            f'''
                            INSERT INTO "{schema}".companies (company_name, company_type)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING;
                            ''',
                            (new_company_name, selected_company_type)
                        )
                        conn.commit()
                    st.success("✅ Company agregada correctamente.")
                except Exception as e:
                    st.error(f"❌ Error al agregar Company: {e}")
            else:
                st.warning("⚠️ Debes llenar ambos campos para agregar una Company.")

elif vista == "Applications":
    st.title("📝 Applications")

    # === Mostrar registros actuales ===
    try:
        df = pd.read_sql(f'''
            SELECT job, education1, education2, education3,
                experience1, experience2, experience3,
                skills, interests, lang, status,
                company_name, company_type, created_at, cv_files
            FROM "{schema}".applications
            ORDER BY created_at DESC;
        ''', conn)
    except Exception:
        df = pd.DataFrame()

    st.dataframe(df, use_container_width=True)

    st.markdown("### ➕ Agregar o Editar Application")

    # === Seleccionar registro existente (opcional) ===
    existing_jobs = df['job'].tolist() if not df.empty else []
    selected_existing_job = st.selectbox("Selecciona una aplicación existente (opcional para editar):", [""] + existing_jobs)


    # Prellenar si se seleccionó uno existente
    if selected_existing_job:
        selected_row = df[df['job'] == selected_existing_job].iloc[0]
        default_values = selected_row.to_dict()
    else:
        default_values = {}
    # === Botón actualizar CV's (movido fuera del formulario) ===
    from Library.CV_generation import CV_GENERATION
    function_app = CV_GENERATION(working_folder, data_access)
    if st.button("Actualizar CV Files"):
        function_app.get_cv_files()
    if st.button("Abre carpeta de CVs"):
        templates_path = os.path.join(working_folder, "CV Templates")
        function_app.open_folder(templates_path)


    # === Formulario ===
    with st.form("application_form", clear_on_submit=False):
        st.subheader("🧠 Información General")
        new_job = st.text_input("Job position", value=default_values.get("job", ""))

        # === Educación ===
        # === Educación ===
        st.markdown("#### 🎓 Education")
        col1, col2 = st.columns(2)  # ← dos columnas amplias
        with col1:
            new_education1 = st.text_area("Education 1", value=default_values.get("education1", ""), height=250)
            new_education2 = st.text_area("Education 2", value=default_values.get("education2", ""), height=250)
        with col2:
            new_education3 = st.text_area("Education 3", value=default_values.get("education3", ""), height=250)

        # === Experiencia ===
        st.markdown("#### 💼 Experience")
        col3, col4 = st.columns(2)
        with col3:
            new_experience1 = st.text_area("Experience 1", value=default_values.get("experience1", ""), height=250)
            new_experience2 = st.text_area("Experience 2", value=default_values.get("experience2", ""), height=250)
        with col4:
            new_experience3 = st.text_area("Experience 3", value=default_values.get("experience3", ""), height=250)
        # === Skills & Interests ===
        st.markdown("#### 🧩 Skills & Interests")
        new_skills = st.text_area("Skills", value=default_values.get("skills", ""), height=120)
        new_interests = st.text_area("Interests", value=default_values.get("interests", ""), height=120)

        # === Idioma y Estado ===
        st.markdown("#### 🌍 Language & Status")
        col7, col8 = st.columns(2)
        with col7:
            lang_options = ["English", "Spanish", "French"]
            new_lang = st.selectbox("Language", options=lang_options, index=lang_options.index(default_values.get("lang", "English")) if default_values.get("lang") in lang_options else 0)
        with col8:
            status_options = ["applied", "interviewing", "offered", "rejected"]
            selected_status = st.selectbox("Status", options=status_options, index=status_options.index(default_values.get("status", "applied")) if default_values.get("status") in status_options else 0)

        # === Empresa y Tipo ===
        st.markdown("#### 🏢 Company Information")
        try:
            companies_df = pd.read_sql(
                f'SELECT company_name, company_type FROM "{schema}".companies ORDER BY company_name;',
                conn
            )
            company_options = companies_df.to_dict('records')
        except Exception:
            company_options = []
        
        
        if company_options:
            company_names = [c['company_name'] for c in company_options]
            selected_company_name = st.selectbox("Company Name", options=company_names, index=company_names.index(default_values.get("company_name", company_names[0])) if default_values.get("company_name") in company_names else 0)
            selected_company_type = next(
                (c['company_type'] for c in company_options if c['company_name'] == selected_company_name),
                default_values.get("company_type", None)
            )
            st.info(f"**Company Type:** {selected_company_type}")
        else:
            selected_company_name = st.text_input("Company Name (if none available)", value=default_values.get("company_name", ""))
            selected_company_type = st.text_input("Company Type", value=default_values.get("company_type", ""))
        # === Sección de archivo de CV vinculado ===
        st.markdown("#### 🏢 CV File")
        # Load cv_files options based on selected lang (note: this uses the default lang for options; for dynamic update, consider moving outside form or using session state)
        try:
            cv_files_df = pd.read_sql(
                f'SELECT cv_file FROM "{schema}".cv_files WHERE lang = %s ORDER BY cv_file;',
                conn,
                params=(new_lang,)
            )
            cv_file_options = cv_files_df['cv_file'].tolist()
        except Exception:
            cv_file_options = []
        selected_cv_file = st.selectbox("CV File", options=[""] + cv_file_options, index=0 if not default_values.get("cv_files") or default_values.get("cv_files") not in cv_file_options else cv_file_options.index(default_values.get("cv_files")) + 1)
        
        # === Botón de envío ===
        submitted = st.form_submit_button("💾 Guardar Application")

        if submitted:
            if new_job and selected_company_name and selected_company_type and selected_status:
                try:
                    with conn.cursor() as cur:
                        # Intentar actualizar primero
                        cur.execute(
                            f'''
                            UPDATE "{schema}".applications
                            SET education1 = %s, education2 = %s, education3 = %s,
                                experience1 = %s, experience2 = %s, experience3 = %s,
                                skills = %s, interests = %s, lang = %s, status = %s,
                                company_name = %s, company_type = %s, cv_files = %s
                            WHERE job = %s;
                            ''',
                            (
                                new_education1, new_education2, new_education3,
                                new_experience1, new_experience2, new_experience3,
                                new_skills, new_interests,
                                new_lang, selected_status,
                                selected_company_name, selected_company_type, selected_cv_file or None,
                                new_job
                            )
                        )
                        if cur.rowcount == 0:
                            # Si no existe, insertar
                            cur.execute(
                                f'''
                                INSERT INTO "{schema}".applications 
                                (job, education1, education2, education3,
                                experience1, experience2, experience3,
                                skills, interests, lang, status,
                                company_name, company_type, cv_files)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                                ''',
                                (
                                    new_job,
                                    new_education1, new_education2, new_education3,
                                    new_experience1, new_experience2, new_experience3,
                                    new_skills, new_interests,
                                    new_lang, selected_status,
                                    selected_company_name, selected_company_type, selected_cv_file or None
                                )
                            )
                        conn.commit()
                    st.success("✅ Application guardada o actualizada correctamente.")
                except Exception as e:
                    st.error(f"❌ Error al guardar la Application: {e}")
            else:
                st.warning("⚠️ Los campos Job, Company Name y Status son obligatorios.")

    
elif vista == "Cover Letters":
    st.title("📄 Cover Letters")

    # === Cargar combinaciones válidas desde applications ===
    try:
        apps_df = pd.read_sql(
            f'SELECT job, lang, company_name FROM "{schema}".applications ORDER BY job;',
            conn
        )
    except Exception:
        apps_df = pd.DataFrame()

    if apps_df.empty:
        st.warning("⚠️ No existen aplicaciones registradas aún. Agrega una antes de crear cartas.")
        st.stop()

    # Crear lista legible para selección
    combo_options = [
        f"{row.job} — {row.lang} — {row.company_name}" for _, row in apps_df.iterrows()
    ]
    selected_combo = st.selectbox("Selecciona una aplicación (Job — Language — Company):", combo_options)

    # Parsear selección
    job_selected, lang_selected, company_selected = selected_combo.split(" — ")

    # === Buscar si ya existe una carta para esa combinación ===
    try:
        query = f'''
            SELECT header, address, date, body, "end", sign
            FROM "{schema}".cover_letters
            WHERE job = %s AND lang = %s AND company_name = %s;
        '''
        cover_df = pd.read_sql(query, conn, params=(job_selected, lang_selected, company_selected))
    except Exception:
        cover_df = pd.DataFrame()

    # Valores iniciales si ya existe
    if not cover_df.empty:
        current = cover_df.iloc[0]
        st.info("✏️ Carta existente: puedes editar los campos abajo.")
    else:
        current = pd.Series({"header": "", "address": "", "date": "", "body": "", "end": "", "sign": ""})
        st.info("🆕 Nueva carta: llena los campos para crearla.")

    # === Formulario ===
    with st.form("cover_letter_form"):
        st.markdown("### 🧾 Información de la carta")

        header = st.text_area("Header", value=current["header"], height=100)
        address = st.text_area("Address", value=current["address"], height=80)
        date_str = st.text_input("Date (YYYY-MM-DD)", value=str(current["date"]) if pd.notna(current["date"]) else "")
        body = st.text_area("Body", value=current["body"], height=250)
        end_text = st.text_area("End", value=current["end"], height=80)
        sign = st.text_area("Sign", value=current["sign"], height=60)

        submitted = st.form_submit_button("💾 Guardar carta")

        if submitted:
            try:
                with conn.cursor() as cur:
                    # 1️⃣ Intentar insertar si no existe
                    cur.execute(f'''
                        INSERT INTO "{schema}".cover_letters
                        (job, lang, company_name, header, address, date, body, "end", sign)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING;
                    ''', (
                        job_selected, lang_selected, company_selected,
                        header, address, date_str if date_str else None, body, end_text, sign
                    ))

                    # 2️⃣ Actualizar siempre (si ya existía, se actualiza)
                    cur.execute(f'''
                        UPDATE "{schema}".cover_letters
                        SET header = %s, address = %s, date = %s, body = %s, "end" = %s, sign = %s
                        WHERE job = %s AND lang = %s AND company_name = %s;
                    ''', (
                        header, address, date_str if date_str else None, body, end_text, sign,
                        job_selected, lang_selected, company_selected
                    ))

                    conn.commit()

                st.success("✅ Carta guardada correctamente.")

            except Exception as e:
                st.error(f"❌ Error al guardar la carta: {e}")
elif vista == "Job tracker":
    st.title("📌 Job tracker")

    # === Cargar tabla job_tracker ===
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
            conn
        )
    except Exception as e:
        st.error(f"❌ Error al cargar job_tracker: {e}")
        st.stop()

    if jt_df.empty:
        st.warning("⚠️ No hay registros en job_tracker. Crea aplicaciones primero.")
        st.stop()

    # === Mostrar tabla sólo con las columnas pedidas ===
    st.subheader("📋 Registros actuales")
    st.dataframe(
        jt_df[
            [
                "company",
                "contact_person",
                "reach_out_day",
                "stage",
                "type",
                "position",
                "posting_url",
                "message",
                "next_stage_deadline",
            ]
        ],
        use_container_width=True,
    )

    st.markdown("---")
    st.markdown("### ✏️ Editar un registro")

    # === Selector company – position ===
    labels = [
        f"{row.company} — {row.position}"
        for _, row in jt_df.iterrows()
    ]
    indices = list(range(len(labels)))

    selected_index = st.selectbox(
        "Selecciona la company–position a editar:",
        indices,
        format_func=lambda i: labels[i],
    )

    selected_row = jt_df.iloc[selected_index]

    # Campos de sólo lectura
    st.text_input("Company", value=selected_row["company"], disabled=True)
    st.text_input("Position", value=selected_row["position"], disabled=True)

    # Valores actuales (manejar NULL/NaN/NaT)
    def safe_str(value):
        return str(value) if pd.notna(value) else ""

    contact_person_val = safe_str(selected_row["contact_person"])
    reach_out_day_val = safe_str(selected_row["reach_out_day"])
    stage_val = safe_str(selected_row["stage"])
    type_val = safe_str(selected_row["type"])
    posting_url_val = safe_str(selected_row["posting_url"])
    message_val = safe_str(selected_row["message"])
    next_deadline_val = safe_str(selected_row["next_stage_deadline"])

    # === Formulario de edición ===
    with st.form("job_tracker_edit_form"):
        contact_person = st.text_input("Contact person", value=contact_person_val)
        reach_out_day_str = st.text_input(
            "Reach out day (YYYY-MM-DD)",
            value=reach_out_day_val,
        )
        stage = st.text_input("Stage", value=stage_val)
        type_field = st.text_input("Type", value=type_val)
        posting_url = st.text_input("Posting URL", value=posting_url_val)
        message = st.text_area("Message", value=message_val, height=150)
        next_stage_deadline_str = st.text_input(
            "Next stage deadline (YYYY-MM-DD)",
            value=next_deadline_val,
        )

        submitted_jt = st.form_submit_button("💾 Guardar cambios")

    if submitted_jt:
        try:
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

            st.success("✅ Registro actualizado correctamente.")

        except Exception as e:
            st.error(f"❌ Error al actualizar el registro: {e}")
