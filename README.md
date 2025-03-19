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

### Run backend
```bash
make back
```

### Run frontend
```bash
make frontend
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
make k8s-network-conf
```

Add the following line to your /etc/hosts
```bash
# Mac
127.0.0.1 model-platform.com
# Linux
minkube ip
IP.RESULT model-platform.com
```

Then run the following command and keep it running!!!
```bash
minikube tunnel
```

Set minikube docker build environment

```bash
eval $(minikube docker-env)
```

Get local ip for minio:

```bash
ipconfig getifaddr en0
or
make get-ip
```

Launch minio local instance

```bash
docker-compose -f infrastructure/minio/docker-compose.yml up
```

Update miniio cluster ip in deployed mlflow registries

Set it in the .env file. and run

```bash
make set-ip
```
