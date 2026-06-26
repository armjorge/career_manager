import streamlit as st
import pandas as pd
import os
import sys
import plotly.express as px
from Library.db_utils import DB_UTILS

# 1) Setup Path to find Library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2) Page Config
st.set_page_config(page_title="📊 Career Analytics", layout="wide")

# 3) Initialize DB
if 'db' not in st.session_state:
    st.session_state.db = DB_UTILS()

db = st.session_state.db
schema = db.schema
engine = db.get_engine()

# 4) Navigation
st.page_link("concept_filing.py", label="🏠 Volver al panel principal")
st.write("---")

st.title("📊 Application Analytics & Insights")

# --- DATA FETCHING ---

@st.cache_data(ttl=300)
def get_monthly_stats():
    # 1. Monthly Applications
    q1 = f"""
        SELECT TO_CHAR(created_at, 'YYYY-MM') AS year_month, COUNT(*) AS apps
        FROM "{schema}".fact_application
        GROUP BY 1
    """
    
    # 2. Ready Resumes (dim_resume_details joins with dim_file)
    q2 = f"""
        SELECT TO_CHAR(fa.created_at, 'YYYY-MM') AS year_month, COUNT(*) AS resumes
        FROM "{schema}".fact_application fa
        JOIN "{schema}".dim_resume_details drd ON drd.application_id = fa.application_id
        JOIN "{schema}".dim_file df ON df.file_id = drd.file_id
        WHERE df.file_hash IS NOT NULL AND df.active_status = TRUE
        GROUP BY 1
    """
    
    # 3. Ready Cover Letters (dim_cover_letter joins with dim_file)
    q3 = f"""
        SELECT TO_CHAR(fa.created_at, 'YYYY-MM') AS year_month, COUNT(*) AS cover_letters
        FROM "{schema}".fact_application fa
        JOIN "{schema}".dim_cover_letter dcl ON dcl.application_id = fa.application_id
        JOIN "{schema}".dim_file df ON df.file_id = dcl.file_id
        WHERE df.file_hash IS NOT NULL AND df.active_status = TRUE
        GROUP BY 1
    """
    
    df1 = pd.read_sql(q1, engine)
    df2 = pd.read_sql(q2, engine)
    df3 = pd.read_sql(q3, engine)
    
    # Merge them all
    df_merged = df1.merge(df2, on='year_month', how='left').merge(df3, on='year_month', how='left')
    df_merged = df_merged.fillna(0).sort_values('year_month')
    return df_merged

@st.cache_data(ttl=300)
def get_status_distribution():
    query = f"SELECT status, COUNT(*) as count FROM {schema}.fact_application GROUP BY 1"
    return pd.read_sql(query, engine)

@st.cache_data(ttl=300)
def get_language_distribution():
    query = f"""
        SELECT dl.language, COUNT(*) as count 
        FROM {schema}.fact_application fa
        JOIN {schema}.dim_language dl ON dl.lang_id = fa.lang_id
        GROUP BY 1
    """
    return pd.read_sql(query, engine)

@st.cache_data(ttl=300)
def get_category_distribution():
    query = f"""
        SELECT COALESCE(djc.category_name, 'Uncategorized') as category, COUNT(*) as count 
        FROM {schema}.fact_application fa
        LEFT JOIN {schema}.dim_job_category djc ON djc.job_cat_id = fa.job_cat_id
        GROUP BY 1
        ORDER BY count DESC
    """
    return pd.read_sql(query, engine)

@st.cache_data(ttl=300)
def get_industry_distribution():
    query = f"""
        WITH INDUSTRIES AS ( 
            SELECT 
                dc.company_id,
                dct.type_name 
            FROM {schema}.dim_company dc
            LEFT JOIN {schema}.dim_ctype dct ON dc.ctype_id = dct.ctype_id 
        )
        SELECT 
            COALESCE(ind.type_name, 'Other/Unknown') as industry,
            COUNT(*) AS count
        FROM {schema}.fact_application fa  
        LEFT JOIN INDUSTRIES ind ON fa.company_id = ind.company_id
        GROUP BY 1
        ORDER BY count DESC
    """
    return pd.read_sql(query, engine)

