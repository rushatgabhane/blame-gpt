-- Index for pull_request_test_steps.pull_request_id - used in GET_PULL_REQUEST_TEST_STEPS_BY_ID  
CREATE INDEX IF NOT EXISTS idx_pr_test_steps_pr_id ON pull_request_test_steps(pull_request_id);

-- Index for pull_request_embeddings.pull_request_id - used in joins and lookups
CREATE INDEX IF NOT EXISTS idx_pr_embeddings_pr_id ON pull_request_embeddings(pull_request_id);

-- Index for issue_pull_request - used in GET_PULL_REQUESTS_BY_ISSUE_ID join
CREATE INDEX IF NOT EXISTS idx_issue_pr_issue_id ON issue_pull_request(issue_id); 