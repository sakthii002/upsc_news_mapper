import os
import scraper
import mapper

import sys
import traceback

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        sys.exit(1)

    print("Starting Daily News Scrape...")
    try:
        print("Step 1: Fetching articles from RSS feeds...")
        articles = scraper.fetch_articles()
        
        if not articles:
            print("No articles fetched from RSS feeds. Exiting gracefully.")
            return
            
        print(f"Step 2: Fetched {len(articles)} articles. Starting AI analysis and mapping...")
        count = mapper.process_and_save(articles, api_key)
        print(f"Step 3: Successfully processed and saved {count} UPSC-relevant articles.")
    except Exception as e:
        print("-" * 30)
        print("CRITICAL ERROR DURING EXECUTION:")
        traceback.print_exc()
        print("-" * 30)
        sys.exit(1)

if __name__ == "__main__":
    main()
