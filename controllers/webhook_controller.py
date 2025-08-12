import json
import logging
import os

from fastapi import APIRouter, BackgroundTasks, Header, Request, Response
from pydantic import SecretStr

from libs import constants, helpers
from services.webhook_service import process_webhook_comment

logger = logging.getLogger(__name__)

webhook_router = APIRouter()


@webhook_router.post("/api/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks, x_hub_signature_256: str = Header(None)):
    body = await request.body()
    webhook_secret = SecretStr(os.getenv("GITHUB_WEBHOOK_SECRET") or "")

    if not helpers.is_valid_signature(x_hub_signature_256, webhook_secret, body):
        return Response(content="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"failed to parse webhook payload: {e}")
        return Response(content="Invalid JSON payload")

    if payload.get("action") not in ["created", "edited"]:
        return Response(content="Not a comment action")

    comment_body = payload.get("comment", {}).get("body", "")
    if constants.USER_TAG.lower() not in comment_body.lower():
        return Response(content="No @blamegpt mention")

    installation = payload.get("installation", {})
    installation_id = installation.get("id")
    if not installation_id:
        return Response(content="No installation ID found")

    issue_or_pr = payload.get("issue") or payload.get("pull_request")
    if not issue_or_pr:
        return Response(content="No issue or pull request found")

    core_db = request.app.state.db
    docs_db = request.app.state.docs_db

    background_tasks.add_task(process_webhook_comment, payload, core_db, docs_db, installation_id)
    return Response(content="processing webhook")
