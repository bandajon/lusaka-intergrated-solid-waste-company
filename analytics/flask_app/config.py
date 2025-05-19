import os
import secrets

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    
    # Database config (using existing DB params)
    DB_HOST = 'agripredict-prime-prod.caraj6fzskso.eu-west-2.rds.amazonaws.com'
    DB_NAME = 'users'
    DB_USER = 'agripredict'
    DB_PASS = 'Wee8fdm0k2!!'
    DB_PORT = 5432
