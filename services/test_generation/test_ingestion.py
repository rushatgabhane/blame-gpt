import asyncio
import csv
import logging
from pathlib import Path

from libs import helpers
from libs.llm import embedding_model
from libs.sqlite.core.core_sqlite_client import Database as CoreDatabase

logger = logging.getLogger(__name__)

BATCH_SIZE = 50  # Process embeddings in smaller batches to avoid rate limiting


async def ingest_test_steps(core_db: CoreDatabase):
    logger.info("ingesting test steps for pull requests.")

    current_dir = Path(__file__).parent
    csv_file_path = current_dir / "qa_tests.csv"
    
    test_suites_to_process = []
    
    with open(csv_file_path) as file:
        reader = csv.DictReader(file)
        total_rows = 0
        skipped_rows = 0
        
        for row in reader:
            total_rows += 1
            case_id = int(row["CaseID"].replace("C", ""))
            title = row["Title"]
            steps = row["Steps"]

            if not steps or not title or not case_id:
                skipped_rows += 1
                continue

            hash = helpers.compute_sha256(title + "\n\n" + steps)
            if core_db.get_hash_by_case_id(case_id) == hash:
                skipped_rows += 1
                continue

            test_suites_to_process.append((case_id, title, steps, hash))

    logger.info(f"Found {len(test_suites_to_process)} test suites to process out of {total_rows} total ({skipped_rows} skipped)")

    if not test_suites_to_process:
        logger.info("No test suites to process")
        return

    # Process embeddings in batches to avoid rate limiting
    processed_suites = []
    
    for i in range(0, len(test_suites_to_process), BATCH_SIZE):
        batch = test_suites_to_process[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(test_suites_to_process) + BATCH_SIZE - 1) // BATCH_SIZE
        
        logger.info(f"Processing embedding batch {batch_num}/{total_batches} ({len(batch)} items)")
        
        for case_id, title, steps, hash in batch:
            try:
                await asyncio.sleep(0.1)  # Throttle to avoid rate limiting
                embedding = embedding_model.embed_query(steps)
                if embedding:
                    processed_suites.append((case_id, title, steps, hash, embedding))
                else:
                    logger.warning(f"Failed to generate embedding for test case {case_id}")
            except Exception as e:
                logger.error(f"Error processing test case {case_id}: {e}")
                continue

    logger.info(f"Successfully generated embeddings for {len(processed_suites)} test suites")

    # Batch insert to database
    if processed_suites:
        core_db.add_test_suites_batch(processed_suites)
        logger.info(f"Successfully ingested {len(processed_suites)} test suites")
