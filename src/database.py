"""
Database handling module for the website monitor.
Uses raw SQL queries as per requirements.
"""

import json
import logging
import os
# Set up path for imports
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2 import pool
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Get logger from monitor.py's configuration
from src.monitor import logger


class DatabaseManager:
    """Manages database connections and operations using connection pooling."""

    def __init__(self, db_config: Dict[str, Any]):
        """Initialize the database connection pool.

        Args:
            db_config: Dictionary containing database connection parameters
        """
        try:
            # Log connection attempt with masked credentials
            safe_config = db_config.copy()
            if "password" in safe_config:
                safe_config["password"] = "***MASKED***"
            logger.info(
                f"\033[94mInitializing database connection pool with config: {json.dumps(safe_config)}\033[0m"
            )

            # Set defaults for connection parameters
            host = db_config.get("host", "localhost")
            port = db_config.get("port", 5432)
            dbname = db_config.get("dbname", "sitesentinel")
            user = db_config.get("user", "postgres")
            password = db_config.get("password", "")
            sslmode = db_config.get("sslmode", "prefer")

            # Check if database exists, create if it doesn't
            self._ensure_database_exists(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=dbname,
                sslmode=sslmode,
            )

            # Create the connection pool
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
                sslmode=sslmode,
            )

            # Check and update schema if needed
            self._ensure_schema()

            logger.info(
                f"\033[92mDatabase connection pool initialized successfully\033[0m"
            )
        except psycopg2.Error as e:
            logger.error(
                f"\033[91mFailed to initialize database connection pool: {e}\033[0m"
            )
            logger.error(
                f"\033[91mMake sure PostgreSQL is running and the credentials in config.json are correct.\033[0m"
            )
            logger.error(
                f"\033[91mYou can also run setup_db.py to initialize the database.\033[0m"
            )
            raise

    def _ensure_database_exists(
        self, host: str, port: int, user: str, password: str, dbname: str, sslmode: str
    ):
        """Check if the database exists and create it if it doesn't.
        
        Args:
            host: Database host
            port: Database port
            user: Database user
            password: Database password
            dbname: Database name
            sslmode: SSL mode for connection
        """
        try:
            # Connect to the default postgres database
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname="postgres",  # Connect to the default postgres database
                sslmode=sslmode,
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            with conn.cursor() as cursor:
                # Check if the database exists
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (dbname,)
                )
                database_exists = cursor.fetchone()
                
                if not database_exists:
                    logger.info(f"\033[94mCreating database '{dbname}'...\033[0m")
                    cursor.execute(f"CREATE DATABASE {dbname}")
                    logger.info(f"\033[92mDatabase '{dbname}' created successfully\033[0m")
                else:
                    logger.info(f"\033[94mDatabase '{dbname}' already exists\033[0m")
            
            conn.close()
            
            # Connect to the created database and initialize schema
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=dbname,
                sslmode=sslmode,
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            with conn.cursor() as cursor:
                # Read the schema.sql file
                schema_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "schema.sql"
                )
                
                if os.path.exists(schema_path):
                    with open(schema_path, "r") as f:
                        schema_sql = f.read()
                        
                    logger.info(f"\033[94mInitializing database schema...\033[0m")
                    # Split into individual statements to avoid error with existing trigger
                    statements = []
                    current_statement = ""
                    in_dollar_quote = False
                    dollar_quote_tag = ""
                    
                    for line in schema_sql.split('\n'):
                        # Check for beginning or end of dollar-quoted string
                        if not in_dollar_quote:
                            # Look for dollar quote start
                            if '$$' in line:
                                in_dollar_quote = True
                                dollar_quote_tag = '$$'
                                current_statement += line + '\n'
                                continue
                        else:
                            # Look for matching dollar quote end
                            if dollar_quote_tag in line:
                                in_dollar_quote = False
                                dollar_quote_tag = ""
                            current_statement += line + '\n'
                            continue
                        
                        # Handle normal line
                        if ';' in line and not in_dollar_quote:
                            # Found statement end
                            current_statement += line
                            statements.append(current_statement)
                            current_statement = ""
                        else:
                            current_statement += line + '\n'
                    
                    # Add the last statement if any
                    if current_statement.strip():
                        statements.append(current_statement)
                    
                    # Execute each statement
                    for statement in statements:
                        if statement.strip():
                            try:
                                cursor.execute(statement)
                            except Exception as exec_err:
                                logger.warning(f"Statement execution error (continuing): {exec_err}")
                    logger.info(f"\033[92mDatabase schema initialized successfully\033[0m")
                else:
                    logger.warning(f"\033[93mSchema file not found at {schema_path}\033[0m")
            
            conn.close()
        except Exception as e:
            logger.error(f"\033[91mError ensuring database exists: {e}\033[0m")
            # Let the application try to continue, as the tables might already exist

    def _ensure_schema(self):
        """Check if monitoring_results table has necessary columns and add them if missing."""
        try:
            # Check if required columns exist
            columns_to_check = [
                "check_details",
                "content_size_bytes",
                "dns_lookup_time_ms",
            ]
            for column in columns_to_check:
                check_query = f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'monitoring_results' AND column_name = '{column}';
                """
                result = self.execute_query(check_query, fetch=True)

                if not result:
                    # Add missing column
                    logger.info(
                        f"Adding missing {column} column to monitoring_results table"
                    )

                    if column == "check_details":
                        alter_query = """
                            ALTER TABLE monitoring_results ADD COLUMN IF NOT EXISTS check_details JSONB;
                        """
                    elif column == "content_size_bytes":
                        alter_query = """
                            ALTER TABLE monitoring_results ADD COLUMN IF NOT EXISTS content_size_bytes INTEGER;
                        """
                    elif column == "dns_lookup_time_ms":
                        alter_query = """
                            ALTER TABLE monitoring_results ADD COLUMN IF NOT EXISTS dns_lookup_time_ms FLOAT;
                        """

                    self.execute_query(alter_query)
                    logger.info(
                        f"\033[92mAdded {column} column to monitoring_results table\033[0m"
                    )
        except Exception as e:
            logger.error(f"\033[91mError ensuring schema: {e}\033[0m")
            # Don't raise the exception - let the application try to continue

    def _get_connection(self):
        """Get a connection from the pool."""
        conn = self.connection_pool.getconn()
        return conn

    def _release_connection(self, conn):
        """Return a connection to the pool."""
        self.connection_pool.putconn(conn)

    def execute_query(
        self, query: str, params: Optional[Tuple] = None, fetch: bool = False
    ):
        """Execute a SQL query with optional parameters.

        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results

        Returns:
            Query results if fetch=True, otherwise None
        """
        conn = None
        query_start_time = time.time()

        # Skip all query logging

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params)

                # Skip query time logging

                if fetch:
                    result = cursor.fetchall()
                    # Skip row count logging
                    conn.commit()
                    return result

                # Skip affected row count logging
                conn.commit()
                return None

        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            # Define log_query and log_params before using them in the error message
            log_query = query
            log_params = params
            logger.error(
                f"\033[91mDatabase error: {e}\nQuery: {log_query}\nParams: {log_params}\033[0m"
            )
            raise
        finally:
            if conn:
                self._release_connection(conn)

    def get_website_configs(self) -> List[Dict[str, Any]]:
        """Get all active website configurations.

        Returns:
            List of website configuration dictionaries
        """
        query = """
            SELECT id, url, check_interval_seconds, regex_pattern
            FROM website_configs
            WHERE is_active = TRUE
        """
        try:
            logger.info("\033[94mRetrieving all active website configurations\033[0m")
            result = self.execute_query(query, fetch=True)
            configs = [
                {
                    "id": row[0],
                    "url": row[1],
                    "check_interval_seconds": row[2],
                    "regex_pattern": row[3],
                }
                for row in result
            ]
            logger.info(
                f"\033[92mRetrieved {len(configs)} active website configurations\033[0m"
            )
            return configs
        except Exception as e:
            logger.error(f"\033[91mFailed to get website configurations: {e}\033[0m")
            return []

    def add_website_config(
        self, url: str, check_interval_seconds: int, regex_pattern: Optional[str] = None
    ) -> int:
        """Add a new website configuration.

        Args:
            url: Website URL
            check_interval_seconds: Check interval in seconds (5-300)
            regex_pattern: Optional regex pattern to check for

        Returns:
            ID of the newly created configuration
        """
        query = """
            INSERT INTO website_configs (url, check_interval_seconds, regex_pattern)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        params = (url, check_interval_seconds, regex_pattern)
        try:
            # Print a highly visible message when adding a new website
            print(
                f"\033[97;45m ADDING WEBSITE \033[0m \033[1;95m{url}\033[0m \033[0;96mCheck interval: {check_interval_seconds}s\033[0m"
            )
            result = self.execute_query(query, params, fetch=True)
            website_id = result[0][0]
            return website_id
        except Exception as e:
            logger.error(
                f"\033[91mFailed to add website configuration for {url}: {e}\033[0m"
            )
            raise

    def store_monitoring_result(
        self,
        website_id: int,
        response_time_ms: Optional[float],
        http_status: Optional[int],
        success: bool,
        regex_matched: Optional[bool] = None,
        failure_reason: Optional[str] = None,
        check_details: Optional[Dict[str, Any]] = None,
        content_size_bytes: Optional[int] = None,
        dns_lookup_time_ms: Optional[float] = None,
    ) -> int:
        """Store a website monitoring result.

        Args:
            website_id: ID of the monitored website
            response_time_ms: Response time in milliseconds
            http_status: HTTP status code
            success: Whether the check was successful
            regex_matched: Whether the regex pattern matched
            failure_reason: Reason for failure if check failed
            check_details: Additional check details (JSON serializable)
            content_size_bytes: Size of the response content in bytes
            dns_lookup_time_ms: DNS lookup time in milliseconds

        Returns:
            ID of the newly created monitoring result
        """
        # Add monitoring timestamp for real-time tracking
        timestamp = datetime.now()

        try:
            # First try to insert with check_details
            if check_details:
                try:
                    # Convert check_details to JSON if provided
                    check_details_json = json.dumps(check_details)

                    # Extract performance metrics if they exist in check_details
                    if (
                        content_size_bytes is None
                        and "content_size_bytes" in check_details
                    ):
                        content_size_bytes = check_details.get("content_size_bytes")

                    if (
                        dns_lookup_time_ms is None
                        and "dns_lookup_time_ms" in check_details
                    ):
                        dns_lookup_time_ms = check_details.get("dns_lookup_time_ms")

                    query = """
                        INSERT INTO monitoring_results
                        (website_id, response_time_ms, http_status, success, regex_matched, 
                        failure_reason, checked_at, check_details, content_size_bytes, dns_lookup_time_ms)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """
                    params = (
                        website_id,
                        response_time_ms,
                        http_status,
                        success,
                        regex_matched,
                        failure_reason,
                        timestamp,
                        check_details_json,
                        content_size_bytes,
                        dns_lookup_time_ms,
                    )

                    result = self.execute_query(query, params, fetch=True)
                    result_id = result[0][0]
                    return result_id
                except Exception as e:
                    # If it fails, try without check_details
                    if "column" in str(e) and "check_details" in str(e):
                        logger.warning(
                            "Unable to store check_details, falling back to basic insert"
                        )
                    else:
                        # If it's not a column error, reraise
                        raise

            # Extract performance metrics if they exist in check_details
            if (
                content_size_bytes is None
                and check_details
                and "content_size_bytes" in check_details
            ):
                content_size_bytes = check_details.get("content_size_bytes")

            if (
                dns_lookup_time_ms is None
                and check_details
                and "dns_lookup_time_ms" in check_details
            ):
                dns_lookup_time_ms = check_details.get("dns_lookup_time_ms")

            # Fallback query with performance metrics but without check_details
            query = """
                INSERT INTO monitoring_results
                (website_id, response_time_ms, http_status, success, regex_matched, 
                failure_reason, checked_at, content_size_bytes, dns_lookup_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            params = (
                website_id,
                response_time_ms,
                http_status,
                success,
                regex_matched,
                failure_reason,
                timestamp,
                content_size_bytes,
                dns_lookup_time_ms,
            )

            result = self.execute_query(query, params, fetch=True)
            result_id = result[0][0]
            return result_id
        except Exception as e:
            logger.error(
                f"\033[91mFailed to store monitoring result for website {website_id}: {e}\033[0m"
            )
            # Don't raise the exception - instead return None so monitoring can continue
            return None

    def get_recent_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent monitoring results with website URLs.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of monitoring result dictionaries with website URLs
        """
        query = """
            SELECT mr.id, wc.url, mr.response_time_ms, mr.http_status, 
                   mr.success, mr.regex_matched, mr.failure_reason, mr.created_at
            FROM monitoring_results mr
            JOIN website_configs wc ON mr.website_id = wc.id
            ORDER BY mr.created_at DESC
            LIMIT %s
        """
        try:
            logger.info(
                f"\033[94mRetrieving {limit} most recent monitoring results\033[0m"
            )
            result = self.execute_query(query, (limit,), fetch=True)
            results = [
                {
                    "id": row[0],
                    "url": row[1],
                    "response_time_ms": row[2],
                    "http_status": row[3],
                    "success": row[4],
                    "regex_matched": row[5],
                    "failure_reason": row[6],
                    "timestamp": (
                        row[7].strftime("%Y-%m-%d %H:%M:%S") if row[7] else None
                    ),
                }
                for row in result
            ]
            logger.info(
                f"\033[92mRetrieved {len(results)} recent monitoring results\033[0m"
            )
            return results
        except Exception as e:
            logger.error(f"\033[91mFailed to get recent monitoring results: {e}\033[0m")
            return []

    def close(self):
        """Close the connection pool."""
        if hasattr(self, "connection_pool"):
            self.connection_pool.closeall()
            logger.info("\033[92mDatabase connection pool closed\033[0m")
