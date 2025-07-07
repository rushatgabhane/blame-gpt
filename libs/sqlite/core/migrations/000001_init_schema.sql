CREATE TABLE IF NOT EXISTS pull_requests (
    id INTEGER PRIMARY KEY, -- This is the PR number
    title TEXT NOT NULL,
    test TEXT, -- This is the test case for the PR
    explaination TEXT,
    files TEXT,
    code_diff_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pull_request_embeddings (
    pull_request_id INTEGER PRIMARY KEY,
    embedding TEXT,              -- Stored as a JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS issue_embeddings (
    issue_id INTEGER PRIMARY KEY,
    embedding TEXT,              -- Stored as a JSON array
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actual_pull_request_id INTEGER, -- The PR that is actually the culprit used for analysis
    FOREIGN KEY (actual_pull_request_id) REFERENCES pull_requests(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS issue_pull_request (
    issue_id INTEGER NOT NULL,
    pull_request_id INTEGER NOT NULL,
    score float DEFAULT 0.0,
    PRIMARY KEY (issue_id, pull_request_id),
    FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS pull_request_test_steps (
    pull_request_id INTEGER PRIMARY KEY,
    test_steps TEXT, -- this is the generated test steps for the PR
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests(id) ON DELETE CASCADE
);