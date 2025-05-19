# Dashboards package initialization

# Create a Flask Blueprint for serving dashboard assets
from flask import Blueprint, send_from_directory, current_app
import os

dashboard_assets = Blueprint('dashboard_assets', __name__)

@dashboard_assets.route('/dashboards/weigh_events/assets/<path:filename>')
def serve_dashboard_asset(filename):
    """Serve dashboard assets"""
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    return send_from_directory(assets_dir, filename)

# Export the blueprint for registration
__all__ = ['dashboard_assets']