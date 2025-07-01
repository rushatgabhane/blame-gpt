## Why is my shiny new feature not on production yet?

Oh... we have deploy blockers!!

This tool finds the pull requests begging to be reverted so you can go back to shipping.

### Roadmap
This is a rough roadmap. Please suggest small ideas, big ideas, anything and everything!

- [ ] Index a codebase.
- [ ] Q&A over a codebase. Chat with a codebase.
- [ ] Create a bug fixing coding agent. Use existing agents like claude code that can use the codebase index, Q&A feature.
- [ ] Post proposals on Expensify issues to earn revenue.
- [ ] Auditing tool (for a given feature, what code has changed over the past few months).
- [ ] Build moree tools.
- [ ] Make the tools work for any repository.
- [ ] Enterprise support (self hosting, bring your own LLM, auditable code).
- [ ] Sell to more companies.
- [ ] ...
- [ ] 💰💰💰


### How to run locally?

1. Create a virtual env `python3 -m venv venv`
2. Activate the virtual env `source venv/bin/activate`
3. Install requirements `pip install -r requirements.txt`
4. Copy the env file `cp .env.example .env`, and set your personal github token, set openai api key
5. Start the server using `uvicorn main:app --reload`
