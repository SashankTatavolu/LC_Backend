import os
import secrets

class Config:
    # Flask SECRET_KEY - Critical for token generation and session management
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:Sashank123@localhost/testdb')
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:password123@10.2.8.12/lc4u')
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:password123@10.2.8.12/testdb_concept_dictionary_cleaner')
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 60,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-very-secret-key')
    
    # Mail configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'tat.iiith2025@gmail.com'
    MAIL_PASSWORD = 'noal fndb ucip aiui'
    MAIL_DEFAULT_SENDER = 'tat.iiith2025@gmail.com'

class DevelopmentConfig(Config):
    DEBUG = True
    # You can override the SECRET_KEY for development if needed
    # SECRET_KEY = 'dev-secret-key'

class ProductionConfig(Config):
    DEBUG = False
    # For production, always use environment variable
    SECRET_KEY = os.getenv('SECRET_KEY')  # No default for security
    
    # Ensure this raises an error if not set
    if not SECRET_KEY:
        import warnings
        warnings.warn("SECRET_KEY is not set in production environment!")