df_monthly = get_monthly_stats()
df_status = get_status_distribution()
df_lang = get_language_distribution()
df_cat = get_category_distribution()
df_ind = get_industry_distribution()

# --- UI SECTIONS ---

# Row 1: Key Metrics
st.subheader("🚀 Overall Progress")
col1, col2, col3, col4 = st.columns(4)

total_apps = int(df_monthly['apps'].sum())
total_resumes = int(df_monthly['resumes'].sum())
total_cl = int(df_monthly['cover_letters'].sum())
conversion_rate = (total_resumes / total_apps * 100) if total_apps > 0 else 0

col1.metric("Total Applications", total_apps)
col2.metric("Ready Resumes", total_resumes)
col3.metric("Ready Cover Letters", total_cl)
col4.metric("CV Prep Rate", f"{conversion_rate:.1f}%")

st.write("---")

# Row 2: Monthly Trends
st.subheader("📅 Monthly Activity")
if not df_monthly.empty:
    fig_monthly = px.line(
        df_monthly, 
        x="year_month", 
        y=["apps", "resumes", "cover_letters"],
        labels={"value": "Count", "year_month": "Month", "variable": "Metric"},
        title="Application vs. Document Readiness",
        markers=True,
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    st.plotly_chart(fig_monthly, use_container_width=True)
else:
    st.info("No data available for monthly trends.")

# Row 3: Distributions & Insights
st.subheader("🎯 Market Focus")
col_l, col_m, col_r = st.columns(3)

with col_l:
    st.write("**Job Categories**")
    fig_cat = px.pie(df_cat, values='count', names='category', hole=.4)
    st.plotly_chart(fig_cat, use_container_width=True)

with col_m:
    st.write("**Industries / Company Types**")
    fig_ind = px.bar(df_ind, x='count', y='industry', orientation='h', color='industry')
    fig_ind.update_layout(showlegend=False)
    st.plotly_chart(fig_ind, use_container_width=True)

with col_r:
    st.write("**Languages**")
    fig_lang = px.pie(df_lang, values='count', names='language', hole=.4)
    st.plotly_chart(fig_lang, use_container_width=True)

# Row 4: Status
st.write("---")
st.subheader("📊 Current Status")
col_status_plot, col_motivation = st.columns([2, 1])

with col_status_plot:
    fig_status = px.bar(df_status, x='status', y='count', color='status', text_auto=True)
    st.plotly_chart(fig_status, use_container_width=True)

with col_motivation:
    st.info("💡 **Keep it up!** Consistency is key in the job hunt. Every application is a step closer to your next big role. Don't forget to follow up on your 'open' applications!")

# Insights Section
st.write("---")
st.subheader("💡 Strategic Insights")

with st.container():
    col_ins1, col_ins2 = st.columns(2)
    
    with col_ins1:
        if not df_monthly.empty:
            peak_month = df_monthly.loc[df_monthly['apps'].idxmax()]
            st.markdown(f"🔥 **Peak Momentum:** Your highest output was in **{peak_month['year_month']}**. Can you beat that this month?")
        
        if not df_ind.empty:
            top_ind = df_ind.iloc[0]['industry']
            st.markdown(f"🏢 **Primary Industry:** You are focusing heavily on **{top_ind}**. This specialization makes you a stronger candidate in this field!")

    with col_ins2:
        if conversion_rate < 70:
            st.markdown("🛠️ **Workflow Tip:** Your document readiness is at **{:.1f}%**. Try to generate your CV immediately after creating an application to stay agile!".format(conversion_rate))
        else:
            st.markdown("✨ **High Efficiency:** You have a ready CV for almost every application. You're ready for any recruiter's call!")

        if not df_cat.empty:
            top_cat = df_cat.iloc[0]['category']
            st.markdown(f"🎯 **Top Role:** Most of your applications are for **{top_cat}** positions. You're building a very clear professional profile.")

    st.markdown("---")
    st.markdown("🚀 **Remember:** Job hunting is a marathon, not a sprint. Use these analytics to refine your strategy, focus on what works, and keep moving forward. You've got this!")
