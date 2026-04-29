-- Add ON DELETE CASCADE / SET NULL to FK references.
-- SQLite cannot ALTER TABLE to change FK definitions, so each affected
-- table is recreated by copy-and-rename. FKs are temporarily disabled to
-- avoid the rename triggering integrity checks against the old table.
--
-- Affected:
--   generations.insight_id           -> CASCADE   (drop drafts when insight deleted)
--   calendar_slots.generation_id     -> SET NULL  (preserve slot but unlink draft)
--   feed_articles.feed_id            -> CASCADE   (drop articles when feed removed)
--   carousel_data.generation_id      -> CASCADE   (drop carousel when generation deleted)

PRAGMA foreign_keys=OFF;

BEGIN;

CREATE TABLE generations_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id INTEGER NOT NULL,
    draft_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    copied INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insight_id) REFERENCES insights(id) ON DELETE CASCADE
);
INSERT INTO generations_new SELECT id, insight_id, draft_number, content, copied, created_at FROM generations;
DROP TABLE generations;
ALTER TABLE generations_new RENAME TO generations;
CREATE INDEX IF NOT EXISTS idx_generations_insight ON generations(insight_id);

CREATE TABLE calendar_slots_new (
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
    FOREIGN KEY (generation_id) REFERENCES generations(id) ON DELETE SET NULL
);
INSERT INTO calendar_slots_new SELECT id, slot_date, day_of_week, content_type, generation_id, status, scheduled_time, notes, created_at, updated_at FROM calendar_slots;
DROP TABLE calendar_slots;
ALTER TABLE calendar_slots_new RENAME TO calendar_slots;
CREATE INDEX IF NOT EXISTS idx_calendar_slots_date ON calendar_slots(slot_date);
CREATE UNIQUE INDEX IF NOT EXISTS idx_calendar_slots_unique_date ON calendar_slots(slot_date);

CREATE TABLE feed_articles_new (
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
    FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE
);
INSERT INTO feed_articles_new SELECT id, feed_id, title, url, summary, author, published_at, fetched_at, relevance_score, relevance_reason, used, dismissed FROM feed_articles;
DROP TABLE feed_articles;
ALTER TABLE feed_articles_new RENAME TO feed_articles;
CREATE INDEX IF NOT EXISTS idx_feed_articles_feed ON feed_articles(feed_id);

CREATE TABLE carousel_data_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generation_id INTEGER NOT NULL UNIQUE,
    template_type TEXT NOT NULL,
    parsed_content TEXT NOT NULL,
    pdf_filename TEXT,
    slide_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generation_id) REFERENCES generations(id) ON DELETE CASCADE
);
INSERT INTO carousel_data_new SELECT id, generation_id, template_type, parsed_content, pdf_filename, slide_count, created_at FROM carousel_data;
DROP TABLE carousel_data;
ALTER TABLE carousel_data_new RENAME TO carousel_data;

COMMIT;

PRAGMA foreign_keys=ON;
