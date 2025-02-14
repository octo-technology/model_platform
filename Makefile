include .env

k8s-network-conf:
	kubectl apply -f infrastructure/k8s/namespaces.yaml
	kubectl apply -f infrastructure/k8s/nginx-deployment.yaml
	kubectl apply -f infrastructure/k8s/nginx-configmap.yaml
	kubectl rollout restart deployment/nginx-reverse-proxy
	kubectl apply -f infrastructure/k8s/ingress.yaml


run-ci-arm:
	act -W .github/workflows/test.yml --container-architecture linux/arm64

run-ci-amd:
	act -W .github/workflows/test.yml

frontend:
	python -m streamlit run front/app.py --server.runOnSave=true

back:
	python -m model_platform
