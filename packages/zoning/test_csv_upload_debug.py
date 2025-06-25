#!/usr/bin/env python3
"""
Debug CSV upload functionality
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_csv_upload_components():
    """Test CSV upload components to see what might be broken"""
    print("🔍 TESTING CSV UPLOAD COMPONENTS")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test 1: Check if CSVProcessor can be imported
        print("🔧 Test 1: CSVProcessor Import")
        print("-" * 30)
        try:
            from app.utils.csv_processor import CSVProcessor
            print("✅ CSVProcessor import successful")
        except Exception as e:
            print(f"❌ CSVProcessor import failed: {str(e)}")
            return False
        
        # Test 2: Check if CSVUploadForm can be imported
        print("\\n🔧 Test 2: CSVUploadForm Import")
        print("-" * 30)
        try:
            from app.forms.zone import CSVUploadForm
            print("✅ CSVUploadForm import successful")
        except Exception as e:
            print(f"❌ CSVUploadForm import failed: {str(e)}")
            return False
        
        # Test 3: Check database models
        print("\\n🔧 Test 3: Database Models")
        print("-" * 30)
        try:
            from app.models import Zone, CSVImport, ZoneTypeEnum, ImportStatusEnum
            print("✅ Database models import successful")
        except Exception as e:
            print(f"❌ Database models import failed: {str(e)}")
            return False
        
        # Test 4: Check Flask app context 
        print("\\n🔧 Test 4: Flask App Context")
        print("-" * 30)
        try:
            from app import create_app, db
            app = create_app()
            with app.app_context():
                print("✅ Flask app context created successfully")
                print(f"   Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')}")
                
                # Check if CSV temp folder is configured
                csv_temp = app.config.get('CSV_TEMP_FOLDER', 'Not configured')
                print(f"   CSV temp folder: {csv_temp}")
                
                if csv_temp != 'Not configured' and os.path.exists(csv_temp):
                    print(f"   ✅ CSV temp folder exists")
                elif csv_temp != 'Not configured':
                    print(f"   ⚠️  CSV temp folder doesn't exist: {csv_temp}")
                    # Try to create it
                    try:
                        os.makedirs(csv_temp, exist_ok=True)
                        print(f"   ✅ Created CSV temp folder")
                    except Exception as e:
                        print(f"   ❌ Failed to create CSV temp folder: {str(e)}")
                
        except Exception as e:
            print(f"❌ Flask app context failed: {str(e)}")
            return False
        
        # Test 5: Check CSV processor basic functionality
        print("\\n🔧 Test 5: CSV Processor Basic Test")
        print("-" * 30)
        try:
            processor = CSVProcessor()
            print("✅ CSVProcessor instance created successfully")
            print(f"   Lusaka bounds: {processor.LUSAKA_BOUNDS}")
        except Exception as e:
            print(f"❌ CSVProcessor instance creation failed: {str(e)}")
            return False
        
        # Test 6: Check if there are any recent error logs
        print("\\n🔧 Test 6: Check Error Logs")
        print("-" * 30)
        try:
            # Check if there's a debug file
            if os.path.exists('debug_upload_error.py'):
                print("✅ Found debug_upload_error.py file")
            else:
                print("⚠️  No debug_upload_error.py file found")
                
            # Check for any upload-related files
            upload_files = [f for f in os.listdir('.') if 'upload' in f.lower() or 'csv' in f.lower()]
            if upload_files:
                print(f"📁 Found upload-related files: {upload_files}")
            else:
                print("📁 No upload-related files found")
                
        except Exception as e:
            print(f"❌ Error log check failed: {str(e)}")
        
        print("\\n✅ All components test completed successfully!")
        print("\\n💡 CSV upload should be working. Possible issues:")
        print("   - JavaScript errors on frontend")
        print("   - File permissions on upload folder")
        print("   - Form validation failures")
        print("   - Database connection issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 DEBUGGING CSV UPLOAD FUNCTIONALITY")
    print("Checking all components to identify the issue")
    print()
    
    success = test_csv_upload_components()
    
    if success:
        print("\\n🎯 NEXT STEPS:")
        print("1. Check browser console for JavaScript errors")
        print("2. Verify file upload permissions")
        print("3. Test with a small CSV file")
        print("4. Check Flask logs for any errors")
    else:
        print("\\n❌ Found issues with CSV upload components")
        print("Check the error messages above")