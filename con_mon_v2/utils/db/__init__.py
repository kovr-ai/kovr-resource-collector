"""
Database module for con_mon_v2.

Provides both PostgreSQL and CSV database implementations with singleton patterns.
"""

from con_mon_v2.utils.config import settings
from .pgs import PostgreSQLDatabase, get_db as get_pgs_db
from .csv import CSVDatabase, get_db as get_csv_db

def get_db(*args, **kwargs):
    """
    Get database instance based on environment configuration.
    
    Returns CSV database by default, PostgreSQL if DB_USE_POSTGRES=true
    """
    use_csv = bool(settings.CSV_DATA)

    if use_csv:
        return get_csv_db()
    else:
        return get_pgs_db()

__all__ = [
    # PostgreSQL Database
    'PostgreSQLDatabase',
    # CSV Database  
    'CSVDatabase',
    # Database Function
    'get_db',
]
