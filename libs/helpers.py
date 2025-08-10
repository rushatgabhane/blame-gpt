import hashlib
import logging
import os
import random
from datetime import datetime
from email.utils import format_datetime

import numpy as np

from libs.constants import ENVIRONMENT_PRODUCTION, THINKING_VERBS

logger = logging.getLogger(__name__)


def cosine_similarity(vec1, vec2) -> float:
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2)


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def blockquote(text: str) -> str:
    lines = text.strip().splitlines()
    return "\n".join([f"> {line}" for line in lines])


def now_rfc1123(nowUTC: datetime) -> str:
    """Example: 'Wed, 25 Oct 2023 19:17:59 GMT'"""
    return format_datetime(nowUTC)


def now_8601(nowUTC: datetime) -> str:
    """Example: '2023-10-25T19:17:59Z'"""
    return nowUTC.isoformat().replace("+00:00", "Z")


def is_production_environment() -> bool:
    """
    Check if the current environment is production.
    We want to avoid adding comments to repositories in non-production environments.
    """
    return os.getenv("ENVIRONMENT") == ENVIRONMENT_PRODUCTION


def thinking_verb() -> str:
    """
    Get a random verb from the THINKING_VERBS list to use as a prefix for yield statements.
    Example: "Manifesting", "Contemplating", "Wizarding", etc.
    """
    return random.choice(THINKING_VERBS)
