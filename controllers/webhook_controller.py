import json
import logging
import os

from fastapi import APIRouter, Header, Request, Response

from libs import constants, helpers
from services.webhook_service import process_webhook_comment

logger = logging.getLogger(__name__)

webhook_router = APIRouter()


@webhook_router.post("/api/webhook/github")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    body = await request.body()
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET") or ""

    if not helpers.is_valid_signature(x_hub_signature_256, webhook_secret, body):
        logger.warning("invalid webhook signature received")
        return Response(status_code=403, content="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"failed to parse webhook payload: {e}")
        return Response(status_code=400, content="Invalid JSON payload")

    if payload.get("action") not in ["created", "edited"]:
        return Response(status_code=200, content="Not a comment action")

    comment_body = payload.get("comment", {}).get("body", "")
    if constants.USER_TAG.lower() not in comment_body.lower():
        return Response(status_code=200, content="No @blamegpt mention")

    installation = payload.get("installation", {})
    installation_id = installation.get("id")
    if not installation_id:
        return Response(status_code=400, content="No installation ID found")

    issue_or_pr = payload.get("issue") or payload.get("pull_request")
    if not issue_or_pr:
        return Response(status_code=200, content="No issue or pull request found")

    try:
        core_db = request.app.state.db
        docs_db = request.app.state.docs_db

        await process_webhook_comment(payload, core_db, docs_db, installation_id)
        return Response(status_code=200, content="Webhook processed successfully")

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return Response(status_code=500, content="Internal server error")
