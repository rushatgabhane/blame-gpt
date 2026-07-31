import logging

from dotenv import load_dotenv

# Load before importing any other modules to ensure environment variables are set
load_dotenv()
logging.basicConfig(level=logging.INFO)


import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from controllers.bitbucket_webhook_controller import bitbucket_webhook_router
from controllers.user_controller import user_router
from controllers.webhook_controller import webhook_router
from libs import constants
from libs.helpers import is_production_environment
from libs.sqlite.core import core_sqlite_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = core_sqlite_client.Database(constants.CACHE_DB_PATH)
    app.state.db = db

    logger.info("database connections initialized.")
    logger.info(f"ENVIRONMENT set as: {os.getenv('ENVIRONMENT')}.")
    yield
    db.close()


# hide API docs in production
_docs_enabled = not is_production_environment()
app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)

app.include_router(user_router)
app.include_router(webhook_router)
app.include_router(bitbucket_webhook_router)
