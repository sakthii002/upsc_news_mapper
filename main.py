import os
import sys
import traceback

# Force unbuffered real-time logs for GitHub Actions
sys.stdout.reconfigure(line_buffering=True)

print(">>> BOOTING UPSC NEWS MAPPER (REAL-TIME LOGS ENABLED)...")

import scraper
import mapper

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CRITICAL ERROR: GEMINI_API_KEY not found in environment variables.")
        sys.exit(1)

    print(">>> STARTING DAILY NEWS SCRAPE...")
    try:
        print("Step 1: Fetching articles from RSS feeds...")
        articles = scraper.fetch_articles()
        
        if not articles:
            print("Step 1 Result: No new articles fetched. Everything is up to date.")
            return
            
        print(f"Step 2: Fetched {len(articles)} articles. Starting AI analysis...")
        count = mapper.process_and_save(articles, api_key)
        print(f"Step 3: Processed {count} UPSC-relevant articles.")
    except Exception as e:
        print("-" * 30)
        print("CRITICAL ERROR DURING EXECUTION:")
        traceback.print_exc()
        print("-" * 30)
        sys.exit(1)

if __name__ == "__main__":
    main()
