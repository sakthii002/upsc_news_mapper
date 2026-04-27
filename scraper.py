import feedparser
import requests
from bs4 import BeautifulSoup
import time
import socket

# Set global timeout to prevent hanging
socket.setdefaulttimeout(30)

FEEDS = {
    "National": "https://www.thehindu.com/news/national/feeder/default.rss",
    "International": "https://www.thehindu.com/news/international/feeder/default.rss",
    "Business": "https://www.thehindu.com/business/feeder/default.rss",
    "Editorial": "https://www.thehindu.com/opinion/feeder/default.rss",
    "Sci-Tech": "https://www.thehindu.com/sci-tech/feeder/default.rss"
}

def get_article_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # The Hindu usually stores content in these div classes
            content_div = soup.find('div', class_='article--container') or \
                          soup.find('div', class_='article-body-container') or \
                          soup.find('div', class_='content-body')
            
            if content_div:
                paragraphs = content_div.find_all('p')
                return "\n".join([p.get_text() for p in paragraphs])
            return ""
    except Exception as e:
        print(f"  !! Error downloading {url}: {e}")
    return ""

def fetch_articles():
    articles_data = []
    
    for section, url in FEEDS.items():
        print(f"Fetching {section} news...")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                try:
                    text = get_article_text(entry.link)
                    if text:
                        articles_data.append({
                            "title": entry.title,
                            "link": entry.link,
                            "published": entry.published if hasattr(entry, 'published') else time.strftime("%Y-%m-%d"),
                            "section": section,
                            "text": text
                        })
                    else:
                        print(f"  !! No text found for {entry.link}")
                except Exception as e:
                    print(f"  !! Error parsing {entry.link}: {e}")
        except Exception as e:
            print(f"  !! Error reading feed {section}: {e}")
    return articles_data

if __name__ == "__main__":
    articles = fetch_articles()
    print(f"Fetched {len(articles)} articles.")
