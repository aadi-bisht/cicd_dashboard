# CI/CD Monitoring Dashboard

A self-hosted CI/CD and observability project: a small Flask microservice app that is built, tested, and deployed automatically to Kubernetes on AWS, with the whole environment created from code and monitored through live Grafana dashboards.

> **Status:** In progress (Week 3). The roadmap below shows what is done and what is next.

## What this project does

The goal is to show the full path from a `git push` to a monitored production-style deployment:

1. Code is pushed to GitHub.
2. A Jenkins pipeline tests the code, builds Docker images, and pushes them to a registry.
3. Terraform provisions the AWS infrastructure the app runs on.
4. The pipeline deploys the new image to a Kubernetes cluster.
5. Prometheus scrapes metrics from every service, and Grafana turns them into dashboards showing app health and pipeline health.

Each stage depends on the one before it, so the project exercises the whole toolchain end to end instead of treating each tool in isolation.

## Architecture

```
Git push -> Jenkins -> Docker image -> Registry
                                          |
Terraform -> AWS (VPC, cluster) -> Kubernetes <-- deploy
                                          |
                          Flask services expose /metrics
                                          |
                               Prometheus -> Grafana
```

The container image tag (for example `api:abc123`) is the handoff between the build half and the run half: the pipeline builds and pushes it, then tells Kubernetes to run exactly that tag.

## Tech stack

| Layer | Tool |
|---|---|
| Application | Python, Flask |
| Containers | Docker |
| CI/CD | Jenkins |
| Infrastructure as Code | Terraform |
| Cloud | AWS |
| Orchestration | Kubernetes |
| Monitoring | Prometheus, Grafana |

## Services

| Service | Endpoints | Purpose |
|---|---|---|
| `api` | `GET /items`, `POST /items`, `GET /health`, `GET /metrics` | Simple item store. Exists to generate real traffic and metrics. |

- `/health` returns 200 OK and is used for Kubernetes health checks.
- `/metrics` exposes request count and latency in Prometheus format via `prometheus_client`.

## Repository structure

```
cicd-dashboard/
  monitoring/
    prometheus.yml
    dashboard.json
  services/
    api/
      Dockerfile
      app.py
      requirements.txt
    inventory/
      app.py
      requirements.txt
      Dockerfile
  docker-compose.yml
  README.md
```

More folders (`terraform/`, `k8s/`, `Jenkinsfile`) will be added as each stage is built.

## Roadmap

- [x] Flask `api` service with `/health` and `/metrics`
- [x] Dockerfile and local container run
- [x] Second Flask service
- [ ] Jenkins pipeline: test, build, push image
- [ ] Terraform: AWS networking and Kubernetes cluster
- [ ] Kubernetes manifests and automated deploy from the pipeline
- [x] Prometheus scraping the services
- [x] Grafana dashboards for app and pipeline health
- [ ] Architecture diagram and dashboard screenshots
- [ ] Stretch: Helm chart, ArgoCD, OpenTelemetry

## What I learned

![Grafana_dashboard1](monitoring/Grafana_dashboard.png)

![Grafana_dashboard2](monitoring/Grafana_dashboard_2.png)
Traffic ramps up in two stages, then drops off.
flask-inventory goes down twice, once at the left edge (off the screen) and once around 23:47 to 23:53.
During the second outage, flask-api error rate jumps from about 6% to about 50%, because every call to inventory returns a 503.
p95 latency for flask-api rises to a few seconds, which is the 2-second timeout showing up.
Both services return to normal after inventory recovers.

## Author

Kshitiz (Aadi) Bisht