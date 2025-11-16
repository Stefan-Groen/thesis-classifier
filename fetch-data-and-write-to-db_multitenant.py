"""
Multi-Tenant Article Fetching Script

This script fetches articles from RSS feeds and stores them in the database.
Articles are organization-agnostic (shared across all organizations).

Key Changes from Original:
- Articles table no longer has classification columns
- Articles are stored once and shared across all organizations
- No changes needed to the fetching logic itself
- The classification happens in LLM_multitenant.py instead
"""

import feedparser
import psycopg
import os
from dotenv import load_dotenv
from datetime import datetime


def fetch_feeds(url):
    """
    Fetch articles from RSS feeds
    """
    feed = feedparser.parse(url)
    articles = feed.entries
    len_feed = len(feed.entries)
    return articles, len_feed


def store_articles(articles):
    """
    Checks if articles are already stored in database, if not stores them.
    Function only returns the count of NEW articles.

    NOTE: Articles are now organization-agnostic (shared across all organizations)
    Classification happens later in LLM_multitenant.py
    """
    # Get connection string from .env file
    CONN_STRING = os.getenv('DATABASE_URL')
    if not CONN_STRING:
        raise ValueError("DATABASE_URL not found in environment variables.")

    new_article_count = 0

    try:
        with psycopg.connect(CONN_STRING) as conn:
            with conn.cursor() as cursor:
                for article in articles:
                    title = article.get('title', 'N/A')
                    link = article.get('link', 'N/A')
                    summary = article.get('summary', 'N/A')
                    source = article.get('title_detail', {}).get('base', 'N/A')

                    date_published = None
                    raw_date = article.get('published')

                    # Parse standard RSS date to datetime object (with timezone)
                    # Fallback for formats without timezone
                    if raw_date:
                        try:
                            dt = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %z')
                            date_published = dt
                        except ValueError:
                            try:
                                dt = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S')
                                date_published = dt
                            except ValueError:
                                pass

                    # Insert article (organization-agnostic)
                    # Note: No classification fields here anymore
                    sql = '''
                    INSERT INTO articles (title, link, date_published, summary, source)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (link) DO NOTHING
                    RETURNING id;
                    '''

                    cursor.execute(sql, (
                        title,
                        link,
                        date_published,
                        summary,
                        source
                    ))

                    # If fetchone() returns a result, it means a new row was inserted
                    if cursor.fetchone():
                        new_article_count += 1

        # 'with' block auto-commits here
        return new_article_count

    except (psycopg.OperationalError, Exception) as e:
        print(f"Database connection or query error: {e}")
        return 0  # Return 0 on error


def main():
    # Load environment variables from .env file
    load_dotenv()

    NOS_links = [
        'https://feeds.nos.nl/nosnieuwsalgemeen',
        'https://feeds.nos.nl/nosnieuwsbinnenland',
        'https://feeds.nos.nl/nosnieuwsbuitenland',
        'https://feeds.nos.nl/nosnieuwspolitiek',
        'https://feeds.nos.nl/nosnieuwseconomie',
        'https://feeds.nos.nl/nosnieuwsopmerkelijk',
        'https://feeds.nos.nl/nosnieuwskoningshuis',
        'https://feeds.nos.nl/nosnieuwscultuurenmedia',
        'https://feeds.nos.nl/nosnieuwstech',
        'https://feeds.nos.nl/nossportalgemeen',
        'https://feeds.nos.nl/nosvoetbal',
        'https://feeds.nos.nl/nossportwielrennen',
        'https://feeds.nos.nl/nossportschaatsen',
        'https://feeds.nos.nl/nossporttennis',
        'https://feeds.nos.nl/nossportformule1',
        'https://feeds.nos.nl/nieuwsuuralgemeen',
        'https://feeds.nos.nl/nosop3',
    ]

    total_new_articles = 0

    for url in NOS_links:
        try:
            articles, len_feed = fetch_feeds(url)
            number_of_new_articles_stored = store_articles(articles)
            print(f'--> Stored {number_of_new_articles_stored} new articles out of {len_feed} from {url}.')
            total_new_articles += number_of_new_articles_stored
        except Exception as e:
            print(f"Failed to process feed {url}: {e}")

    print(f"\n=== Run complete. Total new articles stored: {total_new_articles} ===")
    print(f"\nNext step: Run LLM_multitenant.py to classify these articles for all organizations")


if __name__ == "__main__":
    main()
