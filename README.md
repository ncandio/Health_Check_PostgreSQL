# PostgreSQL Health Check

A robust Python application for monitoring website availability and performing content verification with PostgreSQL database integration.

## Overview

This application allows you to monitor multiple websites simultaneously, checking for:
- Website availability (HTTP status codes)
- Response time
- Content validation via regex patterns
- Detailed performance metrics (DNS lookup time, content size, etc.)

All monitoring data is stored in a PostgreSQL database for historical analysis and reporting.

## Features

- **Real-time monitoring** of website availability and performance
- **Content validation** with customizable regex patterns
- **PostgreSQL integration** for persistent storage of monitoring results
- **Distributed computing** support with Dask for high-performance monitoring
- **Comprehensive reporting** with availability statistics
- **High configurability** through JSON config files
- **Detailed logging** of all monitoring activities

## Requirements

- Python 3.8+
- PostgreSQL 12+
- Required Python packages (see `requirements.txt`)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/Health_Check_PostgreSQL.git
   cd Health_Check_PostgreSQL
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify PostgreSQL installation**:
   ```bash
   # Check if PostgreSQL is installed
   python check_postgres.py
   ```

## Database Setup

1. **Set up PostgreSQL**:

   For Linux/macOS:
   ```bash
   chmod +x setup_postgres.sh
   ./setup_postgres.sh
   ```

   For Windows:
   ```
   setup_postgres.bat
   ```

2. **Initialize the database schema**:
   ```bash
   python setup_db.py
   ```

## Configuration

The application uses a JSON configuration file (`config.json`) with the following structure:

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "dbname": "website_monitor",
    "user": "postgres",
    "password": "postgres",
    "sslmode": "prefer"
  },
  "websites": [
    {
      "url": "https://www.example.com",
      "check_interval_seconds": 60,
      "regex_pattern": "Example Pattern"
    }
  ],
  "max_workers": 50,
  "retry_limit": 3,
  "connection_timeout": 10,
  "use_dask": true
}
```

You can modify this file to:
- Configure database connection parameters
- Add/remove websites to monitor
- Set check intervals for each website
- Define regex patterns for content validation
- Adjust performance settings (workers, timeouts, etc.)
- Enable/disable Dask distributed computing

## Running the Application

Start the monitoring service:

```bash
python src/main.py
```

The application will:
1. Connect to the PostgreSQL database
2. Load the website configurations
3. Start monitoring each website at the specified intervals
4. Store results in the database

## Querying Monitoring Data

The application includes a utility for querying the database:

```bash
# Show monitoring summary for the last 24 hours
python query_db.py --summary

# Analyze website performance
python query_db.py --analyze --days 7

# Query specific tables
python query_db.py --query monitoring_results --limit 20

# Run custom SQL queries
python query_db.py --sql "SELECT * FROM monitoring_results WHERE success = false"

# List all database tables
python query_db.py --list-tables

# Describe table structure
python query_db.py --describe website_configs
```

## Performance Optimization

For monitoring a large number of websites, the application supports Dask distributed computing:

1. Enable Dask in the config.json file: `"use_dask": true`
2. Adjust the number of workers: `"max_workers": 50`

When Dask is enabled, the application will display a link to the Dask dashboard for real-time monitoring of task execution.

## Project Structure

- `src/` - Core application code
  - `main.py` - Main entry point
  - `monitor.py` - Website monitoring logic
  - `database.py` - Database operations
  - `scheduler.py` - Task scheduling
  - `validators.py` - Input validation
- `schema.sql` - Database schema
- `setup_db.py` - Database initialization
- `query_db.py` - Database query utility
- `check_postgres.py` - PostgreSQL installation checker
- `setup_postgres.sh/bat` - PostgreSQL setup scripts
- `config.json` - Application configuration
- `logs/` - Application logs

## Logging

The application logs detailed information about monitoring activities to the `logs/` directory. The main log file is `website_monitor.log`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.