"""
Configuration Module
====================
Manages application-wide configuration, database settings, and environment variables.

This module loads configuration from environment variables using python-dotenv
and provides a centralized configuration object for all modules.

Time Complexity: O(1) - Single-pass initialization
Space Complexity: O(1) - Constant memory usage
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Configuration class for managing application settings.
    
    Attributes:
        DB_HOST (str): Database hostname
        DB_PORT (int): Database port number
        DB_NAME (str): Database name
        DB_USER (str): Database username
        DB_PASSWORD (str): Database password
        IMPORT_DIR (str): Directory for importing data files
        EXPORT_DIR (str): Directory for exporting reports
        DEBUG (bool): Debug mode flag
        LOG_LEVEL (str): Logging level (INFO, DEBUG, ERROR, etc.)
    """
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME', 'operations_consolidation')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # Directory Configuration
    IMPORT_DIR = os.getenv('IMPORT_DIR', './data/imports')
    EXPORT_DIR = os.getenv('EXPORT_DIR', './data/exports')
    
    # Ensure directories exist
    Path(IMPORT_DIR).mkdir(parents=True, exist_ok=True)
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Application Settings
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # API Configuration
    RENDER_API_KEY = os.getenv('RENDER_API_KEY', '')
    
    # Performance Settings (for AC10 - Response time < 5 seconds)
    QUERY_TIMEOUT_SECONDS = 5
    
    # Batch Configuration
    IMPORT_BATCH_SIZE = 1000  # Process imports in batches to optimize memory
    
    @classmethod
    def get_db_connection_string(cls):
        """
        Constructs PostgreSQL connection string from configuration.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            str: PostgreSQL connection string for psycopg2
        """
        return (f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@"
                f"{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}")
    
    @classmethod
    def validate_configuration(cls):
        """
        Validates that all critical configuration parameters are set.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            tuple: (bool, str) - (is_valid, error_message)
                   Returns (True, '') if configuration is valid,
                   (False, error) otherwise
        """
        errors = []
        
        if not cls.DB_USER:
            errors.append("DB_USER environment variable not set")
        if not cls.DB_PASSWORD:
            errors.append("DB_PASSWORD environment variable not set")
        if not cls.DB_HOST:
            errors.append("DB_HOST environment variable not set")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, ""


if __name__ == '__main__':
    # Test configuration
    is_valid, error = Config.validate_configuration()
    if is_valid:
        print("✓ Configuration is valid")
        print(f"Database: {Config.DB_USER}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}")
    else:
        print(f"✗ Configuration error: {error}")
