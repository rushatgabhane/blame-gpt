from fastapi import Header, HTTPException
import os
import logging

logger = logging.getLogger(__name__)


def verify_user_auth_token(authorization: str = Header(...)):
    expected_token = os.getenv("USER_API_AUTH_TOKEN")
    if not expected_token:
        logger.error("USER_API_AUTH_TOKEN is not set in environment variables.")
        raise HTTPException(status_code=500)

    if not authorization or authorization != f"Bearer {expected_token}":
        raise HTTPException(status_code=403)


def verify_internal_auth_token(internal_auth: str = Header(...)):
    expected_internal_token = os.getenv("INTERNAL_API_AUTH_TOKEN")
    if not expected_internal_token:
        logger.error("INTERNAL_API_AUTH_TOKEN is not set in environment variables.")
        raise HTTPException(status_code=500)

    if not internal_auth or internal_auth != f"Bearer {expected_internal_token}":
        raise HTTPException(status_code=403)
