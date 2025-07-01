## Why is my shiny new feature not on production yet?

Oh... we have deploy blockers!!

This tool finds the pull requests begging to be reverted so you can go back to shipping.


(Blame the PR, not your coworker. Probably.)


### How to run locally?

1. Create a virtual env `python3 -m venv venv`
2. Activate the virtual env `source venv/bin/activate`
3. Install requirements `pip install -r requirements.txt`
4. Copy the env file `cp .env.example .env`, and set your personal github token, set openai api key
5. Start the server using `uvicorn main:app --reload`
