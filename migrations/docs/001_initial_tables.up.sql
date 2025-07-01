-- Initial tables for docs database
CREATE TABLE IF NOT EXISTS docs (
    path TEXT PRIMARY KEY,             -- relative to articles 'expenses/categories/New-Category.md'
    title TEXT NOT NULL,               -- 'New-Category.md'
    content_hash TEXT NOT NULL,        -- SHA256 of raw text
    embedding TEXT NOT NULL,
    content TEXT NOT NULL,          -- raw content of the file
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);