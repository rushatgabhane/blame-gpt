import os

REPO_OWNER = "Expensify"
REPO_NAME = "App"
CACHE_DB_PATH = "data/cache.db"
DOCS_DB_PATH = "data/docs.db"

LABELS = {
    "DeployBlockerCash": "DeployBlockerCash",
    "DeployBlocker": "DeployBlocker",
}

EN_TS = "en.ts"
USER_TAG = "@blamegpt"

ENVIRONMENT_PRODUCTION = "production"
ENVIRONMENT_DEVELOPMENT = "development"

# Vector search configuration
VECTOR_SEARCH_K = int(os.getenv("VECTOR_SEARCH_K", "5"))
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "3072"))  # OpenAI text-embedding-3-large
