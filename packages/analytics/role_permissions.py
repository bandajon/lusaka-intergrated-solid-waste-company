#!/usr/bin/env python3
"""
Role-Based Access Control (RBAC) for LISWMC Platform
----------------------------------------------------
Defines roles and their permissions across all services.
"""

from enum import Enum
from typing import Dict, List, Set

class ServicePermission(Enum):
    """Service access permissions"""
    # Portal permissions
    PORTAL_ACCESS = "portal.access"
    PORTAL_ADMIN = "portal.admin"
    
    # Analytics Dashboard permissions
    ANALYTICS_VIEW = "analytics.view"
    ANALYTICS_EXPORT = "analytics.export"
    ANALYTICS_ADMIN = "analytics.admin"
    
    # Data Management permissions
    DATA_VIEW = "data.view"
    DATA_UPLOAD = "data.upload"
    DATA_CLEAN = "data.clean"
    DATA_IMPORT = "data.import"
    DATA_EXPORT = "data.export"
    DATA_DELETE = "data.delete"
    DATA_ADMIN = "data.admin"
    
    # Company Management permissions
    COMPANY_VIEW = "company.view"
    COMPANY_UNIFY = "company.unify"
    COMPANY_QR = "company.qr"
    COMPANY_ADMIN = "company.admin"
    
    # Zoning Service permissions
    ZONING_VIEW = "zoning.view"
    ZONING_CREATE = "zoning.create"
    ZONING_EDIT = "zoning.edit"
    ZONING_DELETE = "zoning.delete"
    ZONING_ANALYZE = "zoning.analyze"
    ZONING_ADMIN = "zoning.admin"
    
    # User Management permissions
    USER_VIEW = "user.view"
    USER_CREATE = "user.create"
    USER_EDIT = "user.edit"
    USER_DELETE = "user.delete"
    USER_ADMIN = "user.admin"

class Role(Enum):
    """User roles"""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    OPERATOR = "operator"
    VIEWER = "viewer"

# Role hierarchy (higher roles inherit permissions from lower roles)
ROLE_HIERARCHY = {
    Role.ADMIN: [Role.MANAGER, Role.ANALYST, Role.OPERATOR, Role.VIEWER],
    Role.MANAGER: [Role.ANALYST, Role.OPERATOR, Role.VIEWER],
    Role.ANALYST: [Role.VIEWER],
    Role.OPERATOR: [Role.VIEWER],
    Role.VIEWER: []
}

# Define permissions for each role
ROLE_PERMISSIONS: Dict[Role, Set[ServicePermission]] = {
    Role.VIEWER: {
        # Basic view access to all services
        ServicePermission.PORTAL_ACCESS,
        ServicePermission.ANALYTICS_VIEW,
        ServicePermission.DATA_VIEW,
        ServicePermission.COMPANY_VIEW,
        ServicePermission.ZONING_VIEW,
    },
    
    Role.OPERATOR: {
        # Can perform basic operations
        ServicePermission.PORTAL_ACCESS,
        ServicePermission.ANALYTICS_VIEW,
        ServicePermission.ANALYTICS_EXPORT,
        ServicePermission.DATA_VIEW,
        ServicePermission.DATA_UPLOAD,
        ServicePermission.DATA_CLEAN,
        ServicePermission.COMPANY_VIEW,
        ServicePermission.COMPANY_QR,
        ServicePermission.ZONING_VIEW,
    },
    
    Role.ANALYST: {
        # Can analyze and modify data
        ServicePermission.PORTAL_ACCESS,
        ServicePermission.ANALYTICS_VIEW,
        ServicePermission.ANALYTICS_EXPORT,
        ServicePermission.DATA_VIEW,
        ServicePermission.DATA_UPLOAD,
        ServicePermission.DATA_CLEAN,
        ServicePermission.DATA_IMPORT,
        ServicePermission.DATA_EXPORT,
        ServicePermission.COMPANY_VIEW,
        ServicePermission.COMPANY_UNIFY,
        ServicePermission.COMPANY_QR,
        ServicePermission.ZONING_VIEW,
        ServicePermission.ZONING_CREATE,
        ServicePermission.ZONING_EDIT,
        ServicePermission.ZONING_ANALYZE,
    },
    
    Role.MANAGER: {
        # Can manage most aspects except user management
        ServicePermission.PORTAL_ACCESS,
        ServicePermission.ANALYTICS_VIEW,
        ServicePermission.ANALYTICS_EXPORT,
        ServicePermission.ANALYTICS_ADMIN,
        ServicePermission.DATA_VIEW,
        ServicePermission.DATA_UPLOAD,
        ServicePermission.DATA_CLEAN,
        ServicePermission.DATA_IMPORT,
        ServicePermission.DATA_EXPORT,
        ServicePermission.DATA_DELETE,
        ServicePermission.COMPANY_VIEW,
        ServicePermission.COMPANY_UNIFY,
        ServicePermission.COMPANY_QR,
        ServicePermission.COMPANY_ADMIN,
        ServicePermission.ZONING_VIEW,
        ServicePermission.ZONING_CREATE,
        ServicePermission.ZONING_EDIT,
        ServicePermission.ZONING_DELETE,
        ServicePermission.ZONING_ANALYZE,
        ServicePermission.USER_VIEW,
    },
    
    Role.ADMIN: {
        # Full access to everything
        ServicePermission.PORTAL_ACCESS,
        ServicePermission.PORTAL_ADMIN,
        ServicePermission.ANALYTICS_VIEW,
        ServicePermission.ANALYTICS_EXPORT,
        ServicePermission.ANALYTICS_ADMIN,
        ServicePermission.DATA_VIEW,
        ServicePermission.DATA_UPLOAD,
        ServicePermission.DATA_CLEAN,
        ServicePermission.DATA_IMPORT,
        ServicePermission.DATA_EXPORT,
        ServicePermission.DATA_DELETE,
        ServicePermission.DATA_ADMIN,
        ServicePermission.COMPANY_VIEW,
        ServicePermission.COMPANY_UNIFY,
        ServicePermission.COMPANY_QR,
        ServicePermission.COMPANY_ADMIN,
        ServicePermission.ZONING_VIEW,
        ServicePermission.ZONING_CREATE,
        ServicePermission.ZONING_EDIT,
        ServicePermission.ZONING_DELETE,
        ServicePermission.ZONING_ANALYZE,
        ServicePermission.ZONING_ADMIN,
        ServicePermission.USER_VIEW,
        ServicePermission.USER_CREATE,
        ServicePermission.USER_EDIT,
        ServicePermission.USER_DELETE,
        ServicePermission.USER_ADMIN,
    }
}

