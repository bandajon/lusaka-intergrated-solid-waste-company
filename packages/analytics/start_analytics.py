#!/usr/bin/env python3
"""
LISWMC Analytics Unified Startup Script
---------------------------------------
Unified script to start various analytics components.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from config import AnalyticsConfig

def get_project_root():
    """Get the project root directory"""
    current_dir = Path(__file__).resolve().parent
    # Go up until we find the project root (contains packages/)
    while current_dir.parent != current_dir:
        if (current_dir / 'packages').exists():
            return current_dir
        current_dir = current_dir.parent
    return Path.cwd()

def start_dash_dashboard():
    """Start the Dash analytics dashboard"""
    print("🚀 Starting LISWMC Dash Analytics Dashboard...")
    print("=" * 50)
    print("📋 Dashboard Features:")
    print("   🔐 Secure login required")
    print("   📊 Real-time waste collection analytics")
    print("   📈 Interactive charts and filters")
    print("   🚛 Vehicle performance tracking")
    print("   📍 Location-based insights")
    print("   💰 Fee calculation and reporting")
    print("")
    print(f"🌐 Dashboard available at: {AnalyticsConfig.get_dash_url()}")
    print("=" * 50)
    
    try:
        # Run the dashboard
        subprocess.run([sys.executable, 'db_dashboard.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting dashboard: {e}")
        sys.exit(1)

def start_flask_app():
    """Start the Flask data management application"""
    print("🚀 Starting LISWMC Flask Data Management App...")
    print("=" * 50)
    print("📋 Flask App Features:")
    print("   📁 File upload and processing")
    print("   🧹 Data cleaning and validation")
    print("   🏢 Company unification tool")
    print("   🚗 License plate cleaning")
    print("   💾 Database import/export")
    print("   📊 Data management utilities")
    print("")
    print(f"🌐 Flask App available at: {AnalyticsConfig.get_flask_url()}")
    print("=" * 50)
    
    try:
        # Set up the Python path and environment
        env = os.environ.copy()
        env['PYTHONPATH'] = str(get_project_root())
        
        # Create the Flask app startup script content
        flask_startup_code = '''
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Now import and create the Flask app
from packages.analytics.flask_app import create_app
from datetime import datetime

app = create_app()

# Create uploads directory if it doesn't exist
uploads_dir = Path(__file__).resolve().parent / 'uploads'
uploads_dir.mkdir(exist_ok=True)

# Add jinja2 global variables
@app.context_processor
def inject_globals():
    return dict(now=datetime.now())

if __name__ == '__main__':
    print("✅ Flask app starting...")
    from config import AnalyticsConfig
    app.run(debug=True, host=AnalyticsConfig.FLASK_HOST, port=AnalyticsConfig.FLASK_PORT)
'''
        
        # Write the startup script
        startup_script = Path(__file__).parent / 'flask_startup_temp.py'
        startup_script.write_text(flask_startup_code)
        
        try:
            # Run the Flask app
            subprocess.run([sys.executable, str(startup_script)], 
                         env=env, check=True, cwd=str(get_project_root()))
        finally:
            # Clean up temp file
            if startup_script.exists():
                startup_script.unlink()
                
    except KeyboardInterrupt:
        print("\n👋 Flask app stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting Flask app: {e}")
        sys.exit(1)

def start_portal():
    """Start the unified portal application"""
    print("🚀 Starting LISWMC Analytics Portal...")
    print("=" * 50)
    print("🏠 Portal Features:")
    print("   🔐 Unified authentication")
    print("   🎯 Single sign-on access")
    print("   👥 User management")
    print("   📊 Application dashboard")
    print("   🔗 Quick links to all services")
    print("")
    print(f"🌐 Portal available at: {AnalyticsConfig.get_portal_url()}")
    print("=" * 50)
    
    try:
        # Run the portal
        subprocess.run([sys.executable, 'portal.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Portal stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting portal: {e}")
        sys.exit(1)

def start_zoning():
    """Start the zoning service"""
    print("🚀 Starting LISWMC Zoning Service...")
    print("=" * 50)
    print("🗺️  Zoning Service Features:")
    print("   🔐 Secure login required")
    print("   📍 Geographic zone management")
    print("   🏘️  Population and demographics analysis")
    print("   🚛 Waste collection optimization")
    print("   📊 GIS analytics and reporting")
    print("   🌍 Google Earth Engine integration")
    print("")
    print(f"🌐 Zoning Service available at: http://localhost:5001")
    print("=" * 50)
    
    try:
        # Set up the Python path and environment
        env = os.environ.copy()
        env['PYTHONPATH'] = str(get_project_root())
        
        # Change to zoning directory and run
        zoning_dir = get_project_root() / 'packages' / 'zoning'
        subprocess.run([sys.executable, 'run.py'], 
                      env=env, check=True, cwd=str(zoning_dir))
    except KeyboardInterrupt:
        print("\n👋 Zoning service stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting zoning service: {e}")
        sys.exit(1)

def start_both():
    """Start both dashboard and Flask app in separate processes"""
    print("🚀 Starting LISWMC Complete Analytics Suite...")
    print("=" * 50)
    AnalyticsConfig.print_urls()
    print("=" * 50)
    
    try:
        # Use the existing start_both.sh script if it exists
        if Path('start_both.sh').exists():
            subprocess.run(['./start_both.sh'], check=True)
        else:
            print("⚠️  start_both.sh script not found, starting services individually...")
            print("   Starting dashboard and Flask app in background...")
            
            # Start dashboard in background
            dashboard_process = subprocess.Popen([sys.executable, 'db_dashboard.py'])
            print(f"   📊 Dashboard started (PID: {dashboard_process.pid})")
            
            # Wait a bit
            import time
            time.sleep(2)
            
            # Start Flask app in foreground
            print("   🔧 Starting Flask app...")
            subprocess.run([sys.executable, 'start_analytics.py', '--flask'])
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Analytics suite stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting analytics suite: {e}")
        sys.exit(1)

def start_all():
    """Start all services: dashboard, Flask app, and zoning service"""
    print("🚀 Starting LISWMC Complete Platform...")
    print("=" * 50)
    print("🏢 All Services:")
    print("   📊 Analytics Dashboard (port 5007)")
    print("   🔧 Data Management (port 5002)")
    print("   🗺️  Zoning Service (port 5001)")
    print("   🏠 Unified Portal (port 5000)")
    print("=" * 50)
    
    try:
        import time
        
        # Start all services in background
        dashboard_process = subprocess.Popen([sys.executable, 'db_dashboard.py'])
        print(f"   📊 Dashboard started (PID: {dashboard_process.pid})")
        time.sleep(1)
        
        # Start Flask app
        env = os.environ.copy()
        env['PYTHONPATH'] = str(get_project_root())
        flask_startup_code = '''
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Now import and create the Flask app
from packages.analytics.flask_app import create_app
from datetime import datetime

app = create_app()

# Create uploads directory if it doesn't exist
uploads_dir = Path(__file__).resolve().parent / 'uploads'
uploads_dir.mkdir(exist_ok=True)

# Add jinja2 global variables
@app.context_processor
def inject_globals():
    return dict(now=datetime.now())

if __name__ == '__main__':
    from config import AnalyticsConfig
    app.run(debug=True, host=AnalyticsConfig.FLASK_HOST, port=AnalyticsConfig.FLASK_PORT)
'''
        
        startup_script = Path(__file__).parent / 'flask_startup_temp.py'
        startup_script.write_text(flask_startup_code)
        
        flask_process = subprocess.Popen([sys.executable, str(startup_script)], 
                                       env=env, cwd=str(get_project_root()))
        print(f"   🔧 Flask app started (PID: {flask_process.pid})")
        time.sleep(1)
        
        # Start zoning service
        zoning_dir = get_project_root() / 'packages' / 'zoning'
        zoning_process = subprocess.Popen([sys.executable, 'run.py'], 
                                        env=env, cwd=str(zoning_dir))
        print(f"   🗺️  Zoning service started (PID: {zoning_process.pid})")
        time.sleep(2)
        
        # Start portal in foreground
        print("   🏠 Starting unified portal...")
        subprocess.run([sys.executable, 'portal.py'])
        
    except KeyboardInterrupt:
        print("\n👋 All services stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting services: {e}")
        sys.exit(1)
    finally:
        # Clean up temp file
        startup_script = Path(__file__).parent / 'flask_startup_temp.py'
        if startup_script.exists():
            startup_script.unlink()

def run_tests():
    """Run the analytics test suite"""
    print("🧪 Running LISWMC Analytics Test Suite...")
    print("=" * 50)
    
    test_files = [
        'test_company_unifier.py',
        'test_plate_cleaner.py',
        'test_deployment.py'
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"📋 Running {test_file}...")
            try:
                subprocess.run([sys.executable, test_file], check=True)
                print(f"✅ {test_file} passed")
            except subprocess.CalledProcessError as e:
                print(f"❌ {test_file} failed: {e}")
        else:
            print(f"⚠️  {test_file} not found, skipping...")
    
    print("=" * 50)
    print("🏁 Test suite completed")

def main():
    """Main startup function"""
    parser = argparse.ArgumentParser(
        description='LISWMC Analytics Unified Startup Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python start_analytics.py --portal       # Start unified analytics portal (RECOMMENDED)
  python start_analytics.py --dashboard    # Start Dash analytics dashboard
  python start_analytics.py --flask        # Start Flask data management app
  python start_analytics.py --zoning       # Start zoning service
  python start_analytics.py --both         # Start both analytics services
  python start_analytics.py --all          # Start all services (COMPLETE PLATFORM)
  python start_analytics.py --test         # Run test suite
  python start_analytics.py --company-test # Test company unification
        '''
    )
    
    parser.add_argument('--portal', action='store_true',
                       help='Start the unified analytics portal (RECOMMENDED)')
    parser.add_argument('--dashboard', action='store_true',
                       help='Start the Dash analytics dashboard')
    parser.add_argument('--flask', action='store_true',
                       help='Start the Flask data management application')
    parser.add_argument('--zoning', action='store_true',
                       help='Start the zoning service')
    parser.add_argument('--both', action='store_true',
                       help='Start both dashboard and Flask app')
    parser.add_argument('--all', action='store_true',
                       help='Start all services (dashboard, Flask, zoning, and portal)')
    parser.add_argument('--test', action='store_true',
                       help='Run the analytics test suite')
    parser.add_argument('--company-test', action='store_true',
                       help='Test the company unification tool')
    
    args = parser.parse_args()
    
    # Change to the analytics directory
    analytics_dir = Path(__file__).parent
    os.chdir(analytics_dir)
    
    # Check if no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        print("\n" + "=" * 50)
        print("🏠 LISWMC Analytics Portal (Recommended):")
        print(f"   {AnalyticsConfig.get_portal_url()} - Unified access to all apps")
        print("")
        AnalyticsConfig.print_urls()
        print("   🗺️  Zoning Service: http://localhost:5001")
        print("   🧪 Test Suite")
        print("=" * 50)
        return
    
    # Execute based on arguments
    if args.portal:
        start_portal()
    elif args.dashboard:
        start_dash_dashboard()
    elif args.flask:
        start_flask_app()
    elif args.zoning:
        start_zoning()
    elif args.both:
        start_both()
    elif args.all:
        start_all()
    elif args.test:
        run_tests()
    elif args.company_test:
        print("🧪 Testing Company Unification Tool...")
        try:
            subprocess.run([sys.executable, 'test_company_unifier.py'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Company unification test failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()