# Rate Limiting and Retry Logic

This document describes the rate limiting and retry logic implemented to handle API rate limits for both GitHub and OpenAI APIs.

## Overview

The implementation provides:
- **Rate limiting** with configurable requests per minute
- **Exponential backoff** with jitter for retries
- **Task queues** to manage concurrent requests
- **Smart retry logic** that parses error messages for optimal wait times
- **Configurable limits** for easy adjustment

## Architecture

### Components

1. **Rate Limiter** (`libs/rate_limiter.py`)
   - Thread-safe rate limiting with async/await support
   - Exponential backoff with jitter
   - Parses retry-after headers and error messages
   - Separate limiters for GitHub and OpenAI

2. **Task Queue** (`libs/task_queue.py`)
   - Manages concurrent API requests
   - Batched processing with configurable concurrency
   - Support for both sync and async functions
   - Comprehensive error handling and reporting

3. **Configuration** (`libs/constants.py`)
   - Centralized rate limit configuration
   - Easy to adjust limits without code changes

### Rate Limits

Current conservative settings:
- **GitHub API**: 50 requests/minute, 3 concurrent tasks, 3 max retries
- **OpenAI API**: 30 requests/minute, 2 concurrent tasks, 5 max retries

## Usage

### Decorators

The simplest way to add rate limiting to existing functions:

```python
from libs.rate_limiter import rate_limited_github, rate_limited_openai

@rate_limited_github
def fetch_pull_request(pr_id):
    return repo.get_pull(pr_id)

@rate_limited_openai
def generate_summary(text):
    return llm.invoke(text)
```

### Task Queues

For batch processing multiple items:

```python
from libs.task_queue import github_task_queue

# Process multiple PR IDs
results = github_task_queue.execute_sync_batch(
    tasks=[fetch_pull_request for _ in pr_ids],
    args_list=[(pr_id,) for pr_id in pr_ids]
)

# Check results
successful = [r for r in results if r.success]
failed = [r for r in results if not r.success]
```

## Error Handling

The system handles various types of errors:

1. **Rate Limit Errors (429)**
   - Automatic retry with exponential backoff
   - Parses suggested wait time from error messages
   - Respects retry-after headers

2. **Transient Errors**
   - Network timeouts, connection errors
   - Server errors (5xx)
   - Automatic retry with backoff

3. **Non-Retryable Errors**
   - Authentication errors (401, 403)
   - Not found errors (404)
   - Client errors (4xx except 429)

## Monitoring

The system provides comprehensive logging:
- Rate limit warnings when approaching limits
- Retry attempts with delay information
- Success/failure statistics for batch operations
- Error details for troubleshooting

## Configuration

Adjust rate limits in `libs/constants.py`:

```python
RATE_LIMITS = {
    "GITHUB_REQUESTS_PER_MINUTE": 50,  # Increase for higher GitHub limits
    "OPENAI_REQUESTS_PER_MINUTE": 30,  # Adjust based on your OpenAI plan
    "GITHUB_MAX_CONCURRENT_TASKS": 3,  # Max parallel GitHub calls
    "OPENAI_MAX_CONCURRENT_TASKS": 2,  # Max parallel OpenAI calls
    "GITHUB_MAX_RETRIES": 3,           # Retry attempts for GitHub
    "OPENAI_MAX_RETRIES": 5,           # Retry attempts for OpenAI
}
```

## Testing

Run the test suite to validate functionality:

```bash
cd /home/runner/work/blame-gpt/blame-gpt
PYTHONPATH=. python /tmp/test_rate_limiting.py
```

The tests validate:
- Basic rate limiting behavior
- Task queue concurrency control
- Decorator functionality
- Error handling and retries