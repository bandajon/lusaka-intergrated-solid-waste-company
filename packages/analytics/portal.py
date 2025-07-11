#!/usr/bin/env python3
"""
LISWMC Analytics Portal - Unified Entry Point
=============================================
Central portal providing single sign-on access to all analytics applications
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path for imports
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# Add shared directory to path for auth imports
shared_dir = Path(__file__).resolve().parent.parent / 'shared'
sys.path.insert(0, str(shared_dir))

# Import existing authentication system
from auth import auth_manager
from role_permissions import permission_manager, ServicePermission
from session_bridge import session_bridge
from config import AnalyticsConfig
from qr_code_service import qr_service

app = Flask(__name__, 
           template_folder='portal_templates',
           static_folder='portal_static')

# Configure app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'liswmc-portal-secret-key-2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

# Create templates directory if it doesn't exist
os.makedirs(app.template_folder, exist_ok=True)
os.makedirs(app.static_folder, exist_ok=True)

@app.before_request
def make_session_permanent():
    """Make sessions permanent with 8-hour timeout"""
    session.permanent = True

def require_login(f):
    """Decorator to require login for protected routes"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_permission(permission: ServicePermission):
    """Decorator to require specific permission"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user_role = session.get('role', 'viewer')
            if not permission_manager.has_permission(user_role, permission):
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

@app.route('/')
def index():
    """Main portal page - redirect to dashboard if logged in, otherwise show login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please provide both username and password', 'error')
            return render_template('login.html')
        
        # Authenticate user
        success, message, user_data = auth_manager.authenticate_user(username, password)
        
        if success:
            # Store user info in session
            session['user_id'] = user_data['user_id']
            session['username'] = user_data['username']
            session['full_name'] = user_data['full_name']
            session['email'] = user_data['email']
            session['role'] = user_data['role']
            session['login_time'] = datetime.now().isoformat()
            
            # Create shared session token for cross-app authentication
            session_token = session_bridge.create_session(user_data)
            session['shared_session_token'] = session_token
            
            # Get role display name
            role_display = permission_manager.get_role_display_name(user_data['role'])
            
            flash(f'Welcome back, {user_data["full_name"] or user_data["username"]}! Logged in as {role_display}.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(message, 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    username = session.get('username', 'User')
    
    # Invalidate shared session token
    shared_token = session.get('shared_session_token')
    if shared_token:
        session_bridge.invalidate_session(shared_token)
    
    session.clear()
    flash(f'Goodbye {username}! You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@require_login
def dashboard():
    """Main dashboard with links to all applications"""
    user_data = {
        'username': session.get('username'),
        'full_name': session.get('full_name'),
        'email': session.get('email'),
        'role': session.get('role'),
        'role_display': permission_manager.get_role_display_name(session.get('role', 'viewer')),
        'login_time': session.get('login_time')
    }
    
    # Get the shared session token for SSO
    shared_token = session.get('shared_session_token', '')
    
    # Get accessible services for the user's role
    user_role = session.get('role', 'viewer')
    accessible_services = permission_manager.get_accessible_services(user_role)
    
    # Define available applications with permission checks
    all_applications = [
        {
            'id': 'analytics_dashboard',
            'name': 'Analytics Dashboard',
            'description': 'Real-time waste collection analytics and visualization',
            'url': f'http://localhost:{AnalyticsConfig.DASH_PORT}',
            'icon': '📊',
            'features': [
                'Real-time data visualization',
                'Interactive charts and filters',
                'Vehicle performance tracking',
                'Location-based insights',
                'Fee calculation and reporting'
            ],
            'required_permission': ServicePermission.ANALYTICS_VIEW,
            'accessible': accessible_services.get('analytics', False)
        },
        {
            'id': 'data_management',
            'name': 'Data Management',
            'description': 'File upload, processing, and database management',
            'url': f'http://localhost:{AnalyticsConfig.FLASK_PORT}?analytics_token={shared_token}',
            'icon': '🔧',
            'features': [
                'File upload and processing',
                'Data cleaning and validation',
                'Database import/export',
                'CSV processing utilities'
            ],
            'required_permission': ServicePermission.DATA_VIEW,
            'accessible': accessible_services.get('data_management', False)
        },
        {
            'id': 'company_unification',
            'name': 'Company Unification',
            'description': 'Identify and merge duplicate company entries',
            'url': f'http://localhost:{AnalyticsConfig.FLASK_PORT}/companies/unify?analytics_token={shared_token}',
            'icon': '🏢',
            'features': [
                'Duplicate company detection',
                'Smart similarity matching',
                'Database cascading merges',
                'Billing accuracy improvement'
            ],
            'required_permission': ServicePermission.COMPANY_UNIFY,
            'accessible': permission_manager.has_permission(user_role, ServicePermission.COMPANY_UNIFY)
        },
        {
            'id': 'zoning_service',
            'name': 'Zoning Service',
            'description': 'Geographic zone management and GIS analytics',
            'url': f'http://localhost:5001/auth/sso?analytics_token={shared_token}',
            'icon': '🗺️',
            'features': [
                'Geographic zone management',
                'Population and demographics analysis',
                'Waste collection optimization',
                'GIS analytics and reporting',
                'Google Earth Engine integration'
            ],
            'required_permission': ServicePermission.ZONING_VIEW,
            'accessible': accessible_services.get('zoning', False)
        },
        {
            'id': 'company_qr_codes',
            'name': 'Company QR Codes',
            'description': 'Generate and email QR codes for companies',
            'url': '/company-qr-codes',
            'icon': '📱',
            'features': [
                'Company lookup and search',
                'QR code generation',
                'Email delivery to companies',
                'Digital company identification'
            ],
            'required_permission': ServicePermission.COMPANY_QR,
            'accessible': permission_manager.has_permission(user_role, ServicePermission.COMPANY_QR)
        },
        {
            'id': 'user_management',
            'name': 'User Management',
            'description': 'Manage users, roles, and permissions',
            'url': '/admin/users',
            'icon': '👥',
            'features': [
                'User account management',
                'Role and permission control',
                'Account security monitoring',
                'Activity logging'
            ],
            'required_permission': ServicePermission.USER_VIEW,
            'accessible': accessible_services.get('user_management', False)
        }
    ]
    
    # Filter applications based on accessibility
    applications = [app for app in all_applications if app['accessible']]
    
    # Get permission summary for the user
    permissions_summary = {
        'total_services': len(all_applications),
        'accessible_services': len(applications),
        'can_manage_users': permission_manager.has_permission(user_role, ServicePermission.USER_CREATE),
        'can_export_data': permission_manager.has_permission(user_role, ServicePermission.DATA_EXPORT),
        'can_manage_zones': permission_manager.has_permission(user_role, ServicePermission.ZONING_CREATE),
    }
    
    return render_template('dashboard.html', 
                         user=user_data, 
                         applications=applications,
                         permissions_summary=permissions_summary,
                         config=AnalyticsConfig)

@app.route('/profile')
@require_login
def profile():
    """User profile page"""
    user_data = {
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'full_name': session.get('full_name'),
        'email': session.get('email'),
        'role': session.get('role'),
        'role_display': permission_manager.get_role_display_name(session.get('role', 'viewer')),
        'login_time': session.get('login_time')
    }
    
    # Get additional user details from database
    detailed_user = auth_manager.get_user_by_id(user_data['user_id'])
    if detailed_user:
        user_data.update(detailed_user)
    
    # Get user permissions
    user_role = session.get('role', 'viewer')
    user_permissions = permission_manager.get_role_permissions(user_role)
    accessible_services = permission_manager.get_accessible_services(user_role)
    
    return render_template('profile.html', 
                         user=user_data,
                         permissions=user_permissions,
                         accessible_services=accessible_services)

@app.route('/admin/users')
@require_permission(ServicePermission.USER_VIEW)
def admin_users():
    """Admin page for user management"""
    users = auth_manager.list_users()
    available_roles = permission_manager.get_available_roles()
    
    # Check if user can create/edit users
    user_role = session.get('role', 'viewer')
    can_create = permission_manager.has_permission(user_role, ServicePermission.USER_CREATE)
    can_edit = permission_manager.has_permission(user_role, ServicePermission.USER_EDIT)
    can_delete = permission_manager.has_permission(user_role, ServicePermission.USER_DELETE)
    
    return render_template('admin_users.html', 
                         users=users,
                         available_roles=available_roles,
                         can_create=can_create,
                         can_edit=can_edit,
                         can_delete=can_delete)

@app.route('/admin/create_user', methods=['POST'])
@require_permission(ServicePermission.USER_CREATE)
def admin_create_user():
    """Create a new user (requires USER_CREATE permission)"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    role = request.form.get('role', 'viewer')
    
    if not username or not password:
        flash('Username and password are required', 'error')
        return redirect(url_for('admin_users'))
    
    # Validate role
    valid_roles = [r['value'] for r in permission_manager.get_available_roles()]
    if role not in valid_roles:
        flash('Invalid role selected', 'error')
        return redirect(url_for('admin_users'))
    
    success, message = auth_manager.create_user(username, password, full_name, email, role)
    
    if success:
        flash(f'User {username} created successfully with role: {permission_manager.get_role_display_name(role)}', 'success')
    else:
        flash(f'Error creating user: {message}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/api/status')
def api_status():
    """API endpoint to check service status"""
    services = {
        'portal': {'status': 'running', 'port': AnalyticsConfig.PORTAL_PORT},
        'dashboard': {'status': 'unknown', 'port': AnalyticsConfig.DASH_PORT},
        'flask_app': {'status': 'unknown', 'port': AnalyticsConfig.FLASK_PORT},
        'zoning': {'status': 'unknown', 'port': 5001}
    }
    
    return jsonify({
        'status': 'ok',
        'services': services,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/check_session')
def check_session():
    """API endpoint to check if user has valid session (for cross-app auth)"""
    token = request.args.get('token') or request.headers.get('X-Session-Token')
    
    if not token:
        return jsonify({'authenticated': False, 'message': 'No session token provided'})
    
    user_data = session_bridge.get_session(token)
    if user_data:
        return jsonify({
            'authenticated': True,
            'user': {
                'username': user_data.get('username'),
                'full_name': user_data.get('full_name'),
                'role': user_data.get('role'),
                'email': user_data.get('email')
            }
        })
    else:
        return jsonify({'authenticated': False, 'message': 'Invalid or expired session'})

@app.route('/change_password', methods=['POST'])
@require_login
def change_password():
    """Change user password"""
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not all([old_password, new_password, confirm_password]):
        flash('All password fields are required', 'error')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('profile'))
    
    if len(new_password) < 6:
        flash('New password must be at least 6 characters long', 'error')
        return redirect(url_for('profile'))
    
    success, message = auth_manager.change_password(
        session['user_id'], old_password, new_password
    )
    
    if success:
        flash('Password changed successfully', 'success')
    else:
        flash(f'Error changing password: {message}', 'error')
    
    return redirect(url_for('profile'))

@app.route('/company-qr-codes')
@require_permission(ServicePermission.COMPANY_QR)
def company_qr_codes():
    """Company QR codes page"""
    search_term = request.args.get('search', '')
    companies = qr_service.get_companies(search_term if search_term else None)
    
    return render_template('company_qr_codes.html', 
                         companies=companies, 
                         search_term=search_term)

@app.route('/api/generate-qr-code', methods=['POST'])
@require_permission(ServicePermission.COMPANY_QR)
def generate_qr_code():
    """Generate QR code for a company"""
    try:
        company_id = request.form.get('company_id')
        if not company_id:
            return jsonify({'success': False, 'error': 'Company ID is required'})
        
        company_data = qr_service.get_company_by_id(company_id)
        if not company_data:
            return jsonify({'success': False, 'error': 'Company not found'})
        
        qr_result = qr_service.generate_qr_code(company_data)
        
        if qr_result['success']:
            return jsonify({
                'success': True,
                'qr_code': qr_result['qr_code_base64'],
                'company_name': company_data['company_name']
            })
        else:
            return jsonify({'success': False, 'error': qr_result['error']})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/email-qr-code', methods=['POST'])
@require_permission(ServicePermission.COMPANY_QR)
def email_qr_code():
    """Email QR code to company"""
    try:
        company_id = request.form.get('company_id')
        if not company_id:
            return jsonify({'success': False, 'error': 'Company ID is required'})
        
        company_data = qr_service.get_company_by_id(company_id)
        if not company_data:
            return jsonify({'success': False, 'error': 'Company not found'})
        
        qr_result = qr_service.generate_qr_code(company_data)
        if not qr_result['success']:
            return jsonify({'success': False, 'error': qr_result['error']})
        
        email_result = qr_service.send_qr_code_email(company_data, qr_result)
        
        return jsonify(email_result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.context_processor
def inject_globals():
    """Inject global variables into templates"""
    return {
        'now': datetime.now(),
        'config': AnalyticsConfig,
        'user': {
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'role': session.get('role'),
            'role_display': permission_manager.get_role_display_name(session.get('role', 'viewer'))
        } if 'user_id' in session else None,
        'permission_manager': permission_manager,
        'ServicePermission': ServicePermission
    }

if __name__ == '__main__':
    print("🚀 Starting LISWMC Analytics Portal...")
    print("=" * 50)
    print(f"🌐 Portal available at: {AnalyticsConfig.get_portal_url()}")
    print(f"📊 Analytics Dashboard: {AnalyticsConfig.get_dash_url()}")
    print(f"🔧 Data Management: {AnalyticsConfig.get_flask_url()}")
    print(f"🗺️  Zoning Service: http://localhost:5001")
    print("=" * 50)
    print("\n📋 Available Roles:")
    for role in permission_manager.get_available_roles():
        print(f"   • {role['name']}: {role['description']}")
    print("=" * 50)
    
    app.run(
        debug=True, 
        host=AnalyticsConfig.PORTAL_HOST, 
        port=AnalyticsConfig.PORTAL_PORT
    )