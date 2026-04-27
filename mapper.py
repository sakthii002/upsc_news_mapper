import os
import json
import google.generativeai as genai
from datetime import datetime

# Set up Gemini API
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT_TEMPLATE = """
You are an expert UPSC mentor. Analyze the following news article and provide a structured response for a UPSC aspirant.

ARTICLE TITLE: {title}
ARTICLE TEXT: {text}

---
Your response MUST be in JSON format with the following keys:
1. "is_relevant": (boolean) Whether this article is relevant to the UPSC syllabus.
2. "summary": (string) A concise summary (3-5 bullet points) of the article.
3. "mapping": (list of strings) Map the article to specific GS papers (GS1, GS2, GS3, GS4) and specific syllabus topics (e.g., "GS2: International Relations", "GS3: Environment", "Prelims: Science & Tech").
4. "analysis": (string) A brief "Why it matters for UPSC" note.

JSON Output:
"""

import time

def analyze_article(model, article):
    prompt = PROMPT_TEMPLATE.format(title=article['title'], text=article['text'][:5000]) # Limit text to 5000 chars
    response = model.generate_content(prompt)
    
    # Check if response was blocked by safety filters
    if not response.candidates or not response.candidates[0].content.parts:
        print(f"Warning: Gemini blocked response for '{article['title']}' (Safety/Other)")
        return None
        
    content = response.text.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)

def process_and_save(articles, api_key):
    genai.configure(api_key=api_key)
    
    # User-specified model priority order starting from 3-flash-preview
    model_names = ['gemini-3-flash-preview', 'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-flash-lite-latest']
    current_model_idx = 0
    
    processed_news = []
    
    for article in articles:
        print(f"Analyzing: {article['title']}")
        success = False
        
        # Try current and subsequent models until success or exhaustion
        while current_model_idx < len(model_names) and not success:
            model_name = model_names[current_model_idx]
            print(f"  -> Using model: {model_name}")
            model = genai.GenerativeModel(model_name)
            
            try:
                analysis = analyze_article(model, article)
                success = True # Successfully got a response (even if None)
                
                if analysis and analysis.get("is_relevant"):
                    print(f"     [Relevant] mapped to: {analysis.get('mapping')}")
                    article_data = {
                        "title": article["title"],
                        "link": article["link"],
                        "published": article["published"],
                        "section": article["section"],
                        "summary": analysis["summary"],
                        "mapping": analysis["mapping"],
                        "analysis": analysis["analysis"],
                        "date_processed": datetime.now().strftime("%Y-%m-%d")
                    }
                    processed_news.append(article_data)
                else:
                    print("     [Not Relevant] skipping.")
                    
            except Exception as e:
                error_msg = str(e)
                # Check for quota, rate limit, or permission errors that suggest switching
                if any(x in error_msg.lower() for x in ["429", "quota", "limit", "403", "permission"]):
                    print(f"  !! Model {model_name} failed (Limit/Permission). Error: {error_msg}")
                    print(f"  !! Switching from {model_name} to next model...")
                    current_model_idx += 1
                    # success remains False, so the while loop will retry with the NEW current_model_idx
                else:
                    print(f"  !! Unexpected error with {model_name}: {e}")
                    success = True # Stop retrying THIS article for unknown errors to prevent infinite loops
        
        # Add a small delay to avoid hitting rate limits
        time.sleep(1)
        
        if current_model_idx >= len(model_names):
            print("CRITICAL: All models in the hierarchy have failed or exhausted quota.")
            break
    
    # Save to JSON
    output_path = "data/news_data.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    existing_data = []
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            try:
                existing_data = json.load(f)
            except:
                existing_data = []
    
    # Append new data and remove duplicates based on link
    combined_data = {a['link']: a for a in existing_data + processed_news}.values()
    
    with open(output_path, 'w') as f:
        json.dump(list(combined_data), f, indent=4)
    
    return len(processed_news)

if __name__ == "__main__":
    # This is for local testing if API key is in env
    import scraper
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        articles = scraper.fetch_articles()
        count = process_and_save(articles[:5], api_key) # Test with 5 articles
        print(f"Processed and saved {count} relevant articles.")
    else:
        print("GEMINI_API_KEY not found in environment.")
