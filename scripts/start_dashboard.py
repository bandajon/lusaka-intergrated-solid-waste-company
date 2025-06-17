#!/usr/bin/env python3
"""
LISWMC Dashboard Startup Script
------------------------------
Simple script to start the authenticated dashboard.
"""

import sys
import os

def main():
    """Start the dashboard"""
    print("🚀 Starting LISWMC Analytics Dashboard...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('packages/analytics/db_dashboard.py'):
        print("❌ Please run this script from the project root directory")
        print("   (where analytics/ folder is located)")
        sys.exit(1)
    
    print("📋 Dashboard Features:")
    print("   🔐 Secure login required")
    print("   📊 Real-time waste collection analytics")
    print("   📈 Business hours: 8AM-5PM (Zambia time)")
    print("   🚛 Vehicle performance tracking")
    print("   📍 Location-based insights")
    print("   💰 Fee calculation and reporting")
    print("")
    print("")
    print("🌐 Dashboard will be available at: http://localhost:5007")
    print("")
    print("Starting dashboard...")
    print("=" * 50)
    
    # Import and run the dashboard
    try:
        # Add current directory to Python path to ensure imports work
        sys.path.insert(0, os.getcwd())
        os.system('python packages/analytics/db_dashboard.py')
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 