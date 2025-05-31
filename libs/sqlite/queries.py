CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS pull_requests (
    id INTEGER PRIMARY KEY, -- This is the PR number
    title TEXT NOT NULL,
    test TEXT, -- This is the test case for the PR
    explaination TEXT,
    files TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pull_request_embeddings (
    pull_request_id INTEGER PRIMARY KEY,
    embedding TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS issue_embeddings (
    issue_id INTEGER PRIMARY KEY,
    embedding TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY,           -- GitHub issue number
    title TEXT NOT NULL,
    steps TEXT,
    raw_body TEXT,
    labels TEXT,                       -- Stored as a JSON array
    is_processed BOOLEAN DEFAULT FALSE,
    culprit_pull_requests TEXT,              -- JSON array of CulpritPullRequest objects
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS issue_pull_request (
    issue_id INTEGER NOT NULL,
    pull_request_id INTEGER NOT NULL,
    PRIMARY KEY (issue_id, pull_request_id),
    FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests(id) ON DELETE CASCADE
);

"""

INSERT_PULL_REQUEST = """
INSERT OR REPLACE INTO pull_requests (id, title, test, explaination, files)
VALUES (?, ?, ?, ?, ?);
"""

GET_PULL_REQUEST_BY_ID_WITH_EMBEDDING = """
SELECT pr.id, pr.title, pr.test, pr.explaination, pr.files, pe.embedding
FROM pull_requests pr
LEFT JOIN pull_request_embeddings pe ON pe.pull_request_id = pr.id
WHERE pr.id = ?;
"""

INSERT_ISSUE = """
INSERT OR REPLACE INTO issues (id, title, steps, raw_body, labels)
VALUES (?, ?, ?, ?, ?);
"""

GET_ALL_ISSUES = """
SELECT * FROM issues;
"""

INSERT_ISSUE_PULL_REQUEST = """
INSERT OR IGNORE INTO issue_pull_request (issue_id, pull_request_id)
VALUES (?, ?);
"""

GET_ALL_ISSUE_PULL_REQUESTS = """
SELECT issue_id, pull_request_id from issue_pull_request;
"""

GET_PULL_REQUESTS_BY_ISSUE_ID = """
SELECT pr.id, pr.title, pr.test, pr.explaination, pr.files, pe.embedding
FROM pull_requests pr
JOIN issue_pull_request ipr ON ipr.pull_request_id = pr.id
LEFT JOIN pull_request_embeddings pe ON pe.pull_request_id = pr.id
WHERE ipr.issue_id = ?;
"""

UPDATE_ISSUE_PROCESSED_AND_CULPRITS = """
UPDATE issues
SET is_processed = ?, culprit_pull_requests = ?
WHERE id = ?;
"""

GET_ISSUE_BY_ID = """
SELECT * FROM issues WHERE id = ?;
"""

GET_ISSUE_IS_PROCESSED = """
SELECT is_processed FROM issues WHERE id = ?
"""

GET_PULL_REQUEST_EMBEDDING = """
SELECT embedding FROM pull_request_embeddings WHERE pull_request_id = ?;
"""

INSERT_PULL_REQUEST_EMBEDDING = """
INSERT OR REPLACE INTO pull_request_embeddings (pull_request_id, embedding)
VALUES (?, ?);
"""

INSERT_ISSUE_EMBEDDING = """
INSERT OR REPLACE INTO issue_embeddings (issue_id, embedding)
VALUES (?, ?);
"""
