#!/usr/bin/env python3
"""
Verification script to check if all CI/CD components are in place
"""
import os
import sys

def check_file_exists(filepath, description):
    """Check if a file exists and print status"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists and print status"""
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        print(f"✅ {description}: {dirpath}")
        return True
    else:
        print(f"❌ {description}: {dirpath} - NOT FOUND")
        return False

def main():
    print("🔍 Verifying CI/CD Setup for Personal Finance Tracker")
    print("=" * 60)
    
    all_good = True
    
    # Check essential files
    files_to_check = [
        (".github/workflows/cicd.yaml", "GitHub Actions Workflow"),
        ("Dockerfile", "Docker Configuration"),
        ("requirements.txt", "Python Dependencies"),
        ("run.py", "Flask Application Entry Point"),
        ("k8s/app-deployment.yaml", "Kubernetes Deployment"),
        ("tests/__init__.py", "Tests Package Init"),
        ("tests/test_app.py", "Basic Tests"),
        ("app/__init__.py", "Flask App Init"),
        ("app/routes.py", "Flask Routes"),
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_good = False
    
    # Check directories
    dirs_to_check = [
        (".github/workflows", "GitHub Actions Directory"),
        ("tests", "Tests Directory"),
        ("app", "Flask App Directory"),
        ("k8s", "Kubernetes Manifests Directory"),
    ]
    
    for dirpath, description in dirs_to_check:
        if not check_directory_exists(dirpath, description):
            all_good = False
    
    print("\n" + "=" * 60)
    
    # Check specific content
    print("\n🔍 Checking File Contents:")
    
    # Check if health endpoint exists in routes
    try:
        with open("app/routes.py", "r") as f:
            content = f.read()
            if "/health" in content:
                print("✅ Health endpoint found in routes.py")
            else:
                print("❌ Health endpoint NOT found in routes.py")
                all_good = False
    except Exception as e:
        print(f"❌ Error reading routes.py: {e}")
        all_good = False
    
    # Check if Dockerfile has correct CMD
    try:
        with open("Dockerfile", "r") as f:
            content = f.read()
            if "CMD [" in content and "start.sh" in content:
                print("✅ Dockerfile CMD configuration looks good")
            else:
                print("⚠️ Dockerfile CMD might need verification")
    except Exception as e:
        print(f"❌ Error reading Dockerfile: {e}")
        all_good = False
    
    # Check if CI/CD has correct image reference
    try:
        with open(".github/workflows/cicd.yaml", "r") as f:
            content = f.read()
            if "personal-finance-tracker-web" in content:
                print("✅ CI/CD workflow has correct image name")
            else:
                print("❌ CI/CD workflow image name might be incorrect")
                all_good = False
    except Exception as e:
        print(f"❌ Error reading CI/CD workflow: {e}")
        all_good = False
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("🎉 ALL CHECKS PASSED! Your setup is ready for CI/CD")
        print("\n📋 Next Steps:")
        print("1. Add GitHub Secrets:")
        print("   - DOCKERHUB_USERNAME")
        print("   - DOCKERHUB_TOKEN")
        print("   - TOKEN (GitHub Personal Access Token)")
        print("2. Push to GitHub main branch")
        print("3. Monitor GitHub Actions workflow")
        print("4. Check ArgoCD for automatic deployment")
    else:
        print("❌ SOME ISSUES FOUND! Please fix the above issues before pushing to GitHub")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
