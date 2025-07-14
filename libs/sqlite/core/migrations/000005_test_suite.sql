CREATE TABLE IF NOT EXISTS test_suite (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    steps TEXT NOT NULL,
    hash TEXT NOT NULL,
    embedding BLOB NOT NULL,      -- List of floats stored as a BLOB
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
