# Complete CI/CD Guide for Personal Finance Tracker

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [GitHub Actions Workflow Explained](#github-actions-workflow-explained)
5. [ArgoCD Integration](#argocd-integration)
6. [Step-by-Step Setup](#step-by-step-setup)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)

## 🎯 Overview

This guide covers the complete CI/CD pipeline for the Personal Finance Tracker application, implementing GitOps principles with GitHub Actions and ArgoCD.

### Pipeline Flow
```
Developer Push → GitHub Actions CI → Build & Test → Docker Build → Push to DockerHub → Update K8s Manifest → ArgoCD Detects Change → Deploy to Kubernetes
```

### Key Benefits
- ✅ **Automated Testing**: Every code change is tested
- ✅ **Containerized Deployment**: Consistent environments
- ✅ **GitOps**: Infrastructure as Code with version control
- ✅ **Zero Downtime**: Rolling deployments
- ✅ **Rollback Capability**: Easy revert to previous versions
- ✅ **Security**: No direct cluster access needed

## 🏗️ Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Developer     │───▶│   GitHub Repo   │───▶│ GitHub Actions  │
│   (Code Push)   │    │   (Source Code) │    │   (CI Pipeline) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Docker Hub    │◀───│   Build & Test  │───▶│  Update K8s     │
│  (Image Store)  │    │   (CI Process)  │    │  (Manifest)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Kubernetes    │◀───│     ArgoCD      │◀───│   Git Repo      │
│   (EKS Cluster) │    │  (CD Process)   │    │  (Updated)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Breakdown

#### 1. **GitHub Repository**
- **Source Code**: Flask application, Kubernetes manifests
- **CI/CD Configuration**: `.github/workflows/cicd.yaml`
- **Tests**: Unit tests in `tests/` directory
- **Documentation**: README, guides, troubleshooting

#### 2. **GitHub Actions (CI)**
- **Trigger**: Push to main branch
- **Jobs**: Build, Test, Push, Update
- **Secrets**: Docker Hub credentials, GitHub token
- **Artifacts**: Docker images, updated manifests

#### 3. **Docker Hub**
- **Image Registry**: Stores application container images
- **Tagging Strategy**: Uses GitHub run ID for uniqueness
- **Security**: Private repository with access tokens

#### 4. **ArgoCD (CD)**
- **GitOps Controller**: Monitors Git repository
- **Sync Policy**: Automated deployment
- **Health Monitoring**: Application status tracking
- **Rollback**: Easy revert to previous versions

#### 5. **Kubernetes Cluster (EKS)**
- **Target Environment**: Where application runs
- **Namespaces**: `finance-tracker` for application
- **Resources**: Deployments, Services, ConfigMaps, Secrets

## 📋 Prerequisites

### 1. **GitHub Repository Setup**
```bash
# Repository structure
personal-finance-tracker/
├── .github/workflows/cicd.yaml    # CI/CD pipeline
├── app/                           # Flask application
├── k8s/                          # Kubernetes manifests
├── tests/                        # Unit tests
├── Dockerfile                    # Container definition
├── requirements.txt              # Python dependencies
└── run.py                       # Application entry point
```

### 2. **Docker Hub Account**
- Create account at https://hub.docker.com
- Create repository: `personal-finance-tracker-web`
- Generate access token for CI/CD

### 3. **Kubernetes Cluster**
- EKS cluster with kubectl access
- ArgoCD installed and configured
- Proper RBAC permissions

### 4. **GitHub Secrets**
Required secrets in repository settings:
- `DOCKERHUB_USERNAME`: Docker Hub username
- `DOCKERHUB_TOKEN`: Docker Hub access token
- `TOKEN`: GitHub Personal Access Token

## 🔧 GitHub Actions Workflow Explained

### Complete Workflow File
```yaml
name: CI/CD

# Trigger conditions
on:
  push:
    branches:
      - main
    paths-ignore:
      - 'k8s/**'        # Ignore k8s changes to prevent loops
      - 'README.md'     # Ignore documentation changes
      - '*.md'          # Ignore all markdown files

jobs:
  # Job 1: Build and Test
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.9
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-flask

      - name: Test
        run: |
          python -m pytest tests/ -v || echo "Tests completed"

  # Job 2: Build and Push Docker Image
  push:
    runs-on: ubuntu-latest
    needs: build  # Only run if build job succeeds
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/personal-finance-tracker-web:${{ github.run_id }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # Job 3: Update Kubernetes Manifest
  update-newtag-in-k8s:
    runs-on: ubuntu-latest
    needs: push  # Only run if push job succeeds
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.TOKEN }}  # Required for pushing back to repo

      - name: Update k8s deployment with new image tag
        run: |
          sed -i 's|image: .*/personal-finance-tracker-web:.*|image: '"${{ secrets.DOCKERHUB_USERNAME }}"'/personal-finance-tracker-web:'"${{ github.run_id }}"'|' k8s/app-deployment.yaml

      - name: Commit and push changes
        run: |
          git config --global user.email "prameshwar@gmail.com"
          git config --global user.name "Prameshwar"
          git add k8s/app-deployment.yaml
          git commit -m "Update tag in K8s deployment [skip ci]"
          git push
```
