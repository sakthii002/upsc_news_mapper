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
# Premium CSS — Editorial × Knowledge Dashboard
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;0,8..60,600;1,8..60,300&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

/* ── Root Palette ─────────────────────────── */
:root {
    --ink:         #0d1117;
    --ink-light:   #374151;
    --ink-muted:   #6b7280;
    --paper:       #faf9f7;
    --paper-warm:  #f3f0eb;
    --border:      #e5e0d8;
    --border-light:#ede9e3;
    --accent:      #1a3a5c;
    --accent-hover:#0f2540;
    --rule:        #c8bfb0;

    /* GS Paper accent colours */
    --prelims-hue: #0e4f6b;   /* deep teal    */
    --gs1-hue:     #6b3a0e;   /* warm amber   */
    --gs2-hue:     #0e2f6b;   /* royal navy   */
    --gs3-hue:     #1a5c2e;   /* forest green */
    --gs4-hue:     #4a1060;   /* deep violet  */
    --others-hue:  #4a3000;   /* dark sienna  */
}

/* ── Global Reset ─────────────────────────── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--paper) !important;
    color: var(--ink);
}

/* ── App Background ───────────────────────── */
.stApp {
    background-color: var(--paper) !important;
}
.main .block-container {
    padding: 2rem 2.5rem 4rem;
    max-width: 1280px;
}

/* ── Sidebar ──────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--ink) !important;
    border-right: 1px solid #1e2a36;
}
[data-testid="stSidebar"] * {
    color: #d4c9b8 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #f5f0e8 !important;
    font-family: 'Playfair Display', serif !important;
    letter-spacing: 0.02em;
}
[data-testid="stSidebar"] .stMarkdown p {
    font-size: 0.82rem;
    line-height: 1.6;
    color: #8a9db5 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #2a3a4a !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] label,
[data-testid="stSidebar"] [data-testid="stSelectbox"] div {
    color: #c8bfb0 !important;
}

/* Sidebar primary button ── Fetch & Analyze */
[data-testid="stSidebar"] div.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #1a3a5c 0%, #0e2030 100%) !important;
    color: #e8e0d4 !important;
    border: 1px solid #2a4a6c !important;
    border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.04em;
    padding: 0.6rem 1rem !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background: linear-gradient(135deg, #2a5080 0%, #1a3050 100%) !important;
    border-color: #4a7aac !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
}

/* ── Masthead ─────────────────────────────── */
.masthead {
    border-bottom: 3px double var(--rule);
    padding-bottom: 1.25rem;
    margin-bottom: 0.5rem;
}
.masthead-kicker {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--ink-muted);
    margin-bottom: 0.4rem;
}
.masthead-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: 700;
    color: var(--ink);
    line-height: 1.1;
    margin: 0 0 0.4rem;
    letter-spacing: -0.01em;
}
.masthead-title span {
    color: var(--accent);
}
.masthead-sub {
    font-family: 'Source Serif 4', serif;
    font-style: italic;
    font-size: 1rem;
    color: var(--ink-muted);
    font-weight: 300;
}
.masthead-meta {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.75rem;
    color: var(--rule);
    letter-spacing: 0.06em;
    margin-top: 0.8rem;
    text-transform: uppercase;
}

/* ── Horizontal rule separator ───────────── */
.rule-thin {
    border: none;
    border-top: 1px solid var(--border);
    margin: 0.75rem 0 1.5rem;
}

/* ── Active filter banner ─────────────────── */
.filter-banner {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: #eef3f9;
    border: 1px solid #c2d4e8;
    border-left: 4px solid var(--accent);
    border-radius: 6px;
    padding: 0.6rem 1rem;
    margin-bottom: 1rem;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.875rem;
    color: var(--accent);
}
.filter-banner strong {
    font-weight: 600;
}

/* Clear filter button */
[data-testid="stMainBlockContainer"] div.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--ink-muted) !important;
    border-radius: 20px !important;
    font-size: 0.75rem !important;
    padding: 0.2rem 0.8rem !important;
}

