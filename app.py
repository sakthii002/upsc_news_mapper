import streamlit as st
import json
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="UPSC Daily News Mapper", layout="wide")

st.title("📰 UPSC Daily News Mapper")
st.markdown("Mapping *The Hindu* news to UPSC Prelims & Mains Syllabus.")

def load_data():
    try:
        with open("upsc_news_mapper/data/news_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

data = load_data()

if not data:
    st.info("No news data available yet. Please run the scraper.")
else:
    df = pd.DataFrame(data)
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date filter
    all_dates = sorted(df['date_processed'].unique(), reverse=True)
    selected_date = st.sidebar.selectbox("Select Date", ["All"] + all_dates)
    
    # Topic filter
    all_mappings = set()
    for m_list in df['mapping']:
        for m in m_list:
            all_mappings.add(m)
    selected_mapping = st.sidebar.multiselect("Filter by Syllabus Topic", sorted(list(all_mappings)))
    
    # Filtering logic
    filtered_df = df.copy()
    if selected_date != "All":
        filtered_df = filtered_df[filtered_df['date_processed'] == selected_date]
    
    if selected_mapping:
        filtered_df = filtered_df[filtered_df['mapping'].apply(lambda x: any(m in x for m in selected_mapping))]
    
    st.write(f"Showing {len(filtered_df)} relevant articles.")
    
    for idx, row in filtered_df.iterrows():
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"[{row['title']}]({row['link']})")
                st.markdown(f"**Section:** {row['section']} | **Published:** {row['published']}")
            with col2:
                for tag in row['mapping']:
                    st.button(tag, key=f"{idx}_{tag}", disabled=True)
            
            st.markdown("### Summary")
            st.write(row['summary'])
            
            with st.expander("UPSC Analysis"):
                st.write(row['analysis'])
            
            st.divider()

st.sidebar.markdown("---")
st.sidebar.write("Developed for UPSC Aspirants.")
