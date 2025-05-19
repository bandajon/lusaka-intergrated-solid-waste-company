from flask import Flask, render_template, redirect, url_for, send_from_directory
from datetime import datetime
import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import database manager and plate cleaner utilities
from flask_app.utils.db_manager import DatabaseManager

# Create app
app = Flask(__name__, 
           template_folder='flask_app/templates',
           static_folder='flask_app/static')

# Configure app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['DB_HOST'] = 'agripredict-prime-prod.caraj6fzskso.eu-west-2.rds.amazonaws.com'
app.config['DB_NAME'] = 'users'
app.config['DB_USER'] = 'agripredict'
app.config['DB_PASS'] = 'Wee8fdm0k2!!'
app.config['DB_PORT'] = 5432

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register routes
from flask_app.routes import main_bp
app.register_blueprint(main_bp)

# Create a route to serve dashboard assets directly
@app.route('/dashboards/weigh_events/assets/<path:filename>')
def serve_dashboard_assets(filename):
    """Serve dashboard assets directly"""
    assets_dir = os.path.join(os.path.dirname(__file__), 'flask_app/dashboards/assets')
    print(f"SERVING ASSET: {filename} from {assets_dir}")
    return send_from_directory(assets_dir, filename)

# Create test pages to check if routing works properly
@app.route('/dashboard-test')
def dashboard_test():
    """Test page that links to the dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard Test Page</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css">
    </head>
    <body class="bg-gray-100 p-10">
        <div class="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-md">
            <h1 class="text-3xl font-bold mb-6">Dashboard Test Page</h1>
            
            <p class="mb-4">Let's test the dashboard functionality:</p>
            
            <div class="space-y-4">
                <div class="p-4 border rounded bg-blue-50">
                    <h2 class="font-bold">Test Dashboard URL</h2>
                    <p>Click to access the dashboard directly</p>
                    <a href="/dashboards/weigh_events/" 
                       class="mt-2 inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                       Open Dashboard
                    </a>
                </div>
                
                <div class="p-4 border rounded bg-green-50">
                    <h2 class="font-bold">Test Dashboard Assets</h2>
                    <p>Click to test if assets are being served correctly</p>
                    <a href="/dashboards/weigh_events/assets/style.css" 
                       class="mt-2 inline-block px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700" target="_blank">
                       Test CSS File
                    </a>
                    <a href="/dashboards/weigh_events/assets/scripts.js" 
                       class="mt-2 inline-block px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700" target="_blank">
                       Test JS File
                    </a>
                </div>
                
                <div class="p-4 border rounded bg-purple-50">
                    <h2 class="font-bold">Test Simple Dashboard</h2>
                    <p>Click to test a minimal dashboard page</p>
                    <a href="/simple-dashboard" 
                       class="mt-2 inline-block px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700">
                       Simple Dashboard
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/simple-dashboard')
def simple_dashboard():
    """A simple dashboard page with direct navigation links"""
    weigh_events_url = "/dashboards/weigh_events/"
    
    # Print info for debugging
    print(f"Simple dashboard requested. Weigh events URL: {weigh_events_url}")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple Dashboard</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css">
    </head>
    <body class="bg-gray-100">
        <nav class="bg-white border-b border-gray-200 p-4">
            <div class="max-w-7xl mx-auto flex justify-between items-center">
                <h1 class="text-xl font-bold">LISWMC Analytics</h1>
                <a href="/dashboard-test" class="text-blue-600 hover:text-blue-800">Back to Test Page</a>
            </div>
        </nav>
        
        <div class="max-w-7xl mx-auto p-6">
            <div class="bg-white p-6 rounded-lg shadow-md">
                <h2 class="text-2xl font-bold mb-4">Dashboard Access</h2>
                <p class="mb-6">Access the weighing events dashboard using one of the following methods:</p>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="p-4 border rounded bg-blue-50">
                        <h3 class="font-bold text-lg mb-2">Direct Dashboard Link</h3>
                        <p class="mb-4">Open in a new tab</p>
                        <a href="{weigh_events_url}" target="_blank"
                           class="block w-full py-2 px-4 bg-blue-600 text-white text-center rounded hover:bg-blue-700">
                           Open Dashboard
                        </a>
                    </div>
                    
                    <div class="p-4 border rounded bg-purple-50">
                        <h3 class="font-bold text-lg mb-2">Immediate Redirect</h3>
                        <p class="mb-4">Go directly to the dashboard</p>
                        <a href="/direct-to-weigh-events" 
                           class="block w-full py-2 px-4 bg-purple-600 text-white text-center rounded hover:bg-purple-700">
                           Go to Dashboard
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# Direct redirect to weigh events dashboard
@app.route('/direct-to-weigh-events')
def direct_to_weigh_events():
    """Direct redirect to the weigh events dashboard"""
    return redirect('/dashboards/weigh_events/')

# Register Dash app - do this after defining routes for simplicity
from flask_app.dashboards.weigh_events_dashboard import dash_app as weigh_events_dash

# Set server to our Flask app instance
weigh_events_dash.server = app

# Debug information for Dash app setup
print("✅ Dash app imported and configured")
print(f"✅ Dash app has {len(weigh_events_dash.callback_map)} callbacks")
print(f"✅ Dash app layout has {len(weigh_events_dash.layout.children) if hasattr(weigh_events_dash.layout, 'children') else 0} children")

# Register the dash app routes under a URL prefix with Werkzeug DispatcherMiddleware
from werkzeug.middleware.dispatcher import DispatcherMiddleware

class PathDebugMiddleware:
    """Middleware to debug URL paths"""
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        print(f"DEBUG - Request path: {path}")
        return self.app(environ, start_response)

# Wrap the Flask app with the middleware
app.wsgi_app = PathDebugMiddleware(app.wsgi_app)

# Mount the Dash app at the specified URL prefix
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/dashboards/weigh_events': weigh_events_dash.server
})

# Add jinja2 global variables
@app.context_processor
def inject_globals():
    return dict(now=datetime.now())

# Simple redirect to dashboard test page
@app.route('/')
def index_redirect():
    return redirect(url_for('dashboard_test'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)