include .env
export $(shell sed 's/=.*//' .env)

PGSQL_HOST := modelplatform-pgsql
PGSQL_NAMESPACE := pgsql
POSTGRES_PASSWORD := your_postgres_password
POSTGRES_USER := postgres
SHELL := /bin/bash

k8s-network-conf:
	kubectl apply -f infrastructure/k8s/namespaces.yaml
	kubectl apply -f infrastructure/k8s/minio-deployment.yaml
	kubectl apply -f infrastructure/k8s/nginx-deployment.yaml
	kubectl apply -f infrastructure/k8s/nginx-configmap.yaml
	kubectl rollout restart deployment/nginx-reverse-proxy
	kubectl apply -f infrastructure/k8s/ingress.yaml


k8s-backend:
	@if [ "$$SHELL" = "/bin/zsh" ] || [ "$$SHELL" = "/usr/bin/zsh" ]; then \
		eval $$(minikube docker-env) && docker build ./ -f ./backend/Dockerfile --no-cache -t backend && kubectl apply -f infrastructure/k8s/backend-deployment.yaml ; \
	elif [ "$$SHELL" = "/usr/bin/fish" ] || [ "$$SHELL" = "/bin/fish" ] || [ -n "$$FISH_VERSION" ]; then \
		eval $$(minikube -p minikube docker-env) && docker build ./ -f ./backend/Dockerfile --no-cache -t backend && kubectl apply -f infrastructure/k8s/backend-deployment.yaml ; \
	else \
		eval $$(minikube docker-env) && docker build ./ -f ./backend/Dockerfile --no-cache -t backend && kubectl apply -f infrastructure/k8s/backend-deployment.yaml ; \
	fi
	kubectl rollout restart deployment/backend -n model-platform

k8s-frontend:
	@if [ "$$SHELL" = "/bin/zsh" ] || [ "$$SHELL" = "/usr/bin/zsh" ]; then \
		eval $$(minikube docker-env) && docker build ./ -f ./frontend/Dockerfile -t frontend && kubectl apply -f infrastructure/k8s/frontend-deployment.yaml ; \
	elif [ "$$SHELL" = "/usr/bin/fish" ] || [ "$$SHELL" = "/bin/fish" ] || [ -n "$$FISH_VERSION" ]; then \
		eval $$(minikube -p minikube docker-env) && docker build ./ -f ./frontend/Dockerfile -t frontend && kubectl apply -f infrastructure/k8s/frontend-deployment.yaml ; \
	else \
		eval $$(minikube docker-env) && docker build ./ -f ./frontend/Dockerfile -t frontend && kubectl apply -f infrastructure/k8s/frontend-deployment.yaml ; \
	fi
	kubectl rollout restart deployment/frontend -n model-platform

k8s-modelplatform: k8s-modelplatform k8s-backend k8s-frontend

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
	kubectl delete namespace monitoring --ignore-not-found
	until ! kubectl get namespace monitoring &>/dev/null; do sleep 2; done

	kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	helm repo update
	helm install kube-prometheus-stack --namespace monitoring prometheus-community/kube-prometheus-stack
	helm upgrade kube-prometheus-stack prometheus-community/kube-prometheus-stack \
		-n monitoring \
		-f infrastructure/k8s/monitoring/prometheus-values.yaml
	helm upgrade kube-prometheus-stack prometheus-community/kube-prometheus-stack \
		-n monitoring \
		-f infrastructure/k8s/monitoring/grafana-values.yaml
	kubectl rollout restart deployment/nginx-reverse-proxy

run-ci-arm:
	act -W .github/workflows/test.yml --container-architecture linux/arm64

run-ci-amd:
	act -W .github/workflows/test.yml

front:
	python -m streamlit run frontend/app.py --server.runOnSave=true

back:
	eval $(minikube docker-env); python -m backend

build-mlflow:
	@if [ "$$SHELL" = "/bin/zsh" ] || [ "$$SHELL" = "/usr/bin/zsh" ]; then \
		eval $$(minikube docker-env) && docker build -t mlflow -f infrastructure/registry/Dockerfile .; \
	elif [ "$SHELL" = "/usr/bin/fish" ] || [ "$SHELL" = "/bin/fish" ] || [ -n "$FISH_VERSION" ]; then \
		eval $(minikube -p minikube docker-env) && docker build -t mlflow -f infrastructure/registry/Dockerfile . ; \
	else \
		eval $$(minikube docker-env) && docker build -t mlflow -f infrastructure/registry/Dockerfile .; \
	fi

MINIKUBE_GATEWAY := $(shell minikube ssh "ip route" | grep '^default' | awk '{print $$3}')

get-ip:
	@echo "Gateway Minikube: $(MINIKUBE_GATEWAY)"

set-ip:
	python backend/domain/use_cases/main_update_registries_minio_ip.py

model-platform: back front
