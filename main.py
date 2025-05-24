from contextlib import asynccontextmanager
from dotenv import load_dotenv
import logging


load_dotenv()
logging.basicConfig(level=logging.INFO)


from fastapi import FastAPI
from libs.sqlite.sqlite_client import Database
from controllers.blame_controller import blame_router
from controllers.issue_controller import issue_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database()
    app.state.db = db
    yield
    db.close()


app = FastAPI(lifespan=lifespan)

app.include_router(blame_router)
app.include_router(issue_router)
