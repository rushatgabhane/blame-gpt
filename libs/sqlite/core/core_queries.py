INSERT_PULL_REQUEST = """
INSERT OR REPLACE INTO pull_requests (id, repo_id, title, test, explanation, files, code_diff_summary, linked_issue_ids)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""

GET_PULL_REQUEST_BY_ID_WITH_EMBEDDING = """
SELECT pr.id, pr.title, pr.test, pr.explanation, pr.files, pr.code_diff_summary, pr.linked_issue_ids, pe.embedding
FROM pull_requests pr
LEFT JOIN pull_request_embeddings pe ON pe.pull_request_id = pr.id AND pe.repo_id = pr.repo_id
WHERE pr.id = ? AND pr.repo_id = ?;
"""

INSERT_ISSUE = """
INSERT OR REPLACE INTO issues (id, repo_id, title, steps, raw_body, labels)
VALUES (?, ?, ?, ?, ?, ?);
"""

GET_ISSUE_BY_ID = """
SELECT id, title, steps, raw_body, labels, is_processed, culprit_pull_requests, actual_pull_request_id
FROM issues
WHERE id = ? AND repo_id = ?;
"""

GET_ALL_ISSUES = """
SELECT id, title, steps, raw_body, labels, is_processed, culprit_pull_requests FROM issues;
"""

GET_ALL_PULL_REQUEST_IDS = """
SELECT id FROM pull_requests WHERE repo_id = ?
"""

INSERT_ISSUE_PULL_REQUEST = """
INSERT OR IGNORE INTO issue_pull_request (issue_id, pull_request_id, repo_id)
VALUES (?, ?, ?);
"""

GET_ALL_ISSUE_PULL_REQUESTS = """
SELECT issue_id, pull_request_id, score from issue_pull_request;
"""

GET_PULL_REQUESTS_BY_ISSUE_ID = """
SELECT pr.id, pr.title, pr.test, pr.explanation, pr.files, pr.code_diff_summary, pe.embedding
FROM pull_requests pr
JOIN issue_pull_request ipr ON ipr.pull_request_id = pr.id AND ipr.repo_id = pr.repo_id
LEFT JOIN pull_request_embeddings pe ON pe.pull_request_id = pr.id AND pe.repo_id = pr.repo_id
WHERE ipr.issue_id = ? AND ipr.repo_id = ?;
"""

UPDATE_ISSUE_PROCESSED_AND_CULPRITS = """
UPDATE issues
SET is_processed = ?, culprit_pull_requests = ?
WHERE id = ? AND repo_id = ?;
"""

GET_ISSUE_IS_PROCESSED = """
SELECT is_processed FROM issues WHERE id = ? AND repo_id = ?
"""

GET_PULL_REQUEST_EMBEDDING = """
SELECT embedding FROM pull_request_embeddings WHERE pull_request_id = ? AND repo_id = ?;
"""

INSERT_PULL_REQUEST_EMBEDDING = """
INSERT OR REPLACE INTO pull_request_embeddings (pull_request_id, repo_id, embedding)
VALUES (?, ?, ?);
"""

INSERT_ISSUE_EMBEDDING = """
INSERT OR REPLACE INTO issue_embeddings (issue_id, repo_id, embedding)
VALUES (?, ?, ?);
"""

UPDATE_ISSUE_PULL_REQUEST_SCORE = """
UPDATE issue_pull_request
SET score = ?
WHERE issue_id = ? AND pull_request_id = ? AND repo_id = ?;
"""

UPDATE_ISSUE_ACTUAL_PULL_REQUEST = """
UPDATE issues
SET actual_pull_request_id = ?
WHERE id = ? AND repo_id = ?;
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
u.id, u.username, u.email, u.name, u.avatar_url, u.is_active,
lc.id, lc.usage_log_id, lc.llm_model, lc.tokens_used, lc.cost_usd_thousandths, lc.created_at
FROM usage_logs ul
JOIN users u ON u.id = ul.user_id
LEFT JOIN llm_calls lc ON lc.usage_log_id = ul.id
ORDER BY ul.created_at DESC;
"""

GET_USAGE_LOGS_BY_USER_ID = """
SELECT ul.id, ul.command_name, ul.comment_url, ul.output, ul.issue_or_pull_request_url, ul.created_at
FROM usage_logs ul
WHERE ul.user_id = ?;
"""

ADD_LLM_CALL = """
INSERT INTO llm_calls (usage_log_id, llm_model, tokens_used, cost_usd_thousandths)
VALUES (?, ?, ?, ?);
"""


GET_PULL_REQUEST_REVIEW_SHA = """
SELECT last_reviewed_commit_sha FROM pull_request_reviews
WHERE pull_request_id = ? AND repo_id = ?;
"""

INSERT_OR_UPDATE_PULL_REQUEST_REVIEW = """
INSERT OR REPLACE INTO pull_request_reviews (pull_request_id, repo_id, last_reviewed_commit_sha, updated_at)
VALUES (?, ?, ?, CURRENT_TIMESTAMP);
"""
