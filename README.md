# SiteSentinel

A robust Python application for monitoring website availability and content verification with PostgreSQL database integration.

![SiteSentinel](images/sitesentinel.png)

## Overview

This system periodically checks configured websites, verifies their availability, and optionally validates content using regex patterns. It stores all monitoring results in a PostgreSQL database for historical tracking and analysis.

## Features

- **Configurable website monitoring** with customizable check intervals
- **Content verification** using regex patterns
- **Response time tracking** and HTTP status code validation
- **Dual-mode scheduling** with thread-based and Dask distributed computing
- **Simple thread-based scheduler** implementation for reliability
- **PostgreSQL database integration** with local or remote PostgreSQL
- **Comprehensive logging** system with rotation
- **Graceful shutdown** handling
- **Dask dashboard** for real-time monitoring of distributed tasks

## Architecture

The application consists of several modular components:

- `main.py`: Entry point and orchestration
- `database.py`: PostgreSQL database integration using connection pooling
- `monitor.py`: Website availability and content checking
- `scheduler.py`: Dual-mode scheduler supporting threads and Dask distributed computing
- `validators.py`: Configuration validation

## Implementation Notes

- Multiple processing and threading approaches are provided:
  - The scheduler supports both a simple thread-based implementation for maximum reliability and a Dask-based distributed computing approach
  - Enable Dask by setting `"use_dask": true` in config.json
  - Configure number of Dask workers with the `max_workers` setting in config.json
  - When Dask is enabled, a dashboard URL will be displayed at startup for monitoring tasks (typically at http://localhost:8787)
  - The Dask console is available at http://localhost:8787 and the URL is logged at 10-second intervals for easy access
- Configuration supports 1000 websites with regex pattern matching
- Comprehensive test suite for scheduler, database, and website monitoring
- Connects to a PostgreSQL database (configured in config.json)

## Running the Application

### Setting up a Virtual Environment

It's recommended to use a virtual environment to isolate the project dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment (Linux/Mac)
source venv/bin/activate

# Activate the virtual environment (Windows)
venv\Scripts\activate
```

### Installing Dependencies and Running

Once the virtual environment is activated:

```bash
# Install dependencies
pip install -r requirements.txt

# Set up the PostgreSQL database
python setup_db.py

# Run the application
python src/main.py
```

To deactivate the virtual environment when finished:

```bash
deactivate
```

### Database Setup

#### Prerequisites

Before setting up the database, make sure PostgreSQL is installed on your system. You can check this by running:

```bash
python check_postgres.py
```

This script will verify if PostgreSQL is installed and provide installation instructions if needed.

#### Setup Scripts

The project includes several setup scripts to help you get started with PostgreSQL:

#### Automatic PostgreSQL Setup

For a guided setup experience, run one of the following scripts based on your operating system:

**Linux/macOS:**
```bash
./setup_postgres.sh
```

**Windows:**
```bash
setup_postgres.bat
```

These scripts will:
1. Check if PostgreSQL is installed
2. Start the PostgreSQL service if needed (Linux/macOS)
3. Create the required user and database
4. Set appropriate permissions

#### Manual Database Setup

If you prefer to set up the database manually or if you're on Windows, use:

```bash
python setup_db.py
```

This Python script will:
1. Connect to PostgreSQL using the credentials in config.json
2. Create the database if it doesn't exist
3. Set up all necessary tables, indexes, and views

Make sure PostgreSQL is running and the credentials in `config.json` are correct.


## Configuration

The `config.json` file includes:
- Database connection parameters
- Website monitoring configurations (URLs, intervals, regex patterns)
- Application settings (worker count, timeouts, etc.)
- Scheduler options (`use_dask: true/false` for enabling distributed execution)

## Execution Modes

SiteSentinel offers two execution modes that can be configured in the `config.json` file:

1. **Thread-based Execution** (Default): This is the standard mode using Python's built-in threading capabilities.
   - Set `"use_dask": false` in config.json
   - Offers excellent reliability and simplicity
   - Best for smaller deployments or when monitoring fewer websites
   - Runs with a configurable thread pool defined by `max_workers`

2. **Distributed Execution with Dask**: Enables parallel processing across multiple cores or even machines.
   - Set `"use_dask": true` in config.json
   - Provides a dashboard for real-time task monitoring at http://localhost:8787
   - Offers better performance for large-scale monitoring (hundreds or thousands of websites)
   - Distributes load across configurable number of workers
   - Handles task queuing, retries, and resource management

To switch between modes, simply update the `use_dask` parameter in your config.json file and restart the application.

### Dask Dashboard

When running SiteSentinel with Dask enabled, a web-based dashboard is automatically available at http://localhost:8787. This dashboard provides:

- Real-time visualization of running tasks
- Worker status and resource utilization
- Task progress and completion statistics
- Performance metrics and timing information
- Diagnostic tools for troubleshooting

The dashboard URL is displayed in the console output and logged every 10 seconds for convenient access. This powerful monitoring interface is especially valuable when scaling to thousands of websites.

## Scaling to 10,000 Websites

SiteSentinel is designed to efficiently monitor thousands of websites. Below is a sample of a configuration with 10,000 website entries.

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "dbname": "sitesentinel",
    "user": "postgres",
    "password": "postgres",
    "sslmode": "prefer"
  },
  "max_workers": 500,
  "retry_limit": 3,
  "connection_timeout": 10,
  "use_dask": true,
  "websites": [
    {
      "url": "https://www.google.com",
      "check_interval_seconds": 30,
      "regex_pattern": "Google Search"
    },
    {
      "url": "https://www.bing.com",
      "check_interval_seconds": 60,
      "regex_pattern": "Microsoft Bing"
    },
    {
      "url": "https://www.yahoo.com",
      "check_interval_seconds": 120,
      "regex_pattern": "Yahoo Search"
    }
    // Additional 9,997 website entries would be here
  ]
}
```

### Scaling Considerations

When scaling to 10,000 websites:

1. **Distribution of Check Intervals**
   - Critical websites: 30-60 second intervals (~5% of sites)
   - Important websites: 120-300 second intervals (~35% of sites)
   - Standard monitoring: 600 second intervals (~60% of sites)

2. **Resource Planning**
   - Database capacity: ~10GB for a year of monitoring history
   - Network bandwidth: ~50 requests per second at peak
   - CPU utilization: Scales linearly with concurrent checks

3. **Performance Optimization**
   - Concurrent connections: Configurable up to 1000 simultaneous checks
   - Database indexes: Optimized for time-series queries
   - Result caching: Reduces database load for frequently accessed sites

4. **Monitoring Distribution**
   - Consider distributing monitoring across multiple nodes for geographical diversity
   - Implement retry logic with exponential backoff for transient failures
   - Use separate worker pools for different check intervals

For large-scale deployments, the Dask execution mode is strongly recommended to efficiently manage the workload across multiple workers.

## Database Management

A utility script is provided to query and analyze the PostgreSQL database:

```bash
# List all database tables
./query_db.py --list-tables

# Describe a table's structure
./query_db.py --describe TABLE_NAME

# Query table data with optional filters
./query_db.py --query TABLE_NAME [--limit N] [--where "condition"] [--order-by "column"]

# Run custom SQL queries
./query_db.py --sql "SELECT * FROM table WHERE condition"

# View monitoring summary for the last 24 hours
./query_db.py --summary

# Analyze website performance
./query_db.py --analyze [--website-id ID] [--days N]
```

For more information on available options:
```bash
./query_db.py --help
```

## Testing

The testing suite includes:

1. **Scheduler Tests**: Validates the custom thread-based scheduling system
   ```
   python -m pytest test/test_scheduler.py
   ```

2. **Database Tests**: Verifies database connection and table creation functionality
   ```
   python -m pytest test/test_database.py
   ```

3. **Website Monitoring Tests**: Tests the system with 500 different websites
   ```
   python -m pytest test/test_500_websites.py
   ```

The system has been configured to handle up to 1000 websites in the original configuration file.

## Requirements

See `requirements.txt` for dependencies.