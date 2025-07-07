CREATE TABLE IF NOT EXISTS pull_request_test_steps (
    pull_request_id INTEGER PRIMARY KEY,
    test_steps TEXT, -- this is the generated test steps for the PR
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests(id) ON DELETE CASCADE
);