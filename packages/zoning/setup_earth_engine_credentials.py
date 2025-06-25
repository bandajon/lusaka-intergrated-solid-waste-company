#!/usr/bin/env python3
"""
Setup script for Google Earth Engine service account credentials
"""
import os
import json
import sys

def setup_earth_engine_credentials():
    """Interactive setup for Earth Engine service account credentials"""
    print("🛠️  Google Earth Engine Service Account Setup")
    print("=" * 50)
    print()
    
    print("This script will help you set up your Google Earth Engine service account credentials.")
    print("You'll need the JSON credentials file downloaded from Google Cloud Console.")
    print()
    
    # Check if credentials already exist
    config_dir = os.path.join(os.path.dirname(__file__), 'config')
    credentials_path = os.path.join(config_dir, 'earth-engine-service-account.json')
    
    if os.path.exists(credentials_path):
        print(f"📁 Existing credentials found at: {credentials_path}")
        overwrite = input("Do you want to overwrite them? (y/N): ").lower().strip()
        if overwrite != 'y':
            print("Setup cancelled.")
            return False
    
    print()
    print("Please choose an option:")
    print("1. Paste the JSON credentials directly")
    print("2. Provide the path to your credentials file")
    print("3. Cancel")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == '1':
        # Direct JSON input
        print()
        print("Please paste your service account JSON credentials below.")
        print("(The JSON should start with { and end with })")
        print("Press Enter twice when done:")
        print()
        
        lines = []
        empty_line_count = 0
        
        while True:
            line = input()
            if not line.strip():
                empty_line_count += 1
                if empty_line_count >= 2:
                    break
            else:
                empty_line_count = 0
                lines.append(line)
        
        json_content = '\n'.join(lines)
        
        try:
            # Validate JSON
            credentials = json.loads(json_content)
            
            # Validate required fields
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in credentials]
            
            if missing_fields:
                print(f"❌ Invalid credentials: Missing fields: {', '.join(missing_fields)}")
                return False
            
            if credentials['type'] != 'service_account':
                print("❌ Invalid credentials: Not a service account")
                return False
            
            # Save credentials
            os.makedirs(config_dir, exist_ok=True)
            with open(credentials_path, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            print(f"✅ Credentials saved to: {credentials_path}")
            print(f"📧 Service account: {credentials['client_email']}")
            print(f"🏗️  Project ID: {credentials['project_id']}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format: {str(e)}")
            return False
    
    elif choice == '2':
        # File path input
        print()
        file_path = input("Enter the path to your credentials JSON file: ").strip()
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r') as f:
                credentials = json.load(f)
            
            # Validate required fields
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in credentials]
            
            if missing_fields:
                print(f"❌ Invalid credentials: Missing fields: {', '.join(missing_fields)}")
                return False
            
            if credentials['type'] != 'service_account':
                print("❌ Invalid credentials: Not a service account")
                return False
            
            # Copy to config directory
            os.makedirs(config_dir, exist_ok=True)
            with open(credentials_path, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            print(f"✅ Credentials copied to: {credentials_path}")
            print(f"📧 Service account: {credentials['client_email']}")
            print(f"🏗️  Project ID: {credentials['project_id']}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Error reading file: {str(e)}")
            return False
    
    elif choice == '3':
        print("Setup cancelled.")
        return False
    
    else:
        print("❌ Invalid choice.")
        return False

def test_credentials():
    """Test the configured credentials"""
    print()
    print("🧪 Testing Earth Engine authentication...")
    
    try:
        # Import here to avoid issues if earthengine is not installed
        import ee
        from config.config import Config
        from app.utils.earth_engine_analysis import EarthEngineAnalyzer
        
        # Test authentication
        analyzer = EarthEngineAnalyzer()
        auth_status = analyzer.get_auth_status()
        
        if auth_status['initialized']:
            print("✅ Earth Engine authentication successful!")
            
            # Test a simple operation
            try:
                dataset = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').first()
                info = dataset.getInfo()
                print("✅ Earth Engine API access confirmed!")
                return True
            except Exception as e:
                print(f"⚠️  Earth Engine API test failed: {str(e)}")
                return False
        else:
            print(f"❌ Earth Engine authentication failed: {auth_status['error_details']}")
            return False
    
    except ImportError as e:
        print(f"❌ Missing dependencies: {str(e)}")
        print("Please install the required packages: pip install earthengine-api")
        return False
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print()
    success = setup_earth_engine_credentials()
    
    if success:
        print()
        if input("Do you want to test the credentials now? (Y/n): ").lower().strip() != 'n':
            test_success = test_credentials()
            if test_success:
                print()
                print("🎉 Earth Engine setup completed successfully!")
                print("Your zone analytics will now use real satellite data.")
            else:
                print()
                print("⚠️  Setup completed but testing failed.")
                print("The system will use enhanced estimates mode until the issue is resolved.")
        else:
            print()
            print("✅ Credentials saved. You can test them later using:")
            print("python test_earth_engine_service_account.py")
    else:
        print()
        print("❌ Setup failed. The system will continue using enhanced estimates mode.")
    
    print()
    print("For more information, see: https://developers.google.com/earth-engine/guides/service_account")