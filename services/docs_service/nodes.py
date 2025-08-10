import json
import logging

from libs import constants
from libs.helpers import blockquote, cosine_similarity
from libs.llm import ModelNames, embedding_model, llm
from libs.prompt_templates.doc_edit_evaluation import doc_edit_evaluation_parser, doc_edit_evaluation_prompt
from libs.prompt_templates.doc_edit_suggestion import doc_edit_parser, doc_edit_suggestions_prompt
from libs.prompt_templates.pull_request_intent import pull_request_intent_parser, pull_request_intent_prompt
from libs.sqlite.core import core_sqlite_client
from libs.sqlite.docs import docs_sqlite_client
from models.models import DocEditEvaluation, DocUpdateDiff, DocWithScore, PullRequestIntent, State
from services import user_service
from services.github import pull_request_service
from services.github.comment_service import add_comment_to_pull_request

logger = logging.getLogger(__name__)


def pull_request_node(state: State, db: core_sqlite_client.Database) -> State:
    pull_request_id = state["pull_request_id"]
    pull_request = pull_request_service.add_pull_request_if_not_exist(pull_request_id, db, None)
    if not pull_request:
        state["should_docs_update"] = False
        return state

    file_patches = pull_request_service.get_pull_request_patch(pull_request.id)
    patch = [p.patch for p in file_patches if p.filename.endswith("en.ts")]

    en_patch_str = "\n".join(patch)
    state["pull_request"] = pull_request
    state["en_patch"] = en_patch_str

    logger.info(f"{pull_request_id}: patch loaded successfully")
    return state


def pull_request_intent_node(state: State, db: core_sqlite_client.Database) -> State:
    pull_request = state["pull_request"]
    en_patch = state["en_patch"] or ""
    if not pull_request:
        logger.error(f"{state['pull_request_id']}: pull request not found in state")
        state["should_docs_update"] = False
        return state

    input = pull_request_intent_prompt.format(
        title=pull_request.title,
        test=pull_request.test,
        explanation=pull_request.explaination,
        en_patch=en_patch,
    )

    output = llm.invoke(input)
    user_service.track_llm_usage(db, state["usage_log_id"], output, ModelNames.GPT_5)
    p: PullRequestIntent = pull_request_intent_parser.invoke(output)
    if not p or not p.intent:
        logger.error(f"{pull_request.id}: intent parsing failed. output: {output}")
        state["should_docs_update"] = False
        return state

    if p.is_bug_fix:
        logger.info(f"{pull_request.id}: is a bug fix, no docs update needed")
        state["should_docs_update"] = False
        return state

    logger.info(f"{pull_request.id}: intent done")

    state["intent"] = p.intent
    return state


def get_relevant_docs_node(state: State, docs_db: docs_sqlite_client.Database) -> State:
    intent = state["intent"]
    if not intent:
        logger.error(f"{state['pull_request_id']}: no intent found in state")
        return state

    query_embedding = embedding_model.embed_query(intent)
    docs = docs_db.get_all_docs_with_embeddings()

    scored_docs: list[DocWithScore] = []
    for doc in docs:
        if "expensify-classic" in doc.path.lower():
            continue

        similarity = cosine_similarity(query_embedding, doc.embedding)
        scored_docs.append(DocWithScore(doc=doc, score=similarity))

    scored_docs.sort(key=lambda x: x.score, reverse=True)

    threshold = 0.2
    # Todo: use a combination of exact and semantic search
    docs_above_threshold = [doc for doc in scored_docs if doc.score >= threshold]
    if not docs_above_threshold:
        state["should_docs_update"] = False
        logger.info(
            f"{state['pull_request_id']}: no relevant docs found. highest score: {scored_docs[0].score if scored_docs else 'N/A'}"
        )
        return state

    for doc in docs_above_threshold:
        logger.info(f"{state['pull_request_id']}: doc: {doc.doc.path}, score: {doc.score:.4f}")

    top_n = 5
    top_n_docs = docs_above_threshold[: top_n if len(docs_above_threshold) > top_n else len(docs_above_threshold)]

    state["relevant_docs"] = [doc.doc for doc in top_n_docs]
    return state


def doc_edit_suggestions_node(state: State, db: core_sqlite_client.Database) -> State:
    relevant_docs = state["relevant_docs"]
    if not relevant_docs:
        logger.error(f"{state['pull_request_id']}: no relevant docs found in state")
        return state

    suggestions: list[DocUpdateDiff] = []

    for doc in relevant_docs:
        content = doc.raw_content or ""
        input = doc_edit_suggestions_prompt.format(
            intent=state["intent"],
            path=doc.path,
            content=content,
        )

        output = llm.invoke(input)
        user_service.track_llm_usage(db, state["usage_log_id"], output, ModelNames.GPT_5)
        p = doc_edit_parser.invoke(output)
        if not p or not p.edits:
            logger.info(f"{state['pull_request_id']}: doc {doc.path}: edit suggestions is empty")
            continue

        suggestion = DocUpdateDiff(
            path=doc.path,
            edits=p.edits,
        )
        suggestions.append(suggestion)

    state["doc_edit_suggestions"] = suggestions
    return state


def doc_edit_evaluation_node(state: State, db: core_sqlite_client.Database) -> State:
    suggestions = state["doc_edit_suggestions"]
    if not suggestions:
        logger.error(f"{state['pull_request_id']}: no article update suggestions found in state")
        return state

    input = doc_edit_evaluation_prompt.format(
        intent=state["intent"],
        suggestions_json=json.dumps([s.model_dump() for s in suggestions]),
    )

    output = llm.invoke(input)
    user_service.track_llm_usage(db, state["usage_log_id"], output, ModelNames.GPT_5)
    p: DocEditEvaluation = doc_edit_evaluation_parser.invoke(output)

    state["should_docs_update"] = p.should_docs_update
    state["update_reason"] = p.update_reason

    if not p.should_docs_update:
        logger.info(f"{state['pull_request_id']}: doc edit evaluation: no updates needed for PR ")
        return state

    i = 0
    comment = "### Suggested HelpDot changes for this PR\n\n"
    comment += "\n<details>\n"
    comment += f"{p.update_reason}\n\n"
    for i, e in enumerate(p.edits_to_apply, start=1):
        path = e.path.replace(".md", "")
        comment += "\n---\n\n"
        comment += f"#### Article: [{path}](https://help.expensify.com/articles/{path})\n\n"
        comment += f"**Edit {i}:**\n"

        for edit in e.edits:
            comment += f"**Before:**\n {blockquote(edit.before.strip())}\n\n"
            comment += f"**After:**\n {blockquote(edit.after.strip())}\n"

    comment += "\n</details>\n"
    comment += "\n\nPlease review the suggested changes and apply them if necessary."

    state["comment"] = comment

    logger.info(
        f"{state['pull_request_id']}: doc edit evaluation: should update: {p.should_docs_update}, reason: {p.update_reason}"
    )
    return state


def add_comment_node(state: State) -> State:
    pull_request_id = state["pull_request_id"]
    comment = state["comment"]

    if not comment or not pull_request_id:
        logger.info(f"{pull_request_id}: no comment to add")
        return state

    add_comment_to_pull_request(pull_request_id, comment)
    return state
