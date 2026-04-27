import os
import scraper
import mapper

import sys

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        sys.exit(1)

    print("Starting Daily News Scrape...")
    try:
        articles = scraper.fetch_articles()
        
        if not articles:
            print("No articles fetched.")
            return
            
        print(f"Fetched {len(articles)} articles. Starting AI analysis...")
        count = mapper.process_and_save(articles, api_key)
        print(f"Successfully processed and saved {count} UPSC-relevant articles.")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
