import feedparser
import trafilatura
import psycopg2
from psycopg2 import sql
import re
import os
import html
from sentence_transformers import SentenceTransformer
import torch
from pathlib import Path
from dotenv import load_dotenv
from textblob import TextBlob
from textblob_nl import PatternAnalyzer

# Database configuration
DB_CONFIG = {
    "dbname": "rss",
    "user": "john",
    "password": "geheimwachtwoord",
    "host": "localhost",
    "port": "5432"
}


def get_clean_text(url):
    """Fetches only the main text and ignores menus/footers."""
    try:
        # Download the page
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return "Could not download page"

        # Extract the text (automatically removes junk)
        # include_comments=False ensures clean extraction
        result = trafilatura.extract(downloaded, include_comments=False, include_tables=True)

        return result if result else "No usable text found"
    except Exception as e:
        return f"Extraction error: {e}"


def save_to_postgres(source, articles):
    """Saves articles and prevents duplicates via URL."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        insert_query = """
                       INSERT INTO rss_artikelen (
                           bron, titel, samenvatting, volledige_tekst, url, 
                           title_embedding, summary_embedding, text_embedding,
                           titel_polariteit, titel_subjectiviteit,
                           samenvatting_polariteit, samenvatting_subjectiviteit,
                           tekst_polariteit, tekst_subjectiviteit
                       )
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (url) DO \
                       UPDATE \
                           SET volledige_tekst = EXCLUDED.volledige_tekst, \
                               title_embedding = EXCLUDED.title_embedding, \
                               summary_embedding = EXCLUDED.summary_embedding, \
                               text_embedding = EXCLUDED.text_embedding, \
                               titel_polariteit = EXCLUDED.titel_polariteit, \
                               titel_subjectiviteit = EXCLUDED.titel_subjectiviteit, \
                               samenvatting_polariteit = EXCLUDED.samenvatting_polariteit, \
                               samenvatting_subjectiviteit = EXCLUDED.samenvatting_subjectiviteit, \
                               tekst_polariteit = EXCLUDED.tekst_polariteit, \
                               tekst_subjectiviteit = EXCLUDED.tekst_subjectiviteit; -- Update text and embeddings if URL already exists \
                       """

        for art in articles:
            cur.execute(insert_query, (
                source, art['title'], art['summary'], art['full_text'], art['url'], 
                art['title_embedding'], art['summary_embedding'], art['full_text_embedding'],
                art['title_polarity'], art['title_subjectivity'],
                art['summary_polarity'], art['summary_subjectivity'],
                art['text_polarity'], art['text_subjectivity']
            ))

        conn.commit()
        cur.close()
        conn.close()
        print(f"Database successfully updated with {len(articles)} items.")
    except Exception as e:
        print(f"Database error: {e}")


def run_crawler(source, feed_url, model):
    print(f"Starting to crawl: {feed_url}")
    feed = feedparser.parse(feed_url)
    cleaned_articles = []
    
    for entry in feed.entries:
        print(f"Cleaning: {entry.title[:60]}...")

        # Get the pure text without HTML junk
        full_text = get_clean_text(entry.link)
        
        # Remove HTML tags from the summary
        raw_summary = entry.get('summary', '')
        clean_summary = html.unescape(re.sub(r'<[^>]+>', '', raw_summary)).strip()

        # Sentiment Analysis
        title_blob = TextBlob(str(entry.title), analyzer=PatternAnalyzer())
        summary_blob = TextBlob(str(clean_summary), analyzer=PatternAnalyzer())
        text_blob = TextBlob(str(full_text), analyzer=PatternAnalyzer())

        print(f"Generating embeddings...")
        embeddings = model.encode([entry.title, clean_summary, full_text], convert_to_tensor=True, device="mps")

        cleaned_articles.append({
            "source": source,
            "title": entry.title,
            "summary": clean_summary,
            "url": entry.link,
            "full_text": full_text,
            "title_embedding": embeddings[0].tolist(),
            "summary_embedding": embeddings[1].tolist(),
            "full_text_embedding": embeddings[2].tolist(),
            "title_polarity": title_blob.sentiment[0],
            "title_subjectivity": title_blob.sentiment[1],
            "summary_polarity": summary_blob.sentiment[0],
            "summary_subjectivity": summary_blob.sentiment[1],
            "text_polarity": text_blob.sentiment[0],
            "text_subjectivity": text_blob.sentiment[1]
        })

    save_to_postgres(source, cleaned_articles)


# Load environment variables from .env so the CSV file name can be configured.
script_dir = Path(__file__).resolve().parent
load_dotenv()


model_name = os.environ.get("SENTENCE_EMBEDDING_MODEL")
if not model_name:
    print("Error: SENTENCE_EMBEDDING_MODEL was not found in .env or environment.")
    exit(1)

print("Loading embedding model...")
model = SentenceTransformer(model_name, device='mps')

run_crawler("Mediacourant", "https://www.mediacourant.nl/feed/", model)
run_crawler("Nu.nl Achterklap", "https://www.nu.nl/rss/Achterklap", model)
run_crawler("Nu.nl Media & Cultuur", "https://www.nu.nl/rss/entertainment", model)
