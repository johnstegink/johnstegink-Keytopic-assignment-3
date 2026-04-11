from flask import render_template, request, flash, redirect, url_for
from app.blueprints.rss import rss_bp
from app.blueprints.rss.utils import parse_rss_feed


@rss_bp.route('/', methods=['GET', 'POST'])
def index():
    """Home page with RSS feed input form"""
    articles = []
    feed_url = ''
    feed_title = ''
    base_on = 'summary'

    if request.method == 'POST':
        feed_url = request.form.get('feed_url', '').strip()
        base_on = request.form.get('base_on', 'samenvatting')

        if feed_url:
            result = parse_rss_feed(feed_url, base_on)

            if result['success']:
                articles = result['articles']
                feed_title = result['feed_title']
            else:
                flash(result['error'], 'error')
        else:
            flash('Voer een geldige RSS-feed-URL in.', 'error')

    return render_template('index.html',
                         articles=articles,
                         feed_url=feed_url,
                         feed_title=feed_title,
                         base_on=base_on)
