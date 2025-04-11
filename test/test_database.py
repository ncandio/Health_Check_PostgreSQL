"""
Tests for the database schema and connection functionality.
"""

import unittest
import os
import sys
import json
import psycopg2
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the project modules
from src.database import DatabaseManager


class TestDatabase(unittest.TestCase):
    """Test cases for database connectivity and schema."""

    def setUp(self):
        """Set up test environment."""
        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Create a database connection
        self.db_config = self.config['database']
        self.connection = psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            dbname=self.db_config['dbname'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            sslmode=self.db_config['sslmode']
        )
        
        # Create a DatabaseManager instance
        self.db_manager = DatabaseManager(self.db_config)
    
    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()
        
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
    
    def test_connection(self):
        """Test that the database connection works."""
        # Simply check that the connection is open
        self.assertFalse(self.connection.closed, "Database connection should be open")
    
    def test_website_configs_table(self):
        """Test that the website_configs table exists with the expected schema."""
        with self.connection.cursor() as cursor:
            # Check if the table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'website_configs'
                );
            """)
            table_exists = cursor.fetchone()[0]
            self.assertTrue(table_exists, "website_configs table should exist")
            
            # Check table columns
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'website_configs'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            # Create a dict of column name to data type
            column_types = {col[0]: col[1] for col in columns}
            
            # Verify essential columns exist
            self.assertIn('id', column_types, "website_configs should have an id column")
            self.assertIn('url', column_types, "website_configs should have a url column")
            self.assertIn('check_interval_seconds', column_types, 
                          "website_configs should have a check_interval_seconds column")
            self.assertIn('regex_pattern', column_types, "website_configs should have a regex_pattern column")
            self.assertIn('is_active', column_types, "website_configs should have an is_active column")
            
            # Check primary key exists
            cursor.execute("""
                SELECT a.attname 
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = 'website_configs'::regclass AND i.indisprimary;
            """)
            pk_columns = cursor.fetchall()
            pk_column_names = [col[0] for col in pk_columns]
            self.assertIn('id', pk_column_names, "website_configs should have id as primary key")
    
    def test_monitoring_results_table(self):
        """Test that the monitoring_results table exists with the expected schema."""
        with self.connection.cursor() as cursor:
            # Check if the table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'monitoring_results'
                );
            """)
            table_exists = cursor.fetchone()[0]
            self.assertTrue(table_exists, "monitoring_results table should exist")
            
            # Check table columns
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'monitoring_results'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            # Create a dict of column name to data type
            column_types = {col[0]: col[1] for col in columns}
            
            # Verify essential columns exist
            self.assertIn('id', column_types, "monitoring_results should have an id column")
            self.assertIn('website_id', column_types, "monitoring_results should have a website_id column")
            self.assertIn('checked_at', column_types, "monitoring_results should have a checked_at column")
            self.assertIn('response_time_ms', column_types, 
                         "monitoring_results should have a response_time_ms column")
            self.assertIn('http_status', column_types, "monitoring_results should have an http_status column")
            self.assertIn('success', column_types, "monitoring_results should have a success column")
            
            # Check for the newer performance metrics columns
            performance_columns = ['content_size_bytes', 'dns_lookup_time_ms', 'check_details']
            for col in performance_columns:
                self.assertIn(col, column_types, f"monitoring_results should have a {col} column")
            
            # Check primary key exists
            cursor.execute("""
                SELECT a.attname 
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = 'monitoring_results'::regclass AND i.indisprimary;
            """)
            pk_columns = cursor.fetchall()
            pk_column_names = [col[0] for col in pk_columns]
            self.assertIn('id', pk_column_names, "monitoring_results should have id as primary key")
            
            # Check foreign key exists
            cursor.execute("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column
                FROM
                    information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE
                    tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = 'monitoring_results';
            """)
            fk_constraints = cursor.fetchall()
            
            # Verify website_id references the website_configs table
            website_id_fk = False
            for constraint in fk_constraints:
                if (constraint[1] == 'website_id' and 
                    constraint[2] == 'website_configs' and 
                    constraint[3] == 'id'):
                    website_id_fk = True
                    break
            
            self.assertTrue(website_id_fk, 
                           "website_id should be a foreign key referencing website_configs.id")
    
    def test_monitoring_stats_table(self):
        """Test that the monitoring_stats table exists with the expected schema."""
        with self.connection.cursor() as cursor:
            # Check if the table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'monitoring_stats'
                );
            """)
            table_exists = cursor.fetchone()[0]
            self.assertTrue(table_exists, "monitoring_stats table should exist")
            
            # Check table columns
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'monitoring_stats'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            # Create a dict of column name to data type
            column_types = {col[0]: col[1] for col in columns}
            
            # Verify essential columns exist
            self.assertIn('id', column_types, "monitoring_stats should have an id column")
            self.assertIn('website_id', column_types, "monitoring_stats should have a website_id column")
            self.assertIn('day_date', column_types, "monitoring_stats should have a day_date column")
            self.assertIn('total_checks', column_types, "monitoring_stats should have a total_checks column")
            self.assertIn('successful_checks', column_types, 
                         "monitoring_stats should have a successful_checks column")
            self.assertIn('avg_response_time_ms', column_types, 
                         "monitoring_stats should have an avg_response_time_ms column")
    
    def test_indexes(self):
        """Test that important indexes exist."""
        with self.connection.cursor() as cursor:
            # Query to get all indexes
            cursor.execute("""
                SELECT
                    t.relname AS table_name,
                    i.relname AS index_name,
                    a.attname AS column_name
                FROM
                    pg_class t,
                    pg_class i,
                    pg_index ix,
                    pg_attribute a
                WHERE
                    t.oid = ix.indrelid
                    AND i.oid = ix.indexrelid
                    AND a.attrelid = t.oid
                    AND a.attnum = ANY(ix.indkey)
                    AND t.relkind = 'r'
                    AND t.relname IN ('monitoring_results', 'website_configs', 'monitoring_stats')
                ORDER BY
                    t.relname,
                    i.relname;
            """)
            indexes = cursor.fetchall()
            
            # Create a dictionary to track which indexes we found
            found_indexes = {}
            for idx in indexes:
                table_name = idx[0]
                index_name = idx[1]
                column_name = idx[2]
                
                if table_name not in found_indexes:
                    found_indexes[table_name] = {}
                if index_name not in found_indexes[table_name]:
                    found_indexes[table_name][index_name] = []
                    
                found_indexes[table_name][index_name].append(column_name)
            
            # Check for required indexes
            required_indexes = [
                ('monitoring_results', 'website_id'),
                ('monitoring_results', 'checked_at'),
                ('monitoring_results', 'success'),
                ('monitoring_results', 'http_status'),
                ('website_configs', 'is_active'),
                ('monitoring_stats', 'website_id'),
                ('monitoring_stats', 'day_date')
            ]
            
            for table, column in required_indexes:
                has_index = False
                if table in found_indexes:
                    for index_name, columns in found_indexes[table].items():
                        if column in columns:
                            has_index = True
                            break
                
                self.assertTrue(has_index, f"There should be an index on {table}.{column}")
    
    def test_database_manager_initialization(self):
        """Test that the DatabaseManager can be initialized."""
        # This test passes if setUp succeeded in creating a DatabaseManager
        self.assertIsNotNone(self.db_manager, "DatabaseManager should be initialized")
    
    def test_database_manager_query_execution(self):
        """Test that the DatabaseManager can execute queries."""
        # Try to execute a simple query
        result = self.db_manager.execute_query("SELECT 1 as test", fetch=True)
        self.assertEqual(result[0][0], 1, "DatabaseManager should be able to execute queries")
    
    def test_stored_procedures(self):
        """Test that important stored procedures exist."""
        with self.connection.cursor() as cursor:
            # Check for update_updated_at_column function
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_proc
                    WHERE proname = 'update_updated_at_column'
                );
            """)
            function_exists = cursor.fetchone()[0]
            self.assertTrue(function_exists, "update_updated_at_column function should exist")
            
            # Check for cleanup_old_monitoring_results function
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_proc
                    WHERE proname = 'cleanup_old_monitoring_results'
                );
            """)
            function_exists = cursor.fetchone()[0]
            self.assertTrue(function_exists, "cleanup_old_monitoring_results function should exist")
            
            # Check trigger exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_trigger
                    WHERE tgname = 'update_website_configs_updated_at'
                );
            """)
            trigger_exists = cursor.fetchone()[0]
            self.assertTrue(trigger_exists, "update_website_configs_updated_at trigger should exist")
    
    def test_view_exists(self):
        """Test that the monitoring summary view exists."""
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.views
                    WHERE table_name = 'vw_monitoring_summary'
                );
            """)
            view_exists = cursor.fetchone()[0]
            self.assertTrue(view_exists, "vw_monitoring_summary view should exist")


if __name__ == "__main__":
    unittest.main()