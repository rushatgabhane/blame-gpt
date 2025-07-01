"""Rate limiting and retry utilities for API calls."""

import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Optional, Dict
import openai
from github import GithubException

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe rate limiter with exponential backoff and retry logic."""

    def __init__(self, max_requests_per_minute: int = 60, max_retries: int = 3):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_retries = max_retries
        self.requests = []
        self._lock = asyncio.Lock()

    async def _clean_old_requests(self):
        """Remove requests older than 1 minute."""
        current_time = time.time()
        self.requests = [req_time for req_time in self.requests if current_time - req_time < 60]

    async def _wait_if_needed(self):
        """Wait if we're approaching the rate limit."""
        await self._clean_old_requests()

        if len(self.requests) >= self.max_requests_per_minute:
            # Wait until the oldest request is more than 1 minute old
            oldest_request = min(self.requests)
            wait_time = 60 - (time.time() - oldest_request) + 1  # Add 1 second buffer
            if wait_time > 0:
                logger.info(f"Rate limit approaching, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                await self._clean_old_requests()

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with rate limiting and retry logic."""
        async with self._lock:
            await self._wait_if_needed()
            self.requests.append(time.time())

        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except (GithubException, openai.RateLimitError) as e:
                if attempt == self.max_retries:
                    logger.error(f"Max retries exceeded for {func.__name__}: {e}")
                    raise

                # Calculate exponential backoff with jitter
                base_delay = 2**attempt
                jitter = random.uniform(0.1, 0.5)
                delay = base_delay + jitter

                # For OpenAI rate limits, extract suggested wait time if available
                if isinstance(e, openai.RateLimitError):
                    if hasattr(e, "response") and e.response and "retry-after" in e.response.headers:
                        delay = max(delay, float(e.response.headers["retry-after"]))
                    # Also check for rate limit message with suggested wait time
                    error_message = str(e)
                    if "Please try again in" in error_message:
                        try:
                            wait_time_str = error_message.split("Please try again in ")[1].split("s.")[0]
                            suggested_delay = float(wait_time_str.replace("s", ""))
                            delay = max(delay, suggested_delay + 1)  # Add 1 second buffer
                        except (IndexError, ValueError):
                            pass

                # For GitHub rate limits, check for retry-after header
                elif isinstance(e, GithubException) and e.status == 429:
                    if hasattr(e, "headers") and "retry-after" in e.headers:
                        delay = max(delay, int(e.headers["retry-after"]))

                logger.warning(
                    f"Rate limit hit for {func.__name__}, retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_retries + 1})"
                )
                await asyncio.sleep(delay)
            except Exception as e:
                # For other exceptions, only retry if it might be transient
                if attempt == self.max_retries or not _is_retryable_error(e):
                    raise

                delay = (2**attempt) + random.uniform(0.1, 0.5)
                logger.warning(f"Transient error for {func.__name__}, retrying in {delay:.2f}s: {e}")
                await asyncio.sleep(delay)


def _is_retryable_error(error: Exception) -> bool:
    """Check if an error is worth retrying."""
    error_str = str(error).lower()
    retryable_patterns = [
        "timeout",
        "connection",
        "network",
        "temporary",
        "server error",
        "service unavailable",
        "bad gateway",
        "gateway timeout",
    ]
    return any(pattern in error_str for pattern in retryable_patterns)


# Global rate limiters for different services
from libs import constants

github_rate_limiter = RateLimiter(
    max_requests_per_minute=constants.RATE_LIMITS["GITHUB_REQUESTS_PER_MINUTE"],
    max_retries=constants.RATE_LIMITS["GITHUB_MAX_RETRIES"],
)
openai_rate_limiter = RateLimiter(
    max_requests_per_minute=constants.RATE_LIMITS["OPENAI_REQUESTS_PER_MINUTE"],
    max_retries=constants.RATE_LIMITS["OPENAI_MAX_RETRIES"],
)


def rate_limited_github(func: Callable) -> Callable:
    """Decorator for GitHub API calls with rate limiting."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        return await github_rate_limiter.execute(func, *args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        return asyncio.run(github_rate_limiter.execute(func, *args, **kwargs))

    # Return async wrapper if the original function is async, otherwise sync
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def rate_limited_openai(func: Callable) -> Callable:
    """Decorator for OpenAI API calls with rate limiting."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        return await openai_rate_limiter.execute(func, *args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        return asyncio.run(openai_rate_limiter.execute(func, *args, **kwargs))

    # Return async wrapper if the original function is async, otherwise sync
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
