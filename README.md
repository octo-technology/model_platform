# Model Platform

**Deploy, govern, and monitor ML models on Kubernetes — with built-in EU AI Act compliance.**

![Python](https://img.shields.io/badge/Python-FastAPI-009688?style=flat-square&logo=fastapi)
![Kubernetes](https://img.shields.io/badge/Infra-Kubernetes-326CE5?style=flat-square&logo=kubernetes)
![MLflow](https://img.shields.io/badge/Registry-MLflow-0194E2?style=flat-square&logo=mlflow)
![License](https://img.shields.io/badge/License-Open_Source-00A3BE?style=flat-square)

---

## What is Model Platform?

Model Platform is an open-source MLOps platform that lets ML engineers **version, deploy, host, and govern** machine learning models on Kubernetes with minimal configuration. It bridges the gap between model training (MLflow) and production serving — while generating the compliance documentation that the **EU AI Act** now requires.

## Why?

Deploying ML models to production is still manual and fragmented. Most teams glue together scripts, CI pipelines, and custom tooling — with no audit trail and no governance story.

Meanwhile, the **EU AI Act** (effective 2025) requires documentation, traceability, risk classification, and human oversight for AI systems. Compliance can't be an afterthought bolted onto spreadsheets.

Model Platform solves both: **one platform for deployment and governance**.

## Key Features

- **One-click deployment** — Push any MLflow model to Kubernetes with a single action. Auto-provisioned namespace, service, and ingress.
- **EU AI Act compliance cards** — Auto-generated regulatory documentation per model: risk classification, Article 11 technical docs, traceability records.
- **AI-assisted compliance review** — Claude analyzes your model card and generates AI Act compliance assessments.
- **Per-project namespace isolation & RBAC** — Each project gets its own Kubernetes namespace with role-based access control.
- **Governance audit export** — One-click ZIP export of all compliance artifacts for regulatory review.
- **Automatic monitoring dashboards** — Grafana dashboards auto-provisioned per deployed model (latency, throughput, errors).
- **Full-text search across model metadata** — Search across all model cards, descriptions, and metadata from a single search bar.

## Screenshots

### Projects Overview
![Projects Overview](docs/images/projects-overview.png)
*Multi-project platform with governance scope visible at a glance — project cards show owner, deployed models, and MLflow status.*

### EU AI Act Governance
![EU AI Act Governance](docs/images/governance-ai-act.png)
*Auto-generated EU AI Act compliance cards with risk classification, Article 11 documentation, and traceability — the unique differentiator.*

### Model Deployment
![Model Search](docs/images/model-deployment.png)
*Deploy and monitor model in one click*

## Architecture

```mermaid
graph LR
    User([User / CLI]) --> Frontend[Frontend<br/>HTML/CSS/JS]
    User --> CLI[CLI<br/>Typer]
    Frontend --> NGINX[NGINX<br/>Reverse Proxy]
    CLI --> Backend
    NGINX --> Backend[Backend<br/>FastAPI]
    Backend --> MLflow[(MLflow<br/>Model Registry)]
    Backend --> PostgreSQL[(PostgreSQL<br/>Metadata)]
    Backend --> MinIO[(MinIO<br/>S3 Artifacts)]
    Backend --> K8s[Kubernetes<br/>Model Serving]
    Backend --> Grafana[Grafana<br/>Monitoring]
    Backend --> Claude[Claude AI<br/>Compliance Review]

    style Frontend fill:#00A3BE,color:#fff
    style Backend fill:#0E2356,color:#fff
    style NGINX fill:#009639,color:#fff
    style MLflow fill:#0194E2,color:#fff
    style PostgreSQL fill:#336791,color:#fff
    style MinIO fill:#C72C48,color:#fff
    style K8s fill:#326CE5,color:#fff
    style Grafana fill:#F46800,color:#fff
    style Claude fill:#D97706,color:#fff
```

## Quick Start

See **[HOWTO.md](HOWTO.md)** for full setup instructions (Minikube, Helm, secrets, deployment).

```bash
# TL;DR
brew install minikube kubectl helm
minikube start --cpus 2 --memory 7800 --disk-size 50g
make k8s-infra
make create-backend-secret POSTGRES_PWD=... JWT_SECRET=... ADMIN_EMAIL=... ADMIN_PWD=...
make k8s-modelplatform
# → http://model-platform.com
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | **FastAPI** (Python, Clean Architecture) |
| Frontend | **HTML/CSS/JS** (served by NGINX) |
| CLI | **Typer** (`mp` command) |
| Model Registry | **MLflow** |
| Database | **PostgreSQL** |
| Object Storage | **MinIO** (S3-compatible) |
| Orchestration | **Kubernetes** (Minikube for dev) |
| Monitoring | **Grafana / Prometheus** |
| AI Compliance | **Claude** (Anthropic) |

## Documentation

- [HOWTO.md](HOWTO.md) — Setup & deployment guide
- [CONTRIBUTING.md](CONTRIBUTING.md) — Contribution guidelines
- [docs/](docs/) — Architecture decisions, model card templates, and more

---

<p align="center">
  <img src="frontend/assets/octo_logo.png" alt="OCTO Technology" height="40" />
  <br/>
  Built by <strong>OCTO Technology</strong>
</p>
