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

nginx-proxy-k8s:
	kubectl apply -f infrastructure/k8s_nginx/nginx-deployment.yaml
	kubectl apply -f infrastructure/k8s_nginx/nginx-configmap.yaml
	kubectl rollout restart deployment/nginx-reverse-proxy

run-ci-arm:
	act -W .github/workflows/test.yml --container-architecture linux/arm64

run-ci-amd:
	act -W .github/workflows/test.yml

frontend:
	python -m streamlit run front/app.py --server.runOnSave=true

back:
	python -m model_platform
