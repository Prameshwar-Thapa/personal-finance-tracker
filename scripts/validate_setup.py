#!/usr/bin/env python3
"""
Setup Validation Script for Personal Finance Tracker

This script validates that the Flask application is properly configured
and can find all required templates and static files. It performs:
- Template folder validation
- Static file verification  
- Flask configuration checks
- Development environment validation

Usage:
    python validate_setup.py

This is useful for:
- Deployment verification
- Troubleshooting template issues
- Confirming proper file structure
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def test_templates():
    """Test if Flask can find all required templates"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Testing Flask Template Configuration...")
        print(f"Template folder: {app.template_folder}")
        print(f"Static folder: {app.static_folder}")
        
        # Check if template folder exists
        if os.path.exists(app.template_folder):
            print("✅ Template folder exists")
            
            # List all templates
            templates = os.listdir(app.template_folder)
            print(f"📁 Found templates: {templates}")
            
            # Check required templates
            required_templates = [
                'base.html',
                'index.html', 
                'login.html',
                'register.html',
                'dashboard.html',
                'add_transaction.html',
                'transactions.html'
            ]
            
            missing_templates = []
            for template in required_templates:
                if template in templates:
                    print(f"✅ {template} - Found")
                else:
                    print(f"❌ {template} - Missing")
                    missing_templates.append(template)
            
            if not missing_templates:
                print("🎉 All required templates found!")
            else:
                print(f"⚠️  Missing templates: {missing_templates}")
                
        else:
            print(f"❌ Template folder not found: {app.template_folder}")
        
        # Check static folder
        if os.path.exists(app.static_folder):
            print("✅ Static folder exists")
            
            # Check CSS and JS files
            css_file = os.path.join(app.static_folder, 'css', 'style.css')
            js_file = os.path.join(app.static_folder, 'js', 'main.js')
            
            if os.path.exists(css_file):
                print("✅ CSS file exists")
            else:
                print("❌ CSS file missing")
                
            if os.path.exists(js_file):
                print("✅ JS file exists")
            else:
                print("❌ JS file missing")
        else:
            print(f"❌ Static folder not found: {app.static_folder}")

if __name__ == '__main__':
    test_templates()
