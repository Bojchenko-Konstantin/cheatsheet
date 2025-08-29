ENV_FILE ?= dev

# Run the server, default mode - dev,
# to change it you have to include ENV_FILE variable.
# Example: make runserver ENV_FILE="prod".
runserver:
	ENV_FILE=$(ENV_FILE) uvicorn src.main:app --reload

# Run tests.
tests:
	ENV_FILE="test" pytest
