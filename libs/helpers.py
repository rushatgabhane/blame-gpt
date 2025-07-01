import re
import numpy as np
import hmac
import hashlib
import logging
import difflib
import html

logger = logging.getLogger(__name__)


def parse_issue_url(issue_url: str) -> tuple[str, str, int] | None:
    pattern = r"^https://github\.com/([^/]+)/([^/]+)/issues/(\d+)$"
    match = re.match(pattern, issue_url)

    if not match:
        return None

    owner, repo, issue_number = match.groups()
    return owner, repo, int(issue_number)


def cosine_similarity(vec1, vec2):
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
