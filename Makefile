include .env
export $(shell sed 's/=.*//' .env)

k8s-network-conf:
	kubectl apply -f infrastructure/k8s/namespaces.yaml
	kubectl apply -f infrastructure/k8s/nginx-deployment.yaml
	kubectl apply -f infrastructure/k8s/nginx-configmap.yaml
	kubectl rollout restart deployment/nginx-reverse-proxy
	kubectl apply -f infrastructure/k8s/ingress.yaml

k8s-pgsql:
	kubectl create namespace pgsql
	kubectl apply -f infrastructure/k8s/persistent_volume.yaml
	helm install $(PGSQL_HOST) bitnami/postgresql \
	  --set persistence.existingClaim=task-pv-claim \
	  --set global.postgresql.auth.postgresPassword=$(POSTGRES_PASSWORD) \
	  --set global.postgresql.auth.username=$(POSTGRES_USER) \
	  --set global.postgresql.auth.password=$(POSTGRES_PASSWORD) \
	  --namespace=$(PGSQL_NAMESPACE

run-ci-arm:
	act -W .github/workflows/test.yml --container-architecture linux/arm64

run-ci-amd:
	act -W .github/workflows/test.yml

frontend:
	python -m streamlit run front/app.py --server.runOnSave=true

back:
	python -m model_platform

build-mlflow:
	docker build -t mlflow -f infrastructure/registry/Dockerfile .

get-ip:
	ipconfig getifaddr en0
	python model_platform/domain/use_cases/main_update_registries_minio_ip.py

model-platform: back frontend
