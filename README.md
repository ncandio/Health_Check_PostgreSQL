# Website Monitoring System

A robust Python application for monitoring website availability and content verification.

## Overview

This system periodically checks configured websites, verifies their availability, and optionally validates content using regex patterns. It stores all monitoring results in a PostgreSQL database for historical tracking and analysis.

> **IMPORTANT**: This branch with Dask integration is EXPERIMENTAL and for RESEARCH purposes only. The Dask implementation ([https://docs.dask.org/en/stable/index.html](https://docs.dask.org/en/stable/index.html)) provides distributed computing capabilities, but is not recommended for production use in this version.

## Features

- **Configurable website monitoring** with customizable check intervals
- **Content verification** using regex patterns
- **Response time tracking** and HTTP status code validation
- **Dual-mode scheduling** with thread-based and Dask distributed computing
- **PostgreSQL database integration** via Aiven
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
  - A third approach using pyuv for event-based processing is also available
- Configuration supports 1000 websites with regex pattern matching
- Comprehensive test suite for scheduler, database, and website monitoring
- Connects to an Aiven PostgreSQL database (configured in config.json)

## Running the Application

To launch the application:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```



## Configuration

The `config.json` file includes:
- Database connection parameters
- Website monitoring configurations (URLs, intervals, regex patterns)
- Application settings (worker count, timeouts, etc.)
- Scheduler options (`use_dask: true/false` for enabling distributed execution)

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
