from fastapi import APIRouter
from services import historical_deploy_blocker_pipeline
import logging

logger = logging.getLogger(__name__)

deploy_blocker_router = APIRouter()


@deploy_blocker_router.get("/deploy_blockers")
async def get_deploy_blockers():
    await run_historical_deploy_blocker_pipeline()
    return "", 200

async def run_historical_deploy_blocker_pipeline():
    """
    Run the historical deploy blocker pipeline.
    """
    async for step in historical_deploy_blocker_pipeline.run():
        logger.info(step)

