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
import io
from datetime import datetime
import datetime as dt


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

    # === Load FULL table for safe editing ===
    try:
        df_full = pd.read_sql(f'''
            SELECT *
            FROM "{schema}".applications
            ORDER BY created_at DESC;
        ''', conn)
    except Exception:
        df_full = pd.DataFrame()

    # === Display only selected columns ===
    if df_full is not None and not df_full.empty:
        show_cols = [c for c in cols_show if c in df_full.columns]
        st.dataframe(df_full[show_cols], use_container_width=True)

        # Export view (only shown cols)
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

    # === Build selector using application_id ===
    selected_pk = None
    original = {}

    if df_full is not None and not df_full.empty and PK in df_full.columns:
        options = df_full[[PK, "job", "company_name", "created_at"]].copy()
        options["label"] = (
            options["job"].fillna("").astype(str)
            + " | "
            + options["company_name"].fillna("").astype(str)
            + " | "
            + options["created_at"].astype(str)
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
        st.warning(f"No encontré columna '{PK}'. No se puede editar de forma segura.")
        selected_pk = None
        original = {}

    # === Helper: normalize values to compare ===
    def _norm(v):
        return "" if v is None else v

    # === Edit/Create form ===
    # --- options (fuera o justo antes del form) ---
    try:
        lang_opts = pd.read_sql(
            f'SELECT lang FROM "{schema}".languages ORDER BY lang;',
            conn
        )["lang"].dropna().astype(str).tolist()
    except Exception:
        lang_opts = []

    try:
        company_opts = pd.read_sql(
            f'SELECT company_name FROM "{schema}".companies ORDER BY company_name;',
            conn
        )["company_name"].dropna().astype(str).tolist()
    except Exception:
        company_opts = []

    status_opts = ["applied", "interviewing", "offered", "rejected"]

    with st.form("applications_form", clear_on_submit=False):

        # --- job (libre) ---
        job_val = st.text_input("Job position", value=original.get("job", "") or "")

        # --- lang (constraint: languages) ---
        default_lang = (original.get("lang") or "")
        if default_lang and default_lang not in lang_opts:
            lang_opts = [default_lang] + lang_opts  # evita crash si quedó un valor legacy

        lang_idx = lang_opts.index(default_lang) if default_lang in lang_opts else 0
        lang_val = st.selectbox("Language", options=lang_opts, index=lang_idx if lang_opts else 0)

        # --- company_name (constraint: companies) ---
        default_company = (original.get("company_name") or "")
        if default_company and default_company not in company_opts:
            company_opts = [default_company] + company_opts

        comp_idx = company_opts.index(default_company) if default_company in company_opts else 0
        company_name_val = st.selectbox("Company name", options=company_opts, index=comp_idx if company_opts else 0)

        # --- company_type (constraint: companies filtered by company_name) ---
        try:
            company_type_opts = pd.read_sql(
                f'''
                SELECT company_type
                FROM "{schema}".companies
                WHERE company_name = %(company_name)s
                ORDER BY company_type;
                ''',
                conn,
                params={"company_name": company_name_val}
            )["company_type"].dropna().astype(str).tolist()
        except Exception:
            company_type_opts = []

        default_company_type = (original.get("company_type") or "")
        if default_company_type and default_company_type not in company_type_opts:
            company_type_opts = [default_company_type] + company_type_opts

        ct_idx = company_type_opts.index(default_company_type) if default_company_type in company_type_opts else 0
        company_type_val = st.selectbox(
            "Company type",
            options=company_type_opts if company_type_opts else [""],
            index=ct_idx if company_type_opts else 0,
            disabled=(not company_type_opts)  # si no hay tipos, bloquea para evitar basura
        )

        # --- status (constraint: CHECK) ---
        default_status = (original.get("status") or "")
        if default_status and default_status not in status_opts:
            status_opts = [default_status] + status_opts  # por si hay legacy

        st_idx = status_opts.index(default_status) if default_status in status_opts else 0
        status_val = st.selectbox("Status", options=status_opts, index=st_idx)

        # --- cv_files (constraint: cv_files filtered by lang) ---
        try:
            cv_file_opts = pd.read_sql(
                f'''
                SELECT cv_file
                FROM "{schema}".cv_files
                WHERE lang = %(lang)s
                ORDER BY cv_file;
                ''',
                conn,
                params={"lang": lang_val}
            )["cv_file"].dropna().astype(str).tolist()
        except Exception:
            cv_file_opts = []

        # permitir vacío (sin template vinculado)
        cv_file_opts = [""] + cv_file_opts

        default_cv_file = (original.get("cv_files") or "")
        if default_cv_file and default_cv_file not in cv_file_opts:
            cv_file_opts = [default_cv_file] + cv_file_opts

        cv_idx = cv_file_opts.index(default_cv_file) if default_cv_file in cv_file_opts else 0
        cv_files_val = st.selectbox("CV file (optional)", options=cv_file_opts, index=cv_idx)

        # --- long text fields (libres) ---
        education1_val = st.text_area("Education 1", value=original.get("education1", "") or "", height=90)
        education2_val = st.text_area("Education 2", value=original.get("education2", "") or "", height=90)
        education3_val = st.text_area("Education 3", value=original.get("education3", "") or "", height=90)

        experience1_val = st.text_area("Experience 1", value=original.get("experience1", "") or "", height=120)
        experience2_val = st.text_area("Experience 2", value=original.get("experience2", "") or "", height=120)
        experience3_val = st.text_area("Experience 3", value=original.get("experience3", "") or "", height=120)

        skills_val = st.text_area("Skills", value=original.get("skills", "") or "", height=120)
        interests_val = st.text_area("Interests", value=original.get("interests", "") or "", height=90)

        # --- final dict (lo que ya usas para diff/update/insert) ---
        new_values = {
            "job": job_val,
            "lang": lang_val,
            "company_name": company_name_val,
            "company_type": company_type_val,
            "status": status_val,
            "cv_files": cv_files_val,

            "education1": education1_val,
            "education2": education2_val,
            "education3": education3_val,
            "experience1": experience1_val,
            "experience2": experience2_val,
            "experience3": experience3_val,
            "skills": skills_val,
            "interests": interests_val,
        }

        col_a, col_b = st.columns(2)
        with col_a:
            submit_update = st.form_submit_button("💾 Guardar cambios")
        with col_b:
            submit_insert = st.form_submit_button("➕ Crear nueva aplicación")

    # === UPDATE: only changed columns ===
    if submit_update:
        if selected_pk is None:
            st.error("Selecciona una aplicación existente para editar.")
        else:
            changed = {
                k: v for k, v in new_values.items()
                if _norm(v) != _norm(original.get(k))
            }

            if not changed:
                st.info("No hay cambios para guardar.")
            else:
                set_clause = ", ".join([f'"{k}" = %({k})s' for k in changed.keys()])
                params = dict(changed)
                params[PK] = selected_pk

                sql = f'''
                    UPDATE "{schema}".applications
                    SET {set_clause}
                    WHERE "{PK}" = %({PK})s;
                '''

                try:
                    with conn.cursor() as cur:
                        cur.execute(sql, params)
                    conn.commit()
                    st.success(f"Actualizado ✅ ({len(changed)} campo(s))")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error al actualizar: {e}")

    # === INSERT: insert only provided fields ===
    if submit_insert:
        # optional: you can enforce required fields here
        insert_cols = list(new_values.keys())
        cols_sql = ", ".join([f'"{c}"' for c in insert_cols])
        placeholders = ", ".join([f"%({c})s" for c in insert_cols])

        sql = f'''
            INSERT INTO "{schema}".applications ({cols_sql})
            VALUES ({placeholders});
        '''
        try:
            with conn.cursor() as cur:
                cur.execute(sql, new_values)
            conn.commit()
            st.success("Creada ✅")
            st.rerun()
        except Exception as e:
            conn.rollback()
            st.error(f"Error al crear: {e}")

    # === CV buttons (outside form) ===
    log_box = st.empty()


    from Library.CV_generation import CV_GENERATION
    gen = CV_GENERATION(working_folder, data_access)

    if st.button("📄 Generar CV para este registro", disabled=(selected_pk is None)):
        try:
            df_cv = df_full[df_full["application_id"] == selected_pk].copy()

            if df_cv.empty:
                ui_log("No se encontró el registro seleccionado en memoria.", "error")
            else:
                ui_log("Iniciando generación de CV...", "info")
                
                gen.postgre_to_docx("cv", df_cv, ui_log=ui_log)   # 👈 pass logger
                ui_log("Proceso de generación ejecutado ✅", "success")
        except Exception as e:
            ui_log(f"Error generando CV: {e}", "error")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📁 Abre carpeta de plantillas curriculum"):
            templates_path = os.path.join(working_folder, "CV Templates")
            gen.open_folder(templates_path)

    with col2:
        if st.button("📁 Abre carpeta de archivos finales"):
            gen.open_folder(gen.output_path)        
    
elif vista == "Cover Letters":
    # --- UI logger for this vista ---
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
    
    # === Cargar combinaciones desde cover_letters (única fuente de verdad) ===
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

    # Crear lista legible para selección
    combo_options = [
        f"{row.job} — {row.lang} — {row.company_name}" 
        for _, row in covers_df.iterrows()
    ]
    
    # Initialize session state for selected index if not exists
    if 'cover_letter_selected_index' not in st.session_state:
        st.session_state.cover_letter_selected_index = 0
    
    selected_index = st.selectbox(
        "Selecciona una aplicación (Job — Language — Company):", 
        range(len(combo_options)),
        format_func=lambda i: combo_options[i],
        index=st.session_state.cover_letter_selected_index,
        key='cover_selector'
    )
    
    # Update session state when selection changes
    st.session_state.cover_letter_selected_index = selected_index

    # Obtener la fila seleccionada directamente
    current = covers_df.iloc[selected_index]
    
    # Info sobre el estado de la carta
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

        # Handle date default value
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
                cover_id = int(current["cover_id"])  # Convert numpy.int64 to Python int

                # Simple UPDATE of all fields
                with conn.cursor() as cur:
                    cur.execute(
                        f'''
                        UPDATE "{schema}".cover_letters
                        SET header = %s, 
                            address = %s, 
                            date = %s, 
                            body = %s, 
                            "end" = %s, 
                            sign = %s
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
    
    from Library.CV_generation import CV_GENERATION        
    gen = CV_GENERATION(working_folder, data_access)
    
    if st.button("Crear Cover Letter"):
        try:
            # IMPORTANT: Reload ALL data fresh from DB before generating
            covers_df_fresh = pd.read_sql(
                f'''
                SELECT cover_id, job, lang, company_name, 
                       header, address, date, body, "end", sign
                FROM "{schema}".cover_letters
                ORDER BY cover_id DESC;
                ''',
                conn
            )
            
            # Get the currently selected combination from the fresh data
            job_sel = covers_df_fresh.iloc[selected_index]["job"]
            lang_sel = covers_df_fresh.iloc[selected_index]["lang"]
            company_sel = covers_df_fresh.iloc[selected_index]["company_name"]
            
            # Query again for this specific combination (ensures we have latest)
            query = f'''
                SELECT cover_id, job, lang, company_name,
                       header, address, date, body, "end", sign
                FROM "{schema}".cover_letters
                WHERE job = %s AND lang = %s AND company_name = %s;
            '''
            
            cover_df_latest = pd.read_sql(
                query, 
                conn, 
                params=(job_sel, lang_sel, company_sel)
            )

            if cover_df_latest.empty:
                ui_log("No existe cover letter para esta combinación.", "error")
            else:
                row = cover_df_latest.iloc[0]

                df_cl = pd.DataFrame([{
                    "job": row["job"],
                    "lang": row["lang"],
                    "company_name": row["company_name"],
                    "header": row["header"] if pd.notna(row["header"]) else "",
                    "address": row["address"] if pd.notna(row["address"]) else "",
                    "date": row["date"] if pd.notna(row["date"]) else None,
                    "body": row["body"] if pd.notna(row["body"]) else "",
                    "end": row["end"] if pd.notna(row["end"]) else "",
                    "sign": row["sign"] if pd.notna(row["sign"]) else "",
                }])

                ui_log("Iniciando generación de Cover Letter...", "info")
                gen.postgre_to_docx("coverletter", df_cl, ui_log=ui_log)
                ui_log("Cover Letter generada ✅", "success")

        except Exception as e:
            ui_log(f"Error generando Cover Letter: {e}", "error")

            
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📁 Abre carpeta de plantillas cover letters"):
            templates_path = os.path.join(working_folder, "CV Templates")  # same folder
            gen.open_folder(templates_path)

    with col2:
        if st.button("📁 Abre carpeta de archivos finales"):
            gen.open_folder(gen.output_path)

  


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
