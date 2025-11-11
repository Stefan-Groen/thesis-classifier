CREATE TABLE IF NOT EXISTS articles (
  id                  SERIAL PRIMARY KEY,
  status              TEXT DEFAULT 'PENDING',
  title               TEXT NOT NULL,
  link                TEXT NOT NULL UNIQUE,
  summary             TEXT,
  date_published      TIMESTAMPTZ,
  source              TEXT,
  date_added          TIMESTAMPTZ DEFAULT NOW(),
  classification      TEXT DEFAULT '' CHECK (classification IN ('Threat','Opportunity','Neutral','Error: Unknown','')),
  explanation         TEXT DEFAULT '',
  reasoning           TEXT DEFAULT '',
  classification_date TIMESTAMPTZ,
  starred             BOOLEAN DEFAULT false NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_articles_date_published ON articles(date_published);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_classification ON articles(classification);
CREATE INDEX IF NOT EXISTS idx_articles_classification_date ON articles(classification_date);
CREATE INDEX IF NOT EXISTS idx_articles_starred ON articles(starred);