from datetime import datetime
from flask_login import UserMixin
from app import db, bcrypt
from sqlalchemy import Enum
import enum


class RoleEnum(enum.Enum):
    ADMIN = "admin"
    PLANNER = "planner"
    VIEW_ONLY = "view_only"


class User(UserMixin, db.Model):
    """User model with role-based access control"""
    __tablename__ = 'zoning_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(Enum(RoleEnum), nullable=False, default=RoleEnum.VIEW_ONLY)
    
    # Profile information
    full_name = db.Column(db.String(120))
    department = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    zones_created = db.relationship('Zone', backref='creator', lazy='dynamic',
                                  foreign_keys='Zone.created_by')
    zones_modified = db.relationship('Zone', backref='modifier', lazy='dynamic',
                                   foreign_keys='Zone.modified_by')
    csv_imports = db.relationship('CSVImport', backref='uploader', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check if password matches hash"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        """Check if user has a specific role"""
        if isinstance(role, str):
            return self.role == RoleEnum[role.upper()]
        return self.role == role
    
    def can_edit_zones(self):
        """Check if user can edit zones"""
        return self.role in [RoleEnum.ADMIN, RoleEnum.PLANNER]
    
    def can_delete_zones(self):
        """Check if user can delete zones"""
        return self.role == RoleEnum.ADMIN
    
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role == RoleEnum.ADMIN
    
    def __repr__(self):
        return f'<User {self.username} ({self.role.value})>'


class Role(db.Model):
    """Additional role permissions table for fine-grained control"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Permissions
    can_create_zones = db.Column(db.Boolean, default=False)
    can_edit_zones = db.Column(db.Boolean, default=False)
    can_delete_zones = db.Column(db.Boolean, default=False)
    can_upload_csv = db.Column(db.Boolean, default=False)
    can_export_data = db.Column(db.Boolean, default=True)
    can_run_analysis = db.Column(db.Boolean, default=True)
    can_manage_users = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Role {self.name}>'