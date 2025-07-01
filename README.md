# BlameGPT

BlameGPT finds the PR causing a deploy blocker so you can go back to shipping.

## Vision
Beat cursor, greptile etc by building AI tools that integrate into existing processes of engineers working in a company.

## How it started?
See this [document](https://docs.google.com/document/d/10Dh3L7Eir5FpBl4IhhwVS-__Ff9Z-xIFyyEpIt9GkBQ). 

## Product roadmap
This is a rough roadmap. Please suggest **small ideas, big ideas**, anything and everything!

- [x] Find a culprit pull request for a given deploy blocker.
- [ ] Find culprit pull request for any issue, not just deploy blockers.
- [ ] Index a codebase (graph, rag, or hybrid of both, or something better).
- [ ] Q&A over a codebase. Chat with a codebase.
- [ ] Create a bug fixing coding agent. Use existing agents like claude code that can use the codebase index, Q&A feature.
- [ ] Post proposals on Expensify issues to earn revenue.
- [ ] Auditing tool (for a given feature, what code has changed over the past few months).
- [ ] Build moree tools.
- [ ] Make the tools work for any repository.
- [ ] Enterprise support (jira, self hosting, bring your own LLM, auditable code).
- [ ] Sell to more companies.
- [ ] ...
- [ ] 💰💰💰


### How to run locally?

1. Create a virtual env `python3 -m venv venv`
2. Activate the virtual env `source venv/bin/activate`
3. Install requirements `pip install -r requirements.txt`
4. Copy the env file `cp .env.example .env`, and set your personal github token, set openai api key
5. Start the server using `uvicorn main:app --reload`


