CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    avatar_url TEXT NOT NULL,
    email TEXT,   -- Github email will be null for private accounts. We can later add OAuth to get email.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    command_name TEXT NOT NULL,
    comment_url TEXT NOT NULL,
    output TEXT,
    issue_or_pull_request_url TEXT,  -- The issue or pull request where the command was executed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usage_log_id INTEGER NOT NULL,
    llm_model TEXT NOT NULL,
    tokens_used INTEGER NOT NULL,
    cost_usd_cents INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usage_log_id) REFERENCES usage_logs(id) ON DELETE CASCADE
);
