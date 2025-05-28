import re
import numpy as np


def parse_issue_url(issue_url: str) -> tuple[str, str, int] | None:
    """
    Strictly matches URLs like: https://github.com/Expensify/App/issues/25034
    """
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
