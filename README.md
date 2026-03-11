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

*C4 Container diagram — shows the major containers and their interactions within the Kubernetes cluster.*

```mermaid
graph TB
    User([👤 User])
    CLI([⌨️ CLI — Typer])

    User -->|model-platform.com| Ingress
    CLI -->|REST API| Ingress

    subgraph K8s["☸ Kubernetes Cluster"]

        subgraph NS_Default["default namespace"]
            Ingress[NGINX Ingress]
            Proxy[NGINX Reverse Proxy]
            Ingress --> Proxy
        end

        subgraph NS_MP["model-platform namespace"]
            Frontend["Frontend\nHTML/CSS/JS\n:80"]
            Backend["Backend\nFastAPI\n:8000"]
        end

        subgraph NS_Data["Shared Infrastructure"]
            PostgreSQL[("PostgreSQL\nMetadata & Users\n:5432")]
            MinIO[("MinIO\nS3 Artifacts\n:9000")]
        end

        subgraph NS_Monitoring["monitoring namespace"]
            Grafana["Grafana\nDashboards\n:80"]
            Prometheus["Prometheus\nMetrics\n:9090"]
        end

        subgraph NS_Project["project namespace (1 per ML project)"]
            MLflow["MLflow\nModel Registry\n:5000"]
            Model1["Model Service A\n:8000"]
            Model2["Model Service B\n:8000"]
        end

        Proxy -->|"/"| Frontend
        Proxy -->|"/api/"| Backend
        Proxy -->|"/registry/{project}/"| MLflow
        Proxy -->|"/deploy/{project}/{model}/predict"| Model1
        Proxy -->|"/grafana/"| Grafana

        Backend -->|"SQL"| PostgreSQL
        Backend -->|"K8s API"| NS_Project
        Backend -->|"HTTP"| Grafana
        MLflow -->|"S3"| MinIO
        Model1 -.->|"metrics"| Prometheus
        Model2 -.->|"metrics"| Prometheus
        Prometheus --> Grafana
    end

    Backend -->|"AI Act review"| Claude["Claude AI\nCompliance\n(external)"]

    style K8s fill:none,stroke:#326CE5,stroke-width:2px
    style NS_Default fill:#E8F5E9,stroke:#009639
    style NS_MP fill:#E3F2FD,stroke:#0E2356
    style NS_Data fill:#FFF3E0,stroke:#E65100
    style NS_Monitoring fill:#FBE9E7,stroke:#F46800
    style NS_Project fill:#E0F7FA,stroke:#00A3BE,stroke-dasharray:5
    style Frontend fill:#00A3BE,color:#fff
    style Backend fill:#0E2356,color:#fff
    style Proxy fill:#009639,color:#fff
    style Ingress fill:#009639,color:#fff
    style PostgreSQL fill:#336791,color:#fff
    style MinIO fill:#C72C48,color:#fff
    style MLflow fill:#0194E2,color:#fff
    style Grafana fill:#F46800,color:#fff
    style Prometheus fill:#E6522C,color:#fff
    style Claude fill:#D97706,color:#fff
    style Model1 fill:#00A3BE,color:#fff
    style Model2 fill:#00A3BE,color:#fff
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
