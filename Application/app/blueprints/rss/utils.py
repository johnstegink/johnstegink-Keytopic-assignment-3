import feedparser
import requests
from datetime import datetime


def parse_rss_feed(feed_url):
    """
    Parse an RSS feed and extract article information

    Args:
        feed_url: URL of the RSS feed

    Returns:
        Dictionary with success status, articles list, and feed title or error message
    """
    try:
        # Validate URL format
        if not feed_url.startswith(('http://', 'https://')):
            return {
                'success': False,
                'error': 'De URL moet beginnen met http:// of https://'
            }

        # Try to fetch the feed with timeout
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()

        # Parse the feed
        feed = feedparser.parse(response.content)

        # Check if the feed was parsed successfully
        if feed.bozo and not feed.entries:
            return {
                'success': False,
                'error': 'Kon de RSS-feed niet verwerken. Controleer of de URL correct is.'
            }

        # Extract feed title
        feed_title = feed.feed.get('title', 'RSS-feed')

        # Extract articles
        articles = []
        for entry in feed.entries[:20]:  # Limit to 20 articles
            # Get summary/description
            summary = entry.get('summary', entry.get('description', ''))

            # Clean and truncate summary
            if summary:
                # Remove HTML tags (basic cleaning)
                import re
                summary = re.sub(r'<[^>]+>', '', summary)
                # Truncate to 200 characters
                if len(summary) > 200:
                    summary = summary[:197] + '...'
            else:
                summary = 'Geen samenvatting beschikbaar.'

            # Get publication date
            published = entry.get('published', entry.get('updated', ''))
            if published:
                try:
                    # Try to parse and format the date
                    parsed_date = feedparser._parse_date(entry.get('published_parsed',
                                                                   entry.get('updated_parsed')))
                    if parsed_date:
                        published = datetime(*parsed_date[:6]).strftime('%d-%m-%Y')
                except:
                    pass

            article = {
                'title': entry.get('title', 'Geen titel'),
                'link': entry.get('link', '#'),
                'summary': summary,
                'published': published,
                'author': entry.get('author', '')
            }

            articles.append(article)

        return {
            'success': True,
            'articles': articles,
            'feed_title': feed_title
        }

    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'De verbinding duurde te lang. Probeer het opnieuw.'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Kon de feed niet ophalen: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Er is een fout opgetreden: {str(e)}'
        }

