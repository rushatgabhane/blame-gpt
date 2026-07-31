import hmac
import logging
import os

from fastapi import Header, HTTPException
from pydantic import SecretStr

logger = logging.getLogger(__name__)


def _verify_bearer_token(authorization: str, token: SecretStr, name: str):
    # fail closed: an unset token must never allow access
    if not token.get_secret_value():
        logger.error(f"{name} is not configured")
        raise HTTPException(status_code=503)

    expected = f"Bearer {token.get_secret_value()}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=403)


# Used for authenticating customer facing APIs
def verify_user_auth_token(authorization: str = Header(...)):
    _verify_bearer_token(authorization, SecretStr(os.getenv("USER_API_AUTH_TOKEN") or ""), "USER_API_AUTH_TOKEN")


# Used for authenticating internal APIs that should not be exposed to customers
def verify_internal_auth_token(authorization: str = Header(...)):
    _verify_bearer_token(
        authorization, SecretStr(os.getenv("INTERNAL_API_AUTH_TOKEN") or ""), "INTERNAL_API_AUTH_TOKEN"
    )
