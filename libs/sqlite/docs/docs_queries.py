CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS docs (
    path TEXT PRIMARY KEY,             -- relative to articles 'expenses/categories/New-Category.md'
    title TEXT NOT NULL,               -- 'New-Category.md'
    content_hash TEXT NOT NULL,        -- SHA256 of raw text
    content TEXT NOT NULL,          -- raw content of the file
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE IF NOT EXISTS doc_embeddings USING vec0(
    path TEXT PRIMARY KEY,
    embedding float[1536]
);
"""

GET_CONTENT_HASH = """
SELECT content_hash FROM docs WHERE path = ?;
"""

UPSERT_DOC = """
INSERT OR REPLACE INTO docs (path, title, content_hash, content, last_updated)
VALUES (?, ?, ?, ?, ?);
"""

UPSERT_DOC_EMBEDDING = """
INSERT OR REPLACE INTO doc_embeddings (path, embedding)
VALUES (?, ?);
"""

DELETE_DOC = """
DELETE FROM docs WHERE path = ?;
"""

GET_ALL_PATHS = """
SELECT path FROM docs;
"""

GET_ALL_DOCS_WITH_EMBEDDINGS = """
SELECT d.path, d.title, d.content_hash, de.embedding, d.content 
FROM docs d
LEFT JOIN doc_embeddings de ON de.path = d.path
WHERE de.embedding IS NOT NULL;
"""

GET_DOC_WITH_CONTENT_BY_PATH = """
SELECT path, title, content_hash, content FROM docs 
WHERE path = ?;
"""
