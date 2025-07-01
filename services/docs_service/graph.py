from langgraph.graph import END, StateGraph

from libs.sqlite.core import core_sqlite_client
from libs.sqlite.docs import docs_sqlite_client
from models.models import State
from services.docs_service.nodes import (
    add_comment_node,
    doc_edit_evaluation_node,
    doc_edit_suggestions_node,
    get_relevant_docs_node,
    pull_request_intent_node,
    pull_request_node,
)


def build_graph(db: core_sqlite_client.Database, docs_db: docs_sqlite_client.Database):
    builder = StateGraph(State)

    builder.add_node("pull_request_node", lambda state: pull_request_node(state, db))
    builder.add_node("pull_request_intent_node", pull_request_intent_node)
    builder.add_node(
        "get_relevant_docs_node", lambda state: get_relevant_docs_node(state, docs_db)
    )
    builder.add_node(
        "doc_edit_suggestions_node", lambda state: doc_edit_suggestions_node(state)
    )
    builder.add_node("doc_edit_evaluation_node", doc_edit_evaluation_node)
    builder.add_node("add_comment_node", add_comment_node)

    builder.set_entry_point("pull_request_node")

    builder.add_edge("pull_request_node", "pull_request_intent_node")

    builder.add_conditional_edges(
        "pull_request_intent_node",
        lambda state: END
        if state["should_docs_update"] is False
        else "get_relevant_docs_node",
    )
    builder.add_conditional_edges(
        "get_relevant_docs_node",
        lambda state: END
        if state["should_docs_update"] is False
        else "doc_edit_suggestions_node",
    )

    builder.add_edge("doc_edit_suggestions_node", "doc_edit_evaluation_node")
    builder.add_edge("doc_edit_evaluation_node", "add_comment_node")
    builder.add_edge("add_comment_node", END)

    return builder.compile()
