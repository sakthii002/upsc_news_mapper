import feedparser
from newspaper import Article
import time

FEEDS = {
    "National": "https://www.thehindu.com/news/national/feeder/default.rss",
    "International": "https://www.thehindu.com/news/international/feeder/default.rss",
    "Business": "https://www.thehindu.com/business/feeder/default.rss",
    "Editorial": "https://www.thehindu.com/opinion/feeder/default.rss",
    "Sci-Tech": "https://www.thehindu.com/sci-tech/feeder/default.rss"
}

def fetch_articles():
    articles_data = []
    for section, url in FEEDS.items():
        print(f"Fetching {section} news...")
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:  # Reduced from 10 to 5 to save AI tokens
            try:
                article = Article(entry.link)
                article.download()
                if article.download_state == 2: # 2 is SUCCESS
                    article.parse()
                    articles_data.append({
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.published if hasattr(entry, 'published') else time.strftime("%Y-%m-%d"),
                        "section": section,
                        "text": article.text
                    })
                else:
                    print(f"Download failed for {entry.link}")
            except Exception as e:
                print(f"Failed to fetch {entry.link}: {e}")
    return articles_data

if __name__ == "__main__":
    articles = fetch_articles()
    print(f"Fetched {len(articles)} articles.")
