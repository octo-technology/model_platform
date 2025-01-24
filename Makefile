include .env

mlflow_server:
	mlflow server \
		--backend-store-uri postgresql://user:password@127.0.0.1:5432/mlflowdb \
		--artifacts-destination s3://bucket \
		--host localhost \
		--port $(MLFLOW_PORT)


registry_server:
	docker-compose -f infrastructure/docker-compose.yml up -d
	make mlflow_server


run-ci-arm:
	act -W .github/workflows/test.yml --container-architecture linux/arm64

run-ci-amd:
	act -W .github/workflows/test.yml
