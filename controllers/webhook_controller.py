import json
import logging
import os

from fastapi import APIRouter, BackgroundTasks, Header, Request, Response
from pydantic import SecretStr

from libs import constants, helpers
from services.webhook_service import process_webhook_comment, process_webhook_pr_event

logger = logging.getLogger(__name__)

webhook_router = APIRouter()


@webhook_router.post("/api/webhook/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
):
    body = await request.body()
    webhook_secret = SecretStr(os.getenv("GITHUB_WEBHOOK_SECRET") or "")

    if not helpers.is_valid_signature(x_hub_signature_256, webhook_secret, body):
        return Response(content="Invalid signature", status_code=401)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"failed to parse webhook payload: {e}")
        return Response(content="Invalid JSON payload", status_code=400)

    if x_github_event not in ["issue_comment", "pull_request"]:
        return Response(content="Unsupported event type")

    installation = payload.get("installation", {})
    installation_id = installation.get("id")
    if not installation_id:
        return Response(content="No installation ID found")

    core_db = request.app.state.db

    # Handle pull request events (opened, synchronize for automatic dependency analysis)
    if x_github_event == "pull_request":
        if payload.get("action") not in ["opened", "synchronize"]:
            return Response(content="Not a PR action we handle")
        
        pull_request = payload.get("pull_request")
        if not pull_request:
            return Response(content="No pull request found")
            
        # Skip if PR is draft
        if pull_request.get("draft", False):
            return Response(content="Skip draft PR")
        
        background_tasks.add_task(process_webhook_pr_event, payload, core_db, installation_id)
        return Response(content="processing PR webhook")

    # Handle comment events (existing logic)
    if x_github_event == "issue_comment":
        if payload.get("action") not in ["created", "edited"]:
            return Response(content="Not a comment action")

        comment_body = payload.get("comment", {}).get("body", "")
        if constants.USER_TAG.lower() not in comment_body.lower():
            return Response(content=f"No {constants.USER_TAG.lower()} mention")

        issue_or_pr = payload.get("issue") or payload.get("pull_request")
        if not issue_or_pr:
            return Response(content="No issue or pull request found")

        background_tasks.add_task(process_webhook_comment, payload, core_db, installation_id)
        return Response(content="processing webhook")

    return Response(content="Unsupported event")
