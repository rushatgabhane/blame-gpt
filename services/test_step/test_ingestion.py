import asyncio
import csv
import logging
from pathlib import Path

from libs import helpers
from libs.llm import embedding_model
from libs.sqlite.core.core_sqlite_client import Database as CoreDatabase

logger = logging.getLogger(__name__)


async def ingest_test_steps(core_db: CoreDatabase):
    logger.info("ingesting test steps for pull requests.")

    current_dir = Path(__file__).parent
    csv_file_path = current_dir / "qa_tests.csv"
    with open(csv_file_path) as file:
        reader = csv.DictReader(file)
        i = 0
        for row in reader:
            i += 1
            case_id = int(row["CaseID"].replace("C", ""))
            title = row["Title"]
            steps = row["Steps"]

            if not steps or not title or not case_id:
                continue

            hash = helpers.compute_sha256(title + "\n\n" + steps)
            if core_db.get_hash_by_case_id(case_id) == hash:
                continue

            # Handle delete case ??

            await asyncio.sleep(0.5)  # Throttle to avoid rate limiting
            embedding = embedding_model.embed_query(steps)
            if not embedding:
                continue

            core_db.add_test_suite(case_id=case_id, title=title, steps=steps, hash=hash, embedding=embedding)
            logger.info(f"added test case # {i}")
