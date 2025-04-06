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

- The scheduler uses a simple thread-based implementation for maximum reliability
  - A previous implementation using Dask is preserved in `scheduler.py.bck2`
- Configuration supports 10 websites with regex pattern matching
- Tests are provided for the scheduler component using pytest
- Connects to an companyX PostgreSQL database (configured in config.json)

## Configuration

The `config.json` file includes:
- Database connection parameters
- Website monitoring configurations (URLs, intervals, regex patterns)
- Application settings (worker count, timeouts, etc.)

## Testing

Unit tests focus on the scheduler component:
```
python -m pytest test/test_scheduler.py
```

## Requirements

See `requirements.txt` for dependencies.