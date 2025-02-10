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

### Optional: Populate SQLLite database with projects
```bash
python dev_utils/populate_sqlitedb.py
```

### Run backend
```bash
python -m model_platform
```

### Run frontend
```bash
python -m streamlit run front/app.py --server.runOnSave=true
```

### Running CI locally
You will need to install nektos act https://nektosact.com/installation/
```bash
#mac ARM
make run-ci-arm
```
or
```bash
#Intel processors
make run-ci-amd
```


### K8S - MINIKUBE

You'll need to have minikube installed

```bash
#recommended configuration to avoid freezing/timeouts
minikube start --cpus 2 --memory 7800
```

Then activate the ingress addon
```bash
minikube addons enable ingress
```

Deploy nginx reverse proxy
```bash
make nginx-proxy-k8s
```

Add the following line to your /etc/hosts
```bash
127.0.0.1 model-platform.com
```

Then run the following command and keep it running!!!
```bash
minikube tunnel
```
