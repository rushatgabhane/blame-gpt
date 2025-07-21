-- Add vector search support for test suites
-- This migration creates a new virtual table using sqlite-vec for efficient similarity search

CREATE VIRTUAL TABLE IF NOT EXISTS test_suite_vectors USING vec0(
    case_id INTEGER,
    title TEXT,
    steps TEXT,
    hash TEXT,
    embedding float[3072] -- OpenAI text-embedding-3-large dimensions
);

CREATE INDEX IF NOT EXISTS idx_test_suite_vectors_case_id 
ON test_suite_vectors(case_id);
