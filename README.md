## Why is my shiny new feature not on production yet?

Oh... we have deploy blockers!!

This tool finds the pull requests begging to be reverted so you can go back to shipping.


(Blame the PR, not your coworker. Probably.)


## Finding the PR causing a deploy blocker
<img src="https://github.com/user-attachments/assets/c049bc22-b194-45ef-b2c7-1e58bd6a999b" height=500>

## Enterprise & Self-Hosted LLM Support

blame-gpt now supports bring-your-own LLM (BYOLLM) and self-hosted models for enterprise deployments.

### Supported LLM Providers

- **OpenAI** (default): Uses OpenAI API
- **Anthropic**: Uses Anthropic's Claude models  
- **Custom**: Self-hosted or other OpenAI-compatible endpoints

### Configuration

Set these environment variables to configure your LLM provider:

```bash
# LLM Provider (openai, anthropic, custom)
LLM_PROVIDER=openai

# For self-hosted models
LLM_BASE_URL=http://your-llm-server:8080/v1

# Model names (customize based on your deployment)
LLM_REASONING_MODEL=o3-2025-04-16
LLM_REASONING_CHEAP_MODEL=o3-mini-2025-01-31
LLM_CHEAP_MODEL=gpt-4.1-mini
LLM_EMBEDDING_MODEL=text-embedding-3-large

# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
CUSTOM_API_KEY=your_custom_key

# Custom headers for authentication (JSON format)
LLM_CUSTOM_HEADERS={"Authorization": "Bearer your-token"}
```

### Examples

#### Self-hosted OpenAI-compatible model
```bash
LLM_PROVIDER=custom
LLM_BASE_URL=http://localhost:8080/v1
CUSTOM_API_KEY=your-local-api-key
LLM_REASONING_MODEL=llama-2-70b
LLM_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

#### Anthropic Claude
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-key
LLM_REASONING_MODEL=claude-3-sonnet-20240229
# Note: Anthropic doesn't provide embeddings, will fallback to OpenAI
```

#### Enterprise deployment with custom headers
```bash
LLM_PROVIDER=custom
LLM_BASE_URL=https://your-enterprise-llm.company.com/api/v1
CUSTOM_API_KEY=your-enterprise-key
LLM_CUSTOM_HEADERS={"X-Enterprise-Auth": "bearer-token", "X-Tenant-ID": "your-tenant"}
```
