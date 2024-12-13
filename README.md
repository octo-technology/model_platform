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

**Ensure you have an mlflow server listening at mlflow_tracking_uri**


### Run
```bash
poetry run python -m model_platform
```
