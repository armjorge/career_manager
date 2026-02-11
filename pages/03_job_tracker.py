import streamlit as st
import pandas as pd
import os
import sys
import plotly.express as px
import plotly.graph_objects as go


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

# 2. Localize to UTC (assuming your DB server uses UTC) 
# and then convert to GMT-6
# We use 'Etc/GMT+6' because in the TZ database, signs are reversed, 
# or use a city name like 'America/Mexico_City' to handle Daylight Savings.
apps_df["created_at"] = (
    apps_df["created_at"]
    .dt.tz_localize('UTC') 
    .dt.tz_convert('America/Mexico_City')
)


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
## Sección de inteligencia
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. PREPARE FILTER DATA ---
# Create sorting key and display key
apps_df['month_year_key'] = apps_df['created_at'].dt.strftime('%Y-%m')
apps_df['display_month'] = apps_df['created_at'].dt.strftime('%B %Y')

# Get unique months sorted descending (newest first)
month_options = (
    apps_df.sort_values("month_year_key", ascending=False)[['month_year_key', 'display_month']]
    .drop_duplicates()
)

# Add "All Time" to the top of the list
options_list = ["All Time"] + month_options['display_month'].tolist()

# --- 2. SIDEBAR FILTER ---
st.sidebar.header("📊 Filter Intelligence")
selected_display = st.sidebar.selectbox("Select Time Range", options=options_list)

# --- 3. APPLY FILTER LOGIC ---
if selected_display == "All Time":
    filtered_df = apps_df.copy()
    title_suffix = "All Time"
else:
    # Find the corresponding YYYY-MM key for the selected display name
    selected_month_key = month_options.loc[
        month_options['display_month'] == selected_display, 'month_year_key'
    ].iloc[0]
    filtered_df = apps_df[apps_df['month_year_key'] == selected_month_key]
    title_suffix = selected_display

# --- 4. CALCULATE METRICS ---
status_order = ['applied', 'interviewing', 'offered', 'rejected']
counts = filtered_df['status'].value_counts().reindex(status_order, fill_value=0)

# --- 5. DISPLAY UI ---
st.subheader(f"📈 Performance: {title_suffix}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Apps", len(filtered_df))
col2.metric("Interviews", counts['interviewing'])
col3.metric("Offers 🏆", counts['offered'])
col4.metric("Rejections", counts['rejected'])

st.divider()

# --- 6. THE FUNNEL VISUALIZATION ---
# Using the standard progression stages
prog_stages = ['applied', 'interviewing', 'offered']
prog_values = [counts[s] for s in prog_stages]

fig = go.Figure(go.Funnel(
    y = prog_stages,
    x = prog_values,
    textinfo = "value+percent initial",
    marker = {"color": ["#636EFA", "#EF553B", "#00CC96"]},
    connector = {"line": {"color": "gray", "width": 2}}
))

fig.update_layout(
    title=f"Application Progression ({title_suffix})",
    margin=dict(l=20, r=20, t=50, b=20),
    height=400
)

st.plotly_chart(fig, use_container_width=True)