import os
from dotenv import load_dotenv
from colorama import Fore, Style, init
from Library.yaml_creator import YAMLCREATOR
from Library.chrome_helper import CHROME_HELPER
import pandas as pd
from docx import Document
import yaml
from sqlalchemy import create_engine
import sys
import subprocess



class CARRIER_MANAGEMENT:
    # Orchstrate the main flow
    def menu(self):
        init(autoreset=True)
        print(f"{Fore.BLUE}CV MANAGEMENT{Style.RESET_ALL}")
        # Initialize the main components
        print("""Generación de CVs a partir de datos en PostgreSQL
              1) Inicializar la base en SQL 
              2) Poblar con datos
              3) Reemplazar datos en word. 
              """)
        user_choice = input("Seleccione una opción (1-3): ")

        if user_choice == "1":
            print("Inicializando base de datos en PostgreSQL...")
            from Library.SQL_management import CSV_TO_SQL
            CSV_TO_SQL(self.working_folder, self.data_access).csv_to_sql_process()
        elif user_choice == "2":
            print("Poblando la base de datos con datos de ejemplo...")
            streamlit_path = os.path.join(".","concept_filing.py")
            try:
                subprocess.run([sys.executable, "-m", "streamlit", "run", streamlit_path], check=True)
            except Exception as e:
                print(f"❌ Error al ejecutar Streamlit: {e}")            
        elif user_choice == "3":
            from Library.CV_generation import CV_GENERATION
            CV_GENERATION(self.working_folder, self.data_access).postgre_to_docx()

        else: 
            print("Opción no válida. Saliendo.")
            
    def __init__(self):
        self.folder_root = self.get_root_path()
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        env_file = os.path.join(env_path, '.env')
        folder_name = "MAIN_PATH"
        db_key = "DB_URL"
        
        self.working_folder = "."
        pg_dict = {}

        if os.path.exists(env_file):
            load_dotenv(dotenv_path=env_file)
            self.working_folder = os.getenv(folder_name)
            pg_dict = {"DB_URL": os.getenv(db_key)} 

        yaml_path = os.path.join(env_path, 'config', 'config.yml')
        with open(yaml_path, 'r') as file:
            data_access = yaml.safe_load(file)
            if data_access is None:
                data_access = {}
            data_access.update(pg_dict)  # ⚠️ Esto solo funciona si data_access es una lista
        os.makedirs(self.working_folder, exist_ok=True)
        self.data_yaml = YAMLCREATOR(self.working_folder).data
        # Initialize Sprint 1.1: Get product list
        self.chrome_helper = CHROME_HELPER()
        root_path = os.path.join(os.path.dirname(__file__))
        config_path = os.path.join(root_path, "config", "config.yml")
        with open(config_path, 'r') as f:
            self.data_access = yaml.safe_load(f)    
            env_file = ".env"
            load_dotenv(env_file)
            pg_dict = {"DB_URL": os.getenv("DB_URL")}
            self.data_access.update(pg_dict)
        self.output_path = os.path.join(self.working_folder, "Output CVs")
        os.makedirs(self.output_path, exist_ok=True)
        
    # Get the root path
    def get_root_path(self):
        # Get the directory where main.py lives (repo folder)
        repo_path = os.path.dirname(os.path.abspath(__file__))
        repo_name = os.path.basename(repo_path)
        print(f"Current script path: {os.path.abspath(__file__)}")
        env_file = ".env"
        # Load .env if it exists
        full_repo_path = None
        if os.path.exists(env_file):
            load_dotenv(env_file)
            full_repo_path = os.getenv("MAIN_PATH") or os.getenv("Main_path")
            if not full_repo_path:
                with open(env_file, "r") as env_handle:
                    for line in env_handle:
                        stripped = line.strip()
                        if not stripped or stripped.startswith("#"):
                            continue
                        if stripped.lower().startswith("main_path"):
                            if ":" in stripped:
                                _, value = stripped.split(":", 1)
                            elif "=" in stripped:
                                _, value = stripped.split("=", 1)
                            else:
                                value = ""
                            full_repo_path = value.strip()
                            break
        if not full_repo_path:
            path_user = input("Please paste the path where the repo files will be created or enter to use the root: ")
            if path_user.strip():
                if os.path.exists(path_user):
                    full_repo_path = os.path.join(path_user, repo_name)
                else:
                    print("Path does not exist, using root")
                    full_repo_path = os.path.join(repo_path, repo_name)
            else:
                full_repo_path = os.path.join(repo_path, repo_name)
            os.makedirs(full_repo_path, exist_ok=True)
            # Write to .env
            with open(env_file, "a+") as f:
                f.seek(0)
                content = f.read()
                if "MAIN_PATH=" not in content:
                    f.write(f"MAIN_PATH={full_repo_path}\n")
            # Check if full_repo_path is inside repo_path
            if full_repo_path.startswith(repo_path + os.sep):
                gitignore_path = ".gitignore"
                with open(gitignore_path, "r") as f:
                    content = f.read()
                if f"{repo_name}/" not in content:
                    with open(gitignore_path, "a") as f:
                        f.write(f"{repo_name}/\n")
        return full_repo_path


if __name__ == "__main__":
    app = CARRIER_MANAGEMENT()
    app.menu()

    