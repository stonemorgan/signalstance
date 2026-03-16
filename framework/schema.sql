CREATE TABLE IF NOT EXISTS insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    raw_input TEXT NOT NULL,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id INTEGER NOT NULL,
    draft_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    copied INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insight_id) REFERENCES insights(id)
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calendar_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_date DATE NOT NULL,
    day_of_week INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    generation_id INTEGER,
    status TEXT NOT NULL DEFAULT 'empty',
    scheduled_time TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generation_id) REFERENCES generations(id)
);

CREATE TABLE IF NOT EXISTS feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_fetched_at TIMESTAMP,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feed_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    summary TEXT,
    author TEXT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    relevance_score REAL,
    relevance_reason TEXT,
    used INTEGER DEFAULT 0,
    dismissed INTEGER DEFAULT 0,
    FOREIGN KEY (feed_id) REFERENCES feeds(id)
);

CREATE TABLE IF NOT EXISTS carousel_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generation_id INTEGER NOT NULL UNIQUE,
    template_type TEXT NOT NULL,
    parsed_content TEXT NOT NULL,
    pdf_filename TEXT,
    slide_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generation_id) REFERENCES generations(id)
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_calendar_slots_date ON calendar_slots(slot_date);
CREATE INDEX IF NOT EXISTS idx_generations_insight ON generations(insight_id);
CREATE INDEX IF NOT EXISTS idx_feed_articles_feed ON feed_articles(feed_id);

-- Uniqueness constraint on calendar slots
CREATE UNIQUE INDEX IF NOT EXISTS idx_calendar_slots_unique_date ON calendar_slots(slot_date);
