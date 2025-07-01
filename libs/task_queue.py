"""Task queue system for managing concurrent API requests."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of a task execution."""

    success: bool
    result: Any = None
    error: Optional[Exception] = None
    task_id: Optional[str] = None


class TaskQueue:
    """Manages concurrent API requests with configurable limits."""

    def __init__(self, max_concurrent_tasks: int = 5, max_workers: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._task_counter = 0

    async def execute_async_batch(self, tasks: List[Callable], *args_list, **kwargs_list) -> List[TaskResult]:
        """Execute a batch of async tasks with concurrency control."""
        if not tasks:
            return []

        async def execute_single_task(
            task_func: Callable, task_args: tuple, task_kwargs: dict, task_id: str
        ) -> TaskResult:
            async with self.semaphore:
                try:
                    logger.debug(f"Executing task {task_id}")
                    if asyncio.iscoroutinefunction(task_func):
                        result = await task_func(*task_args, **task_kwargs)
                    else:
                        result = task_func(*task_args, **task_kwargs)
                    return TaskResult(success=True, result=result, task_id=task_id)
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    return TaskResult(success=False, error=e, task_id=task_id)

        # Prepare task arguments
        if not args_list:
            args_list = [() for _ in tasks]
        if not kwargs_list:
            kwargs_list = [{} for _ in tasks]

        # Create and execute tasks
        async_tasks = []
        for i, (task_func, task_args, task_kwargs) in enumerate(zip(tasks, args_list, kwargs_list)):
            task_id = f"task_{self._task_counter}_{i}"
            async_tasks.append(execute_single_task(task_func, task_args, task_kwargs, task_id))

        self._task_counter += 1
        results = await asyncio.gather(*async_tasks, return_exceptions=False)
        return results

    def execute_sync_batch(
        self, tasks: List[Callable], args_list: List[tuple] = None, kwargs_list: List[dict] = None
    ) -> List[TaskResult]:
        """Execute a batch of sync tasks with ThreadPoolExecutor and concurrency control."""
        if not tasks:
            return []

        if not args_list:
            args_list = [() for _ in tasks]
        if not kwargs_list:
            kwargs_list = [{} for _ in tasks]

        results = []

        # Use ThreadPoolExecutor with limited workers
        with ThreadPoolExecutor(max_workers=min(self.max_concurrent_tasks, self.max_workers)) as executor:
            # Submit tasks in batches to respect concurrency limits
            batch_size = self.max_concurrent_tasks
            for i in range(0, len(tasks), batch_size):
                batch_tasks = tasks[i : i + batch_size]
                batch_args = args_list[i : i + batch_size]
                batch_kwargs = kwargs_list[i : i + batch_size]

                # Submit current batch
                futures = {}
                for j, (task_func, task_args, task_kwargs) in enumerate(zip(batch_tasks, batch_args, batch_kwargs)):
                    task_id = f"batch_{self._task_counter}_{i+j}"
                    future = executor.submit(task_func, *task_args, **task_kwargs)
                    futures[future] = task_id

                # Wait for current batch to complete
                for future in as_completed(futures):
                    task_id = futures[future]
                    try:
                        result = future.result()
                        results.append(TaskResult(success=True, result=result, task_id=task_id))
                        logger.debug(f"Task {task_id} completed successfully")
                    except Exception as e:
                        results.append(TaskResult(success=False, error=e, task_id=task_id))
                        logger.error(f"Task {task_id} failed: {e}")

        self._task_counter += 1
        return results


# Global task queue instances for different use cases
from libs import constants

github_task_queue = TaskQueue(
    max_concurrent_tasks=constants.RATE_LIMITS["GITHUB_MAX_CONCURRENT_TASKS"],
    max_workers=constants.RATE_LIMITS["GITHUB_MAX_CONCURRENT_TASKS"] + 2,
)
openai_task_queue = TaskQueue(
    max_concurrent_tasks=constants.RATE_LIMITS["OPENAI_MAX_CONCURRENT_TASKS"],
    max_workers=constants.RATE_LIMITS["OPENAI_MAX_CONCURRENT_TASKS"] + 1,
)
general_task_queue = TaskQueue(max_concurrent_tasks=5, max_workers=10)  # For mixed tasks


async def process_items_in_batches(
    items: List[Any], process_func: Callable[[Any], Any], batch_size: int = 5, task_queue: TaskQueue = None
) -> List[TaskResult]:
    """Process a list of items in batches using the specified processing function."""
    if not items:
        return []

    if task_queue is None:
        task_queue = general_task_queue

    results = []

    # Process items in batches
    for i in range(0, len(items), batch_size):
        batch_items = items[i : i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} with {len(batch_items)} items")

        # Create tasks for current batch
        tasks = [process_func for _ in batch_items]
        args_list = [(item,) for item in batch_items]

        # Execute batch
        if asyncio.iscoroutinefunction(process_func):
            batch_results = await task_queue.execute_async_batch(tasks, *args_list)
        else:
            batch_results = task_queue.execute_sync_batch(tasks, args_list)

        results.extend(batch_results)

        # Small delay between batches to be nice to APIs
        if i + batch_size < len(items):
            await asyncio.sleep(0.5)

    successful_results = [r for r in results if r.success]
    failed_results = [r for r in results if not r.success]

    logger.info(f"Batch processing completed: {len(successful_results)} successful, {len(failed_results)} failed")

    return results
