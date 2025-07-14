import logging

from dotenv import load_dotenv

# Load before importing any other modules to ensure environment variables are set
load_dotenv()
logging.basicConfig(level=logging.INFO)


import asyncio
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from controllers._deploy_blocker_controller import deploy_blocker_router
from controllers.blame_controller import blame_router
from controllers.docs_controller import docs_router
from controllers.issue_controller import issue_router
from controllers.test_steps_controller import test_steps_router
from controllers.user_controller import user_router
from libs import constants
from libs.helpers import is_production_environment
from libs.sqlite.core import core_sqlite_client
from libs.sqlite.docs import docs_sqlite_client
from services.docs_service.sync import sync_docs
from services.github.notification_service import listen_notifications
from services.test_generation import test_ingestion

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

    app.state.last_checked = datetime.now(UTC)  # thread safe across multiple fastapi workers. so not a global variable
    scheduler.add_job(
        func=listen_notifications,
        args=(app.state.db, app.state.docs_db, app),
        trigger=IntervalTrigger(seconds=7),
        id="listen_notifications",
        name="listen to github notifications",
        max_instances=25,
    )

    scheduler.start()

    logger.info(f"ENVIRONMENT set as: {os.getenv('ENVIRONMENT')}.")
    logger.info("Make sure to set the .env file from .env.example before running the app.")
    yield

    scheduler.shutdown(wait=False)
    docs_db.close()
    db.close()


app = FastAPI(lifespan=lifespan)

app.include_router(blame_router)
app.include_router(issue_router)
app.include_router(deploy_blocker_router)
app.include_router(docs_router)
app.include_router(user_router)
app.include_router(test_steps_router)
