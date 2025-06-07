CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS docs (
    path TEXT PRIMARY KEY,             -- relative to articles 'expenses/categories/New-Category.md'
    title TEXT NOT NULL,               -- 'New-Category.md'
    content_hash TEXT NOT NULL,        -- SHA256 of raw text
    embedding TEXT NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

GET_CONTENT_HASH = "SELECT content_hash FROM docs WHERE path = ?;"

UPSERT_DOC = """
INSERT OR REPLACE INTO docs (path, title, content_hash, embedding, last_updated)
VALUES (?, ?, ?, ?, ?);
"""

DELETE_DOC = "DELETE FROM docs WHERE path = ?;"
