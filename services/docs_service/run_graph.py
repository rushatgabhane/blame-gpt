import logging

from libs.sqlite.core import core_sqlite_client
from libs.sqlite.docs import docs_sqlite_client
from models.models import State

from .graph import build_graph

logger = logging.getLogger(__name__)


async def docs(pull_request_id: int, db: core_sqlite_client.Database, docs_db: docs_sqlite_client.Database, usage_log_id: int | None = None):
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
    }

    graph = build_graph(db, docs_db)
    graph.invoke(initial_state)