/* ── Tabs ─────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background: var(--paper-warm);
    border-bottom: 2px solid var(--border);
    padding: 0;
    border-radius: 0;
}
.stTabs [data-baseweb="tab"] {
    height: 42px;
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    border-radius: 0;
    padding: 0 1.25rem;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    font-size: 0.82rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--ink-muted);
    margin-bottom: -2px;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--ink);
    background: rgba(0,0,0,0.03);
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 3px solid var(--accent) !important;
    background: transparent !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem;
}

/* ── Article Count Badge ──────────────────── */
.count-badge {
    display: inline-block;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--ink-muted);
    margin-bottom: 1.25rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--border-light);
    width: 100%;
}
.count-badge b {
    color: var(--ink);
    font-weight: 700;
}

/* ── Article Card ─────────────────────────── */
.article-card {
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.5rem 1.75rem 1.25rem;
    margin-bottom: 1.25rem;
    position: relative;
    transition: box-shadow 0.25s ease, border-color 0.25s ease;
}
.article-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
    border-radius: 4px 0 0 4px;
    background: var(--card-accent, var(--accent));
    opacity: 0.7;
    transition: opacity 0.2s;
}
.article-card:hover {
    box-shadow: 0 4px 24px rgba(0,0,0,0.07);
    border-color: #d0c8be;
}
.article-card:hover::before {
    opacity: 1;
}

/* Card: per-paper accent colours via class */
.card-prelims { --card-accent: var(--prelims-hue); }
.card-gs1     { --card-accent: var(--gs1-hue); }
.card-gs2     { --card-accent: var(--gs2-hue); }
.card-gs3     { --card-accent: var(--gs3-hue); }
.card-gs4     { --card-accent: var(--gs4-hue); }
.card-others  { --card-accent: var(--others-hue); }

.card-section-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--ink-muted);
    margin-bottom: 0.3rem;
}
.article-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--ink);
    text-decoration: none;
    line-height: 1.35;
    display: block;
    margin-bottom: 0.45rem;
    transition: color 0.15s ease;
}
.article-title:hover {
    color: var(--accent);
    text-decoration: underline;
    text-underline-offset: 3px;
    text-decoration-thickness: 1px;
}
.article-meta {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.75rem;
    color: var(--rule);
    letter-spacing: 0.04em;
    margin-bottom: 1rem;
}
.article-meta span {
    margin-right: 1rem;
}
.article-meta span::before {
    content: '· ';
    color: var(--border);
}
.article-meta span:first-child::before {
    content: '';
}
.summary-text {
    font-family: 'Source Serif 4', serif;
    font-size: 0.92rem;
    line-height: 1.75;
    color: var(--ink-light);
    font-weight: 300;
}

/* ── Tags Column ──────────────────────────── */
.tags-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--ink-muted);
    margin-bottom: 0.6rem;
}

/* Override Streamlit buttons used as tags */
.tag-button-wrapper div.stButton > button {
    display: block !important;
    width: 100% !important;
    text-align: left !important;
    background: transparent !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    color: var(--ink-light) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    padding: 0.3rem 0.6rem !important;
    margin-bottom: 0.35rem !important;
    letter-spacing: 0.01em;
    line-height: 1.4 !important;
    white-space: normal !important;
    height: auto !important;
    transition: all 0.15s ease !important;
}
.tag-button-wrapper div.stButton > button:hover {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #ffffff !important;
    transform: none !important;
    box-shadow: 0 2px 8px rgba(26,58,92,0.25) !important;
}

/* ── Expander (UPSC Analysis) ─────────────── */
.streamlit-expanderHeader {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--ink-muted) !important;
    background: var(--paper-warm) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: 4px !important;
    padding: 0.5rem 0.75rem !important;
}
.streamlit-expanderContent {
    background: var(--paper-warm) !important;
    border: 1px solid var(--border-light) !important;
    border-top: none !important;
    border-radius: 0 0 4px 4px !important;
    padding: 0.75rem !important;
    font-family: 'Source Serif 4', serif !important;
    font-size: 0.875rem !important;
    line-height: 1.7 !important;
    color: var(--ink-light) !important;
}

