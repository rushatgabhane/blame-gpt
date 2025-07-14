ALTER TABLE pull_requests ADD COLUMN linked_issue_ids TEXT;
-- This column will store a JSON array of issue IDs linked to the PR
