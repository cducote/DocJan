"""
PostgreSQL versioning operations for DocJanitor.
"""
import os
import json
import subprocess


def backup_database(pg_database, output_file="backup.sql"):
    """
    Create a backup of the PostgreSQL database
    
    Args:
        pg_database (str): Database name
        output_file (str): Output file name
        
    Returns:
        bool: Success or failure
    """
    try:
        # Run pg_dump command
        cmd = ["pg_dump", "-c", "-U", "postgres", "-d", pg_database, "-f", output_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Database backup failed: {result.stderr}")
            return False
        
        print(f"Database backed up to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error backing up database: {str(e)}")
        return False


def restore_database(pg_database, input_file="backup.sql"):
    """
    Restore a PostgreSQL database from backup
    
    Args:
        pg_database (str): Database name
        input_file (str): Input file name
        
    Returns:
        bool: Success or failure
    """
    try:
        # Check if backup file exists
        if not os.path.exists(input_file):
            print(f"Backup file {input_file} not found")
            return False
        
        # Run psql command
        cmd = ["psql", "-U", "postgres", "-d", pg_database, "-f", input_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Database restore failed: {result.stderr}")
            return False
        
        print(f"Database restored from {input_file}")
        return True
    
    except Exception as e:
        print(f"Error restoring database: {str(e)}")
        return False
