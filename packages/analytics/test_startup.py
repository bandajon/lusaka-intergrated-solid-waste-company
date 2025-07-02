#!/usr/bin/env python3
"""
Startup Test Script
------------------
Quick test to verify all startup methods work correctly.
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def test_flask_import():
    """Test if Flask app can be imported without errors"""
    print("🧪 Testing Flask app imports...")
    
    try:
        # Test the main flask_app import
        from flask_app import create_app
        app = create_app()
        print("   ✅ flask_app.create_app() works")
        
        # Test company unifier import
        from flask_app.utils.company_unifier import CompanyUnifier
        unifier = CompanyUnifier()
        print("   ✅ CompanyUnifier import works")
        
        # Test config import
        from config import AnalyticsConfig
        print(f"   ✅ Config loaded - Flask port: {AnalyticsConfig.FLASK_PORT}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False

def test_app_py_import():
    """Test if app.py can be imported (used by start_both.sh)"""
    print("🧪 Testing app.py imports...")
    
    try:
        import app
        print("   ✅ app.py imports successfully")
        return True
    except Exception as e:
        print(f"   ❌ app.py import error: {e}")
        return False

def test_port_availability():
    """Test if required ports are available"""
    print("🧪 Testing port availability...")
    
    from config import AnalyticsConfig
    
    ports_to_test = [
        (AnalyticsConfig.FLASK_PORT, "Flask"),
        (AnalyticsConfig.DASH_PORT, "Dash")
    ]
    
    available_ports = []
    
    for port, service in ports_to_test:
        try:
            # Try to connect to see if something is already running
            response = requests.get(f"http://localhost:{port}", timeout=2)
            print(f"   ⚠️  Port {port} ({service}) is in use - service already running")
        except requests.exceptions.RequestException:
            print(f"   ✅ Port {port} ({service}) is available")
            available_ports.append(port)
    
    return available_ports

def test_startup_script():
    """Test the unified startup script"""
    print("🧪 Testing startup script...")
    
    try:
        # Test help output
        result = subprocess.run([sys.executable, 'start_analytics.py'], 
                              capture_output=True, text=True, timeout=10)
        
        if "LISWMC Analytics Services" in result.stdout:
            print("   ✅ Startup script help works")
            return True
        else:
            print(f"   ❌ Unexpected startup script output: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"   ❌ Startup script error: {e}")
        return False

def test_company_unification():
    """Test company unification functionality"""
    print("🧪 Testing company unification...")
    
    try:
        result = subprocess.run([sys.executable, 'test_company_unifier.py'], 
                              capture_output=True, text=True, timeout=30)
        
        if "All tests completed successfully" in result.stdout:
            print("   ✅ Company unification tests pass")
            return True
        else:
            print(f"   ❌ Company unification test failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Company unification test error: {e}")
        return False

def main():
    """Run all startup tests"""
    print("🚀 LISWMC Analytics Startup Test Suite")
    print("=" * 50)
    
    tests = [
        ("Flask App Imports", test_flask_import),
        ("app.py Imports", test_app_py_import),
        ("Port Availability", test_port_availability),
        ("Startup Script", test_startup_script),
        ("Company Unification", test_company_unification),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🏁 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your analytics setup is ready to use.")
        print("\n💡 Quick Start:")
        print("   python start_analytics.py --flask    # Start data management")
        print("   python start_analytics.py --dashboard # Start analytics")
        print("   python start_analytics.py --both     # Start both")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)