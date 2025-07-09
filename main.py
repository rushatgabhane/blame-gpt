import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)


from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from controllers.blame_controller import blame_router
from controllers.deploy_blocker_controller import deploy_blocker_router
from controllers.docs_controller import docs_router
from controllers.issue_controller import issue_router
from libs import constants
from libs.sqlite.core import core_sqlite_client
from libs.sqlite.docs import docs_sqlite_client
from services.docs_service.sync import sync_docs
from services.github.notification_service import listen_notifications

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
        args=(docs_db,),
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_docs_sync",
        name="daily docs sync",
    )

    scheduler.add_job(
        func=listen_notifications,
        args=(db, docs_db),
        trigger=IntervalTrigger(seconds=5),
        id="listen_notifications",
        name="listen to github notifications",
    )

    scheduler.start()

    yield

    scheduler.shutdown(wait=False)
    docs_db.close()
    db.close()


app = FastAPI(lifespan=lifespan)

app.include_router(blame_router)
app.include_router(issue_router)
app.include_router(deploy_blocker_router)
app.include_router(docs_router)
