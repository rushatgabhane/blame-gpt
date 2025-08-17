import logging

from dotenv import load_dotenv

# Load before importing any other modules to ensure environment variables are set
load_dotenv()
logging.basicConfig(level=logging.INFO)


import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from controllers.user_controller import user_router
from controllers.webhook_controller import webhook_router
from libs import constants
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


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(webhook_router)
