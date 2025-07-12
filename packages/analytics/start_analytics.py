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
        
        # Run the main Flask app directly
        subprocess.run([sys.executable, 'app.py'], 
                     env=env, check=True, cwd=str(Path(__file__).parent))
                
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
    print("   📱 Integrated QR code generation")
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
    print("🚀 Starting LISWMC Analytics Suite...")
    print("=" * 50)
    print("🏢 Analytics Services:")
    print(f"   📊 Analytics Dashboard: {AnalyticsConfig.get_dash_url()}")
    print(f"   🔧 Data Management: {AnalyticsConfig.get_flask_url()}")
    print("=" * 50)
    
    try:
        import time
        
        # Start dashboard in background
        dashboard_process = subprocess.Popen([sys.executable, 'db_dashboard.py'])
        print(f"   📊 Dashboard started (PID: {dashboard_process.pid})")
        time.sleep(2)
        
        # Start Flask app in foreground
        print("   🔧 Starting Flask app...")
        env = os.environ.copy()
        env['PYTHONPATH'] = str(get_project_root())
        subprocess.run([sys.executable, 'app.py'], env=env, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Analytics suite stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting analytics suite: {e}")
        sys.exit(1)

def start_all():
    """Start all services: dashboard, Flask app, zoning service, and portal"""
    print("🚀 Starting LISWMC Complete Platform...")
    print("=" * 50)
    print("🏢 All Services:")
    print(f"   📊 Analytics Dashboard (port {AnalyticsConfig.DASH_PORT})")
    print(f"   🔧 Data Management (port {AnalyticsConfig.FLASK_PORT})")
    print(f"   🗺️  Zoning Service (port 5001)")
    print(f"   🏠 Unified Portal (port {AnalyticsConfig.PORTAL_PORT})")
    print("      └─ 📱 QR Code Service (integrated)")
    print("=" * 50)
    
    try:
        import time
        
        # Start all services in background
        processes = []
        
        # Start dashboard
        dashboard_process = subprocess.Popen([sys.executable, 'db_dashboard.py'])
        processes.append(dashboard_process)
        print(f"   ✅ Dashboard started (PID: {dashboard_process.pid})")
        time.sleep(1)
        
        # Start Flask app
        env = os.environ.copy()
        env['PYTHONPATH'] = str(get_project_root())
        
        flask_process = subprocess.Popen([sys.executable, 'app.py'], 
                                       env=env, cwd=str(Path(__file__).parent))
        processes.append(flask_process)
        print(f"   ✅ Flask app started (PID: {flask_process.pid})")
        time.sleep(1)
        
        # Start zoning service
        zoning_dir = get_project_root() / 'packages' / 'zoning'
        zoning_process = subprocess.Popen([sys.executable, 'run.py'], 
                                        env=env, cwd=str(zoning_dir))
        processes.append(zoning_process)
        print(f"   ✅ Zoning service started (PID: {zoning_process.pid})")
        time.sleep(2)
        
        # Start portal in foreground
        print("   🏠 Starting unified portal (with integrated QR service)...")
        print(f"\n🌟 Platform ready! All services started.")
        print("💡 Access the platform through the Unified Portal:")
        print(f"   🏠 Portal: {AnalyticsConfig.get_portal_url()}")
        print()
        
        subprocess.run([sys.executable, 'portal.py'])
        
        # If portal exits, clean up other processes
        print("\n🧹 Cleaning up background processes...")
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception:
                pass
        
    except KeyboardInterrupt:
        print("\n👋 All services stopped by user")
        # Clean up background processes
        print("🧹 Cleaning up background processes...")
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception:
                pass
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting services: {e}")
        sys.exit(1)

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
    parser.add_argument('--qr', action='store_true',
                       help='[DEPRECATED] QR service is now integrated into the portal')
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
        print("📋 Individual Services:")
        print(f"   📊 Analytics Dashboard: {AnalyticsConfig.get_dash_url()}")
        print(f"   🔧 Data Management: {AnalyticsConfig.get_flask_url()}")
        print(f"   🗺️  Zoning Service: http://localhost:5001")
        print(f"   📱 QR Code Service: Integrated in Portal")
        print("   🧪 Test Suite")
        print("=" * 50)
        print("\n💡 Tip: Use 'python start_analytics.py --all' to start everything")
        print("   or use 'python ../../../start_platform.py --all' from project root")
        return
    
    # Execute based on arguments
    if args.portal:
        start_portal()
    elif args.dashboard:
        start_dash_dashboard()
    elif args.flask:
        start_flask_app()
    elif args.qr:
        print("⚠️  QR code service is now integrated into the portal.")
        print("   Please use 'python start_analytics.py --portal' to access QR functionality.")
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