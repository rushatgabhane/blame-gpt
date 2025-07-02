# BlameGPT

BlameGPT finds the PR causing a deploy blocker so you can go back to shipping.

## Vision
Beat cursor, greptile etc by building AI tools that integrate into existing processes of engineers working in a company.

## How it started?
See this [document](https://docs.google.com/document/d/10Dh3L7Eir5FpBl4IhhwVS-__Ff9Z-xIFyyEpIt9GkBQ). 

## Product roadmap
This is a rough roadmap. Please suggest **small ideas, big ideas**, anything and everything by creating a new issue!

- **Culprit detection**
  - [x] Find a culprit pull request for a given deploy blocker
  - [ ] Generalise to *any* issue, not just deploy blockers

- **Code understanding**
  - [ ] Index a codebase (graph, RAG, hybrid, or better)
  - [ ] Q&A / “Chat with the codebase”
  - [ ] Auditing tool – “show everything that changed for feature X in the last N months”
      
- **Test generator for evaluating agent**
  - [ ] For a given issue, we won't know if solution is correct. So write tests (similar to [swe-lancer](https://github.com/openai/SWELancer-Benchmark/blob/6fee3b0200d90f5b24aab36de6c787ec849e76aa/issues/102/test.py#L97) for frontend), and figure out for backend too.
  - [ ] The solver can then use these tests to see if solution is correct, and run in a loop.

- **Review bot**
  - [ ] Analyze past deploy blockers and build a **review bot** to prevent new deploy blockers

- **QA test steps generation**
  - [ ] For a PR, authors can generate test steps to start with.

- **Analytics**
  - [ ] Build dashboards  
- **Autonomous coding agents**
  - [ ] Bug fixing agent powered by MCP connected to Claude-Code, using the code-index + Q&A features

- **Issue improvements**
  - [ ] Parse images & log attachments from issues (screenshots, stack traces, etc.)

- **Internal dog-fooding**
  - [ ] Install BlameGPT on **our own repo** and use it daily

- **Monetisation & growth**
  - [ ] User acquisition using comment. Users can `@blamegpt` on any issue and we can invoke a tool, and auto create a freemium account.
    - i.e. use bottom up approach to acquire users. Figure out bottom up approach for private repos too. 
  - [ ] Post solution proposals on Expensify issues (earn revenue)
  - [ ] Build more tools
  - [ ] Make the tool-suite work for *any* repository
  - [ ] Enterprise tier  
        - Jira integration  
        - Self-hosting / BYO-LLM  
        - Auditable code paths
  - [ ] Sell to more companies
  - [ ] 💰💰💰

### How to run locally?

1. Use python version `3.13`
2. Create a virtual env `python3 -m venv venv`
3. Activate the virtual env `source venv/bin/activate`
4. Install requirements `pip install -r requirements.txt`
5. Copy the env file `cp .env.example .env`, and set your personal github token, set openai api key
6. Start the server using `uvicorn main:app --reload`


### Project Structure

```
blame-gpt/
├── controllers/          # FastAPI route handlers
│   ├── blame_controller.py
│   ├── issue_controller.py
│   └── ...
├── frontend/            # React TypeScript frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── libs/                # Shared libraries and utilities
│   ├── github.py
│   ├── llm.py
│   └── sqlite/          # Database clients
├── middlewares/
├── models/              # Pydantic data models
├── services/            # Business logic layer
│   ├── blame_pipeline.py
│   ├── github/
│   └── docs_service/
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
