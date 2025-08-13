# CI/CD Setup for Personal Finance Tracker

## 🚀 Overview

This project uses GitHub Actions for CI/CD with ArgoCD for GitOps deployment to Kubernetes.

## 📋 Pipeline Flow

```
Code Push → GitHub Actions → Build & Test → Docker Build → Push to DockerHub → Update K8s Manifest → ArgoCD Deploys
```

## 🔧 Setup Requirements

### 1. GitHub Secrets

Add these secrets in your GitHub repository (Settings → Secrets and variables → Actions):

- **`DOCKERHUB_USERNAME`** - Your Docker Hub username (e.g., `prameshwar884`)
- **`DOCKERHUB_TOKEN`** - Your Docker Hub access token
- **`TOKEN`** - GitHub Personal Access Token with repo permissions

### 2. ArgoCD Application

Ensure your ArgoCD application is configured with:
- **Repository**: `https://github.com/your-username/personal-finance-tracker`
- **Path**: `k8s`
- **Auto-sync**: Enabled

## 🎯 How It Works

### CI (Continuous Integration)
1. **Trigger**: Push to main branch (ignores k8s/ changes)
2. **Build Job**:
   - Sets up Python 3.9
   - Installs dependencies
   - Runs pytest tests
3. **Push Job**:
   - Builds Docker image
   - Pushes to Docker Hub with GitHub run ID as tag

### CD (Continuous Deployment)
1. **Update Job**:
   - Updates `k8s/app-deployment.yaml` with new image tag
   - Commits and pushes changes back to repo
2. **ArgoCD**:
   - Detects manifest changes
   - Automatically deploys to Kubernetes

## 📁 Project Structure

```
personal-finance-tracker/
├── .github/workflows/cicd.yaml    # CI/CD pipeline
├── tests/                         # Unit tests
│   ├── __init__.py
│   └── test_app.py
├── k8s/                          # Kubernetes manifests
│   └── app-deployment.yaml       # Updated by CI/CD
├── app/                          # Flask application
├── Dockerfile                    # Container build
└── requirements.txt              # Python dependencies
```

## 🔍 Testing

Run tests locally:
```bash
pip install pytest pytest-flask
python -m pytest tests/ -v
```

## 🐳 Docker

Build locally:
```bash
docker build -t personal-finance-tracker-web .
docker run -p 5000:5000 personal-finance-tracker-web
```

## 📊 Monitoring

- **GitHub Actions**: Check workflow status in Actions tab
- **Docker Hub**: Verify new images are pushed
- **ArgoCD**: Monitor deployment status in ArgoCD UI
- **Kubernetes**: Check pod status with `kubectl get pods -n finance-tracker`

## 🛠️ Troubleshooting

### Common Issues

1. **Tests Fail**: Check test output in GitHub Actions logs
2. **Docker Build Fails**: Verify Dockerfile and dependencies
3. **Push Fails**: Check Docker Hub credentials
4. **ArgoCD Not Syncing**: Verify repository access and auto-sync settings

### Verification Script

Run the verification script to check setup:
```bash
python3 verify_setup.py
```

## 🎉 Success Indicators

✅ GitHub Actions workflow completes successfully  
✅ New Docker image appears in Docker Hub  
✅ K8s deployment file is updated with new tag  
✅ ArgoCD shows "Synced" status  
✅ Application pods restart with new image  

## 📝 Notes

- Pipeline ignores changes to `k8s/` directory to prevent infinite loops
- Uses `[skip ci]` in commit messages to prevent triggering CI on deployment updates
- Health endpoint at `/health` is used for Kubernetes probes
- Docker images are tagged with GitHub run ID for uniqueness
