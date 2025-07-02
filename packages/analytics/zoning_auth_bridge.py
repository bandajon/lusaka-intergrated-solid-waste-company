#!/usr/bin/env python3
"""
Zoning Service Authentication Bridge
-----------------------------------
Provides authentication integration between analytics portal and zoning service
"""

import requests
import os
from pathlib import Path
from auth import auth_manager
from session_bridge import session_bridge

class ZoningAuthBridge:
    """Bridge to handle authentication between analytics portal and zoning service"""
    
    def __init__(self):
        self.zoning_base_url = "http://localhost:5001"
        self.analytics_base_url = "http://localhost:5000"
    
    def create_zoning_user_from_analytics(self, analytics_user_data):
        """Create or update a user in zoning service based on analytics user data"""
        try:
            # Map analytics roles to zoning roles
            role_mapping = {
                'admin': 'ADMIN',
                'user': 'PLANNER',
                'viewer': 'VIEW_ONLY'
            }
            
            zoning_role = role_mapping.get(analytics_user_data.get('role', 'user'), 'VIEW_ONLY')
            
            # Prepare user data for zoning service
            zoning_user_data = {
                'username': analytics_user_data['username'],
                'email': analytics_user_data.get('email', f"{analytics_user_data['username']}@liswmc.local"),
                'full_name': analytics_user_data.get('full_name', analytics_user_data['username']),
                'role': zoning_role,
                'external_auth': True,  # Flag to indicate this is externally authenticated
                'analytics_user_id': analytics_user_data['user_id']
            }
            
            return zoning_user_data
            
        except Exception as e:
            print(f"Error creating zoning user data: {e}")
            return None
    
    def authenticate_with_zoning(self, session_token):
        """Authenticate a user with the zoning service using analytics session token"""
        try:
            # Get user data from analytics session
            user_data = session_bridge.get_session(session_token)
            if not user_data:
                return False, "Invalid or expired session"
            
            # Create zoning user data
            zoning_user_data = self.create_zoning_user_from_analytics(user_data)
            if not zoning_user_data:
                return False, "Error preparing user data for zoning service"
            
            # Here we would typically make an API call to the zoning service
            # to establish authentication, but since we're integrating the services,
            # we can use a shared session approach
            
            return True, zoning_user_data
            
        except Exception as e:
            print(f"Error authenticating with zoning service: {e}")
            return False, f"Authentication error: {str(e)}"
    
    def get_zoning_login_url(self, analytics_session_token):
        """Generate a login URL for the zoning service with SSO token"""
        return f"{self.zoning_base_url}/auth/sso?token={analytics_session_token}"
    
    def validate_analytics_session(self, session_token):
        """Validate an analytics session token"""
        user_data = session_bridge.get_session(session_token)
        return user_data is not None, user_data

# Global bridge instance
zoning_auth_bridge = ZoningAuthBridge()