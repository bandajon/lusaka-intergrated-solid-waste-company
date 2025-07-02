#!/usr/bin/env python3
"""
Analytics Authentication Middleware for Zoning Service
-----------------------------------------------------
Allows zoning service to authenticate users from analytics portal
"""

import requests
from flask import request, session, redirect, url_for, flash
from functools import wraps
import json
from datetime import datetime

class AnalyticsAuthMiddleware:
    """Middleware to handle authentication from analytics portal"""
    
    def __init__(self, app=None):
        self.app = app
        self.analytics_portal_url = "http://localhost:5000"
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app"""
        app.before_request(self.check_analytics_auth)
    
    def check_analytics_auth(self):
        """Check for analytics authentication before each request"""
        # Skip authentication check for certain routes
        skip_routes = [
            'auth.login', 
            'auth.logout', 
            'auth.sso',
            'static'
        ]
        
        if request.endpoint in skip_routes:
            return
        
        # Check for SSO token in URL parameters
        sso_token = request.args.get('analytics_token')
        if sso_token:
            return self.handle_sso_login(sso_token)
        
        # Check if user is already authenticated locally
        if 'user_id' in session:
            return
        
        # Check for analytics session token in headers or cookies
        analytics_token = (
            request.headers.get('X-Analytics-Session') or 
            request.cookies.get('analytics_session')
        )
        
        if analytics_token:
            return self.authenticate_from_analytics(analytics_token)
    
    def handle_sso_login(self, sso_token):
        """Handle SSO login from analytics portal"""
        try:
            # Validate token with analytics portal
            response = requests.get(
                f"{self.analytics_portal_url}/api/check_session",
                params={'token': sso_token},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('authenticated'):
                    user_data = data.get('user', {})
                    
                    # Create local session
                    session['user_id'] = user_data.get('username')  # Use username as ID
                    session['username'] = user_data.get('username')
                    session['full_name'] = user_data.get('full_name')
                    session['email'] = user_data.get('email')
                    session['role'] = self.map_analytics_role(user_data.get('role'))
                    session['analytics_auth'] = True
                    session['analytics_token'] = sso_token
                    session['login_time'] = datetime.now().isoformat()
                    
                    flash(f'Welcome {user_data.get("full_name", user_data.get("username"))}!', 'success')
                    
                    # Redirect to clean URL without token
                    clean_url = request.url.split('?')[0]
                    return redirect(clean_url)
            
        except Exception as e:
            print(f"SSO authentication error: {e}")
            flash('Authentication error. Please try logging in again.', 'error')
            return redirect(url_for('auth.login'))
    
    def authenticate_from_analytics(self, analytics_token):
        """Authenticate user using analytics session token"""
        try:
            # Validate token with analytics portal
            response = requests.get(
                f"{self.analytics_portal_url}/api/check_session",
                headers={'X-Session-Token': analytics_token},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('authenticated'):
                    user_data = data.get('user', {})
                    
                    # Update local session if not already set
                    if 'user_id' not in session:
                        session['user_id'] = user_data.get('username')
                        session['username'] = user_data.get('username')
                        session['full_name'] = user_data.get('full_name')
                        session['email'] = user_data.get('email')
                        session['role'] = self.map_analytics_role(user_data.get('role'))
                        session['analytics_auth'] = True
                        session['analytics_token'] = analytics_token
                        session['login_time'] = datetime.now().isoformat()
                    
                    return  # Continue with request
            
            # If authentication fails, redirect to login
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            print(f"Analytics authentication error: {e}")
            return redirect(url_for('auth.login'))
    
    def map_analytics_role(self, analytics_role):
        """Map analytics roles to zoning service roles"""
        role_mapping = {
            'admin': 'ADMIN',
            'user': 'PLANNER', 
            'viewer': 'VIEW_ONLY'
        }
        return role_mapping.get(analytics_role, 'VIEW_ONLY')
    
    def get_sso_url(self, analytics_token, redirect_url=None):
        """Generate SSO URL for zoning service"""
        base_url = "http://localhost:5001/auth/sso"
        params = f"analytics_token={analytics_token}"
        if redirect_url:
            params += f"&redirect={redirect_url}"
        return f"{base_url}?{params}"

def require_analytics_auth(f):
    """Decorator to require analytics authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Global middleware instance
analytics_auth_middleware = AnalyticsAuthMiddleware()