-- Drop all tables in reverse order to respect foreign key constraints
DROP TABLE IF EXISTS issue_pull_request;
DROP TABLE IF EXISTS issues;
DROP TABLE IF EXISTS issue_embeddings;
DROP TABLE IF EXISTS pull_request_embeddings;
DROP TABLE IF EXISTS pull_requests;