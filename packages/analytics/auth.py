#!/usr/bin/env python3
"""
Authentication Module for LISWMC Dashboard
------------------------------------------
Handles user authentication, session management, and user operations.
"""

# Import from shared components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
import os
import hashlib
import secrets
import bcrypt
import psycopg2
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import get_db_connection

class AuthManager:
    """Handles authentication and user management for the dashboard"""
    
    def __init__(self):
        self.session_timeout = 60 * 60 * 8  # 8 hours in seconds
        self.max_login_attempts = 5
        self.lockout_duration = 30  # minutes
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    def is_account_locked(self, username: str) -> bool:
        """Check if an account is currently locked"""
        try:
            conn = get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT locked_until, login_attempts 
                FROM liswmc_users 
                WHERE username = %s AND is_active = TRUE
            """, (username,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                return False
                
            locked_until, login_attempts = result
            
            # Check if account is locked
            if locked_until and locked_until > datetime.now():
                return True
                
            # Check if max attempts exceeded
            if login_attempts >= self.max_login_attempts:
                return True
                
            return False
            
        except Exception as e:
            print(f"Error checking account lock status: {e}")
            return False
    
    def lock_account(self, username: str) -> None:
        """Lock an account due to too many failed attempts"""
        try:
            conn = get_db_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            locked_until = datetime.now() + timedelta(minutes=self.lockout_duration)
            
            cursor.execute("""
                UPDATE liswmc_users 
                SET locked_until = %s, login_attempts = %s
                WHERE username = %s
            """, (locked_until, self.max_login_attempts, username))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"Error locking account: {e}")
    
    def increment_login_attempts(self, username: str) -> None:
        """Increment failed login attempts for a user"""
        try:
            conn = get_db_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE liswmc_users 
                SET login_attempts = login_attempts + 1
                WHERE username = %s
            """, (username,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"Error incrementing login attempts: {e}")
    
    def reset_login_attempts(self, username: str) -> None:
        """Reset login attempts and unlock account after successful login"""
        try:
            conn = get_db_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE liswmc_users 
                SET login_attempts = 0, locked_until = NULL, last_login = NOW()
                WHERE username = %s
            """, (username,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"Error resetting login attempts: {e}")
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticate a user with username and password
        Returns: (success, message, user_data)
        """
        try:
            # Check if account is locked
            if self.is_account_locked(username):
                return False, "Account is locked due to too many failed login attempts. Please try again later.", None
            
            conn = get_db_connection()
            if not conn:
                return False, "Database connection failed", None
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, password_hash, full_name, email, role, is_active, login_attempts
                FROM liswmc_users 
                WHERE username = %s
            """, (username,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                return False, "Invalid username or password", None
            
            user_id, db_username, password_hash, full_name, email, role, is_active, login_attempts = result
            
            if not is_active:
                return False, "Account is disabled", None
            
            # Verify password
            if self.verify_password(password, password_hash):
                # Reset login attempts on successful login
                self.reset_login_attempts(username)
                
                user_data = {
                    'user_id': str(user_id),
                    'username': db_username,
                    'full_name': full_name,
                    'email': email,
                    'role': role
                }
                
                return True, "Login successful", user_data
            else:
                # Increment failed attempts
                self.increment_login_attempts(username)
                
                # Check if we should lock the account
                if login_attempts + 1 >= self.max_login_attempts:
                    self.lock_account(username)
                    return False, f"Too many failed attempts. Account locked for {self.lockout_duration} minutes.", None
                
                remaining_attempts = self.max_login_attempts - (login_attempts + 1)
                return False, f"Invalid username or password. {remaining_attempts} attempts remaining.", None
                
        except Exception as e:
            print(f"Authentication error: {e}")
            return False, "Authentication system error", None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by user ID"""
        try:
            conn = get_db_connection()
            if not conn:
                return None
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, full_name, email, role, is_active, created_at, last_login
                FROM liswmc_users 
                WHERE user_id = %s AND is_active = TRUE
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                user_id, username, full_name, email, role, is_active, created_at, last_login = result
                return {
                    'user_id': str(user_id),
                    'username': username,
                    'full_name': full_name,
                    'email': email,
                    'role': role,
                    'is_active': is_active,
                    'created_at': created_at,
                    'last_login': last_login
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def create_user(self, username: str, password: str, full_name: str = None, 
                   email: str = None, role: str = 'user') -> Tuple[bool, str]:
        """
        Create a new user account
        Returns: (success, message)
        """
        try:
            conn = get_db_connection()
            if not conn:
                return False, "Database connection failed"
                
            cursor = conn.cursor()
            
            # Check if username already exists
            cursor.execute("SELECT username FROM liswmc_users WHERE username = %s", (username,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return False, "Username already exists"
            
            # Hash password and create user
            password_hash = self.hash_password(password)
            
            cursor.execute("""
                INSERT INTO liswmc_users (username, password_hash, full_name, email, role)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING user_id
            """, (username, password_hash, full_name, email, role))
            
            user_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            return True, f"User created successfully with ID: {user_id}"
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return False, f"Error creating user: {str(e)}"
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change a user's password
        Returns: (success, message)
        """
        try:
            conn = get_db_connection()
            if not conn:
                return False, "Database connection failed"
                
            cursor = conn.cursor()
            
            # Get current password hash
            cursor.execute("SELECT password_hash FROM liswmc_users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                conn.close()
                return False, "User not found"
            
            current_hash = result[0]
            
            # Verify old password
            if not self.verify_password(old_password, current_hash):
                cursor.close()
                conn.close()
                return False, "Current password is incorrect"
            
            # Hash new password and update
            new_hash = self.hash_password(new_password)
            cursor.execute("""
                UPDATE liswmc_users 
                SET password_hash = %s, updated_at = NOW()
                WHERE user_id = %s
            """, (new_hash, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True, "Password changed successfully"
            
        except Exception as e:
            print(f"Error changing password: {e}")
            return False, f"Error changing password: {str(e)}"
    
    def generate_session_token(self) -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    def list_users(self) -> list:
        """List all users (admin function)"""
        try:
            conn = get_db_connection()
            if not conn:
                return []
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, full_name, email, role, is_active, created_at, last_login, login_attempts
                FROM liswmc_users 
                ORDER BY created_at DESC
            """)
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            users = []
            for row in results:
                user_id, username, full_name, email, role, is_active, created_at, last_login, login_attempts = row
                users.append({
                    'user_id': str(user_id),
                    'username': username,
                    'full_name': full_name,
                    'email': email,
                    'role': role,
                    'is_active': is_active,
                    'created_at': created_at,
                    'last_login': last_login,
                    'login_attempts': login_attempts
                })
            
            return users
            
        except Exception as e:
            print(f"Error listing users: {e}")
            return []

# Global authentication manager instance
auth_manager = AuthManager() 