import difflib
import hashlib
import hmac
import html
import logging
import os
import re
from datetime import datetime
from email.utils import format_datetime

import numpy as np

from libs.constants import ENVIRONMENT_PRODUCTION

logger = logging.getLogger(__name__)


def parse_issue_url(issue_url: str) -> tuple[str, str, int] | None:
    pattern = r"^https://github\.com/([^/]+)/([^/]+)/issues/(\d+)$"
    match = re.match(pattern, issue_url)

    if not match:
        return None

    owner, repo, issue_number = match.groups()
    return owner, repo, int(issue_number)


def cosine_similarity(vec1, vec2) -> float:
    """
    Calculate the cosine similarity between two vectors.
    
    Both input vectors are converted to NumPy float32 arrays before computation. Returns 0.0 if either vector has zero norm; otherwise, returns the cosine similarity as a float.
    """
    vec1 = np.asarray(vec1, dtype=np.float32)
    vec2 = np.asarray(vec2, dtype=np.float32)

    dot_product = np.dot(vec1, vec2)
    norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)

    if norm_product == 0:
        return 0.0

    return float(dot_product / norm_product)


def batch_cosine_similarity(query_vec, vectors) -> np.ndarray:
    """
    Compute cosine similarity scores between a single query vector and a batch of vectors.
    
    Parameters:
        query_vec: The vector to compare against the batch (1D array-like).
        vectors: The batch of vectors to compare (2D array-like, shape [num_vectors, vector_dim]).
    
    Returns:
        np.ndarray: An array of cosine similarity scores, one for each vector in the batch. Returns zeros for vectors with zero norm or if the query vector has zero norm.
    """
    query_vec = np.asarray(query_vec, dtype=np.float32)
    vectors = np.asarray(vectors, dtype=np.float32)

    # Handle empty inputs
    if len(vectors) == 0:
        return np.array([], dtype=np.float32)


    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        return np.zeros(len(vectors), dtype=np.float32)

    query_normalized = query_vec / query_norm


    vector_norms = np.linalg.norm(vectors, axis=1)
    non_zero_mask = vector_norms != 0

    similarities = np.zeros(len(vectors), dtype=np.float32)
    if np.any(non_zero_mask):
        vectors_normalized = vectors[non_zero_mask] / vector_norms[non_zero_mask][:, np.newaxis]
        similarities[non_zero_mask] = np.dot(vectors_normalized, query_normalized)

    return similarities


def is_valid_signature(signature: str | None, secret: str, body: bytes) -> bool:
    """
    Validates an HMAC SHA-256 signature for a given message body and secret key.
    
    Returns True if the provided signature matches the expected HMAC signature; otherwise, returns False.
    """
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


def is_production_environment() -> bool:
    """
    Check if the current environment is production.
    We want to avoid adding comments to repositories in non-production environments.
    """
    return os.getenv("ENVIRONMENT") == ENVIRONMENT_PRODUCTION
