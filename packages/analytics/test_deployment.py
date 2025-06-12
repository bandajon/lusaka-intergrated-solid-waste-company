#!/usr/bin/env python3
"""
Test deployment readiness for LISWMC Analytics Dashboard
"""

import os
import sys
import subprocess

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ Missing {description}: {filepath}")
        return False

def check_requirements():
    """Check if requirements.txt has all needed packages"""
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
            required_packages = ['pandas', 'dash', 'plotly', 'sqlalchemy', 'psycopg2-binary', 'gunicorn']
            
            missing = []
            for package in required_packages:
                if package not in content:
                    missing.append(package)
            
            if not missing:
                print("✅ Requirements.txt contains all necessary packages")
                return True
            else:
                print(f"❌ Missing packages in requirements.txt: {missing}")
                return False
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False

def test_import():
    """Test if the dashboard can be imported"""
    try:
        # Set environment variables for testing
        os.environ['DEBUG'] = 'false'
        os.environ['PORT'] = '8050'
        
        # Try importing
        from db_dashboard import app
        # Get server object
        server = app.server
        print("✅ Dashboard imports successfully")
        print("✅ WSGI server object available")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def check_deployment_readiness():
    """Main deployment readiness check"""
    print("🚀 LISWMC Analytics Dashboard - Deployment Readiness Check\n")
    
    checks = []
    
    # File checks
    checks.append(check_file_exists('db_dashboard.py', 'Main dashboard file'))
    checks.append(check_file_exists('database_connection.py', 'Database connection module'))
    checks.append(check_file_exists('requirements.txt', 'Requirements file'))
    checks.append(check_file_exists('wsgi.py', 'WSGI entry point'))
    checks.append(check_file_exists('render.yaml', 'Render deployment config'))
    checks.append(check_file_exists('Dockerfile', 'Docker configuration'))
    checks.append(check_file_exists('DEPLOYMENT.md', 'Deployment guide'))
    
    # Content checks
    checks.append(check_requirements())
    checks.append(test_import())
    
    # Summary
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n📊 Deployment Readiness: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 READY FOR DEPLOYMENT!")
        print("\n📋 Next Steps:")
        print("1. Push code to GitHub repository")
        print("2. Create account on render.com")
        print("3. Connect GitHub repo to Render")
        print("4. Set environment variables in Render dashboard")
        print("5. Deploy!")
        print("\nSee DEPLOYMENT.md for detailed instructions")
    else:
        print(f"\n⚠️  Please fix {total - passed} issues before deploying")
    
    return passed == total

if __name__ == "__main__":
    success = check_deployment_readiness()
    sys.exit(0 if success else 1)