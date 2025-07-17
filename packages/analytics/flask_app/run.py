#!/usr/bin/env python3
"""
Flask App Direct Startup
------------------------
Direct startup script for the Flask data management application.
Use this when running from the flask_app directory.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to Python path to enable imports
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Add project root to Python path
project_root = parent_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from flask_app import create_app
    from flask import jsonify
    
    app = create_app()
    
    # Create uploads directory if it doesn't exist
    uploads_dir = parent_dir / 'uploads'
    uploads_dir.mkdir(exist_ok=True)
    
    # Add health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint for Docker containers"""
        try:
            # Check basic application status
            status = {
                'status': 'healthy',
                'service': 'data-management',
                'version': '1.0.0',
                'timestamp': datetime.now().isoformat()
            }
            return jsonify(status), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'service': 'data-management',
                'error': str(e)
            }), 503
    
    # Add jinja2 global variables
    @app.context_processor
    def inject_globals():
        return dict(now=datetime.now())
    
    if __name__ == '__main__':
        # Import config
        from config import AnalyticsConfig
        
        print("🚀 Starting LISWMC Flask Data Management App...")
        print(f"🌐 Available at: {AnalyticsConfig.get_flask_url()}")
        print("📁 Features: File upload, data cleaning, company unification")
        app.run(debug=True, host=AnalyticsConfig.FLASK_HOST, port=AnalyticsConfig.FLASK_PORT)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Try running from the analytics directory using:")
    print("   python start_analytics.py --flask")
    sys.exit(1)
