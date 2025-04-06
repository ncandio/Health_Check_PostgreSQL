"""
Database handling module for the website monitor.
Uses raw SQL queries as per requirements.
"""

import logging
import psycopg2
from psycopg2 import pool
from typing import Dict, List, Optional, Tuple, Any
import time
import json
from datetime import datetime

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
            if 'password' in safe_config:
                safe_config['password'] = '***MASKED***'
            logger.info(f"\033[94mInitializing database connection pool with config: {json.dumps(safe_config)}\033[0m")
            
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                host=db_config.get("host", "localhost"),
                port=db_config.get("port", 5432),
                dbname=db_config.get("dbname", "website_monitor"),
                user=db_config.get("user", "postgres"),
                password=db_config.get("password", ""),
                sslmode=db_config.get("sslmode", "prefer")
            )
            logger.info(f"\033[92mDatabase connection pool initialized successfully\033[0m")
        except psycopg2.Error as e:
            logger.error(f"\033[91mFailed to initialize database connection pool: {e}\033[0m")
            raise

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
            logger.error(f"\033[91mDatabase error: {e}\nQuery: {log_query}\nParams: {log_params}\033[0m")
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
            logger.info(f"\033[92mRetrieved {len(configs)} active website configurations\033[0m")
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
            print(f"\033[97;45m ADDING WEBSITE \033[0m \033[1;95m{url}\033[0m \033[0;96mCheck interval: {check_interval_seconds}s\033[0m")
            result = self.execute_query(query, params, fetch=True)
            website_id = result[0][0]
            return website_id
        except Exception as e:
            logger.error(f"\033[91mFailed to add website configuration for {url}: {e}\033[0m")
            raise

    def store_monitoring_result(
        self,
        website_id: int,
        response_time_ms: Optional[float],
        http_status: Optional[int],
        success: bool,
        regex_matched: Optional[bool] = None,
        failure_reason: Optional[str] = None,
    ) -> int:
        """Store a website monitoring result.

        Args:
            website_id: ID of the monitored website
            response_time_ms: Response time in milliseconds
            http_status: HTTP status code
            success: Whether the check was successful
            regex_matched: Whether the regex pattern matched
            failure_reason: Reason for failure if check failed

        Returns:
            ID of the newly created monitoring result
        """
        # Add monitoring timestamp for real-time tracking
        timestamp = datetime.now()
        
        try:
            query = """
                INSERT INTO monitoring_results
                (website_id, response_time_ms, http_status, success, regex_matched, failure_reason, checked_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
                timestamp,
            )
            
            result = self.execute_query(query, params, fetch=True)
            result_id = result[0][0]
            return result_id
        except Exception as e:
            logger.error(f"\033[91mFailed to store monitoring result for website {website_id}: {e}\033[0m")
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
            logger.info(f"\033[94mRetrieving {limit} most recent monitoring results\033[0m")
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
                    "timestamp": row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None
                }
                for row in result
            ]
            logger.info(f"\033[92mRetrieved {len(results)} recent monitoring results\033[0m")
            return results
        except Exception as e:
            logger.error(f"\033[91mFailed to get recent monitoring results: {e}\033[0m")
            return []

    def close(self):
        """Close the connection pool."""
        if hasattr(self, "connection_pool"):
            self.connection_pool.closeall()
            logger.info("\033[92mDatabase connection pool closed\033[0m")