class PermissionManager:
    """Manages role-based permissions"""
    
    @staticmethod
    def get_role_permissions(role_str: str) -> Set[ServicePermission]:
        """Get all permissions for a role (including inherited permissions)"""
        try:
            role = Role(role_str.lower())
        except ValueError:
            # Default to viewer for unknown roles
            role = Role.VIEWER
        
        permissions = set()
        
        # Add direct permissions
        permissions.update(ROLE_PERMISSIONS.get(role, set()))
        
        # Add inherited permissions from role hierarchy
        for inherited_role in ROLE_HIERARCHY.get(role, []):
            permissions.update(ROLE_PERMISSIONS.get(inherited_role, set()))
        
        return permissions
    
    @staticmethod
    def has_permission(role_str: str, permission: ServicePermission) -> bool:
        """Check if a role has a specific permission"""
        permissions = PermissionManager.get_role_permissions(role_str)
        return permission in permissions
    
    @staticmethod
    def has_any_permission(role_str: str, permissions: List[ServicePermission]) -> bool:
        """Check if a role has any of the specified permissions"""
        user_permissions = PermissionManager.get_role_permissions(role_str)
        return any(perm in user_permissions for perm in permissions)
    
    @staticmethod
    def has_all_permissions(role_str: str, permissions: List[ServicePermission]) -> bool:
        """Check if a role has all of the specified permissions"""
        user_permissions = PermissionManager.get_role_permissions(role_str)
        return all(perm in user_permissions for perm in permissions)
    
    @staticmethod
    def get_accessible_services(role_str: str) -> Dict[str, bool]:
        """Get which services a role can access"""
        permissions = PermissionManager.get_role_permissions(role_str)
        
        return {
            'portal': ServicePermission.PORTAL_ACCESS in permissions,
            'analytics': ServicePermission.ANALYTICS_VIEW in permissions,
            'data_management': ServicePermission.DATA_VIEW in permissions,
            'company_unification': ServicePermission.COMPANY_VIEW in permissions,
            'company_qr': ServicePermission.COMPANY_QR in permissions,
            'zoning': ServicePermission.ZONING_VIEW in permissions,
            'user_management': ServicePermission.USER_VIEW in permissions,
        }
    
    @staticmethod
    def get_role_display_name(role_str: str) -> str:
        """Get a display-friendly name for a role"""
        role_names = {
            'admin': 'Administrator',
            'manager': 'Manager',
            'analyst': 'Data Analyst',
            'operator': 'Operator',
            'viewer': 'Viewer'
        }
        return role_names.get(role_str.lower(), role_str.title())
    
    @staticmethod
    def get_available_roles() -> List[Dict[str, str]]:
        """Get list of available roles with descriptions"""
        return [
            {
                'value': Role.ADMIN.value,
                'name': 'Administrator',
                'description': 'Full system access, user management, all permissions'
            },
            {
                'value': Role.MANAGER.value,
                'name': 'Manager',
                'description': 'Manage data, analytics, and zones. View users.'
            },
            {
                'value': Role.ANALYST.value,
                'name': 'Data Analyst',
                'description': 'Analyze data, create zones, export reports'
            },
            {
                'value': Role.OPERATOR.value,
                'name': 'Operator',
                'description': 'Basic data operations, QR code generation'
            },
            {
                'value': Role.VIEWER.value,
                'name': 'Viewer',
                'description': 'View-only access to all services'
            }
        ]

# Global permission manager instance
permission_manager = PermissionManager() 