import os
from datetime import timedelta

class Config:
    # App Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'seva-pay-hackathon-2025'
    DEBUG = True
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///seva_pay.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Seva Pay Configuration
    QR_EXPIRY_MINUTES = 60
    COMMISSION_RATE = 2.5
    DAILY_TRANSACTION_LIMIT = 50000
    OFFLINE_STORAGE_HOURS = 72
    MAX_RETRY_ATTEMPTS = 3
    
    # Network Configuration
    NETWORK_CHECK_INTERVAL = 300  # seconds
    SYNC_TIMEOUT = 30  # seconds
    
    # Security Configuration
    ENCRYPTION_ENABLED = True
    JWT_SECRET_KEY = 'seva-pay-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # SMS Configuration (for future)
    SMS_API_KEY = os.environ.get('SMS_API_KEY')
    SMS_ENABLED = False
    
    # Supported Regions
    SUPPORTED_STATES = [
        'Uttar Pradesh', 'Haryana', 'Madhya Pradesh', 
        'Gujarat', 'Rajasthan', 'Bihar', 'Odisha'
    ]
    
    # Transaction Categories
    TRANSACTION_CATEGORIES = [
        'Electronics', 'Home & Kitchen', 'Accessories', 
        'Health', 'Home & Garden', 'Beauty', 'Fashion', 
        'Books', 'Sports', 'Groceries'
    ]

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_seva_pay.db'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
