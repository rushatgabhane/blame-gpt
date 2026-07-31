CREATE TABLE IF NOT EXISTS pull_requests (
    id INTEGER NOT NULL, -- This is the PR number
    repo_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    test TEXT, -- This is the test case for the PR
    explaination TEXT,
    files TEXT,
    code_diff_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, repo_id)
);

CREATE TABLE IF NOT EXISTS pull_request_embeddings (
    pull_request_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    embedding BLOB,              -- List of floats stored as a BLOB
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pull_request_id, repo_id),
    FOREIGN KEY (pull_request_id, repo_id) REFERENCES pull_requests(id, repo_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER NOT NULL,           -- GitHub issue number
    repo_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    steps TEXT,
    raw_body TEXT,
    labels TEXT,                       -- Stored as a JSON array
    is_processed BOOLEAN DEFAULT FALSE,
    culprit_pull_requests TEXT,              -- JSON array of CulpritPullRequest objects
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actual_pull_request_id INTEGER, -- The PR that is actually the culprit used for analysis
    PRIMARY KEY (id, repo_id),
    FOREIGN KEY (actual_pull_request_id, repo_id) REFERENCES pull_requests(id, repo_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS issue_embeddings (
    issue_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    embedding BLOB,              -- List of floats stored as a BLOB
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (issue_id, repo_id),
    FOREIGN KEY (issue_id, repo_id) REFERENCES issues(id, repo_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS issue_pull_request (
    issue_id INTEGER NOT NULL,
    pull_request_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    score float DEFAULT 0.0,
    PRIMARY KEY (issue_id, pull_request_id, repo_id),
    FOREIGN KEY (issue_id, repo_id) REFERENCES issues(id, repo_id) ON DELETE CASCADE,
    FOREIGN KEY (pull_request_id, repo_id) REFERENCES pull_requests(id, repo_id) ON DELETE CASCADE
);
