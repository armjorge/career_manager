import os
import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse
import streamlit as st

class DB_UTILS():
    def __init__(self, working_folder=None):
        # 1. Dynamically find the project root (2 levels up from Library/db_utils.py)
        self.BASE_PATH = Path(__file__).resolve().parent.parent
        
        # 2. Load environment variables immediately
        env_file = self.BASE_PATH / ".env"
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)
        
        # 3. Setup Working Folder (use .env value or fallback to a temp folder)
        if working_folder is None:
            working_folder = os.getenv("MAIN_PATH", str(self.BASE_PATH / "temp_files"))
            
        self.working_folder = working_folder
        self.output_path = os.path.join(self.working_folder, "Output CVs")
        self.templates_path = os.path.join(self.working_folder, "CV Templates")
        self.schema = 'career_accelerator'
        
        # Create directories
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs(self.templates_path, exist_ok=True)

    @st.cache_resource
    def get_db_connection(_self):
        # Use the EXACT key from your .env
        db_url = os.getenv("DB_POSTGRESQL")
        
        if not db_url:
            st.error("❌ DB_POSTGRESQL not found in environment variables!")
            st.stop()
            
        parsed = urlparse(db_url)
        return psycopg2.connect(
            dbname=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port
        )
        
    def cv_templates_output(self):
        # Rutas usadas en tu lógica
        output_path = os.path.join( self.working_folder, "Output CVs")
        os.makedirs(output_path, exist_ok=True)
        templates_path = os.path.join(self.working_folder, "CV Templates")
        os.makedirs(templates_path, exist_ok=True)
        print('returning output_path and templates_path')
        return output_path, templates_path

    
    @st.cache_resource
    def mongo_db_connexion(_self):
        from pymongo import MongoClient
        client = MongoClient(os.getenv("DB_MONGO"))
        # Return the specific collection directly
        return client['applications']['pdfs']
