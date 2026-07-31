# BlameGPT Forge app (Bitbucket)

Thin [Atlassian Forge](https://developer.atlassian.com/platform/forge/) app that listens for pull request comment events in Bitbucket Cloud and forwards them to the self-hosted BlameGPT backend. Forge cannot host the Python backend (JS-only runtime, 25s invocation limit, no filesystem), so it acts only as the trigger.

## Setup

1. Install the Forge CLI and log in
   ```bash
   npm install -g @forge/cli
   forge login
   ```
2. Register the app (fills in `app.id` in `manifest.yml`)
   ```bash
   cd forge
   forge register
   ```
3. In `manifest.yml`, replace `blamegpt.example.com` under `permissions.external.fetch.backend` with your BlameGPT server domain.
4. Set the environment variables. The secret must match `BITBUCKET_WEBHOOK_SECRET` in the backend `.env`.
   ```bash
   forge variables set --encrypt BLAMEGPT_WEBHOOK_SECRET <shared_secret>
   forge variables set BLAMEGPT_BACKEND_URL https://<your-backend-domain>
   ```
5. Deploy and install into your Bitbucket workspace
   ```bash
   forge deploy
   forge install --product bitbucket
   ```

Mention `@blamegpt` in a comment on any pull request in the workspace to trigger a review.
