from contextlib import asynccontextmanager
from dotenv import load_dotenv
import logging


load_dotenv()
logging.basicConfig(level=logging.INFO)


from fastapi import FastAPI
from libs.sqlite.core import core_sqlite_client
from libs.sqlite.docs import docs_sqlite_client
from controllers.blame_controller import blame_router
from controllers.issue_controller import issue_router
from controllers.deploy_blocker_controller import deploy_blocker_router


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = core_sqlite_client.Database()
    app.state.db = db

    docs_db = docs_sqlite_client.Database()
    app.state.docs_db = docs_db

    logger.info("database connections initialized.")

    yield
    db.close()


app = FastAPI(lifespan=lifespan)

app.include_router(blame_router)
app.include_router(issue_router)
app.include_router(deploy_blocker_router)
