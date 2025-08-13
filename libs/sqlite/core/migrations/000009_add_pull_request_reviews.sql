CREATE TABLE IF NOT EXISTS pull_request_reviews (
    pull_request_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    last_reviewed_commit_sha TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pull_request_id, repo_id)
);