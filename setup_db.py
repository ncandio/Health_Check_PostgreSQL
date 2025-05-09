#!/usr/bin/env python3
"""
Script to initialize the PostgreSQL database for the website monitor.
This script creates the database if it doesn't exist and sets up the required schema.
"""

import json
import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Read the config file
def load_config(config_path="config.json"):
    with open(config_path, "r") as f:
        return json.load(f)

def main():
    # Load configuration
    config = load_config()
    db_config = config.get("database", {})
    
    # Connection parameters for the default PostgreSQL database
    admin_conn_params = {
        "host": db_config.get("host", "localhost"),
        "port": db_config.get("port", 5432),
        "user": db_config.get("user", "postgres"),
        "password": db_config.get("password", "postgres"),
        "dbname": "postgres"  # Connect to the default postgres database first
    }
    
    target_dbname = db_config.get("dbname", "website_monitor")
    
    # Create the database if it doesn't exist
    try:
        # Connect to the default postgres database
        admin_conn = psycopg2.connect(**admin_conn_params)
        admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        with admin_conn.cursor() as cursor:
            # Check if the database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (target_dbname,)
            )
            database_exists = cursor.fetchone()
            
            if not database_exists:
                print(f"Creating database '{target_dbname}'...")
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(target_dbname)
                    )
                )
                print(f"Database '{target_dbname}' created successfully.")
            else:
                print(f"Database '{target_dbname}' already exists.")
                
        admin_conn.close()
        
        # Now connect to the target database and create the schema
        db_conn_params = admin_conn_params.copy()
        db_conn_params["dbname"] = target_dbname
        
        db_conn = psycopg2.connect(**db_conn_params)
        db_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Read the schema.sql file
        schema_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "schema.sql"
        )
        
        with open(schema_path, "r") as f:
            schema_sql = f.read()
            
        with db_conn.cursor() as cursor:
            print("Creating database schema...")
            cursor.execute(schema_sql)
            print("Database schema created successfully.")
            
        db_conn.close()
        
        print("Database setup completed successfully.")
        return 0
        
    except Exception as e:
        print(f"Error setting up the database: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())