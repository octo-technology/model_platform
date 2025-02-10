include .env

registry_server:
	docker-compose -f infrastructure/docker-compose.yml up -d

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
