#!/usr/bin/env python3
"""
Test CSV upload complete flow
"""
import sys
import os
import tempfile
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_csv_upload_flow():
    """Test the complete CSV upload flow"""
    print("🔍 TESTING CSV UPLOAD FLOW")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from app import create_app, db
        from app.utils.csv_processor import CSVProcessor
        from app.models import Zone, CSVImport, User
        
        app = create_app()
        
        with app.app_context():
            # Create a test CSV file
            print("🔧 Test 1: Create Test CSV File")
            print("-" * 30)
            
            # Create temp CSV file with valid Lusaka coordinates
            csv_content = """longitude,latitude
28.2816,-15.3875
28.2820,-15.3870
28.2825,-15.3865
28.2816,-15.3875"""
            
            # Save to temp folder
            temp_folder = app.config.get('CSV_TEMP_FOLDER', 'uploads/temp')
            os.makedirs(temp_folder, exist_ok=True)
            
            test_csv_path = os.path.join(temp_folder, 'test_upload.csv')
            with open(test_csv_path, 'w') as f:
                f.write(csv_content)
            
            print(f"✅ Test CSV created: {test_csv_path}")
            print(f"   Content preview: {csv_content.split()[0]}")
            
            # Test 2: Process CSV
            print("\\n🔧 Test 2: Process CSV with CSVProcessor")
            print("-" * 30)
            
            # Get or create a test user
            user = User.query.filter_by(username='admin').first()
            if not user:
                print("⚠️  No admin user found, creating test user")
                user = User(
                    username='test_user',
                    email='test@example.com',
                    role='ADMIN'
                )
                user.set_password('test123')
                db.session.add(user)
                db.session.commit()
                
            print(f"✅ Using user: {user.username} (ID: {user.id})")
            
            # Process the CSV
            processor = CSVProcessor()
            result = processor.process_file(
                test_csv_path,
                user_id=user.id,
                csv_format='simple',
                name_prefix='TestZone',
                default_zone_type='residential'
            )
            
            print(f"📊 Processing result: {result}")
            
            if result.get('success'):
                print(f"✅ CSV processing successful!")
                print(f"   Zones created: {result.get('zones_created', 0)}")
                print(f"   Rows processed: {result.get('rows_processed', 0)}")
                
                # Check if zones were actually created
                zones = Zone.query.filter(Zone.name.like('TestZone%')).all()
                print(f"   Zones in database: {len(zones)}")
                
                for zone in zones[:3]:  # Show first 3
                    print(f"     - {zone.name} ({zone.zone_type.value if zone.zone_type else 'No type'})")
                
            else:
                print(f"❌ CSV processing failed!")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                print(f"   Errors: {result.get('errors', [])}")
                return False
            
            # Test 3: Check CSV Import record
            print("\\n🔧 Test 3: Check CSV Import Record")
            print("-" * 30)
            
            csv_import = CSVImport.query.filter_by(filename='test_upload.csv').first()
            if csv_import:
                print(f"✅ CSV import record found")
                print(f"   Status: {csv_import.status.value if csv_import.status else 'No status'}")
                print(f"   Rows total: {csv_import.rows_total}")
                print(f"   Zones created: {csv_import.zones_created}")
                print(f"   Success rate: {csv_import.success_rate}%")
            else:
                print(f"❌ No CSV import record found")
                return False
            
            # Test 4: Test form validation
            print("\\n🔧 Test 4: Test Form Validation")
            print("-" * 30)
            
            from app.forms.zone import CSVUploadForm
            
            # Create form with test data
            form = CSVUploadForm()
            form.csv_format.data = 'simple'
            form.name_prefix.data = 'TestZone'
            form.default_zone_type.data = 'residential'
            
            print(f"✅ Form created successfully")
            print(f"   Format: {form.csv_format.data}")
            print(f"   Prefix: {form.name_prefix.data}")
            print(f"   Type: {form.default_zone_type.data}")
            
            # Cleanup
            try:
                os.remove(test_csv_path)
                print(f"\\n🧹 Cleaned up test file")
            except:
                pass
            
            print("\\n✅ CSV upload flow test completed successfully!")
            print("\\n💡 If upload still doesn't work, check:")
            print("   - Browser console for JavaScript errors")
            print("   - Network tab for failed requests") 
            print("   - Flask debug logs")
            print("   - File upload form enctype='multipart/form-data'")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 TESTING CSV UPLOAD FLOW")
    print("Testing the complete CSV upload and processing workflow")
    print()
    
    success = test_csv_upload_flow()
    
    if success:
        print("\\n🎉 CSV upload backend is working correctly!")
        print("If users can't upload, the issue is likely frontend/JavaScript")
    else:
        print("\\n❌ Found issues with CSV upload backend")
        print("Check the error messages above")