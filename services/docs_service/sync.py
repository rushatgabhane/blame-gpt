import logging
import subprocess
from pathlib import Path

from libs import constants
from libs.helpers import compute_sha256
from libs.llm import embedding_model
from libs.sqlite.docs.docs_sqlite_client import Database

CLONE_DIR = Path(constants.CLONE_DIR)
ARTICLES_DIR = CLONE_DIR / "docs/articles"
REPO_URL = f"https://github.com/{constants.REPO_OWNER}/{constants.REPO_NAME}.git"
logger = logging.getLogger(__name__)


def get_title_from_path(path: str) -> str:
    return path.split("/")[-1] if path else ""


# We need to do this because we don't have github workflows setup on this repo
def clone_or_pull_repo(repo_url: str, clone_path: Path):
    if not clone_path.exists():
        logger.info(f"this might take 5 minutes. cloning repository to {clone_path}")
        subprocess.run(
            ["git", "clone", repo_url, str(clone_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        logger.info(f"this might take a minute. pulling latest changes in {clone_path}")
        subprocess.run(
            ["git", "-C", str(clone_path), "pull"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )


def update_docs_embedding(docs_db: Database):
    logger.info("updating docs embeddings")

    all_docs = list(ARTICLES_DIR.rglob("*.md"))
    current_paths = {str(p.relative_to(ARTICLES_DIR)) for p in all_docs}

    existing_paths = docs_db.get_all_paths()
    for path in existing_paths - current_paths:
        logger.info(f"deleting doc from db: {path}")
        docs_db.delete_doc(path)

    for file_path in all_docs:
        rel_path = str(file_path.relative_to(ARTICLES_DIR))
        content = file_path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        content_hash = compute_sha256(content)
        existing_hash = docs_db.get_content_hash(rel_path)
        if existing_hash == content_hash:
            continue

        title = get_title_from_path(rel_path)
        embedding = embedding_model.embed_query(f"Path: {rel_path}\n\n Content:{content}")

        docs_db.upsert_doc(rel_path, title, content_hash, embedding, content)
    logger.info("docs embeddings updated successfully")


def sync_docs(docs_db: Database):
    try:
        clone_or_pull_repo(REPO_URL, CLONE_DIR)

        # don't update embeddings because docs endpoint has no real users and it is expensive
        # update_docs_embedding(docs_db)
    except Exception as e:
        logger.error(f"failed to sync docs: {e}")
        raise e
