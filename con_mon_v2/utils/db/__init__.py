"""
Database module for con_mon_v2.

Provides both PostgreSQL and CSV database implementations with singleton patterns.
"""

from .pgs import PostgreSQLDatabase, get_db as get_pgs_db
from .csv import CSVDatabase, get_db as get_csv_db

def get_db(*args, **kwargs):
    return get_csv_db(*args, **kwargs)
    return get_pgs_db(*args, **kwargs)

__all__ = [
    # PostgreSQL Database
    'PostgreSQLDatabase',
    'get_db',
    # CSV Database  
    'CSVDatabase',
    'get_csv_db'
]
