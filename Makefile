.PHONY: up down reset inject logs test smoke deploy

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	curl -s -X POST http://localhost:8080/api/demo/reset | python3 -m json.tool

inject:
	curl -s -X POST http://localhost:8080/api/demo/inject | python3 -m json.tool

logs:
	docker compose logs -f

test:
	python3 -m pytest tests/ -v

smoke:
	./scripts/smoke-test.sh

deploy:
	sudo ./scripts/deploy.sh
