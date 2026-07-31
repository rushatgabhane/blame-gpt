import json
import logging
import os

from fastapi import APIRouter, BackgroundTasks, Header, Request, Response
from pydantic import SecretStr

from libs import helpers
from services.bitbucket.webhook_service import process_bitbucket_comment

logger = logging.getLogger(__name__)

bitbucket_webhook_router = APIRouter()


@bitbucket_webhook_router.post("/api/webhook/bitbucket")
async def bitbucket_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None),
):
    body = await request.body()
    webhook_secret = SecretStr(os.getenv("BITBUCKET_WEBHOOK_SECRET") or "")

    if not helpers.is_valid_signature(x_hub_signature_256, webhook_secret, body):
        return Response(content="Invalid signature", status_code=401)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"failed to parse bitbucket webhook payload: {e}")
        return Response(content="Invalid JSON payload", status_code=400)

    if not payload.get("pullrequest", {}).get("id"):
        return Response(content="No pull request found")

    if not payload.get("comment", {}).get("id"):
        return Response(content="No comment found")

    background_tasks.add_task(process_bitbucket_comment, payload, request.app.state.db)
    return Response(content="processing webhook")
