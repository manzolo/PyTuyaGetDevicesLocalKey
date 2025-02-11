DOCKER_COMPOSE := docker compose

.PHONY: start restart cli cli-cache build docker-clean enter-frontend enter-api stop down logs uninstall

# Target to start the containers
start:
	@echo "Restarting $(DOCKER_COMPOSE) containers..."
	$(DOCKER_COMPOSE) up api frontend --remove-orphans -d

# Target to restart the containers
restart:
	@echo "Restarting $(DOCKER_COMPOSE) containers..."
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) rm -f
	$(DOCKER_COMPOSE) up api frontend --remove-orphans -d

# Target to start the cli container
cli:
	@echo "$(DOCKER_COMPOSE) cli..."
	$(DOCKER_COMPOSE) up cli

# Target to start the cli-cache container
cli-cache:
	@echo "$(DOCKER_COMPOSE) cli-cache..."
	$(DOCKER_COMPOSE) up cli-cache

# Target to enter the container
enter-frontend:
	@echo "Entering frontend container..."
	$(DOCKER_COMPOSE) run --remove-orphans frontend /bin/sh

# Target to enter the container
enter-api:
	@echo "Entering api container..."
	$(DOCKER_COMPOSE) run --remove-orphans api /bin/sh

# Target to stop and remove the containers
stop:
	@echo "Stopping and removing $(DOCKER_COMPOSE) containers..."
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) rm -f

# Target to stop and remove the containers
down:
	@echo "Stopping and removing $(DOCKER_COMPOSE) containers..."
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) rm -f

# Target to follow the container logs
logs:
	@echo "Displaying container logs..."
	$(DOCKER_COMPOSE) logs -f

# Target to image build
build:
	@echo "Image build"
	$(DOCKER_COMPOSE) build tuya-localkey-extractor-backend-image
	$(DOCKER_COMPOSE) build tuya-localkey-extractor-frontend-image

# Target to uninstall: stop containers, remove them, and delete all images and volumes
uninstall:
	@echo "Uninstalling..."
	$(DOCKER_COMPOSE) down && $(DOCKER_COMPOSE) rm -f
	$(DOCKER_COMPOSE) down --rmi all --volumes

docker-clean:
	@docker builder prune -f
	@docker system prune -f

help:
	@echo "Available targets:"
	@echo "  start           - Start Docker Compose containers"
	@echo "  restart         - Restart Docker Compose containers"
	@echo "  cli             - Execute cli container"
	@echo "  cli-cache       - Execute cli-cache container"
	@echo "  enter-frontend  - Enter frontend container"
	@echo "  enter-api       - Enter api container"
	@echo "  build           - build images"
	@echo "  docker-clean    - Exec docker builder prune + docker system prune -f"
	@echo "  stop            - Stop and remove Docker Compose containers"
	@echo "  down            - Stop and remove Docker Compose containers"
	@echo "  logs            - Follow container logs"
	@echo "  uninstall       - Remove containers, images, and volumes"
