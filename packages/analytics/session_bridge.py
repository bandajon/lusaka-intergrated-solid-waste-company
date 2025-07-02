#!/usr/bin/env python3
"""
Session Bridge for Authentication Sharing
-----------------------------------------
Allows sharing authentication sessions between Flask portal and Dash app.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

class SessionBridge:
    """
    Manages shared authentication sessions between Flask and Dash applications.
    Uses a simple file-based session store for cross-application session sharing.
    """
    
    def __init__(self, session_dir: str = None):
        """Initialize session bridge with storage directory"""
        if session_dir is None:
            session_dir = os.path.join(os.path.dirname(__file__), '.sessions')
        
        self.session_dir = session_dir
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Session timeout (8 hours)
        self.session_timeout = timedelta(hours=8)
        
    def create_session(self, user_data: Dict) -> str:
        """Create a new shared session and return session token"""
        session_token = self._generate_session_token()
        session_data = {
            'user_data': user_data,
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'expires_at': (datetime.now() + self.session_timeout).isoformat()
        }
        
        session_file = os.path.join(self.session_dir, f"{session_token}.json")
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
            
        return session_token
    
    def get_session(self, session_token: str) -> Optional[Dict]:
        """Retrieve session data by token"""
        if not session_token:
            return None
            
        session_file = os.path.join(self.session_dir, f"{session_token}.json")
        
        if not os.path.exists(session_file):
            return None
            
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
                
            # Check if session has expired
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                self.invalidate_session(session_token)
                return None
                
            # Update last accessed time
            session_data['last_accessed'] = datetime.now().isoformat()
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
                
            return session_data['user_data']
            
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid session file
            self.invalidate_session(session_token)
            return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """Remove a session"""
        if not session_token:
            return False
            
        session_file = os.path.join(self.session_dir, f"{session_token}.json")
        
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
                return True
            except OSError:
                return False
        return False
    
    def cleanup_expired_sessions(self):
        """Remove expired session files"""
        if not os.path.exists(self.session_dir):
            return
            
        for filename in os.listdir(self.session_dir):
            if filename.endswith('.json'):
                session_file = os.path.join(self.session_dir, filename)
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                        
                    expires_at = datetime.fromisoformat(session_data['expires_at'])
                    if datetime.now() > expires_at:
                        os.remove(session_file)
                        
                except (json.JSONDecodeError, KeyError, ValueError, OSError):
                    # Remove invalid session files
                    try:
                        os.remove(session_file)
                    except OSError:
                        pass
    
    def _generate_session_token(self) -> str:
        """Generate a unique session token"""
        import uuid
        return str(uuid.uuid4())

# Global session bridge instance
session_bridge = SessionBridge()