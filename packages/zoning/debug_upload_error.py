#!/usr/bin/env python3
"""
Debug script to capture the exact error causing CSV upload rollback
"""
import os
import sys
import traceback
import logging

# Configure logging to capture all details
logging.basicConfig(level=logging.DEBUG)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_upload_error():
    """Debug the CSV upload error in detail"""
    print("=== CSV Upload Error Debug ===")
    
    try:
        # Initialize Flask app with full error catching
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            from app.models.user import User
            from app.models import Zone
            from app.utils.csv_processor import CSVProcessor
            from app.models.csv_import import CSVImport
            
            # Get test user
            user = User.query.first()
            if not user:
                print("❌ No user found in database")
                return
            
            print(f"✅ Using user: {user.username}")
            
            # Test with your original CSV file
            test_file = 'olej_cbe.csv'
            if not os.path.exists(test_file):
                print(f"❌ Test file {test_file} not found")
                return
            
            print(f"📁 Testing with file: {test_file}")
            
            # Create processor with detailed error logging
            processor = CSVProcessor()
            
            # Count existing records
            zones_before = Zone.query.count()
            imports_before = CSVImport.query.count()
            
            print(f"📊 Before: {zones_before} zones, {imports_before} imports")
            
            try:
                # Process with detailed exception catching
                result = processor.process_file(
                    filepath=test_file,
                    user_id=user.id,
                    csv_format='simple',
                    name_prefix='DebugTest',
                    default_zone_type='residential'
                )
                
                print("📊 Processing Result:")
                print(f"   Success: {result['success']}")
                
                if result['success']:
                    print(f"   Zones created: {result['zones_created']}")
                    print(f"   Warnings: {len(result.get('warnings', []))}")
                    for warning in result.get('warnings', []):
                        print(f"     • {warning}")
                else:
                    print(f"   Error: {result['error']}")
                    
            except Exception as e:
                print(f"❌ Exception during processing:")
                print(f"   Type: {type(e).__name__}")
                print(f"   Message: {str(e)}")
                print(f"   Traceback:")
                traceback.print_exc()
                
                # Check database state after error
                try:
                    zones_after = Zone.query.count()
                    imports_after = CSVImport.query.count()
                    print(f"📊 After error: {zones_after} zones, {imports_after} imports")
                    
                    # Check if there's a partial import record
                    latest_import = CSVImport.query.order_by(CSVImport.id.desc()).first()
                    if latest_import:
                        print(f"📋 Latest import record:")
                        print(f"   ID: {latest_import.id}")
                        print(f"   Status: {latest_import.status}")
                        print(f"   Error: {latest_import.error_log}")
                        print(f"   Warnings: {latest_import.warnings}")
                        
                except Exception as db_check_error:
                    print(f"❌ Error checking database state: {db_check_error}")
            
            # Test basic database operations
            print("\n🧪 Testing basic database operations:")
            try:
                # Test creating a simple zone manually
                from app.models.zone import Zone, ZoneTypeEnum, ZoneStatusEnum
                from shapely.geometry import Polygon, mapping
                
                # Simple test polygon
                coords = [(28.0, -15.0), (28.1, -15.0), (28.1, -15.1), (28.0, -15.1), (28.0, -15.0)]
                polygon = Polygon(coords)
                
                test_zone = Zone(
                    name='DebugTestZone',
                    code='DEBUG_001',
                    zone_type=ZoneTypeEnum.RESIDENTIAL,
                    status=ZoneStatusEnum.DRAFT,
                    geometry=mapping(polygon),
                    area_sqm=1000.0,
                    perimeter_m=400.0,
                    centroid=mapping(polygon.centroid),
                    created_by=user.id
                )
                
                db.session.add(test_zone)
                db.session.commit()
                print("✅ Basic zone creation works")
                
                # Clean up
                db.session.delete(test_zone)
                db.session.commit()
                print("✅ Zone deletion works")
                
            except Exception as basic_error:
                print(f"❌ Basic database operations failed:")
                print(f"   Type: {type(basic_error).__name__}")
                print(f"   Message: {str(basic_error)}")
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_upload_error() 