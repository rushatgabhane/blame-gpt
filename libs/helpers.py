import difflib
import hashlib
import hmac
import html
import logging
import re
from datetime import datetime
from email.utils import format_datetime
from hashlib import sha256

import numpy as np

logger = logging.getLogger(__name__)


def parse_issue_url(issue_url: str) -> tuple[str, str, int] | None:
    pattern = r"^https://github\.com/([^/]+)/([^/]+)/issues/(\d+)$"
    match = re.match(pattern, issue_url)

    if not match:
        return None

    owner, repo, issue_number = match.groups()
    return owner, repo, int(issue_number)


def cosine_similarity(vec1, vec2) -> float:
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2)


def is_valid_signature(signature: str | None, secret: str, body: bytes) -> bool:
    if not secret:
        return False
    if signature is None:
        return False

    expected_signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def highlight_diff_markdown(before: str, after: str) -> str:
    before_words = before.split()
    after_words = after.split()
    diff = difflib.ndiff(before_words, after_words)

    result = []
    for word in diff:
        content = html.escape(word[2:])  # escape Markdown-breaking characters
        if word.startswith("- "):
            result.append(f"~~{content}~~")
        elif word.startswith("+ "):
            result.append(f"`{content}`")
        elif word.startswith("  "):
            result.append(content)
    return " ".join(result)


def blockquote(text: str) -> str:
    lines = text.strip().splitlines()
    return "\n".join([f"> {line}" for line in lines])


def now_rfc1123(nowUTC: datetime) -> str:
    """Example: 'Wed, 25 Oct 2023 19:17:59 GMT'"""
    return format_datetime(nowUTC)


def now_8601(nowUTC: datetime) -> str:
    """Example: '2023-10-25T19:17:59Z'"""
    return nowUTC.isoformat().replace("+00:00", "Z")


def hash_256(string: str) -> str:
    return sha256(string.encode()).hexdigest()
