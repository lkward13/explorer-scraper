"""
Database configuration management.
"""
import os

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'flight_deals'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

def get_connection_string():
    """Returns PostgreSQL connection string from environment variables."""
    return (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?connect_timeout=5"  # 5-second connection timeout
    )

def get_connection_params():
    """Returns connection parameters as a dict for psycopg2.connect()."""
    return DB_CONFIG.copy()

