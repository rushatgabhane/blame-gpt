INSERT_PULL_REQUEST = """
INSERT OR IGNORE INTO pull_requests (id, title, test, explaination, files, code_diff_summary)
VALUES (?, ?, ?, ?, ?, ?);
"""

GET_PULL_REQUEST_BY_ID_WITH_EMBEDDING = """
SELECT pr.id, pr.title, pr.test, pr.explaination, pr.files, pr.code_diff_summary, pe.embedding
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
SELECT issue_id, pull_request_id, score from issue_pull_request;
"""

GET_PULL_REQUESTS_BY_ISSUE_ID = """
SELECT pr.id, pr.title, pr.test, pr.explaination, pr.files, pr.code_diff_summary, pe.embedding
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

UPDATE_ISSUE_PULL_REQUEST_SCORE = """
UPDATE issue_pull_request
SET score = ?
WHERE issue_id = ? AND pull_request_id = ?;
"""

UPADTE_ISSUE_ACTUAL_PULL_REQUEST = """
UPDATE issues
SET actual_pull_request_id = ?
WHERE id = ?;
"""

GET_PULL_REQUEST_TEST_STEPS = """
SELECT pr.id, pr.title, pr.test, pr.explaination, pr.files, pr.code_diff_summary, prts.test_steps
FROM pull_requests pr
LEFT JOIN pull_request_test_steps prts ON prts.pull_request_id = pr.id
WHERE pr.id = ?;
"""

ADD_PULL_REQUEST_TEST_STEPS = """
INSERT OR REPLACE INTO pull_request_test_steps (pull_request_id, test_steps)
VALUES (?, ?);
"""

UPDATE_PULL_REQUEST_TEST_STEPS = """
UPDATE pull_request_test_steps
SET test_steps = ?
WHERE pull_request_id = ?;
"""

ADD_USER = """
INSERT OR IGNORE INTO users (username, email, name, avatar_url)
VALUES (?, ?, ?, ?)
RETURNING id;
"""

GET_USER_BY_USERNAME = """
SELECT id, username, email, name, avatar_url, is_active
FROM users
WHERE username = ?;
"""

GET_USER_ID_BY_USERNAME = """
SELECT id FROM users WHERE username = ?;
"""

GET_ALL_USERS = """
SELECT id, username, email, name, avatar_url, is_active FROM users;
"""

ADD_USAGE_LOG = """
INSERT INTO usage_logs (user_id, command_name, comment_url, output, issue_or_pull_request_url, comment_text)
VALUES (?, ?, ?, ?, ?, ?);
"""

GET_ALL_USAGE_LOGS_FOR_ALL_USERS = """
SELECT ul.id, ul.command_name, ul.comment_url, ul.output, ul.issue_or_pull_request_url, ul.created_at, ul.comment_text, 
u.id, u.username, u.email, u.name, u.avatar_url, u.is_active
FROM usage_logs ul
JOIN users u ON u.id = ul.user_id
ORDER BY ul.created_at DESC;
"""

GET_USAGE_LOGS_BY_USER_ID = """
SELECT ul.id, ul.command_name, ul.comment_url, ul.output, ul.issue_or_pull_request_url, ul.created_at
FROM usage_logs ul
WHERE ul.user_id = ?;
"""

ADD_LLM_CALL = """
INSERT INTO llm_calls (usage_log_id, llm_model, tokens_used, cost_usd_cents)
VALUES (?, ?, ?, ?);
"""
