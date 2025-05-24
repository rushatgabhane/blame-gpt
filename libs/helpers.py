import re


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
