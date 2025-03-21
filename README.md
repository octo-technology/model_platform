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

### Install dependencies

#### Back and front
Install dependencies for back and front
```bash
poetry install
```

#### Set up env vars

Get local ip for minio:

```bash
ipconfig getifaddr en0
or
make get-ip
```

On ubuntu
```text
hostname -I | awk '{print $1}'
```


Configure env variables
```bash
cp .env.example .env
```

Put Ip in `LOCAL_IP` variable

#### Install for platform

Install minikube.


Install helm
```bash
# Ubuntu
sudo snap install helm --classic
```

Configure helm
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```
### To run frontend
```bash
make frontend
```

### To run Back-end

Launch backend
```bash
eval $(minikube docker-env)
cd infrastructure/registry/
docker build . -t mlflow
cd ../..
make back
```

### Start cluster

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

Deploy db

```bash
make k8s-pgsql
```

Add the following line to your /etc/hosts
```bash
# Mac
127.0.0.1 model-platform.com
# Linux
minikube ip
IP.RESULT model-platform.com
```

Then run the following command and keep it running!!!
```bash
minikube tunnel
```

#### Setup storage
Launch minio local instance

```bash
docker-compose -f infrastructure/minio/docker-compose.yml up
```

#### In case of changed local ip (happens when you change wifi)
If you already have mlflow registry running and you change wifi connection :

Update miniio cluster ip in deployed mlflow registries

Set it in the .env file. and run

```bash
make set-ip
```

## Dev expérience
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
