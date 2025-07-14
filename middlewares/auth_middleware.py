import logging
import os

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)
from pydantic import SecretStr


# Used for authenticating customer facing APIs
def verify_user_auth_token(authorization: str = Header(...)):
    expected_token = SecretStr(os.getenv("USER_API_AUTH_TOKEN") or "")

    if not authorization or authorization != f"Bearer {expected_token.get_secret_value()}":
        raise HTTPException(status_code=403)


# Used for authenticating internal APIs that should not be exposed to customers
def verify_internal_auth_token(authorization: str = Header(...)):
    expected_internal_token = SecretStr(os.getenv("INTERNAL_API_AUTH_TOKEN") or "")

    if not authorization or authorization != f"Bearer {expected_internal_token.get_secret_value()}":
        raise HTTPException(status_code=403)
