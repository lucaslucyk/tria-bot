.PHONY: build
build:
	sudo podman build -t tria-bot-app:local .

.PHONY: up
up:
	sudo podman-compose up

.PHONY: detach
detach:
	sudo podman-compose up -d

.PHONY: down
down:
	sudo podman-compose down