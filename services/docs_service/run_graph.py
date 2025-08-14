import logging

from libs.github import get_github_client
from libs.sqlite.core import core_sqlite_client
from libs.sqlite.docs import docs_sqlite_client
from models.models import State

from .graph import build_graph

logger = logging.getLogger(__name__)


def docs(
    pull_request_id: int,
    db: core_sqlite_client.Database,
    docs_db: docs_sqlite_client.Database,
    installation_id: int,
    repo_id: int,
    usage_log_id: int | None = None,
):
    gh_client = get_github_client(installation_id)
    repo_client = gh_client.get_repo(repo_id)

    initial_state: State = {
        "pull_request_id": pull_request_id,
        "pull_request": None,
        "en_patch": None,
        "intent": None,
        "should_docs_update": None,
        "update_reason": None,
        "relevant_docs": None,
        "doc_edit_suggestions": None,
        "comment": None,
        "usage_log_id": usage_log_id,
        "installation_id": installation_id,
        "gh_client": gh_client,
        "repo_client": repo_client,
    }

    graph = build_graph(db, docs_db)
    graph.invoke(initial_state)
