import logging
import sqlite3
import time

from sqlite_vec import sqlite_vec

from libs import constants
from libs.sqlite.core import core_queries
from models.models import TestSuite

logger = logging.getLogger(__name__)


class VectorSearchResult:
    """Result from vector similarity search"""

    def __init__(self, case_id: int, title: str, steps: str, hash: str, distance: float):
        self.case_id = case_id
        self.title = title
        self.steps = steps
        self.hash = hash
        self.distance = distance
        self.similarity = 1.0 - distance

    def to_test_suite(self) -> TestSuite:
        """Convert to TestSuite model (without embedding for efficiency)"""
        return TestSuite(
            id=None,  # Not needed for similarity search
            case_id=self.case_id,
            title=self.title,
            steps=self.steps,
            hash=self.hash,
            embedding=None,  # Not needed, we have similarity score
        )


class VectorService:
    """
    Service for vector similarity search using sqlite-vec extension.
    """

    def __init__(self, db_connection: sqlite3.Connection):
        """
        Initialize with existing database connection.

        Args:
            db_connection: SQLite connection from the main Database class
        """
        self.connection = db_connection
        self._setup_vector_support()

    def _setup_vector_support(self):
        start_time = time.time()
        try:
            self.connection.enable_load_extension(True)
            sqlite_vec.load(self.connection)
            self.connection.enable_load_extension(False)

            version = self.connection.execute("SELECT vec_version()").fetchone()[0]
            setup_time = time.time() - start_time
            logger.info(f"sqlite-vec loaded successfully: {version} (setup took {setup_time:.3f}s)")

        except Exception as e:
            setup_time = time.time() - start_time
            logger.error(f"Failed to setup vector support after {setup_time:.3f}s: {e}", exc_info=True)
            raise

    def add_test_suite_vector(self, case_id: int, title: str, steps: str, hash: str, embedding: list[float]):
        """
        Add a test suite to the vector search table.

        Args:
            case_id: Test case ID
            title: Test case title
            steps: Test case steps
            hash: Content hash
            embedding: Vector embedding (list of floats)
        """
        if not embedding:
            raise ValueError("Embedding cannot be empty")

        if len(embedding) != constants.EMBEDDING_DIMENSION:
            raise ValueError(f"Expected embedding dimension {constants.EMBEDDING_DIMENSION}, got {len(embedding)}")

        start_time = time.time()
        try:
            # Convert embedding list to bytes for sqlite-vec
            embedding_bytes = sqlite_vec.serialize_float32(embedding)

            # Insert into vector table
            self.connection.execute(
                core_queries.INSERT_TEST_SUITE_VECTOR,
                (case_id, title, steps, hash, embedding_bytes),
            )

            self.connection.commit()
            insert_time = time.time() - start_time
            logger.debug(f"Inserted test suite vector {case_id} in {insert_time:.3f}s")

        except Exception as e:
            insert_time = time.time() - start_time
            logger.error(f"Failed to insert test suite vector {case_id} after {insert_time:.3f}s: {e}", exc_info=True)
            raise

    def add_test_suite_vectors_batch(self, test_suites: list[tuple[int, str, str, str, list[float]]]):
        """
        Add multiple test suites to the vector search table in batch.

        Args:
            test_suites: List of tuples (case_id, title, steps, hash, embedding)
        """
        if not test_suites:
            logger.debug("No test suites provided for batch insert")
            return

        start_time = time.time()
        batch_data = []
        skipped_count = 0

        for case_id, title, steps, hash, embedding in test_suites:
            if not embedding:
                logger.warning(f"Skipping test suite {case_id} due to empty embedding")
                skipped_count += 1
                continue

            if len(embedding) != constants.EMBEDDING_DIMENSION:
                logger.warning(f"Skipping test suite {case_id} due to invalid embedding dimension: {len(embedding)}")
                skipped_count += 1
                continue

            # Convert embedding list to bytes for sqlite-vec
            embedding_bytes = sqlite_vec.serialize_float32(embedding)
            batch_data.append((case_id, title, steps, hash, embedding_bytes))

        if batch_data:
            try:
                self.connection.executemany(core_queries.INSERT_TEST_SUITE_VECTOR, batch_data)
                batch_time = time.time() - start_time
                logger.info(
                    f"Batch inserted {len(batch_data)} test suite vectors in {batch_time:.3f}s ({skipped_count} skipped)"
                )
            except Exception as e:
                batch_time = time.time() - start_time
                logger.error(f"Batch insert failed after {batch_time:.3f}s: {e}", exc_info=True)
                raise
        else:
            logger.warning(f"No valid test suites to insert ({skipped_count} skipped)")

    def find_similar_test_suites(
        self, query_embedding: list[float], k: int = constants.VECTOR_SEARCH_K
    ) -> list[VectorSearchResult]:
        """
        Find similar test suites using vector similarity search.

        Args:
            query_embedding: The embedding vector to search for
            k: Number of similar results to return

        Returns:
            List of VectorSearchResult objects, sorted by similarity
        """
        if not query_embedding:
            raise ValueError("Query embedding cannot be empty")

        if len(query_embedding) != constants.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected query embedding dimension {constants.EMBEDDING_DIMENSION}, got {len(query_embedding)}"
            )

        start_time = time.time()
        try:
            query_bytes = sqlite_vec.serialize_float32(query_embedding)
            cursor = self.connection.execute(
                core_queries.SEARCH_SIMILAR_TEST_SUITES,
                (query_bytes, k),
            )

            results = []
            for row in cursor:
                result = VectorSearchResult(case_id=row[0], title=row[1], steps=row[2], hash=row[3], distance=row[4])
                results.append(result)

            search_time = time.time() - start_time
            logger.debug(f"Vector search completed in {search_time:.3f}s, found {len(results)} results (k={k})")
            return results

        except Exception as e:
            search_time = time.time() - start_time
            logger.error(f"Vector search failed after {search_time:.3f}s: {e}", exc_info=True)
            raise
