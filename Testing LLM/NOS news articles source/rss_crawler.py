import feedparser
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
import trafilatura
import random
from newspaper import Article, Config  # Added Config
from textblob import TextBlob
from textblob_nl import PatternAnalyzer


def run_crawler(source, feed_url):
    """
    Crawler with advanced Newspaper3k configuration and extraction tracking.
    """
    print(f"\nStarting to crawl: {source} ({feed_url})")

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    ]

    current_ua = random.choice(user_agents)

    config = Config()
    config.browser_user_agent = current_ua
    config.request_timeout = 15
    config.memoize_articles = False

    try:
        headers = {'User-Agent': current_ua}
        response = requests.get(feed_url, headers=headers, timeout=10)
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"Connection error for {source}: {e}")
        return

    articles = []
    for entry in feed.entries:
        print(f"Processing: {entry.title[:50]}...")
        full_text = ""
        method = "none" # Track which extraction method succeeded

        # STRATEGY 1: Try Trafilatura first
        try:
            downloaded = trafilatura.fetch_url(entry.link)
            if downloaded:
                full_text = trafilatura.extract(downloaded, include_comments=False)
                if full_text and len(full_text) > 150:
                    method = "full_trafilatura"
        except Exception:
            full_text = ""

        # STRATEGY 2: Advanced Newspaper3k Fallback
        if not full_text or len(full_text) < 150:
            try:
                nlp_article = Article(entry.link, config=config)
                nlp_article.download()
                nlp_article.parse()
                full_text = nlp_article.text
                if full_text and len(full_text) > 150:
                    method = "full_newspaper3k"
            except Exception as e:
                print(f"   Newspaper3k failed: {e}")

        # STRATEGY 3: RSS Summary Fallback
        if not full_text or len(full_text) < 100:
            full_text = entry.get('summary', '')
            if len(full_text) > 50:
                method = "rss_summary"
                print(f"   Fallback: Using RSS summary.")
            else:
                method = "failed"
                print(f"   WARNING: No content found for: {source}")

        articles.append({
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source,
            "title": entry.title,
            "content": full_text,
            "extraction_method": method, # New column for transparency
            "url": entry.link
        })

    if articles:
        save_to_csv(source, articles)


def save_to_csv(source, articles):
    """
    Saves articles to a tab-delimited file in 'crawled_data'.
    """
    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir / "crawled_data"
    output_dir.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = output_dir / f"articles_{source.lower().replace(' ', '_')}_{date_str}.txt"

    df = pd.DataFrame(articles)

    if filename.exists():
        df.to_csv(filename, mode='a', sep='\t', index=False, header=False)
    else:
        df.to_csv(filename, sep='\t', index=False)

    print(f"Successfully saved {len(articles)} articles to: {filename}")


if __name__ == "__main__":
    feeds = {
        "Mediacourant": "https://www.mediacourant.nl/feed/",
        "Nu_Achterklap": "https://www.nu.nl/rss/Achterklap",
        "Nu_Entertainment": "https://www.nu.nl/rss/entertainment",
        "RTL_Boulevard": "https://www.rtlboulevard.nl/rss.xml",
        "Telegraaf_Entertainment": "https://www.telegraaf.nl/entertainment/rss",
        "AD_Show": "https://www.ad.nl/show/rss.xml",
        "Nu_Opmerkelijk": "https://www.nu.nl/rss/opmerkelijk"
    }

    for name, url in feeds.items():
        run_crawler(name, url)
