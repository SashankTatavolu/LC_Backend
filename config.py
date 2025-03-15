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
    
    SMTP_SERVER = 'smtp.gmail.com'  # e.g., Gmail SMTP server
    SMTP_PORT = 587  # SMTP port for STARTTLS
    SENDER_EMAIL = 'swethapoppoppu@gmail.com'
    SENDER_PASSWORD = 'ufec wkhp syss ynqa'  # Make sure this is securely handled


    

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
