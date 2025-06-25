from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from config.config import config
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cors = CORS()
bcrypt = Bcrypt()

# WebSocket related (will be initialized in create_app)
socketio = None
websocket_manager = None


def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cors.init_app(app)
    bcrypt.init_app(app)
    
    # Initialize WebSocket support
    from app.utils.websocket_integration import init_websocket
    global socketio, websocket_manager
    socketio, websocket_manager = init_websocket(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Configure user loader
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.views import auth_bp, main_bp, zones_bp, api_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(zones_bp, url_prefix='/zones')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Template context processor to make config available in templates
    @app.context_processor
    def inject_config():
        return dict(config=app.config)
    
    # Create upload directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CSV_TEMP_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CSV_PROCESSED_FOLDER'], exist_ok=True)
    
    return app

# Export for use in other modules
__all__ = ['create_app', 'db', 'socketio', 'websocket_manager']