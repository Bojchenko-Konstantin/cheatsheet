ENV ?= dev

ENV_PATH = .env.$(ENV)

# Run the server, default mode - dev,
# to change it you have to add ENV variable.
# Example: make runserver ENV=dev
runserver:
	ENV_FILE=$(ENV_PATH) uvicorn src.main:app --reload

# Start RabbitMQ container
rabbit:
	@echo "=== Starting RabbitMQ ==="
	@-docker rm -f cheatsheet-rabbitmq 2>/dev/null
	@docker run --rm -d \
		--name cheatsheet-rabbitmq \
		-p "5672:5672" \
		-p "15672:15672" \
		--env "RABBITMQ_DEFAULT_USER=user" \
		--env "RABBITMQ_DEFAULT_PASS=password" \
		--env "RABBITMQ_DEFAULT_VHOST=/" \
		rabbitmq:3.13.7-management-alpine
	@echo "  ✓ RabbitMQ started"
	@echo "  AMQP: localhost:5672"
	@echo "  UI:   http://localhost:15672 (user/password)"


# Start TaskIQ worker (background)
worker:
	@echo "=== Starting TaskIQ Worker (background) ==="
	@-pkill -f "taskiq worker" 2>/dev/null
	@ENV_FILE=$(ENV_PATH) taskiq worker src.infrastructure.broker:BROKER --reload > /dev/null 2>&1 &
	@echo "  ✓ Worker started in background"

# Start TaskIQ worker (foreground)
worker-fg:
	@echo "=== Starting TaskIQ Worker ==="
	ENV_FILE=$(ENV_PATH) taskiq worker src.infrastructure.broker:BROKER

# Stop RabbitMQ and Worker
stop:
	@echo "=== Stopping Services ==="
	@echo "Stopping RabbitMQ..."
	@-docker stop cheatsheet-rabbitmq 2>/dev/null && echo "  ✓ RabbitMQ stopped" || echo "  RabbitMQ not running"
	@-docker rm cheatsheet-rabbitmq 2>/dev/null
	@echo "Stopping TaskIQ worker..."
	@-taskiq worker src.infrastructure.broker:BROKER --stop 2>/dev/null
	@-pkill -f "taskiq worker" 2>/dev/null && echo "  ✓ Worker stopped" || echo "  Worker not running"
	@echo "✓ All services stopped"

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

.PHONY: rabbit worker worker-bg runserver stop migrate test unit integration help
