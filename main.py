import os
import scraper
import mapper

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return

    print("Starting Daily News Scrape...")
    articles = scraper.fetch_articles()
    
    if not articles:
        print("No articles fetched.")
        return
        
    print(f"Fetched {len(articles)} articles. Starting AI analysis...")
    count = mapper.process_and_save(articles, api_key)
    print(f"Successfully processed and saved {count} UPSC-relevant articles.")

if __name__ == "__main__":
    main()
