import sqlite3
from pathlib import Path

# database path
DB_name = 'thesis'
DB_path = Path(f"/Users/stefan/Documents/thesis_code/{DB_name}.db")

def setup_database(DB_path):
    
    # connect to database (creates file if missing)
    connect = sqlite3.connect(DB_path)
    cursor = connect.cursor()

    # create tables for storing articles and classifications
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status TEXT DEFAULT 'PENDING' CHECK(status IN ('FAILED', 'PENDING', 'SENT')),
        title TEXT NOT NULL,
        link TEXT NOT NULL UNIQUE,
        summary TEXT,
        date_published TEXT,
        source TEXT,
        date_added TEXT DEFAULT CURRENT_TIMESTAMP,
        classification TEXT DEFAULT '' CHECK(classification IN ('Threat','Opportunity','Neutral','')),
        explanation TEXT DEFAULT '',
        pdf TEXT DEFAULT ''
            
    );
    """)


    connect.commit()
    connect.close()
    print(f'database created at {DB_path}')


if __name__ == "__main__":
    setup_database(DB_path)

                         
