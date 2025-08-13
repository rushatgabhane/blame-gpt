import logging

from dotenv import load_dotenv

# Load before importing any other modules to ensure environment variables are set
load_dotenv()
logging.basicConfig(level=logging.INFO)


import asyncio
import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

from controllers.blame_controller import blame_router
from controllers.code_review_controller import router as code_review_router
from controllers.docs_controller import docs_router
from controllers.issue_controller import issue_router
from controllers.revert_controller import revert_router
from controllers.test_steps_controller import test_steps_router
from controllers.user_controller import user_router
from controllers.webhook_controller import webhook_router
from libs import constants
from libs.helpers import is_production_environment
from libs.sqlite.core import core_sqlite_client
from libs.sqlite.docs import docs_sqlite_client
from services.docs_service.sync import sync_docs
from services.test_step import test_ingestion

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

# Supress APScheduler logs to WARNING to reduce noise
logging.getLogger("apscheduler").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = core_sqlite_client.Database(constants.CACHE_DB_PATH)
    app.state.db = db

    docs_db = docs_sqlite_client.Database(constants.DOCS_DB_PATH)
    app.state.docs_db = docs_db

    logger.info("database connections initialized.")

    sync_docs(docs_db)
    scheduler.add_job(
        func=sync_docs,
        args=(app.state.docs_db,),
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_docs_sync",
        name="daily docs sync",
    )

    if is_production_environment():
        asyncio.create_task(test_ingestion.ingest_test_steps(app.state.db))

    scheduler.start()

    logger.info(f"ENVIRONMENT set as: {os.getenv('ENVIRONMENT')}.")
    yield

    scheduler.shutdown(wait=False)
    docs_db.close()
    db.close()


app = FastAPI(lifespan=lifespan)

app.include_router(blame_router)
app.include_router(issue_router)
app.include_router(docs_router)
app.include_router(user_router)
app.include_router(test_steps_router)
app.include_router(revert_router)
app.include_router(code_review_router)
app.include_router(webhook_router)
