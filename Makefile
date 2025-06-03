ruff:
	uvx ruff check --fix .
	uvx ruff format .

run:
	uv run -m src.main

docker-run:
	docker-compose -f .docker/docker-compose.yaml down
	docker-compose -f .docker/docker-compose.yaml up --build

docker-db:
	docker-compose -f .docker/docker-compose.yaml up --build db -d