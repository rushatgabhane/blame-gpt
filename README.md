# [Do things that don't scale](https://www.paulgraham.com/ds.html). 
Focus on manual, labor intensive tasks in the early stages, even though they wouldn't be sustainable as we grow. Prioritize building a strong foundation through direct customer interaction (TB, EXFY, DB), even if it's **not scalable** in the long run.

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

## Deployment

Deploy the backend once, then connect it to GitHub, Bitbucket, or both:

- **[Option A: GitHub](#option-a-github)** - blame + code review, via a GitHub App
- **[Option B: Atlassian Bitbucket](#option-b-atlassian-bitbucket--backend)** - code review only, via an Atlassian Forge app

### Deploy the backend (both options)

Clone the repo, copy the env file, and start the server:

```bash
git clone https://github.com/rushatgabhane/blame-gpt.git
cd blame-gpt
cp .env.example .env   # set the keys for your platform, see below
docker compose up
```

Common `.env` keys:

- `OPENAI_API_KEY` - OpenAI / Claude API key
- `ENVIRONMENT=production` - so BlameGPT posts real comments

The server must be reachable over HTTPS (put nginx/Caddy/Cloudflare in front of port 8000).

### Option A: GitHub

1. **Create a GitHub App**
   - Go to **GitHub Settings → Developer settings → GitHub Apps → New GitHub App**
   - Set the webhook URL to `https://<your-server>/api/webhook/github`, and set a webhook secret
   - Permissions: read/write access to **Issues**, **Pull requests**, and **Contents**
   - Subscribe to events: **Issues**, **Pull request**, **Issue comment**, **Pull request review comment**
   - Generate a private key (`.pem`) and note the **App ID**
2. **Configure `.env`**
   - `GITHUB_APP_ID` - App ID from step 1
   - `GITHUB_APP_PRIVATE_KEY` - the private key in PEM format
   - `GITHUB_WEBHOOK_SECRET` - webhook secret from step 1
3. **Select repositories** - install the GitHub App on your account or organization and choose which repos BlameGPT should monitor. You can change this anytime from the app's **Install App** settings page.

### Option B: Atlassian Bitbucket + backend

Code review only - the blame pipeline is GitHub-only. Bitbucket events are delivered by a small [Atlassian Forge](https://developer.atlassian.com/platform/forge/) app (in [`forge/`](forge/)) that forwards pull request comments to the backend. Forge itself cannot host the backend (JS-only runtime, 25s invocation limit).

1. **Create an access token** - a [workspace or repository access token](https://support.atlassian.com/bitbucket-cloud/docs/access-tokens/) with `repository:read` and `pullrequest:write` scopes
2. **Configure `.env`**
   - `BITBUCKET_ACCESS_TOKEN` - token from step 1
   - `BITBUCKET_WEBHOOK_SECRET` - a shared secret you generate; must match the Forge app's `BLAMEGPT_WEBHOOK_SECRET`
3. **Deploy the Forge app**
   ```bash
   npm install -g @forge/cli
   cd forge
   forge login
   forge register                # fills in app.id in manifest.yml
   # edit manifest.yml: replace blamegpt.example.com with your backend domain
   forge variables set --encrypt BLAMEGPT_WEBHOOK_SECRET <shared_secret>
   forge variables set BLAMEGPT_BACKEND_URL https://<your-server>
   forge deploy
   forge install --product bitbucket
   ```
4. **Select repositories** - installing the Forge app into your Bitbucket workspace covers all its repos; BlameGPT only acts on PRs where `@blamegpt` is mentioned.

Mention `@blamegpt` in a PR comment to trigger a review. Reviews are incremental - only commits since the last review are reviewed; say `@blamegpt full review` to re-review the whole PR. See [`forge/README.md`](forge/README.md) for details.

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
