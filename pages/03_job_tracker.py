import streamlit as st
import pandas as pd
import os
import sys


# 1) Setup Path to find Library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Library.db_utils import DB_UTILS

# 2) Page Config
st.set_page_config(page_title="📌 Job Tracker", layout="wide")

# 3) Initialize DB via Session State
if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
schema = db.schema
conn = db.get_db_connection()
engine = db.get_engine()

# 4) Navigation
st.page_link("concept_filing.py", label="🏠 Volver al panel principal")
st.write("---")

st.title("📌 Applications")

# === Load applications table (only needed cols) ===
try:
    apps_df = pd.read_sql(
        f"""
        SELECT
            application_id,
            job,
            company_type,
            company_name,
            created_at,
            status,
            lang
        FROM "{schema}".applications
        ;
        """,
        engine
    )
except Exception as e:
    st.error(f"❌ Error al cargar applications: {e}")
    st.stop()

if apps_df.empty:
    st.warning("⚠️ No hay registros en applications. Agrega aplicaciones primero.")
    st.stop()

# Normalize datetimes
apps_df["created_at"] = pd.to_datetime(apps_df["created_at"])

st.markdown("---")

# === Filters ===
st.subheader("Filtros")
col1, col2, col3, col4 = st.columns([2,2,2,2])

# Date range filter defaults
min_date = apps_df["created_at"].dt.date.min()
max_date = apps_df["created_at"].dt.date.max()
date_range = col1.date_input("Rango de fechas (created_at)", value=(min_date, max_date))
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = min_date
    end_date = max_date

# Multi-select filters
jobs = sorted(apps_df["job"].dropna().unique().tolist())
company_types = sorted(apps_df["company_type"].dropna().unique().tolist())
company_names = sorted(apps_df["company_name"].dropna().unique().tolist())
statuses = sorted(apps_df["status"].dropna().unique().tolist())
langs = sorted(apps_df["lang"].dropna().unique().tolist())

sel_jobs = col2.multiselect("Job", options=jobs)
sel_company_type = col3.multiselect("Company type", options=company_types)
sel_company_name = col4.multiselect("Company name", options=company_names)
sel_status = col1.multiselect("Status", options=statuses)
sel_lang = col2.multiselect("Lang", options=langs)

# Apply filters
mask = (
    (apps_df["created_at"].dt.date >= start_date) &
    (apps_df["created_at"].dt.date <= end_date)
)
if sel_jobs:
    mask &= apps_df["job"].isin(sel_jobs)
if sel_company_type:
    mask &= apps_df["company_type"].isin(sel_company_type)
if sel_company_name:
    mask &= apps_df["company_name"].isin(sel_company_name)
if sel_status:
    mask &= apps_df["status"].isin(sel_status)
if sel_lang:
    mask &= apps_df["lang"].isin(sel_lang)

filtered = apps_df[mask].copy()

# === Metrics cards ===
st.markdown("---")
st.subheader("Métricas")
card1, card2, card3, card4 = st.columns(4)

# Number of records in selected date range (and other filters)
card1.metric(label="Registros en rango", value=len(filtered))

# Monthly total applications (for the month of the end_date)
if not filtered.empty:
    end_month = pd.to_datetime(end_date).to_period("M")
    monthly_total = filtered[filtered["created_at"].dt.to_period("M") == end_month].shape[0]
else:
    monthly_total = 0
card2.metric(label="Total mes seleccionado", value=monthly_total)

# Overall number of applications (entire table)
overall_total = apps_df.shape[0]
card3.metric(label="Total aplicaciones (global)", value=overall_total)

# Starting date (earliest created_at in table)
start_dt = apps_df["created_at"].min()
start_str = start_dt.strftime("%Y-%m-%d") if pd.notnull(start_dt) else "-"
card4.metric(label="Fecha inicio (primer registro)", value=start_str)

st.markdown("---")

# === Display filtered table (only filter columns) ===
st.subheader("Registros filtrados")
display_cols = ["job", "company_type", "company_name", "created_at", "status", "lang"]
st.dataframe(filtered[display_cols].sort_values("created_at", ascending=False), use_container_width=True)


