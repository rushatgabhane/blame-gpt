CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS pull_requests (
    id INTEGER PRIMARY KEY, -- This is the PR number
    title TEXT NOT NULL,
    test TEXT, -- This is the test case for the PR
    explaination TEXT,
    files TEXT
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY,           -- GitHub issue number
    title TEXT NOT NULL,
    steps TEXT,
    raw_body TEXT,
    labels TEXT                       -- Stored as a JSON array
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

GET_ALL_PULL_REQUESTS = """
SELECT * FROM pull_requests;
"""

SELECT_PR_BY_ID = "SELECT * FROM pull_requests WHERE id = ?;"

SELECT_ALL_PR_IDS = "SELECT id FROM pull_requests;"

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
SELECT pr.*
FROM pull_requests pr
JOIN issue_pull_request ipr ON ipr.pull_request_id = pr.id
WHERE ipr.issue_id = ?;
"""
