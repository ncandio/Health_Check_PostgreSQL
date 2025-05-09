#!/usr/bin/env python3
"""
Script to view and query PostgreSQL database contents for the website monitor.
Provides several utility functions to examine tables and data.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor
from tabulate import tabulate

def load_config(config_path="config.json"):
    """Load database configuration from config file."""
    with open(config_path, "r") as f:
        return json.load(f)

def connect_to_db(db_config):
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=db_config.get("host", "localhost"),
            port=db_config.get("port", 5432),
            dbname=db_config.get("dbname", "website_monitor"),
            user=db_config.get("user", "postgres"),
            password=db_config.get("password", ""),
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def list_tables(conn):
    """List all tables in the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            
            print("\n=== Database Tables ===")
            for table in tables:
                print(f"- {table[0]}")
    except Exception as e:
        print(f"Error listing tables: {e}")

def describe_table(conn, table_name):
    """Describe the structure of a specific table."""
    try:
        with conn.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            """, (table_name,))
            
            if not cursor.fetchone():
                print(f"Table '{table_name}' does not exist.")
                return
            
            # Get column information
            cursor.execute("""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            # Get index information
            cursor.execute("""
                SELECT 
                    i.relname as index_name,
                    a.attname as column_name,
                    ix.indisunique as is_unique
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
                    AND t.relname = %s
                ORDER BY
                    i.relname, a.attnum
            """, (table_name,))
            
            indexes = cursor.fetchall()
            
            # Print table structure
            print(f"\n=== Table: {table_name} ===")
            
            # Format and print column information
            column_data = []
            for col in columns:
                col_name, data_type, max_length, nullable = col
                data_type_str = data_type
                if max_length:
                    data_type_str += f"({max_length})"
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                column_data.append([col_name, data_type_str, nullable_str])
            
            print("\nColumns:")
            print(tabulate(column_data, headers=["Column", "Type", "Nullable"], tablefmt="pretty"))
            
            # Format and print index information
            if indexes:
                index_data = {}
                for idx in indexes:
                    idx_name, col_name, is_unique = idx
                    if idx_name not in index_data:
                        index_data[idx_name] = {
                            "columns": [],
                            "unique": is_unique
                        }
                    index_data[idx_name]["columns"].append(col_name)
                
                print("\nIndexes:")
                for idx_name, info in index_data.items():
                    unique_str = "UNIQUE" if info["unique"] else ""
                    columns_str = ", ".join(info["columns"])
                    print(f"- {idx_name} ({unique_str}) ON {columns_str}")
                    
    except Exception as e:
        print(f"Error describing table: {e}")

def query_table(conn, table_name, limit=10, where=None, order_by=None):
    """Query data from a specific table."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            """, (table_name,))
            
            if not cursor.fetchone():
                print(f"Table '{table_name}' does not exist.")
                return
            
            # Build the query
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if where:
                query += f" WHERE {where}"
                
            if order_by:
                query += f" ORDER BY {order_by}"
            else:
                # Default order by created_at or id
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = %s AND 
                          column_name IN ('created_at', 'id')
                    LIMIT 1
                """, (table_name,))
                
                order_col = cursor.fetchone()
                if order_col:
                    order_col = order_col['column_name']
                    query += f" ORDER BY {order_col} DESC"
            
            query += f" LIMIT {limit}"
            
            # Execute the query
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if not rows:
                print(f"No data found in table '{table_name}'.")
                return
            
            # Convert rows to list for tabulate
            headers = rows[0].keys()
            table_data = []
            
            for row in rows:
                # Format datetime objects
                formatted_row = []
                for key, val in row.items():
                    if isinstance(val, datetime):
                        formatted_row.append(val.strftime('%Y-%m-%d %H:%M:%S'))
                    elif isinstance(val, dict) or isinstance(val, list):
                        formatted_row.append(json.dumps(val, indent=2))
                    else:
                        formatted_row.append(val)
                table_data.append(formatted_row)
            
            # Print table data
            print(f"\n=== Data from {table_name} ===")
            print(tabulate(table_data, headers=headers, tablefmt="pretty"))
            print(f"\nShowing {len(rows)} of {limit} requested rows")
            
    except Exception as e:
        print(f"Error querying table: {e}")

def run_custom_query(conn, query):
    """Run a custom SQL query."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            
            if cursor.description is None:  # No results to fetch (e.g., INSERT, UPDATE)
                affected = cursor.rowcount
                conn.commit()
                print(f"Query executed successfully. {affected} rows affected.")
                return
            
            rows = cursor.fetchall()
            
            if not rows:
                print("Query returned no results.")
                return
            
            # Convert rows to list for tabulate
            headers = rows[0].keys()
            table_data = []
            
            for row in rows:
                # Format datetime objects
                formatted_row = []
                for key, val in row.items():
                    if isinstance(val, datetime):
                        formatted_row.append(val.strftime('%Y-%m-%d %H:%M:%S'))
                    elif isinstance(val, dict) or isinstance(val, list):
                        formatted_row.append(json.dumps(val, indent=2))
                    else:
                        formatted_row.append(val)
                table_data.append(formatted_row)
            
            # Print query results
            print("\n=== Query Results ===")
            print(tabulate(table_data, headers=headers, tablefmt="pretty"))
            print(f"\nShowing {len(rows)} rows")
            
    except Exception as e:
        print(f"Error executing query: {e}")
        conn.rollback()

