INSERT_PULL_REQUEST = """
INSERT OR REPLACE INTO pull_requests (id, title, test, explaination, files, code_diff_summary)
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
SELECT pr.id, pr.title, pr.test, pr.explaination, pr.files, pr.code_diff_summary, pe.embedding
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
