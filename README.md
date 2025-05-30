# SiteSentinel

Enterprise-grade website monitoring platform that detects downtime, validates content, and analyzes performance metrics at scale.

<img src="images/sitesentinel.png" width="400" alt="SiteSentinel Logo">

## Overview

SiteSentinel delivers mission-critical website monitoring with powerful content validation, comprehensive metrics collection, and advanced performance analytics. Built for scale, it supports thousands of concurrent checks with flexible execution models and provides real-time insights through its PostgreSQL integration and interactive dashboards.

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

## Requirements

See `requirements.txt` for dependencies.