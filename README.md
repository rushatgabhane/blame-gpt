# [Do things that don't scale](https://www.paulgraham.com/ds.html). 
Focus on manual, labor intensive tasks in the early stages, even though they wouldn't be sustainable as we grow. Prioritize building a strong foundation through direct customer interaction (EXFY, DB), even if it's **not scalable** in the long run.


# BlameGPT
BlameGPT finds the PR causing a deploy blocker so you can go back to shipping.

## Vision
Be obsessed with developer experience. Beat cursor etc by building AI tools that integrate into existing processes of engineers working in a company.
Make the repository public once the roadmap is shipped. Use SaaS model or provide private fork to companies for self hosting at a flat fee.

## How it started?
See this [document](https://docs.google.com/document/d/10Dh3L7Eir5FpBl4IhhwVS-__Ff9Z-xIFyyEpIt9GkBQ). 

### How to run locally?

1. Use python version `3.13`
2. Create a virtual env `python3 -m venv venv`
3. Activate the virtual env `source venv/bin/activate`
4. Install requirements `pip install -r requirements.txt`
5. Copy the env file `cp .env.example .env`, and set your personal github token, set openai api key
6. Start the server using `uvicorn main:app --reload`

### Notebooks
To run the notebooks run `jupyter lab`.

### Project Structure

```
blame-gpt/
├── controllers/          # FastAPI route handlers
│   ├── blame_controller.py
│   ├── issue_controller.py
│   ├── test_steps_controller.py
│   └── docs_controller.py
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
│   ├── blame_pipeline.py
│   ├── github/
|       ├──notification_service.py
|       ├──pull_request_service.py
|       ├──issue_service.py
│   ├── docs_service/
│   └── test_step/
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

### Notification service

The notification service listens for GitHub notifications and processes `@blamegpt` mentions to trigger various commands.

Pipeline:
- Polls GitHub notifications API for new mentions
- Validates notifications are from configured repositories
- Classifies the command type using LLM (blame, test steps, documentation, etc.)
- Creates user records and LLM token usage logs for tracking
- Routes to appropriate pipeline (blame_pipeline, test_step_pipeline, etc.)
- Provides real-time feedback via comment reactions and status updates
- Unsubscribes from processed notifications to avoid duplicates

### Blame pipeline

When a new issue is created, a [github action](https://github.com/Blame-GPT/action/blob/main/action.yml) installed on a repo invokes `api/blame` endpoint.
`blame_pipeline` streams the logs to the action, gets all relevant pull requests, and performs RAG over the issue description and pull requests to rank them.
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

### Test step pipeline

When a PR author or reviewer requests test steps, the `test_step_pipeline` generates comprehensive QA test steps for the pull request.
#### Example
Input: Pull request with linked issues
```
PR: "Add user authentication endpoints"
Linked issue: "Users need to be able to login and logout"
```
Pipeline:
- Fetches the pull request details and linked issues
- Extracts test steps from linked issues to understand requirements
- Finds similar test patterns from past PRs using embedding similarity
- Uses LLM to generate comprehensive test steps based on code changes
- Consolidates similar test steps to remove repetition
- Posts formatted test steps as a comment on the PR for authors to refine


## Product roadmap
This is a rough roadmap. Please suggest **small ideas, big ideas**, anything and everything by creating a new issue!

- **Documentation update on PR**
  - [x] Update user docs if a PR changes UI. (done for helpDot)
 
- **Culprit detection**
  - [x] Find a culprit pull request for a given deploy blocker
  - [ ] Generalise to *any* issue, not just deploy blockers

- **QA test steps generation**
  - [x] For a PR, authors can generate test steps to start with. ([@kevinam99](https://github.com/kevinam99))

- **Code understanding**
  - [ ] Index a codebase (graph, RAG, hybrid, or better)
    - [x] Phase 1 done ([Niteeq](https://github.com/nitee-13)) for EXFY
    - [ ] Phase 2 ... 
  - [ ] Q&A / “Chat with the codebase”

- **Auto revert**
  - [ ] Revert a PR, resolve conflicts and add them to the body.
      
- **Test generator for evaluating agent**
  - [ ] For a given issue, we won't know if solution is correct. So write tests (similar to [swe-lancer](https://github.com/openai/SWELancer-Benchmark/blob/6fee3b0200d90f5b24aab36de6c787ec849e76aa/issues/102/test.py#L97) for frontend), and figure out for backend too.
  - [ ] The solver can then use these tests to see if solution is correct, and run in a loop.

- **Review bot**
  - [ ] Analyze old performance improvement PRs. And build a review bot that catches and suggests the improvements. (see [problem statement here](https://expensify.slack.com/archives/C05LX9D6E07/p1752231564356839))
  - [ ] Analyze past deploy blockers and build a **review bot** to prevent new deploy blockers

- **Analytics**
  - [ ] Build dashboards  
- **Autonomous coding agents**
  - [ ] Bug fixing agent powered by MCP connected to Claude-Code, using the code-index + Q&A features

- **Issue improvements**
  - [ ] Parse images & log attachments from issues (screenshots, stack traces, etc.)

- **Internal dog-fooding**
  - [ ] Install BlameGPT on **our own repo** and use it daily

- **Design doc**
  - [ ] Technical design doc, and diagramGPT
  - [ ] Fit it in the product and cross sell it

- **Monetisation & growth**
  - [x] User acquisition using comment. Users can `@blamegpt` on any issue and we can invoke a tool, and auto create a freemium account.
    - i.e. use bottom up approach to acquire users. Figure out bottom up approach for private repos too. 
  - [ ] Post solution proposals on Expensify issues (earn revenue)
  - [ ] Build more tools
  - [ ] Make the tool-suite work for *any* repository
  - [ ] Enterprise tier  
        - Jira integration  
        - Self-hosting / BYO-LLM
  - [ ] Add memory https://github.com/GreatScottyMac/RooFlow
  - [ ] Sell to DB
  - [ ] Sell to more companies
  - [ ] Apply for seed funding
  - [ ] 💰💰💰

