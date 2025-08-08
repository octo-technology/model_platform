include .env
export $(shell sed 's/=.*//' .env)

PGSQL_HOST := modelplatform-pgsql
PGSQL_NAMESPACE := pgsql
POSTGRES_PASSWORD := your_postgres_password
POSTGRES_USER := postgres
SHELL := /bin/bash

k8s-network-conf:
	kubectl apply -f infrastructure/k8s/namespaces.yaml
	kubectl apply -f infrastructure/k8s/nginx-deployment.yaml
	kubectl apply -f infrastructure/k8s/nginx-configmap.yaml
	kubectl rollout restart deployment/nginx-reverse-proxy
	kubectl apply -f infrastructure/k8s/ingress.yaml

k8s-modelplatform:
	@eval $$(minikube docker-env) && docker build ./ -f ./backend/Dockerfile --no-cache -t backend && docker build ./ -f ./frontend/Dockerfile -t frontend && kubectl apply -f infrastructure/k8s/backend-deployment.yaml && kubectl apply -f infrastructure/k8s/frontend-deployment.yaml
		kubectl get deployments -n model-platform -o name | xargs -I {} kubectl rollout restart {} -n model-platform


k8s-pgsql:
	# Nettoyage
	kubectl delete namespace $(PGSQL_NAMESPACE) --ignore-not-found
	until ! kubectl get namespace $(PGSQL_NAMESPACE) &>/dev/null; do sleep 2; done
	helm uninstall $(PGSQL_HOST) --namespace=$(PGSQL_NAMESPACE) 2>/dev/null || echo "Helm release '$(PGSQL_HOST)' not found, skipping uninstall"

	# Création du namespace
	kubectl create namespace $(PGSQL_NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -

	# Application de la ConfigMap d'initialisation
	kubectl apply -f infrastructure/k8s/pg-init-schemas.yaml
	echo "ConfigMap applied successfully"

	# Installation de PostgreSQL avec Helm
	helm install $(PGSQL_HOST) bitnami/postgresql \
		--set global.postgresql.auth.postgresPassword=$(POSTGRES_PASSWORD) \
		--set global.postgresql.auth.username=$(POSTGRES_USER) \
		--set global.postgresql.auth.password=$(POSTGRES_PASSWORD) \
		--set primary.initdb.scriptsConfigMap=pg-init-schemas \
		--set primary.persistence.enabled=true \
		--set primary.persistence.size=8Gi \
		--namespace=$(PGSQL_NAMESPACE) \
		--timeout=10m \
		--wait

k8s-pgsql-status:
	kubectl get pods -n $(PGSQL_NAMESPACE)
	kubectl get configmap -n $(PGSQL_NAMESPACE)
	kubectl logs -n $(PGSQL_NAMESPACE) -l app.kubernetes.io/name=postgresql

k8s-pgsql-connect:
	kubectl run postgresql-client --rm --restart='Never' --namespace $(PGSQL_NAMESPACE) --image docker.io/bitnami/postgresql:16 --env="PGPASSWORD=$(POSTGRES_PASSWORD)" --command -- psql --host $(PGSQL_HOST)-postgresql --port 5432 -U $(POSTGRES_USER) -d postgres

k8s-pgsql-test:
	kubectl run postgresql-test --rm -i --restart='Never' --namespace $(PGSQL_NAMESPACE) --image docker.io/bitnami/postgresql:13 --env="PGPASSWORD=$(POSTGRES_PASSWORD)" -- psql --host $(PGSQL_HOST)-postgresql --port 5432 -U $(POSTGRES_USER) -d postgres -c "\l"

k8s-pgsql-test-roles:
	kubectl run postgresql-test-roles --rm -i --restart='Never' --namespace $(PGSQL_NAMESPACE) --image docker.io/bitnami/postgresql:16 --env="PGPASSWORD=$(POSTGRES_PASSWORD)" -- psql --host $(PGSQL_HOST)-postgresql --port 5432 -U $(POSTGRES_USER) -d postgres -c "SELECT rolname FROM pg_roles WHERE rolname LIKE 'app_%';"

run-ci-arm:
	act -W .github/workflows/test.yml --container-architecture linux/arm64

run-ci-amd:
	act -W .github/workflows/test.yml

front:
	python -m streamlit run frontend/app.py --server.runOnSave=true

back:
	eval $(minikube docker-env); python -m backend

build-mlflow:
	@eval $$(minikube docker-env) && docker build -t mlflow -f infrastructure/registry/Dockerfile .

get-ip:
	ipconfig getifaddr en0

set-ip:
	python backend/domain/use_cases/main_update_registries_minio_ip.py

model-platform: back front
