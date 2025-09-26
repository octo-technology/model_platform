# What is it ?

A tribe project to build a Model Platform

## Intentions

1. Build a project as a team
2. Test, identify, consolidate convictions on model management at scale
3. Be as portable as possible
4. Use opensource technologies

## Vision and key features of a Model Platform

> **Vision**
<br>For **models developers**, so that they can **focus on building the best model**, we offer **a model platform** that
> can **version, deploy, host, govern** models with as few configuration as possible
<br>For **application developers**, so that they can **integrate models seamlessly**, we offer **a model platform** that
> can provide a simple API to call.

## How to run

### - Setup your K8S env 

A working minikube is needed for dev purposes

    brew install minikube kubectl

Install helm

    brew install helm

### - Start and setup Cluster

Start minikube cluster with recommended specs

```bash
#recommended configuration to avoid freezing/timeouts
minikube start --cpus 2 --memory 7800 --disk-size 50g
```
(You may need to start colima with custom config)

```bash
colima start --cpu 4 --memory 8
```

Activate Ingress controller add-on

```bash
minikube addons enable ingress
```

Activate ssh tunnel to you minikube cluster

```bash
minikube tunnel
```

### - "DNS" setup

Add the following line to your /etc/hosts

```bash
# Mac
127.0.0.1 model-platform.com
# Linux
minikube ip
IP.RESULT model-platform.com
```

### -  Fill .env file 

**Some values are used (pgsql password etc...) in the init scripts !!**

```bash 
Use the .env.example 
```
### - Setup Namespaces, NGINX, Ingress

```bash
make k8s-network-conf
```

### - Deploy a PGSQL instance with helm

Add bitnami pgsql repo to helm

```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

```bash
make k8s-pgsql
```
It will output a lot of logs, don't worry. 

### - Prepare a custom MLFLow Docker image 
With integrated psycopg2 package 

```bash
    make build-mlflow
```

**You should now have a working k8s environment** 

## Deploy the model platform en k8s 

```bash
  make k8s-modelplatform
```

### Connect to model platform

Via fronted 
    
    http://model-platform.com

or

    mp login --username XXXXX --password XXXX

 Root account is the one you set in the .env file



## TROUBLESHOOTING

### Backend cannot find docker executable

    Error executing docker build: [Errno 2] No such file or directory: 'docker'

Run 

    minikube docker-env
    #Check if same in .env
    if not update and run 
    k8s-modelplatform


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

Access the pgsql via local db client

Run
```bash
kubectl port-forward svc/modelplatform-pgsql-postgresql 5432:5432 -n pgsql
```

Add to you db client

    host: localhost
    port: 5432
    user: postgres
    password: your_postgres_password
    db: model_platform_db

you can now access the model_platform_db database