from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from app.models import User, RoleEnum
from app.forms import LoginForm, RegistrationForm, ChangePasswordForm
import requests

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Auto-login in development mode if requested
    if request.args.get('auto') == 'true' and request.environ.get('FLASK_ENV') == 'development':
        admin = User.query.filter_by(username='admin').first()
        if admin:
            login_user(admin, remember=True)
            admin.last_login = datetime.utcnow()
            db.session.commit()
            flash(f'Auto-logged in as {admin.full_name or admin.username}', 'success')
            return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        
        flash(f'Welcome back, {user.full_name or user.username}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register new user (admin only)"""
    if not current_user.has_role('ADMIN'):
        flash('You do not have permission to register new users.', 'danger')
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            department=form.department.data,
            phone=form.phone.data,
            role=RoleEnum(form.role.data)
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {user.username} has been registered successfully!', 'success')
        return redirect(url_for('main.users'))
    
    return render_template('auth/register.html', title='Register User', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change current user's password"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Your password has been changed successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('auth/change_password.html', 
                         title='Change Password', form=form)


@auth_bp.route('/sso')
def sso():
    """Single Sign-On from analytics portal"""
    analytics_token = request.args.get('analytics_token')
    redirect_url = request.args.get('redirect', url_for('main.index'))
    
    if not analytics_token:
        flash('Invalid SSO request. Please log in directly.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Validate token with analytics portal
        response = requests.get(
            'http://localhost:5000/api/check_session',
            params={'token': analytics_token},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('authenticated'):
                user_data = data.get('user', {})
                
                # Map analytics role to zoning role
                role_mapping = {
                    'admin': RoleEnum.ADMIN,
                    'user': RoleEnum.PLANNER,
                    'viewer': RoleEnum.VIEW_ONLY
                }
                zoning_role = role_mapping.get(user_data.get('role', 'viewer'), RoleEnum.VIEW_ONLY)
                
                # Find or create user in zoning service
                user = User.query.filter_by(username=user_data.get('username')).first()
                
                if not user:
                    # Create new user from analytics data
                    user = User(
                        username=user_data.get('username'),
                        email=user_data.get('email', f"{user_data.get('username')}@liswmc.local"),
                        full_name=user_data.get('full_name', user_data.get('username')),
                        role=zoning_role,
                        is_external_auth=True
                    )
                    # Set a dummy password for external auth users
                    user.set_password('external_auth_' + user_data.get('username', 'unknown'))
                    db.session.add(user)
                    db.session.commit()
                else:
                    # Update existing user's role and info
                    user.role = zoning_role
                    user.full_name = user_data.get('full_name', user.full_name)
                    user.email = user_data.get('email', user.email)
                    user.is_external_auth = True
                    user.last_login = datetime.utcnow()
                    db.session.commit()
                
                # Log in the user
                login_user(user, remember=True)
                
                # Store analytics session info
                session['analytics_token'] = analytics_token
                session['analytics_auth'] = True
                
                flash(f'Welcome {user.full_name or user.username}!', 'success')
                return redirect(redirect_url)
        
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        print(f"SSO authentication error: {e}")
        flash('Authentication service unavailable. Please try again later.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """View current user profile"""
    return render_template('auth/profile.html', title='My Profile')