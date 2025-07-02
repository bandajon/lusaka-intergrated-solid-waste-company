#!/usr/bin/env python3
"""
Dash Authentication Check
-------------------------
Helper module to check portal authentication for Dash app.
"""

import requests
from urllib.parse import parse_qs, urlparse
import logging

logger = logging.getLogger(__name__)

def check_portal_session(session_token: str, portal_url: str = "http://localhost:5003") -> tuple:
    """
    Check if session token is valid with the portal.
    
    Returns:
        tuple: (is_authenticated: bool, user_data: dict or None)
    """
    if not session_token:
        return False, None
        
    try:
        response = requests.get(
            f"{portal_url}/api/check_session",
            params={'token': session_token},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('authenticated'):
                return True, data.get('user', {})
                
        return False, None
        
    except Exception as e:
        logger.warning(f"Failed to check portal session: {e}")
        return False, None

def get_session_token_from_url(url: str) -> str:
    """Extract session token from URL parameters"""
    if not url:
        return None
        
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        token = params.get('session_token', [None])[0]
        return token
    except Exception:
        return None

def auto_login_from_portal(request_url: str = None) -> tuple:
    """
    Attempt to automatically log in using portal session token from URL.
    
    Returns:
        tuple: (success: bool, user_data: dict or None, message: str)
    """
    if not request_url:
        return False, None, "No URL provided"
        
    session_token = get_session_token_from_url(request_url)
    if not session_token:
        return False, None, "No session token in URL"
    
    is_authenticated, user_data = check_portal_session(session_token)
    
    if is_authenticated:
        return True, user_data, "Successfully authenticated via portal"
    else:
        return False, None, "Invalid or expired portal session"