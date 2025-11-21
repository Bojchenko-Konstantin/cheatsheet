ENV ?= dev

ENV_PATH = .env.$(ENV)

# Run the server, default mode - dev,
# to change it you have to add ENV variable.
# Example: make runserver ENV=dev
runserver:
	ENV_FILE=$(ENV_PATH) uvicorn src.main:app --reload

# Apply all unapplied migrations to the latest version
migrate:
	ENV_FILE=$(ENV_PATH) alembic upgrade head

# Run all tests.
test:
	ENV_FILE=.env.test pytest

# Run unit tests.
unit:
	ENV_FILE=.env.test pytest -m "not integration"

# Run integration tests.
integration:
	ENV_FILE=.env.test pytest -m integration
