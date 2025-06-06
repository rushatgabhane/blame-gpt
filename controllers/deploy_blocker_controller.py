from fastapi import APIRouter, Depends, Response
from services import historical_deploy_blocker_pipeline
import logging
from middlewares import auth_middleware

logger = logging.getLogger(__name__)

deploy_blocker_router = APIRouter()


@deploy_blocker_router.get(
    "/api/deploy-blockers", dependencies=[Depends(auth_middleware.verify_auth_token)]
)
async def get_deploy_blockers():
    await run_historical_deploy_blocker_pipeline()
    return Response(
        status_code=200, content="historical deploy blocker pipeline started."
    )


async def run_historical_deploy_blocker_pipeline():
    """
    Run the historical deploy blocker pipeline.
    """
    async for step in historical_deploy_blocker_pipeline.run():
        logger.info(step)


@deploy_blocker_router.get(
    "/api/historical-prs",
    dependencies=[Depends(auth_middleware.verify_auth_token)],
)
async def get_historical_prs_api():
    prs = await historical_deploy_blocker_pipeline.get_historical_prs()
    return Response(status_code=200, content="historical PRs pipeline started.")

@deploy_blocker_router.get(
    "/api/get-all-merged-prs",
    dependencies=[Depends(auth_middleware.verify_auth_token)],
)
async def get_all_merged_prs_api():
    await historical_deploy_blocker_pipeline.get_all_merged_prs()
    return Response(status_code=200, content="All merged PRs pipeline started.")