import streamlit as st
import json
import pandas as pd
from datetime import datetime
import os
import re
import scraper
import mapper

# ─────────────────────────────────────────────
# Global Utility Functions
# ─────────────────────────────────────────────
def simplify_tag(tag):
    parts = re.split(r'[:\(\u2013\u2014\-]', tag)
    if len(parts) >= 2:
        paper = parts[0].strip()
        topic = parts[1].strip()
        if paper == "Prelims":
            return f"Prelims: {topic}" if topic else "Prelims"
        return f"{paper}: {topic}"
    return tag.strip()

# ─────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="UPSC Daily News Mapper",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# Sleek Dark Mode CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-dark: #0f172a;
        --card-bg: #1e293b;
        --border-color: #334155;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --accent-blue: #38bdf8;
        --accent-hover: #0ea5e9;
    }

    /* Global Overrides */
    .stApp {
        background-color: var(--bg-dark);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #020617 !important;
        border-right: 1px solid var(--border-color);
    }

    /* Article Card */
    .article-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    .article-card:hover {
        border-color: var(--accent-blue);
        box-shadow: 0 4px 20px rgba(56, 189, 248, 0.1);
        transform: translateY(-2px);
    }

    .article-title {
        color: var(--text-primary);
        font-size: 1.4rem;
        font-weight: 600;
        text-decoration: none;
        display: block;
        margin-bottom: 0.5rem;
    }
    .article-title:hover {
        color: var(--accent-blue);
    }

    .metadata {
        color: var(--text-secondary);
        font-size: 0.85rem;
        margin-bottom: 1rem;
        display: flex;
        gap: 1rem;
    }

    /* Collapsible Section Styling */
    .streamlit-expanderHeader {
        background-color: #0f172a !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    .streamlit-expanderContent {
        background-color: #1e293b !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        color: var(--text-secondary) !important;
        padding: 1rem !important;
    }

    /* Tag Styling */
    div.stButton > button {
        border-radius: 20px;
        border: 1px solid var(--border-color);
        background-color: #334155;
        color: #e2e8f0;
        font-size: 0.75rem;
        padding: 0.2rem 0.8rem;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: var(--accent-blue);
        color: #0f172a;
        border-color: var(--accent-blue);
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 8px 8px 0 0;
        color: var(--text-secondary);
        padding: 10px 20px;
        border: 1px solid var(--border-color);
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--accent-blue) !important;
        color: #0f172a !important;
        font-weight: 600;
    }

    /* Pills Styling */
    [data-testid="stPills"] button {
        background-color: #1e293b !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-secondary) !important;
    }
    [data-testid="stPills"] button[aria-pressed="true"] {
        background-color: var(--accent-blue) !important;
        color: #0f172a !important;
    }

    /* Header Styling */
    h1 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# State Management
# ─────────────────────────────────────────────
if "selected_tag" not in st.session_state:
    st.session_state.selected_tag = None

def clear_filter():
    st.session_state.selected_tag = None

def set_filter(tag):
    st.session_state.selected_tag = tag

# ─────────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        with open("data/news_data.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

raw_data = load_data()

# ─────────────────────────────────────────────
# Sidebar Actions
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Control Center")
    if st.button("🔄 Fetch & Analyze News", use_container_width=True):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("GEMINI_API_KEY not found.")
        else:
            with st.status("Processing updates...") as status:
                try:
                    articles = scraper.fetch_articles()
                    if articles:
                        count = mapper.process_and_save(articles, api_key)
                        status.update(label=f"Done! {count} articles added.", state="complete")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        status.update(label="No new articles.", state="complete")
                except Exception as e:
                    status.update(label="Failed.", state="error")
                    st.error(str(e))
    
    st.divider()
    if raw_data:
        df_side = pd.DataFrame(raw_data)
        all_dates = sorted(df_side['date_processed'].unique().tolist(), reverse=True)
        selected_date = st.selectbox("📅 Archive", ["All Time"] + all_dates)
    else:
        selected_date = "All Time"

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.title("📰 UPSC Daily News Mapper")
st.markdown("<p style='color:#94a3b8; font-size:1.1rem;'>Precision mapping of <i>The Hindu</i> to the UPSC Civil Services Syllabus.</p>", unsafe_allow_html=True)

if not raw_data:
    st.info("Dashboard empty. Hit 'Fetch & Analyze' in the sidebar.")
    st.stop()

# ─────────────────────────────────────────────
# Data Processing
# ─────────────────────────────────────────────
df = pd.DataFrame(raw_data)
df['sort_date'] = pd.to_datetime(df['published'], errors='coerce')
if 'date_processed' in df.columns:
    df['sort_date'] = df['sort_date'].fillna(pd.to_datetime(df['date_processed'], errors='coerce'))
df = df.sort_values(by='sort_date', ascending=False)

if selected_date != "All Time":
    df = df[df['date_processed'] == selected_date]

if st.session_state.selected_tag:
    st.info(f"🎯 Topic: {st.session_state.selected_tag}")
    st.button("Clear Filter ✕", on_click=clear_filter)
    df = df[df['mapping'].apply(lambda x: any(simplify_tag(m) == st.session_state.selected_tag for m in x))]

# ─────────────────────────────────────────────
# Article Card Renderer
# ─────────────────────────────────────────────
def render_article_card(row, idx, tab_prefix):
    with st.container():
        st.markdown(f"""
        <div class="article-card">
            <a class="article-title" href="{row['link']}" target="_blank">{row['title']}</a>
            <div class="metadata">
                <span>📍 {row['section']}</span>
                <span>🕒 {row['published']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            with st.expander("📝 Summary", expanded=False):
                st.write(row['summary'])
            with st.expander("⚖️ UPSC Analysis", expanded=False):
                st.write(row['analysis'])
        
        with col2:
            st.markdown("<p style='font-size:0.7rem; color:#94a3b8; font-weight:600; margin-bottom:5px;'>SYLLABUS MAPPING</p>", unsafe_allow_html=True)
            for tag in row['mapping']:
                st.button(tag, key=f"{tab_prefix}_{idx}_{tag}", on_click=set_filter, args=(simplify_tag(tag),))

# ─────────────────────────────────────────────
# Dashboard Tabs
# ─────────────────────────────────────────────
tabs = st.tabs(["All News", "Prelims", "GS 1", "GS 2", "GS 3", "GS 4"])
paper_map = {"Prelims": "Prelims", "GS 1": "GS1", "GS 2": "GS2", "GS 3": "GS3", "GS 4": "GS4"}

for i, tab_label in enumerate(["All News", "Prelims", "GS 1", "GS 2", "GS 3", "GS 4"]):
    with tabs[i]:
        if tab_label == "All News":
            filtered_df = df
        else:
            target = paper_map[tab_label]
            filtered_df = df[df['mapping'].apply(lambda m_list: any(m.startswith(target) for m in m_list))]
            
            if not filtered_df.empty:
                topics = sorted(list({simplify_tag(m) for m_list in filtered_df['mapping'] for m in m_list if m.startswith(target)}))
                if len(topics) > 1:
                    sel_topic = st.pills("Jump to Topic", ["All"] + topics, key=f"p_{tab_label}")
                    if sel_topic != "All":
                        filtered_df = filtered_df[filtered_df['mapping'].apply(lambda x: any(simplify_tag(m) == sel_topic for m in x))]

        if filtered_df.empty:
            st.write("No matching articles found.")
        else:
            for idx, row in filtered_df.iterrows():
                render_article_card(row, idx, tab_label)
