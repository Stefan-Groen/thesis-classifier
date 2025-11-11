import feedparser
import sqlite3
from datetime import datetime
from pathlib import Path


def fetch_feeds(url):
    ''' Fetch articles from RSS feeds '''
    feed = feedparser.parse(url)
    articles = feed.entries
    len_feed = len(feed.entries)
    return articles, len_feed



def store_articles(articles, db_path):
    ''' checks if articles are already stored, if not stores them. Functions only returns new articles '''

    # open database connection
    connect = sqlite3.connect(db_path)
    cursor = connect.cursor()

    new_articles = []

    # for each article in the article feed of 1 url --> get title, link, summary, source and data published
    for article in articles: 
        title = article.get('title', 'N/A')
        link = article.get('link', 'N/A')
        summary = article.get('summary', 'N/A')
        source = article.get('title_detail', {}).get('base', 'N/A')
        
        raw_date = article.get('published')
        try:
            dt = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %z')
            date_published = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            None

        # check if article link already exists in database
        cursor.execute("SELECT id FROM articles WHERE link = ?", (link,))
        exists = cursor.fetchone()

        # insert into database only if article is new (prevent duplicates)
        if not exists:
            cursor.execute(
                'INSERT INTO articles (title, link, date_published, summary, source) VALUES (?, ?, ?, ?, ?)',
                (title, link, date_published, summary, source)
            )
            new_articles.append(article)
    
    # Save and close database connection
    connect.commit()
    connect.close()

    number_of_new_articles = len(new_articles)
    return number_of_new_articles


def main():
    
    # database path and NOS RSS-feed URLs
    DB_path = Path("/Users/stefan/Documents/thesis_code/rss_DB.db")
    rss_urls_NOS = [
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
    
    # For every URL in the list of URLs, we fetch the articles with the fetch_feeds function
    for url in rss_urls_NOS:
        fetched_articles, len_feed = fetch_feeds(url)
        number_of_new_articles = store_articles(fetched_articles, DB_path)
        print(f'{number_of_new_articles} out of {len_feed} new articles stored from {url}')


if __name__ == "__main__":
    main()





