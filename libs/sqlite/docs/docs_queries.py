GET_CONTENT_HASH = """
SELECT content_hash FROM docs WHERE path = ?;
"""

UPSERT_DOC = """
INSERT OR REPLACE INTO docs (path, title, content_hash, embedding, content, last_updated)
VALUES (?, ?, ?, ?, ?, ?);
"""

DELETE_DOC = """
DELETE FROM docs WHERE path = ?;
"""

GET_ALL_PATHS = """
SELECT path FROM docs;
"""

GET_ALL_DOCS_WITH_EMBEDDINGS = """
SELECT path, title, content_hash, embedding, content FROM docs;
"""

GET_DOC_WITH_CONTENT_BY_PATH = """
SELECT path, title, content_hash, content FROM docs 
WHERE path = ?;
"""
