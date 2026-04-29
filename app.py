import streamlit as st
import json
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="UPSC Daily News Mapper",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Sleek UI
st.markdown("""
<style>
    /* Main Layout */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Card Styling */
    .article-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
        transition: transform 0.2s ease;
    }
    .article-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
    }
    
    /* Typography */
    .article-title {
        color: #1e293b;
        font-size: 1.25rem;
        font-weight: 700;
        text-decoration: none;
        margin-bottom: 0.5rem;
        display: block;
    }
    .article-title:hover {
        color: #2563eb;
    }
    .metadata {
        color: #64748b;
        font-size: 0.875rem;
        margin-bottom: 1rem;
    }
    
    /* Tabs & Pills */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
        color: #475569;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
    }

    /* Tag Styling (handled by Streamlit buttons but we can nudge them) */
    div.stButton > button {
        border-radius: 20px;
        border: 1px solid #e2e8f0;
        background-color: #f1f5f9;
        color: #475569;
        font-size: 0.75rem;
        padding: 0.25rem 0.75rem;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #2563eb;
        color: white;
        border-color: #2563eb;
    }
</style>
""", unsafe_allow_html=True)

# State Management
if "selected_tag" not in st.session_state:
    st.session_state.selected_tag = None

def clear_filter():
    st.session_state.selected_tag = None

def set_filter(tag):
    st.session_state.selected_tag = tag

# Data Loading
@st.cache_data
def load_data():
    try:
        with open("data/news_data.json", "r") as f:
            data = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return []

raw_data = load_data()

# Header
st.title("📰 UPSC Daily News Mapper")
st.markdown("Mapping *The Hindu* news to UPSC Prelims & Mains Syllabus with AI precision.")

if not raw_data:
    st.info("No news data available yet. Please run the scraper.")
else:
    df = pd.DataFrame(raw_data)
    
    # Sort by newest first
    if not df.empty:
        df['sort_date'] = pd.to_datetime(df['published'], errors='coerce')
        if 'date_processed' in df.columns:
            df['sort_date'] = df['sort_date'].fillna(pd.to_datetime(df['date_processed'], errors='coerce'))
        df = df.sort_values(by='sort_date', ascending=False)
    
    # Sidebar: Global Filters
    st.sidebar.header("Global Filters")
    all_dates = sorted(df['date_processed'].unique().tolist(), reverse=True)
    selected_date = st.sidebar.selectbox("Select Date", ["All Dates"] + all_dates)
    
    # Apply Date Filter
    if selected_date != "All Dates":
        df = df[df['date_processed'] == selected_date]

    # Active Filter Banner
    if st.session_state.selected_tag:
        st.info(f"📍 Filtering by Tag: **{st.session_state.selected_tag}**")
        st.button("Clear Tag Filter ✖", on_click=clear_filter)
        df = df[df['mapping'].apply(lambda x: st.session_state.selected_tag in x)]

    # Organized Structure: Tabs
    main_tabs = st.tabs(["All News", "Prelims", "GS 1", "GS 2", "GS 3", "GS 4", "Others"])
    
    paper_map = {
        "Prelims": "Prelims",
        "GS 1": "GS1",
        "GS 2": "GS2",
        "GS 3": "GS3",
        "GS 4": "GS4",
        "Others": "Others"
    }

    def render_article_card(row, idx):
        with st.container():
            st.markdown(f"""
            <div class="article-card">
                <a class="article-title" href="{row['link']}" target="_blank">{row['title']}</a>
                <div class="metadata">Section: {row['section']} | Published: {row['published']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Summary and Tags in columns
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown("**Summary**")
                st.write(row['summary'])
                with st.expander("UPSC Analysis"):
                    st.write(row['analysis'])
            
            with cols[1]:
                st.markdown("**Syllabus Tags**")
                for tag in row['mapping']:
                    st.button(tag, key=f"{idx}_{tag}", on_click=set_filter, args=(tag,))
            st.markdown("<br>", unsafe_allow_html=True)

    for i, tab_name in enumerate(["All News", "Prelims", "GS 1", "GS 2", "GS 3", "GS 4", "Others"]):
        with main_tabs[i]:
            if tab_name == "All News":
                filtered_df = df
            else:
                target = paper_map[tab_name]
                # Filter by paper prefix
                filtered_df = df[df['mapping'].apply(lambda mappings: any(m.startswith(target) for m in mappings))]
                
                # Further divide by syllabus headings within the paper
                if not filtered_df.empty:
                    # Extract unique sub-headings for this paper
                    sub_headings = set()
                    for m_list in filtered_df['mapping']:
                        for m in m_list:
                            if m.startswith(target):
                                sub_headings.add(m)
                    
                    sorted_sub_headings = sorted(list(sub_headings))
                    if len(sorted_sub_headings) > 1:
                        selected_sub = st.pills("Specific Topics", ["All " + tab_name] + sorted_sub_headings, key=f"pills_{tab_name}")
                        if selected_sub and not selected_sub.startswith("All"):
                            filtered_df = filtered_df[filtered_df['mapping'].apply(lambda x: selected_sub in x)]

            if filtered_df.empty:
                st.info(f"No articles found for {tab_name} with current filters.")
            else:
                st.write(f"Showing {len(filtered_df)} articles.")
                for idx, row in filtered_df.iterrows():
                    render_article_card(row, idx)

# Sidebar Footer
st.sidebar.markdown("---")
st.sidebar.write("Developed for UPSC Aspirants.")
st.sidebar.info("Click on any syllabus tag in an article to filter the entire feed by that topic.")