/* ── Pills (sub-topic filter) ─────────────── */
[data-testid="stPills"] {
    margin-bottom: 1.5rem;
}
[data-testid="stPills"] button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    border-radius: 2px !important;
    border: 1px solid var(--border) !important;
    background: #fff !important;
    color: var(--ink-muted) !important;
    padding: 0.25rem 0.7rem !important;
    transition: all 0.15s !important;
}
[data-testid="stPills"] button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: #eef3f9 !important;
}
[data-testid="stPills"] button[aria-pressed="true"],
[data-testid="stPills"] button[data-selected="true"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #fff !important;
    font-weight: 600 !important;
}

/* ── Info / Status messages ───────────────── */
[data-testid="stAlert"] {
    border-radius: 4px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.875rem !important;
}

/* ── Selectbox ────────────────────────────── */
[data-testid="stSidebar"] [data-baseweb="select"] {
    background: #1a2a3a !important;
    border-color: #2a3a4a !important;
}

/* ── Scrollbar cosmetic ───────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--paper); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--rule); }

/* ── Thin divider between cards ──────────── */
.card-divider {
    border: none;
    border-top: 1px solid var(--border-light);
    margin: 0.25rem 0 1.25rem;
    opacity: 0.5;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
PAPER_CSS = {
    "Prelims": "card-prelims",
    "GS1":     "card-gs1",
    "GS2":     "card-gs2",
    "GS3":     "card-gs3",
    "GS4":     "card-gs4",
    "Others":  "card-others",
}

def card_class_for_row(row):
    """Detect dominant paper for this article."""
    for m in row.get('mapping', []):
        for key in PAPER_CSS:
            if m.strip().startswith(key):
                return PAPER_CSS[key]
    return ""

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
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📰 UPSC Mapper")
    st.markdown("---")

    # Primary action button
    if st.button("🔄 Fetch & Analyze News",
                  help="Trigger the scraper and run Gemini AI analysis"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("GEMINI_API_KEY not found in environment.")
        else:
            with st.status("Fetching news from RSS feeds…", expanded=True) as status:
                try:
                    articles = scraper.fetch_articles()
                    if not articles:
                        status.update(label="No new articles found.", state="complete")
                    else:
                        status.write(f"Found {len(articles)} articles. Starting AI analysis…")
                        count = mapper.process_and_save(articles, api_key)
                        status.update(
                            label=f"✔ Processed {count} UPSC-relevant articles!",
                            state="complete"
                        )
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    status.update(label="Error during execution.", state="error")
                    st.error(f"Error: {e}")

    st.markdown("---")

    # Date filter — rendered after data load so we skip if no data
    if raw_data:
        df_sidebar = pd.DataFrame(raw_data)
        all_dates = sorted(
            df_sidebar['date_processed'].dropna().unique().tolist(),
            reverse=True
        ) if not df_sidebar.empty else []
        selected_date = st.selectbox("📅 Filter by Date",
                                      ["All Dates"] + all_dates,
                                      key="date_select")
    else:
        selected_date = "All Dates"

    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem;line-height:1.6;'>Click any **syllabus tag** on an article to filter the entire feed by that topic.</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='font-size:0.72rem;color:#4a6080;'>Developed for UPSC Aspirants</p>",
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────
# Masthead
# ─────────────────────────────────────────────
today_str = datetime.today().strftime("%A, %d %B %Y").upper()
st.markdown(f"""
<div class="masthead">
    <div class="masthead-kicker">Knowledge Dashboard · The Hindu × UPSC Syllabus</div>
    <div class="masthead-title"><span>Daily</span> News Mapper</div>
    <div class="masthead-sub">AI-powered mapping of current affairs to the Civil Services syllabus</div>
    <div class="masthead-meta">{today_str}</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# No Data State
# ─────────────────────────────────────────────
if not raw_data:
    st.info(
        "📭 No news data available yet. "
        "Use **Fetch & Analyze News** in the sidebar to populate the feed."
    )
    st.stop()


# ─────────────────────────────────────────────
# Main DataFrame
# ─────────────────────────────────────────────
df = pd.DataFrame(raw_data)

if not df.empty:
    df['sort_date'] = pd.to_datetime(df['published'], errors='coerce')
    if 'date_processed' in df.columns:
        df['sort_date'] = df['sort_date'].fillna(
            pd.to_datetime(df['date_processed'], errors='coerce')
        )
    df = df.sort_values(by='sort_date', ascending=False)

# Apply Date Filter
if selected_date != "All Dates":
    df = df[df['date_processed'] == selected_date]

# ─────────────────────────────────────────────
# Active Tag Filter Banner
# ─────────────────────────────────────────────
if st.session_state.selected_tag:
    st.markdown(f"""
    <div class="filter-banner">
        <span>🔖</span>
        <span>Filtered by tag: <strong>{st.session_state.selected_tag}</strong></span>
    </div>
    """, unsafe_allow_html=True)
    st.button("✕ Clear tag filter", on_click=clear_filter, type="secondary")
    df = df[df['mapping'].apply(
        lambda x: any(simplify_tag(m) == st.session_state.selected_tag for m in x)
    )]


# ─────────────────────────────────────────────
# Article Card Renderer
# ─────────────────────────────────────────────
def render_article_card(row, idx, tab_prefix):
    accent_class = card_class_for_row(row)
    section_val  = row.get('section', '—')
    pub_val      = row.get('published', '—')

    st.markdown(f"""
    <div class="article-card {accent_class}">
        <div class="card-section-label">{section_val}</div>
        <a class="article-title" href="{row['link']}" target="_blank" rel="noopener">{row['title']}</a>
        <div class="article-meta">
            <span>The Hindu</span>
            <span>{pub_val}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Content + tags split
    left_col, right_col = st.columns([11, 4])

    with left_col:
        st.markdown(f'<p class="summary-text">{row["summary"]}</p>',
                    unsafe_allow_html=True)
        with st.expander("UPSC Analysis ↓"):
            st.write(row['analysis'])

    with right_col:
        st.markdown('<div class="tags-label">Syllabus Tags</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="tag-button-wrapper">', unsafe_allow_html=True)
        for tag in row['mapping']:
            simple = simplify_tag(tag)
            st.button(
                tag,
                key=f"{tab_prefix}_{idx}_{tag}",
                on_click=set_filter,
                args=(simple,)
            )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr class="card-divider">', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────
TAB_NAMES  = ["All News", "Prelims", "GS 1", "GS 2", "GS 3", "GS 4", "Others"]
TAB_KEYS   = ["All News", "Prelims", "GS1",  "GS2",  "GS3",  "GS4",  "Others"]
TAB_LABELS = ["All",      "Prelims", "GS I", "GS II","GS III","GS IV","Others"]

main_tabs = st.tabs(TAB_LABELS)

for i, (tab_name, target_key) in enumerate(zip(TAB_NAMES, TAB_KEYS)):
    with main_tabs[i]:

        if tab_name == "All News":
            filtered_df = df.copy()
        else:
            filtered_df = df[df['mapping'].apply(
                lambda mappings: any(m.strip().startswith(target_key) for m in mappings)
            )].copy()

            # Sub-topic pills
            if not filtered_df.empty:
                sub_headings = set()
                for m_list in filtered_df['mapping']:
                    for m in m_list:
                        if m.strip().startswith(target_key):
                            sub_headings.add(simplify_tag(m))

                sorted_sub = sorted(list(sub_headings))
                if len(sorted_sub) > 1:
                    pill_opts = [f"All {tab_name}"] + sorted_sub
                    selected_sub = st.pills(
                        "Filter by topic",
                        pill_opts,
                        key=f"pills_{tab_name}"
                    )
                    if selected_sub and not selected_sub.startswith("All"):
                        filtered_df = filtered_df[filtered_df['mapping'].apply(
                            lambda x: any(simplify_tag(m) == selected_sub for m in x)
                        )]

        if filtered_df.empty:
            st.info(f"No articles found for **{tab_name}** with the current filters.")
        else:
            n = len(filtered_df)
            label = "article" if n == 1 else "articles"
            st.markdown(
                f'<div class="count-badge">Showing <b>{n}</b> {label}</div>',
                unsafe_allow_html=True
            )
            for idx, row in filtered_df.iterrows():
                render_article_card(row, idx, tab_name)
