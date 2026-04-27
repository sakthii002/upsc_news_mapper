import feedparser
from newspaper import Article
import time

from newspaper import Article, Config
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
    # Setup newspaper config to prevent hangs
    config = Config()
    config.request_timeout = 10 # 10 second timeout per article
    config.fetch_images = False  # Faster
    config.memoize_articles = False
    
    for section, url in FEEDS.items():
        print(f"Fetching {section} news...")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                try:
                    article = Article(entry.link, config=config)
                    article.download()
                    if article.download_state == 2:
                        article.parse()
                        articles_data.append({
                            "title": entry.title,
                            "link": entry.link,
                            "published": entry.published if hasattr(entry, 'published') else time.strftime("%Y-%m-%d"),
                            "section": section,
                            "text": article.text
                        })
                    else:
                        print(f"  !! Download failed (Timeout/Error): {entry.link}")
                except Exception as e:
                    print(f"  !! Error parsing {entry.link}: {e}")
        except Exception as e:
            print(f"  !! Error reading feed {section}: {e}")
    return articles_data

if __name__ == "__main__":
    articles = fetch_articles()
    print(f"Fetched {len(articles)} articles.")
