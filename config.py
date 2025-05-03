import os

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:Sashank123@localhost/testdb')
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:password123@10.2.8.12/lc4u')
    SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,          # Maintain 20 connections in the pool
    "max_overflow": 10,       # Allow up to 10 extra connections
    "pool_timeout": 30,       # Wait 30 seconds before timeout
    "pool_recycle": 1800      # Recycle connections every 30 minutes
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-very-secret-key')
    
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'tat.iiith2025@gmail.com'
    MAIL_PASSWORD = 'noal fndb ucip aiui'
    MAIL_DEFAULT_SENDER = 'tat.iiith2025@gmail.com'

    

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
