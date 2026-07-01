
import os
from dotenv import load_dotenv
from colorama import Fore, Style, init
import pandas as pd
from docx import Document
import yaml
from sqlalchemy import create_engine
import subprocess
from datetime import datetime

class CV_GENERATION():
    def open_folder(self, folder_path):
        """Open a folder in the default file manager, cross-platform."""
        if os.name == 'nt':  # Windows
            os.startfile(folder_path)
        elif os.uname().sysname == 'Darwin':  # macOS
            subprocess.call(['open', folder_path])
        else:  # Linux or other
            subprocess.call(['xdg-open', folder_path])
        
    def get_cv_files(self):
        import hashlib
        from sqlalchemy import text
        
        def calculate_hash(file_path):
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()

        # 1. Scan filesystem
        scanned_files = {} # hash -> filename
        if not os.path.exists(self.templates_path):
            os.makedirs(self.templates_path, exist_ok=True)
            
        for f in os.listdir(self.templates_path):
            if f.endswith('.docx') and not f.startswith('~'):
                path = os.path.join(self.templates_path, f)
                f_hash = calculate_hash(path)
                scanned_files[f_hash] = f

        # 2. Get connection
        db_url = self.data_access.get('DB_URL') or os.getenv("DB_POSTGRESQL")
        if not db_url:
            print("❌ No DB_URL found")
            return 0, 0, 0
            
        engine = create_engine(db_url)
        schema = "consulting_tracker" 
        
        with engine.connect() as conn:
            # 3. Get existing files
            query = text(f'SELECT file_name, file_hash, active_status FROM "{schema}".dim_file')
            df_existing = pd.read_sql(query, conn)
            
            existing_hashes = set(df_existing['file_hash'].tolist())
            active_hashes_in_db = set(df_existing[df_existing['active_status'] == True]['file_hash'].tolist())
            
            new_hashes = set(scanned_files.keys()) - existing_hashes
            hashes_to_deactivate = active_hashes_in_db - set(scanned_files.keys())
            hashes_to_reactivate = (set(scanned_files.keys()) & existing_hashes) - active_hashes_in_db
            
            # 4. Process
            for h in new_hashes:
                fname = scanned_files[h]
                # Heuristic: if 'cover' is in the name, mark as cover letter, else cv
                ftype = 'cover letter' if 'cover' in fname.lower() else 'cv'
                conn.execute(text(f"""
                    INSERT INTO "{schema}".dim_file (file_name, file_hash, file_type, active_status)
                    VALUES (:name, :hash, :type, True)
                """), {"name": fname, "hash": h, "type": ftype})
            
            for h in hashes_to_deactivate:
                conn.execute(text(f"""
                    UPDATE "{schema}".dim_file SET active_status = False WHERE file_hash = :hash
                """), {"hash": h})
                
            for h in hashes_to_reactivate:
                conn.execute(text(f"""
                    UPDATE "{schema}".dim_file SET active_status = True, file_name = :name WHERE file_hash = :hash
                """), {"name": scanned_files[h], "hash": h})
            
            conn.commit()
            return len(new_hashes), len(hashes_to_deactivate), len(hashes_to_reactivate)

    def postgre_to_docx(self, doc_type, one_row_df, ui_log=None):
        def _log(msg: str, level: str = "info"):
            if ui_log is not None:
                ui_log(msg, level)
            else:
                print(msg)       
        """
        New workflow:
        - If df_cv is None: keep legacy flow (load all + user chooses desired row).
        - If df_cv is provided (expected 1-row DataFrame): generate CV directly for that row.
        - Cover letter is fetched by (job, lang, company_name). If it has no content beyond PK cols, skip.
        """
        # --- validate doc_type ---
        allowed_docs = {"coverletter", "cv"}
        doc_type = (doc_type or "").strip().lower()

        if doc_type not in allowed_docs:
            _log(f"Error: doc_type debe ser uno de: {', '.join(sorted(allowed_docs))}", "error")
            return False

        init(autoreset=True)
        _log(f"{Fore.BLUE}CARRIER MANAGEMENT{Style.RESET_ALL}")

        os.makedirs(self.templates_path, exist_ok=True)
        os.makedirs(self.output_path, exist_ok=True)

        # --- validate DF ---
        if one_row_df is None or getattr(one_row_df, "empty", True):
            _log("❌ one_row_df vacío. No hay registro para generar documentos.", "error")
            return False

        if len(one_row_df) != 1:
            _log("⚠️ El dataframe trae más de una fila. Se usará la primera.", "warning")
            one_row_df = one_row_df.iloc[[0]].copy()

        required_cols = ["job", "lang", "company_name"]
        missing = [c for c in required_cols if c not in one_row_df.columns]
        if missing:
            _log(f"❌ Faltan columnas requeridas en one_row_df: {missing}", "error")
            return False

        # --- base fields ---
        job_raw = one_row_df["job"].values[0] or ""
        lang = one_row_df["lang"].values[0] or ""
        company_name = one_row_df["company_name"].values[0] or ""

        # sanitize job for filename
        job = " ".join(str(job_raw).split())
        for ch in [' ', '/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            job = job.replace(ch, "_")

        # --- generate requested document ---
        if doc_type == "cv":
            _log(f"{Fore.CYAN}📄 Generando currículum...{Style.RESET_ALL}")

            cv_files_val = ""
            if "cv_files" in one_row_df.columns:
                cv_files_val = one_row_df["cv_files"].values[0] or ""

            if str(cv_files_val).strip():
                _log("Usando CV template vinculado...", "info")
                template_path = os.path.join(self.templates_path, str(cv_files_val).strip())
            else:
                template_path = os.path.join(self.templates_path, f"Curriculum_{lang}.docx")

            if not os.path.exists(template_path):
                _log(f"❌ No se encontró el template en: {template_path}", "error")
                return False

            output_path = os.path.join(self.output_path, f"{job}_JACJ_CV.docx")
            self.populate_document(template_path, one_row_df, output_path)
            self.open_word_path(output_path)
            _log("✅ CV generado.", "success")
            return True

        elif doc_type == "coverletter":
            raw_date = one_row_df["date"].values[0]

            # Convert to a real datetime, then to python date
            dt_date = pd.to_datetime(raw_date, errors="coerce")

            if pd.isna(dt_date):
                # handle missing/invalid date
                day = month_num = year = None
            else:
                day = int(dt_date.day)
                month_num = int(dt_date.month)
                year = int(dt_date.year) 
            date_issued = ""       
            months = {
                'English': ["January", "February", "March", "April", "May", "June",
                            "July", "August", "September", "October", "November", "December"],
                'Spanish': ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
                'French': ["janvier", "février", "mars", "avril", "mai", "juin",
                        "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
            }
            
            if lang == 'English':
                suffix = 'th'
                if day in [1, 21, 31]:
                    suffix = 'st'
                elif day in [2, 22]:
                    suffix = 'nd'
                elif day in [3, 23]:
                    suffix = 'rd'
                date_issued = f"Mexico City, {months['English'][month_num-1]} {day}{suffix}, {year}"

            elif lang == 'Spanish':
                date_issued = f"Ciudad de México, {day} de {months['Spanish'][month_num-1].capitalize()} de {year}"

            elif lang == 'French':
                date_issued = f"Mexico, le {day} {months['French'][month_num-1].capitalize()} {year}"
            one_row_df['date_issued']= date_issued

            _log(f"{Fore.CYAN}📄 Generando cover letter...{Style.RESET_ALL}")

            template_path = os.path.join(self.templates_path, f"Cover_letter_{lang}.docx")
            if not os.path.exists(template_path):
                _log(f"❌ No se encontró el template en: {template_path}", "error")
                return False

            output_path = os.path.join(self.output_path, f"{job}_JACJ_CLetter.docx")
            self.populate_document(template_path, one_row_df, output_path)
            self.open_word_path(output_path)
            _log("✅ Cover letter generada.", "success")
            return True  


    def open_word_path(self, path):
        """Open a file in the default application, cross-platform."""
        if os.name == 'nt':
            os.startfile(path)
        elif os.uname().sysname == 'Darwin':
            subprocess.call(['open', path])
        else:
            subprocess.call(['xdg-open', path])

    def populate_document(self, template_doc, df, output_file):
        for _, row in df.iterrows():
            job = str(row.get("job", "Unknown"))
            try:
                doc = Document(template_doc)

                # 🔹 Reemplazar placeholders en párrafos con soporte para saltos de línea y bullets
                for p in doc.paragraphs:
                    for key in df.columns:
                        placeholder = f"{{{key}}}"
                        if placeholder in p.text:
                            value = str(row.get(key, "")).replace('\\n', '\n')
                            parts = value.split('\n')

                            # Reemplaza el placeholder por la primera línea
                            p.text = p.text.replace(placeholder, parts[0])

                            # Si hay más líneas, las inserta como nuevos párrafos con el mismo estilo
                            if len(parts) > 1:
                                p_element = p._element
                                body_element = doc._body._element
                                index = list(body_element).index(p_element)

                                for part in parts[1:]:
                                    new_p = doc.add_paragraph(part, style=p.style.name)
                                    new_p_element = new_p._element
                                    body_element.remove(new_p_element)
                                    body_element.insert(index + 1, new_p_element)
                                    index += 1
                doc.save(output_file)
                doc_type = "Carta" if "CLetter" in output_file else "Curriculum"
                print(f"{Fore.GREEN}✅ {doc_type} generado: {output_file}{Style.RESET_ALL}")

            except Exception as e:
                print(f"{Fore.RED}❌ Error generando {job}: {e}{Style.RESET_ALL}")
         

    def __init__(self, working_folder, data_access):
        self.working_folder = working_folder
        os.makedirs(self.working_folder, exist_ok=True)
        self.data_access = data_access
        self.output_path = os.path.join(self.working_folder, "Output CVs")
        os.makedirs(self.output_path, exist_ok=True)
        self.templates_path = os.path.join(self.working_folder, "CV Templates")
        
if __name__ == "__main__":
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    env_file = os.path.join(env_path, '.env')
    folder_name = "MAIN_PATH"
    db_key = "DB_URL"
    
    working_folder = "."
    pg_dict = {}

    if os.path.exists(env_file):
        load_dotenv(dotenv_path=env_file)
        working_folder = os.getenv(folder_name)
        pg_dict = {"DB_URL": os.getenv(db_key)} 

    yaml_path = os.path.join(env_path, 'config', 'config.yml')
    with open(yaml_path, 'r') as file:
        data_access = yaml.safe_load(file)
        if data_access is None:
            data_access = {}
        data_access.update(pg_dict)  # ⚠️ Esto solo funciona si data_access es una lista

    app = CV_GENERATION(working_folder, data_access)
    app.postgre_to_docx()