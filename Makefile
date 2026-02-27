-include .env
export $(shell [ -f .env ] && sed 's/=.*//' .env)

BACKEND_CONFIGMAP := infrastructure/k8s/backend-configmap.yaml
BACKEND_IMAGE := $(shell awk -F'"' '/BACKEND_IMAGE:/ {print $$2}' $(BACKEND_CONFIGMAP))
FRONTEND_IMAGE := $(shell awk -F'"' '/FRONTEND_IMAGE:/ {print $$2}' $(BACKEND_CONFIGMAP))
MLFLOW_IMAGE := $(shell awk -F'"' '/MLFLOW_IMAGE:/ {print $$2}' $(BACKEND_CONFIGMAP))
IMAGE_TAG := $(shell awk -F'"' '/IMAGE_TAG:/ {print $$2}' $(BACKEND_CONFIGMAP))
export BACKEND_IMAGE FRONTEND_IMAGE MLFLOW_IMAGE IMAGE_TAG

PGSQL_HOST := modelplatform-pgsql
PGSQL_NAMESPACE := pgsql
POSTGRES_PASSWORD := your_postgres_password
POSTGRES_USER := postgres
SHELL := /bin/bash

k8s-network-conf:
	kubectl apply -f infrastructure/k8s/namespaces.yaml
	kubectl apply -f infrastructure/k8s/minio-deployment.yaml
	kubectl apply -f infrastructure/k8s/nginx-configmap.yaml
	kubectl apply -f infrastructure/k8s/nginx-deployment.yaml
	kubectl apply -f infrastructure/k8s/ingress.yaml
	kubectl rollout restart deployment/nginx-reverse-proxy

k8s-backend:
	kubectl apply -f infrastructure/k8s/backend-configmap.yaml
	@if [ -f infrastructure/k8s/backend-secret.yaml ]; then \
		kubectl apply -f infrastructure/k8s/backend-secret.yaml; \
	else \
		echo "⚠️  backend-secret.yaml non trouvé. Copiez backend-secret.yaml.example et remplissez les valeurs."; \
		exit 1; \
	fi
	envsubst < infrastructure/k8s/backend-deployment.yaml | kubectl apply -f -
	kubectl rollout restart deployment/backend -n model-platform

k8s-frontend:
	kubectl apply -f infrastructure/k8s/frontend-configmap.yaml
	envsubst < infrastructure/k8s/frontend-deployment.yaml | kubectl apply -f -
	kubectl rollout restart deployment/frontend -n model-platform


restart-modelplatform:
	kubectl get deployments -n model-platform -o name | xargs -I {} kubectl rollout restart {} -n model-platform

k8s-pgsql:
	kubectl delete pv postgresdb-persistent-volume --ignore-not-found
	kubectl delete namespace pgsql --ignore-not-found
	kubectl delete pvc db-persistent-volume-claim -n pgsql --ignore-not-found
	until ! kubectl get namespace pgsql &>/dev/null; do sleep 2; done

	kubectl create namespace pgsql --dry-run=client -o yaml | kubectl apply -f -

	kubectl apply -f infrastructure/k8s/pg-init-schemas.yaml
	kubectl apply -f infrastructure/k8s/pgsql-deployment.yaml
	kubectl apply -f infrastructure/k8s/pgsql-init-job.yaml

k8s-monitoring:
	kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	helm repo update
	helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
		--namespace monitoring \
		-f infrastructure/k8s/monitoring/prometheus-values.yaml \
		-f infrastructure/k8s/monitoring/grafana-values.yaml
	kubectl rollout restart deployment/nginx-reverse-proxy


MINIKUBE_GATEWAY := $(shell minikube ssh "ip route" | grep '^default' | awk '{print $$3}')

create-backend-secret:
	@if [ -z "$(POSTGRES_PWD)" ] || [ -z "$(JWT_SECRET)" ] || [ -z "$(ADMIN_EMAIL)" ] || [ -z "$(ADMIN_PWD)" ]; then \
		echo "❌ Usage: make create-backend-secret POSTGRES_PWD=<pwd> JWT_SECRET=<secret> ADMIN_EMAIL=<email> ADMIN_PWD=<pwd>"; \
		exit 1; \
	fi
	kubectl create secret generic backend-secret \
		--namespace=model-platform \
		--from-literal=POSTGRES_PASSWORD='$(POSTGRES_PWD)' \
		--from-literal=JWT_SECRET='$(JWT_SECRET)' \
		--from-literal=ADMIN_EMAIL='$(ADMIN_EMAIL)' \
		--from-literal=ADMIN_PASSWORD='$(ADMIN_PWD)' \
		--dry-run=client -o yaml > infrastructure/k8s/backend-secret.yaml
	@echo "✅ backend-secret.yaml créé (fichier local uniquement, non commité grâce au .gitignore)"

k8s-backend-local:
	eval $$(minikube docker-env) && \
	docker build -t model-platform-backend:local -f backend/Dockerfile .
	kubectl apply -f infrastructure/k8s/backend-configmap.yaml
	@if [ -f infrastructure/k8s/backend-secret.yaml ]; then \
		kubectl apply -f infrastructure/k8s/backend-secret.yaml; \
	else \
		echo "⚠️  backend-secret.yaml non trouvé. Lancez d'abord: make create-backend-secret POSTGRES_PWD=... JWT_SECRET=... ADMIN_EMAIL=... ADMIN_PWD=..."; \
		exit 1; \
	fi
	BACKEND_IMAGE=model-platform-backend IMAGE_TAG=local \
		envsubst < infrastructure/k8s/backend-deployment.yaml | \
		sed 's/imagePullPolicy: Always/imagePullPolicy: Never/' | \
		kubectl apply -f -
	kubectl rollout restart deployment/backend -n model-platform

k8s-frontend-local:
	eval $$(minikube docker-env) && \
	docker build -t model-platform-frontend:local -f frontend/web/Dockerfile frontend/web
	kubectl apply -f infrastructure/k8s/frontend-configmap.yaml
	FRONTEND_IMAGE=model-platform-frontend IMAGE_TAG=local \
		envsubst < infrastructure/k8s/frontend-deployment.yaml | \
		sed 's/imagePullPolicy: Always/imagePullPolicy: Never/' | \
		kubectl apply -f -
	kubectl rollout restart deployment/frontend -n model-platform

k8s-infra: k8s-network-conf k8s-pgsql k8s-monitoring

k8s-modelplatform: k8s-backend k8s-frontend

dev-back:
	uv run python -m backend

dev-front:
	cd frontend/web && python -m http.server 8080
