#!/usr/bin/env python3
"""
Test script to verify zone deletion functionality
"""

import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import create_app

def test_delete_ajax_endpoint():
    """Test the AJAX delete endpoint directly"""
    print("🧪 Testing Zone Deletion AJAX Endpoint")
    print("=" * 50)
    
    app = create_app()
    
    with app.test_client() as client:
        # First, let's test without authentication (should get 302 redirect)
        print("1. Testing without authentication...")
        response = client.post('/zones/1/delete-ajax')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.data.decode()[:100]}...")
        
        # Check if the route exists
        print("\n2. Checking available routes...")
        with app.app_context():
            rules = []
            for rule in app.url_map.iter_rules():
                if 'delete' in str(rule) or 'zones' in str(rule):
                    rules.append(str(rule))
            
            print("   Zone-related routes:")
            for rule in sorted(rules):
                print(f"     {rule}")
        
        return response.status_code

def check_javascript_function():
    """Check if the JavaScript function exists in the HTML template"""
    print("\n🧪 Checking JavaScript Function in Template")
    print("=" * 50)
    
    try:
        with open('app/templates/zones/list.html', 'r') as f:
            content = f.read()
        
        # Check for the confirmDelete function
        if 'function confirmDelete' in content:
            print("✅ confirmDelete function found in template")
            
            # Extract the function
            start = content.find('function confirmDelete')
            end = content.find('</script>', start)
            if start != -1 and end != -1:
                function_code = content[start:end]
                print(f"   Function length: {len(function_code)} characters")
                
                # Check for key elements
                checks = [
                    ('First warning', '⚠️ WARNING' in function_code),
                    ('Second warning', '🚨 FINAL WARNING' in function_code),
                    ('Name verification', 'type the exact zone name' in function_code),
                    ('AJAX call', 'fetch(' in function_code),
                    ('Delete endpoint', '/delete-ajax' in function_code),
                ]
                
                print("   Function checks:")
                for check_name, passed in checks:
                    status = "✅" if passed else "❌"
                    print(f"     {status} {check_name}")
                
                all_passed = all(passed for _, passed in checks)
                if all_passed:
                    print("✅ JavaScript function appears complete")
                else:
                    print("❌ JavaScript function missing some elements")
                    
                return all_passed
            else:
                print("❌ Could not extract function code")
                return False
        else:
            print("❌ confirmDelete function not found in template")
            return False
            
    except FileNotFoundError:
        print("❌ Template file not found")
        return False
    except Exception as e:
        print(f"❌ Error checking template: {e}")
        return False

def check_button_onclick():
    """Check if the button onclick attribute is correct"""
    print("\n🧪 Checking Button onclick Attribute")
    print("=" * 50)
    
    try:
        with open('app/templates/zones/list.html', 'r') as f:
            content = f.read()
        
        # Look for the delete button
        if 'onclick="confirmDelete(' in content:
            print("✅ Delete button with onclick found")
            
            # Check if the button has proper zone ID parameter
            if '{{ zone.id }}' in content:
                print("✅ Zone ID parameter found in onclick")
                return True
            else:
                print("❌ Zone ID parameter missing from onclick")
                return False
        else:
            print("❌ Delete button onclick not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking button: {e}")
        return False

if __name__ == "__main__":
    print("🔍 ZONE DELETION FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Test 1: Backend endpoint
    backend_status = test_delete_ajax_endpoint()
    
    # Test 2: JavaScript function
    js_function_ok = check_javascript_function()
    
    # Test 3: Button onclick
    button_ok = check_button_onclick()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    print(f"Backend endpoint accessible: {backend_status != 404}")
    print(f"JavaScript function complete: {js_function_ok}")
    print(f"Button onclick correct: {button_ok}")
    
    if backend_status != 404 and js_function_ok and button_ok:
        print("\n✅ Deletion functionality appears properly configured")
        print("\n💡 If clicking still doesn't work, check browser console for:")
        print("   • JavaScript errors")
        print("   • Network request failures")
        print("   • Authentication issues")
        print("   • CSRF token problems")
    else:
        print("\n❌ Issues found with deletion functionality")
        
        if backend_status == 404:
            print("   🔧 Fix: Backend route missing or incorrect")
        if not js_function_ok:
            print("   🔧 Fix: JavaScript function incomplete")
        if not button_ok:
            print("   🔧 Fix: Button onclick attribute incorrect")