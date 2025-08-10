"""
Database module for con_mon_v2.

Provides both PostgreSQL and CSV database implementations with singleton patterns.
"""

import os
from .pgs import PostgreSQLDatabase, get_db as get_pgs_db
from .csv import CSVDatabase, get_db as get_csv_db

def get_db(*args, **kwargs):
    """
    Get database instance based on environment configuration.
    
    Returns CSV database by default, PostgreSQL if DB_USE_POSTGRES=true
    """
    use_postgres = os.getenv('DB_USE_POSTGRES', 'false').lower() == 'true'
    
    if use_postgres:
        return get_pgs_db(*args, **kwargs)
    else:
        return get_csv_db(*args, **kwargs)

__all__ = [
    # PostgreSQL Database
    'PostgreSQLDatabase',
    # CSV Database  
    'CSVDatabase',
    # Database Function
    'get_db',
]
