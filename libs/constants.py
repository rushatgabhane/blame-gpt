GITHUB_API_URL = "https://api.github.com/graphql"
REPO_OWNER = "Expensify"
REPO_NAME = "App"
CACHE_DB_PATH = "data/cache.db"
DOCS_DB_PATH = "data/docs.db"

LABELS = {
    "DeployBlockerCash": "DeployBlockerCash",
    "DeployBlocker": "DeployBlocker",
}

EN_TS = "en.ts"

# Rate limiting configuration
RATE_LIMITS = {
    "GITHUB_REQUESTS_PER_MINUTE": 50,  # Conservative limit for GitHub API
    "OPENAI_REQUESTS_PER_MINUTE": 30,  # Conservative limit for OpenAI API
    "GITHUB_MAX_CONCURRENT_TASKS": 3,  # Max concurrent GitHub API calls
    "OPENAI_MAX_CONCURRENT_TASKS": 2,  # Max concurrent OpenAI API calls
    "GITHUB_MAX_RETRIES": 3,  # Max retries for GitHub API calls
    "OPENAI_MAX_RETRIES": 5,  # Max retries for OpenAI API calls
}
