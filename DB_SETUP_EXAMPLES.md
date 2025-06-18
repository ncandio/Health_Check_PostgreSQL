# SiteSentinel Database Setup and Query Examples

This document provides examples of how to use the database scripts in the SiteSentinel project.

## Prerequisites

Before setting up the database, ensure PostgreSQL is installed:

```bash
# Check if PostgreSQL is installed
python check_postgres.py
```

If PostgreSQL is not installed, the script will provide installation instructions for your operating system.

## Setting Up the Database

### 1. Initialize the Database

```bash
# Run the setup script to create the database and schema
python setup_db.py
```

This script will:
- Create a database named "website_monitor" (or the name specified in config.json)
- Create the necessary tables and indexes defined in schema.sql
- Set up views and functions for monitoring data

### 2. Database Schema Overview

The database consists of several key tables:
- `website_configs`: Stores configuration for websites to monitor
- `monitoring_results`: Stores detailed results of each website check
- `monitoring_stats`: Stores summarized daily statistics

## Querying the Database

The `query_db.py` script provides various utilities to examine and query the database.

### 1. List All Tables

```bash
python query_db.py --list-tables
```

### 2. Describe a Table Structure

```bash
# View the structure of the website_configs table
python query_db.py --describe website_configs

# View the structure of the monitoring_results table
python query_db.py --describe monitoring_results
```

### 3. Query Table Data

```bash
# View the first 10 rows from website_configs
python query_db.py --query website_configs

# View the first 20 rows from monitoring_results
python query_db.py --query monitoring_results --limit 20

# Query with conditions
python query_db.py --query monitoring_results --where "success = false" --limit 10

# Query with ordering
python query_db.py --query monitoring_results --order-by "response_time_ms DESC" --limit 15
```

### 4. View Monitoring Summary

The database includes a view with summary statistics for the last 24 hours:

```bash
python query_db.py --summary
```

### 5. Analyze Website Performance

Analyze performance metrics for monitored websites:

```bash
# Performance analysis for all websites in the last day
python query_db.py --analyze

# Performance analysis for all websites in the last 7 days
python query_db.py --analyze --days 7

# Performance analysis for a specific website
python query_db.py --analyze --website-id 1 --days 3
```

### 6. Run Custom SQL Queries

```bash
# Run a custom SQL query
python query_db.py --sql "SELECT url, COUNT(*) FROM website_configs JOIN monitoring_results ON website_configs.id = monitoring_results.website_id GROUP BY url"
```

## Example Workflow

1. Check PostgreSQL installation
   ```bash
   python check_postgres.py
   ```

2. Set up the database
   ```bash
   python setup_db.py
   ```

3. List tables to verify setup
   ```bash
   python query_db.py --list-tables
   ```

4. View website configurations
   ```bash
   python query_db.py --query website_configs
   ```

5. Check monitoring results
   ```bash
   python query_db.py --query monitoring_results --limit 10
   ```

6. View performance summary
   ```bash
   python query_db.py --summary
   ```

7. Analyze website performance
   ```bash
   python query_db.py --analyze --days 3
   ```