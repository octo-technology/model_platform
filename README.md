# What is it ?

A tribe project to build a Model Platform

## Intentions

1. Build a project as a team
2. Test, identify, consolidate convictions on model management at scale
3. Be as portable as possible
4. Use opensource technologies

## Vision and key features of a Model Platform

> **Vision**
    <br>For **models developers**, so that they can **focus on building the best model**, we offer **a model platform** that can **version, deploy, host, govern** models with as few configuration as possible
    <br>For **application developers**, so that they can **integrate models seamlessly**, we offer **a model platform** that can provide a simple API to call.

## How to run

### Prerequisites
Install dependencies
```bash
poetry install
```

### Configure your environment variables
```bash
cp .env.example .env
```

**Ensure you have a mlflow server listening at mlflow_tracking_uri**
For example to have a local mlflow run
```bash
make registry_server
```

### Run backend
```bash
python -m model_platform
```

### Run frontend
```bash
python -m streamlit run front/app.py --server.runOnSave=true
```


## Install minikube

NB: It requires a docker up and running on your computer.

1. Follow instruction [here](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download)
2. Start minikube with `minikube start`
3. Installer kubectl

Check setup is ok :
```shell
kubectl config current-context
```

Should return `minikube`

Build custom mlflow image
```
eval $(minikube docker-env); docker build -t model-registry infrastructure/registry/.
```