def show_monitoring_summary(conn):
    """Show the monitoring summary from the vw_monitoring_summary view."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM vw_monitoring_summary")
            rows = cursor.fetchall()
            
            if not rows:
                print("No monitoring data available.")
                return
            
            # Format data for display
            table_data = []
            for row in rows:
                formatted_row = []
                for key, val in row.items():
                    if isinstance(val, datetime):
                        formatted_row.append(val.strftime('%Y-%m-%d %H:%M:%S'))
                    else:
                        formatted_row.append(val)
                table_data.append(formatted_row)
            
            headers = rows[0].keys()
            
            print("\n=== Website Monitoring Summary (Last 24 Hours) ===")
            print(tabulate(table_data, headers=headers, tablefmt="pretty"))
            
    except Exception as e:
        print(f"Error retrieving monitoring summary: {e}")

def analyze_website_performance(conn, website_id=None, days=1):
    """Analyze website performance statistics."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Build the query based on parameters
            query = """
                SELECT 
                    wc.url,
                    COUNT(*) AS total_checks,
                    ROUND(AVG(mr.response_time_ms)::numeric, 2) AS avg_response_time_ms,
                    MIN(mr.response_time_ms) AS min_response_time_ms,
                    MAX(mr.response_time_ms) AS max_response_time_ms,
                    ROUND(AVG(mr.dns_lookup_time_ms)::numeric, 2) AS avg_dns_lookup_ms,
                    ROUND(AVG(mr.content_size_bytes)::numeric, 0) AS avg_content_size_bytes,
                    SUM(CASE WHEN mr.success THEN 1 ELSE 0 END) AS success_count,
                    SUM(CASE WHEN NOT mr.success THEN 1 ELSE 0 END) AS failure_count,
                    ROUND((SUM(CASE WHEN mr.success THEN 1 ELSE 0 END)::float / COUNT(*) * 100)::numeric, 2) AS success_rate
                FROM 
                    monitoring_results mr
                JOIN 
                    website_configs wc ON mr.website_id = wc.id
                WHERE 
                    mr.checked_at > NOW() - INTERVAL %s DAY
            """
            
            params = [days]
            
            if website_id:
                query += " AND wc.id = %s"
                params.append(website_id)
                
            query += " GROUP BY wc.url ORDER BY success_rate ASC, avg_response_time_ms DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if not rows:
                print(f"No monitoring data available for the last {days} day(s).")
                return
            
            # Format data for display
            table_data = []
            for row in rows:
                formatted_row = []
                for key, val in row.items():
                    formatted_row.append(val)
                table_data.append(formatted_row)
            
            headers = rows[0].keys()
            
            print(f"\n=== Website Performance Analysis (Last {days} day(s)) ===")
            print(tabulate(table_data, headers=headers, tablefmt="pretty"))
            
    except Exception as e:
        print(f"Error analyzing website performance: {e}")

def main():
    parser = argparse.ArgumentParser(description="Query PostgreSQL database for website monitor")
    parser.add_argument("--list-tables", action="store_true", help="List all tables in the database")
    parser.add_argument("--describe", metavar="TABLE", help="Describe the structure of a specific table")
    parser.add_argument("--query", metavar="TABLE", help="Query data from a specific table")
    parser.add_argument("--limit", type=int, default=10, help="Limit the number of rows returned (default: 10)")
    parser.add_argument("--where", metavar="CONDITION", help="WHERE clause for the query")
    parser.add_argument("--order-by", metavar="COLUMN", help="ORDER BY clause for the query")
    parser.add_argument("--sql", metavar="QUERY", help="Run a custom SQL query")
    parser.add_argument("--summary", action="store_true", help="Show the monitoring summary view")
    parser.add_argument("--analyze", action="store_true", help="Analyze website performance")
    parser.add_argument("--website-id", type=int, help="Filter analysis to a specific website ID")
    parser.add_argument("--days", type=int, default=1, help="Number of days to analyze (default: 1)")
    
    args = parser.parse_args()
    
    # Load configuration and connect to database
    config = load_config()
    db_config = config.get("database", {})
    conn = connect_to_db(db_config)
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        conn.close()
        return
    
    try:
        # Execute the requested operation
        if args.list_tables:
            list_tables(conn)
            
        if args.describe:
            describe_table(conn, args.describe)
            
        if args.query:
            query_table(conn, args.query, args.limit, args.where, args.order_by)
            
        if args.sql:
            run_custom_query(conn, args.sql)
            
        if args.summary:
            show_monitoring_summary(conn)
            
        if args.analyze:
            analyze_website_performance(conn, args.website_id, args.days)
            
    finally:
        conn.close()

if __name__ == "__main__":
    main()