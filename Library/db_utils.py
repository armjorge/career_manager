import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse
import streamlit as st
from sqlalchemy import create_engine

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
        self.schema = 'consulting_tracker'
        
        # Create directories
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs(self.templates_path, exist_ok=True)

    def record_exists(self, table, column, value):
        """Checks if a value exists in a table (case-insensitive)."""
        query = f"SELECT COUNT(*) FROM \"{self.schema}\".{table} WHERE LOWER({column}) = LOWER(%s);"
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (value,))
                exists = cur.fetchone()[0] > 0
            return exists
        finally:
            conn.close()

    def insert_record(self, table, data):
        """Generic insert with conflict avoidance (though we check first)."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO \"{self.schema}\".{table} ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;"
        
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, list(data.values()))
            conn.commit()
            return True
        except Exception as e:
            st.error(f"❌ Database error: {e}")
            return False
        finally:
            conn.close()

    def update_record(self, table, data, condition_column, condition_value):
        """Generic update with last_modification update if column exists."""
        set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
        # We try to set last_modification = CURRENT_TIMESTAMP if it's not in data
        # Note: This assumes the table HAS last_modification column if we want to auto-update it.
        # For simplicity in this generic method, we'll just execute what's given, 
        # but for this specific task I'll make sure it's updated.
        query = f"UPDATE \"{self.schema}\".{table} SET {set_clause}, last_modification = CURRENT_TIMESTAMP WHERE {condition_column} = %s;"
        
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, list(data.values()) + [condition_value])
            conn.commit()
            return True
        except Exception as e:
            st.error(f"❌ Database error: {e}")
            return False
        finally:
            conn.close()

    @st.cache_resource
    def get_engine(_self):
        """Return a cached SQLAlchemy engine (used for pandas.read_sql)."""
        db_url = os.getenv("DB_POSTGRESQL")
        if not db_url:
            st.error("❌ DB_POSTGRESQL not found in environment variables!")
            st.stop()
        try:
            engine = create_engine(db_url, pool_pre_ping=True)
            return engine
        except Exception as e:
            st.error(f"❌ Error creating SQLAlchemy engine: {e}")
            st.stop()

    def get_db_connection(self):
        """
        Create a fresh psycopg2 connection. Not cached — callers should request
        a new connection right before doing cursor/commit/rollback operations.
        """
        db_url = os.getenv("DB_POSTGRESQL")
        if not db_url:
            st.error("❌ DB_POSTGRESQL not found in environment variables!")
            st.stop()
        parsed = urlparse(db_url)
        try:
            conn = psycopg2.connect(
                dbname=parsed.path.lstrip('/'),
                user=parsed.username,
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port
            )
            conn.autocommit = False
            return conn
        except Exception as e:
            st.error(f"❌ Error opening psycopg2 connection: {e}")
            st.stop()
        
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
