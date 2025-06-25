from .auth import auth_bp
from .main import main_bp
from .zones import zones_bp
from .api import api_bp

__all__ = ['auth_bp', 'main_bp', 'zones_bp', 'api_bp']