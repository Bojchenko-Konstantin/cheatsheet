ENV ?= dev

ENV_PATH = .env.$(ENV)

# Run the server, default mode - dev,
# to change it you have to add ENV variable.
# Example: make runserver ENV=dev
runserver:
	ENV_FILE=$(ENV_PATH) uvicorn src.main:app --reload

# Run tests.
tests:
	ENV_FILE=.env.test pytest
