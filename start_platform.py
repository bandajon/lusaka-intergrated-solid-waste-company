#!/usr/bin/env python3
"""
LISWMC Unified Platform Startup Script
=====================================
Single entry point to start the complete LISWMC platform from project root.
"""

import sys
import os
import subprocess
import argparse
import time
import signal
from pathlib import Path

class PlatformManager:
    """Manages the LISWMC platform services"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent
        self.analytics_dir = self.project_root / 'packages' / 'analytics'
        self.zoning_dir = self.project_root / 'packages' / 'zoning'
        self.processes = []
        
        # Service configurations
        self.services = {
            'portal': {
                'name': 'Unified Portal',
                'port': 5005,
                'script': 'portal.py',
                'dir': self.analytics_dir,
                'description': '🏠 Single sign-on entry point for all services (includes QR code generation)'
            },
            'zoning': {
                'name': 'Zoning Service',
                'port': 5001,
                'script': 'run.py',
                'dir': self.zoning_dir,
                'description': '🗺️  Geographic zone management and GIS analytics'
            },
            'flask': {
                'name': 'Data Management App',
                'port': 5002,
                'script': 'flask_app/run.py',
                'dir': self.analytics_dir,
                'description': '🔧 File upload, data cleaning, database management, and company unification'
            },
            'dashboard': {
                'name': 'Analytics Dashboard',
                'port': 5007,
                'script': 'db_dashboard.py',
                'dir': self.analytics_dir,
                'description': '📊 Real-time waste collection analytics and visualization'
            }
        }
    
    def validate_environment(self):
        """Validate that we're in the right directory and dependencies exist"""
        if not (self.analytics_dir).exists():
            print("❌ Error: packages/analytics directory not found")
            print("   Please run this script from the project root directory")
            return False
        
        if not (self.zoning_dir).exists():
            print("❌ Error: packages/zoning directory not found")
            print("   Please run this script from the project root directory")
            return False
        
        return True
    
    def print_banner(self):
        """Print the platform banner"""
        print("=" * 60)
        print("🚀 LISWMC Unified Platform Startup")
        print("=" * 60)
        print("🏢 Lusaka Integrated Solid Waste Management Company")
        print("📍 Complete waste management platform")
        print("=" * 60)
    
    def print_service_info(self, services_to_start):
        """Print information about services being started"""
        print("\n📋 Services to start:")
        for service_key in services_to_start:
            service = self.services[service_key]
            print(f"   {service['description']}")
            print(f"      └─ {service['name']} → http://localhost:{service['port']}")
        print()
    
    def start_service(self, service_key, background=True):
        """Start a single service"""
        service = self.services[service_key]
        
        try:
            # Set up environment
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.project_root)
            
            # Start the service
            cmd = [sys.executable, service['script']]
            
            if background:
                process = subprocess.Popen(
                    cmd,
                    cwd=str(service['dir']),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.processes.append(process)
                print(f"   ✅ {service['name']} started (PID: {process.pid})")
                return process
            else:
                # Foreground process (typically for the last service)
                print(f"   🎯 Starting {service['name']} in foreground...")
                subprocess.run(cmd, cwd=str(service['dir']), env=env, check=True)
                
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to start {service['name']}: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Error starting {service['name']}: {e}")
            return None
    
    def start_analytics_suite(self):
        """Start analytics services (dashboard + flask)"""
        print("🚀 Starting LISWMC Analytics Suite...")
        self.print_service_info(['dashboard', 'flask'])
        
        # Start services in background
        self.start_service('dashboard', background=True)
        time.sleep(1)
        
        # Start Flask in foreground
        self.start_service('flask', background=False)
    
    def start_complete_platform(self):
        """Start all services"""
        print("🚀 Starting Complete LISWMC Platform...")
        self.print_service_info(['dashboard', 'flask', 'zoning', 'portal'])
        
        # Start all services in background except portal (last one)
        services_background = ['dashboard', 'flask', 'zoning']
        for service_key in services_background:
            self.start_service(service_key, background=True)
            time.sleep(1)
        
        # Start portal in foreground
        print(f"\n🌟 Platform ready! All services started.")
        print("💡 Access the platform through the Unified Portal:")
        print(f"   🏠 Portal: http://localhost:{self.services['portal']['port']}")
        print()
        self.start_service('portal', background=False)
    
    def start_single_service(self, service_key):
        """Start a single service"""
        if service_key not in self.services:
            print(f"❌ Unknown service: {service_key}")
            return
        
        service = self.services[service_key]
        print(f"🚀 Starting {service['name']}...")
        self.print_service_info([service_key])
        self.start_service(service_key, background=False)
    
    def cleanup(self):
        """Clean up background processes"""
        print("\n🧹 Cleaning up background processes...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception:
                pass
        self.processes.clear()
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print("\n👋 Shutting down platform...")
        self.cleanup()
        sys.exit(0)

def main():
    """Main startup function"""
    manager = PlatformManager()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    parser = argparse.ArgumentParser(
        description='LISWMC Unified Platform Startup Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python start_platform.py --all          # Start complete platform (RECOMMENDED)
  python start_platform.py --analytics    # Start analytics suite only
  python start_platform.py --dashboard    # Start analytics dashboard only
  python start_platform.py --flask        # Start data management app only
  python start_platform.py --zoning       # Start zoning service only
  python start_platform.py --portal       # Start unified portal only (includes QR code service)

Note: QR code service is integrated into the portal.
        '''
    )
    
    parser.add_argument('--all', action='store_true',
                       help='Start complete platform (all services)')
    parser.add_argument('--analytics', action='store_true',
                       help='Start analytics suite (dashboard + flask)')
    parser.add_argument('--dashboard', action='store_true',
                       help='Start analytics dashboard only')
    parser.add_argument('--flask', action='store_true',
                       help='Start Flask data management app only')
    parser.add_argument('--zoning', action='store_true',
                       help='Start zoning service only')
    parser.add_argument('--portal', action='store_true',
                       help='Start unified portal only (includes QR code service)')
    
    args = parser.parse_args()
    
    # Validate environment
    if not manager.validate_environment():
        sys.exit(1)
    
    manager.print_banner()
    
    # Check if no arguments provided
    if not any(vars(args).values()):
        parser.print_help()
        print("\n" + "=" * 60)
        print("🏠 LISWMC Platform Services:")
        for service_key, service in manager.services.items():
            print(f"   {service['description']}")
            print(f"      └─ http://localhost:{service['port']}")
        print("\n💡 Recommended: python start_platform.py --all")
        print("=" * 60)
        return
    
    try:
        # Execute based on arguments
        if args.all:
            manager.start_complete_platform()
        elif args.analytics:
            manager.start_analytics_suite()
        elif args.dashboard:
            manager.start_single_service('dashboard')
        elif args.flask:
            manager.start_single_service('flask')
        elif args.zoning:
            manager.start_single_service('zoning')
        elif args.portal:
            manager.start_single_service('portal')
            
    except KeyboardInterrupt:
        print("\n👋 Platform stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        manager.cleanup()

if __name__ == "__main__":
    main()