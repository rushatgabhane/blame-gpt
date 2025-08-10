-- Rename column from 'explaination' to 'explanation' to fix typo
ALTER TABLE pull_requests RENAME COLUMN explaination TO explanation;