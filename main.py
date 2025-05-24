from typing import Union
from fastapi import FastAPI
import dotenv
import logging

from controllers.blame_controller import blame_router

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.include_router(blame_router)
