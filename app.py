import streamlit as st
import json
import pandas as pd
from datetime import datetime
import os
import re
import scraper
import mapper

# Global Utility Functions
def simplify_tag(tag):
    # Split by common delimiters: ':', '(', '-', '–' (en dash), '—' (em dash)
    # We want the GS paper and the main topic.
    parts = re.split(r'[:\(\u2013\u2014\-]', tag)
    if len(parts) >= 2:
        paper = parts[0].strip()
        topic = parts[1].strip()
        # Special case for 'Prelims' which might not have a colon in some formats
        if paper == "Prelims":
            return f"Prelims: {topic}" if topic else "Prelims"
        return f"{paper}: {topic}"
    return tag.strip()

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

# Sidebar Actions
st.sidebar.header("Actions")
if st.sidebar.button("🔄 Fetch & Analyze News", help="Manually trigger the scraper and AI analysis"):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.sidebar.error("GEMINI_API_KEY not found in environment.")
    else:
        with st.status("Fetching news from RSS feeds...", expanded=True) as status:
            try:
                articles = scraper.fetch_articles()
                if not articles:
                    status.update(label="No new articles found.", state="complete")
                else:
                    status.write(f"Found {len(articles)} articles. Starting AI analysis...")
                    count = mapper.process_and_save(articles, api_key)
                    status.update(label=f"Successfully processed {count} UPSC-relevant articles!", state="complete")
                    st.cache_data.clear()
                    st.rerun()
            except Exception as e:
                status.update(label="Error during execution.", state="error")
                st.sidebar.error(f"Error: {e}")

# Header
st.title("📰 UPSC Daily News Mapper")
st.markdown("Mapping *The Hindu* news to UPSC Prelims & Mains Syllabus with AI precision.")

if not raw_data:
    st.info("No news data available yet. Use the 'Fetch & Analyze News' button in the sidebar to start.")
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
    all_dates = sorted(df['date_processed'].unique().tolist(), reverse=True) if not df.empty else []
    selected_date = st.sidebar.selectbox("Select Date", ["All Dates"] + all_dates)
    
    # Apply Date Filter
    if selected_date != "All Dates":
        df = df[df['date_processed'] == selected_date]

    # Active Filter Banner
    if st.session_state.selected_tag:
        st.info(f"📍 Filtering by Tag: **{st.session_state.selected_tag}**")
        st.button("Clear Tag Filter ✖", on_click=clear_filter)
        # Check if the simplified version of any mapping in the article matches the selected tag
        df = df[df['mapping'].apply(lambda x: any(simplify_tag(m) == st.session_state.selected_tag for m in x))]

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

    def render_article_card(row, idx, tab_prefix):
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
                    simple = simplify_tag(tag)
                    st.button(tag, key=f"{tab_prefix}_{idx}_{tag}", on_click=set_filter, args=(simple,))
            st.markdown("<br>", unsafe_allow_html=True)

    for i, tab_name in enumerate(["All News", "Prelims", "GS 1", "GS 2", "GS 3", "GS 4", "Others"]):
        with main_tabs[i]:
            if tab_name == "All News":
                filtered_df = df
            else:
                target = paper_map[tab_name]
                # Filter by paper prefix (case-insensitive and robust)
                filtered_df = df[df['mapping'].apply(lambda mappings: any(m.strip().startswith(target) for m in mappings))]
                
                # Further divide by syllabus headings within the paper
                if not filtered_df.empty:
                    # Extract simplified sub-headings for this paper
                    sub_headings = set()
                    for m_list in filtered_df['mapping']:
                        for m in m_list:
                            if m.strip().startswith(target):
                                sub_headings.add(simplify_tag(m))
                    
                    sorted_sub_headings = sorted(list(sub_headings))
                    if len(sorted_sub_headings) > 1:
                        selected_sub = st.pills("Specific Topics", ["All " + tab_name] + sorted_sub_headings, key=f"pills_{tab_name}")
                        if selected_sub and not selected_sub.startswith("All"):
                            # Filter by matching the simplified version of any tag in the article
                            filtered_df = filtered_df[filtered_df['mapping'].apply(
                                lambda x: any(simplify_tag(m) == selected_sub for m in x)
                            )]

            if filtered_df.empty:
                st.info(f"No articles found for {tab_name} with current filters.")
            else:
                st.write(f"Showing {len(filtered_df)} articles.")
                for idx, row in filtered_df.iterrows():
                    render_article_card(row, idx, tab_name)

# Sidebar Footer
st.sidebar.markdown("---")
st.sidebar.write("Developed for UPSC Aspirants.")
st.sidebar.info("Click on any syllabus tag in an article to filter the entire feed by that topic.")
