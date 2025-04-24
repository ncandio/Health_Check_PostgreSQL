# Website Monitoring System

A robust Python application for monitoring website availability and content verification.

## Overview

This system periodically checks configured websites, verifies their availability, and optionally validates content using regex patterns. It stores all monitoring results in a PostgreSQL database for historical tracking and analysis.

## Features

- **Configurable website monitoring** with customizable check intervals
- **Content verification** using regex patterns
- **Response time tracking** and HTTP status code validation
- **Simple thread-based scheduler** implementation for reliability
- **PostgreSQL database integration** via companyX
- **Comprehensive logging** system with rotation
- **Graceful shutdown** handling

## Architecture

The application consists of several modular components:

- `main.py`: Entry point and orchestration
- `database.py`: PostgreSQL database integration using connection pooling
- `monitor.py`: Website availability and content checking
- `scheduler.py`: Simple thread-based task scheduler
- `validators.py`: Configuration validation

## Implementation Notes

- Multiple processing and threading approaches are provided:
  - The current implementation uses a simple thread-based scheduler for maximum reliability
  - An alternative implementation using Dask is preserved in `scheduler.py.bck2`
  - A third approach using pyuv for event-based processing is available
- Configuration supports 1000 websites with regex pattern matching
- Comprehensive test suite for scheduler, database, and website monitoring
- Connects to an companyX PostgreSQL database (configured in config.json)

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

# Run the application
python src/main.py
```

To deactivate the virtual environment when finished:

```bash
deactivate
```


## Configuration

The `config.json` file includes:
- Database connection parameters
- Website monitoring configurations (URLs, intervals, regex patterns)
- Application settings (worker count, timeouts, etc.)

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
