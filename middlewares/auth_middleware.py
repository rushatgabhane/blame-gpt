from fastapi import Header, HTTPException
import os
import logging

logger = logging.getLogger(__name__)


def verify_auth_token(authorization: str = Header(...)):
    expected_token = os.getenv("API_AUTH_TOKEN")
    if not expected_token:
        logger.error("API_AUTH_TOKEN is not set in environment variables.")
        raise HTTPException(status_code=500)

    if not authorization or authorization != f"Bearer {expected_token}":
        raise HTTPException(status_code=403)
