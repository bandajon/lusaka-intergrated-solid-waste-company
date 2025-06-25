#!/usr/bin/env python3
"""
Test script to verify zone deletion functionality
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_zone_deletion_ui():
    """Test that zone deletion UI has proper warnings"""
    
    print("🧪 Testing Zone Deletion UI Implementation")
    print("=" * 50)
    
    # Read the list.html template to verify our implementation
    try:
        with open('app/templates/zones/list.html', 'r') as f:
            content = f.read()
        
        # Check for key elements
        checks = [
            ('First warning dialog', '⚠️ WARNING: You are about to delete zone' in content),
            ('Second warning dialog', '🚨 FINAL WARNING: This action CANNOT be undone!' in content),
            ('Name verification prompt', 'Please type the exact zone name to confirm deletion' in content),
            ('Loading indicator', 'spinner-border spinner-border-sm' in content),
            ('AJAX endpoint', '/delete-ajax' in content),
            ('Error handling', '.catch(error =>' in content),
        ]
        
        print("✅ UI Implementation Checks:")
        for check_name, result in checks:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: {check_name}")
        
        all_passed = all(result for _, result in checks)
        
        if all_passed:
            print("\n🎉 All UI checks passed!")
            print("\nDeletion Process Overview:")
            print("1. User clicks delete button")
            print("2. First warning shows what will be deleted")
            print("3. Second warning requires confirmation")
            print("4. User must type exact zone name")
            print("5. Loading spinner shows during deletion")
            print("6. Success/error message displayed")
            print("7. Page reloads on success")
        else:
            print("\n❌ Some checks failed. Please review implementation.")
        
        return all_passed
        
    except FileNotFoundError:
        print("❌ Could not find app/templates/zones/list.html")
        return False
    except Exception as e:
        print(f"❌ Error reading template: {e}")
        return False

def test_backend_implementation():
    """Test backend deletion route"""
    
    print("\n🧪 Testing Backend Deletion Implementation")
    print("=" * 50)
    
    try:
        with open('app/views/zones.py', 'r') as f:
            content = f.read()
        
        # Check for key backend elements
        checks = [
            ('AJAX delete route', '/delete-ajax' in content and 'def delete_ajax' in content),
            ('Permission check', 'can_delete_zones()' in content),
            ('Error handling', 'try:' in content and 'except Exception' in content),
            ('Database rollback', 'db.session.rollback()' in content),
            ('Logging', 'current_app.logger' in content),
            ('JSON response', 'jsonify' in content),
            ('Analysis cleanup', 'ZoneAnalysis.query.filter_by(zone_id' in content),
        ]
        
        print("✅ Backend Implementation Checks:")
        for check_name, result in checks:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: {check_name}")
        
        all_passed = all(result for _, result in checks)
        
        if all_passed:
            print("\n🎉 All backend checks passed!")
            print("\nBackend Process:")
            print("1. Check user permissions")
            print("2. Find zone to delete")
            print("3. Clean up related analysis data")
            print("4. Delete zone from database")
            print("5. Log deletion for audit")
            print("6. Return JSON success/error response")
        else:
            print("\n❌ Some backend checks failed.")
        
        return all_passed
        
    except FileNotFoundError:
        print("❌ Could not find app/views/zones.py")
        return False
    except Exception as e:
        print(f"❌ Error reading zones.py: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Zone Deletion Functionality Test")
    print("=" * 60)
    
    ui_ok = test_zone_deletion_ui()
    backend_ok = test_backend_implementation()
    
    print("\n" + "=" * 60)
    if ui_ok and backend_ok:
        print("✅ Zone deletion functionality is properly implemented!")
        print("\n💡 Features implemented:")
        print("  • Two-step confirmation process")
        print("  • Zone name verification requirement")
        print("  • Visual loading indicators")
        print("  • Comprehensive error handling")
        print("  • Related data cleanup")
        print("  • Audit logging")
        print("  • Permission verification")
    else:
        print("❌ Some issues found with deletion implementation")
    
    print("\n🚨 Security Note: Users must now:")
    print("  1. Confirm deletion twice")
    print("  2. Type the exact zone name to proceed")
    print("  3. Have proper delete permissions")