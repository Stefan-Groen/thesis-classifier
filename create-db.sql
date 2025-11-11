CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    link TEXT NOT NULL UNIQUE,
    date_published TIMESTAMP WITH TIME ZONE,
    summary TEXT,
    source TEXT,
    date_added TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'PENDING',
    classification TEXT,
    explanation TEXT,
    advice TEXT,
    reasoning TEXT,
    classification_date TIMESTAMP WITH TIME ZONE,
    starred BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_articles_link ON articles(link);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_date_published ON articles(date_published);
CREATE INDEX IF NOT EXISTS idx_articles_starred ON articles(starred);