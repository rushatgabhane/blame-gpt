# [Do things that don't scale](https://www.paulgraham.com/ds.html). 
Focus on manual, labor intensive tasks in the early stages, even though they wouldn't be sustainable as we grow. Prioritize building a strong foundation through direct customer interaction (TB, 

EXFY, DB), even if it's **not scalable** in the long run.


# BlameGPT
BlameGPT finds the PR causing a production issue so you can go back to shipping.
To prevent issues from happening in the first place, BlameGPT does a code review on your PRs.

## How it started?
See this [document](https://docs.google.com/document/d/10Dh3L7Eir5FpBl4IhhwVS-__Ff9Z-xIFyyEpIt9GkBQ). 

### How to run locally?

1. Use python version `3.13`
2. Create a virtual env `python3 -m venv venv`
3. Activate the virtual env `source venv/bin/activate`
4. Install requirements `pip install -r requirements.txt`
5. Copy the env file `cp .env.example .env`, and set your personal github token, set openai api key

> [!WARNING]
> Do NOT set `ENVIRONMENT=production` in your `.env` file - this will create real GitHub comments on live repositories.

6. Start the server using `uvicorn main:app --reload`


#### Github token
- In your personal account, create a new token of type `classic`
- Scope: `repo`, and `notification`

### Notebooks
To run the notebooks run `jupyter lab`.

### Project Structure

```
blame-gpt/
├── controllers/          # FastAPI route handlers
│   ├── webhook_controller.py
│   ├── user_controller.py
├── frontend/            # React TypeScript frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── libs/                # Shared libraries and utilities
│   ├── github.py
│   ├── llm.py
│   ├── prompt_templates/
│   └── sqlite/          # Database clients
├── middlewares/
├── models/              # Pydantic data models
├── services/            # Business logic layer
│   ├── code_review_pipeline.py
│   ├── blame_pipeline.py
│   ├── github/
|       ├──notification_service.py
|       ├──pull_request_service.py
|       ├──issue_service.py
├── main.py              # FastAPI application entry point
└── requirements.txt
```

### Database Migrations
We use Yoyo-migrations to manage database schema changes. 
- All migrations are written in pure SQL.
- The app automatically applies migrations on start. You can also manually apply them using `migrate.sh`
- The migrations are in `libs/sqlite/[db_name]/migrations/`

Naming convention
```sql
000001_init_schema.sql
000002_add_pull_requests_table.sql
000003_add_index_on_issues.sql
```

## Flows
### Code review

Automated code review triggered by `@blamegpt` mentions on pull requests. Reviews code changes for quality, bugs, performance, and security issues, then posts structured feedback as GitHub PR reviews with line-by-line comments.

### Blame pipeline

When a new issue is created, `blame` gets all relevant pull requests, and performs RAG over the issue description and pull requests to rank them.
#### Example
Input: Issue
```
Users cannot login. I went to login page, submitted username and password, but I'm getting a server error.
```
Pipeline: 
- Converts the issue to an embedding
- Gets all the recent PRs
- Converts PR title, description and code summary to embeddings, saves them to DB so new issues don't have to recompute.
- And then finds the relevant PRs using cosine similarity between the issue embedding and PR embedding.
- ~Top 20 similar PRs are sent to LLM to find the top 3 culprit PRs.
- Using blamegpt's personal github token, we add a comment to the issue.
