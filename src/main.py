"""
Main entry point for the website monitor application.
"""

import json
import logging
import signal
import sys
import time
from typing import Dict, List, Any

from src.database import DatabaseManager
from src.monitor import WebsiteMonitor
from src.scheduler import Scheduler
from src.validators import validate_website_config

# Setup comprehensive logging is handled in monitor.py, which is imported first
# But we'll configure a specialized logger for this module with real-time monitoring focus
# We'll focus on emphasizing website monitoring, not internal details

import os
from datetime import datetime

# Ensure monitor.py logging is initialized first
from src.monitor import root_logger

# Create special file just for main application events
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
main_log_file = os.path.join(log_dir, f'application_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# Create a separate file handler for main application events with timestamp in filename
main_file_handler = logging.FileHandler(main_log_file)
main_file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
main_file_handler.setLevel(logging.INFO)

# Get module logger and add the special handler
logger = logging.getLogger(__name__)
logger.addHandler(main_file_handler)

# Enhanced startup banner with better visibility
print(f"\033[97;46m{'='*80}\033[0m")
print(f"\033[97;46m WEBSITE MONITORING SYSTEM STARTING \033[0m")
print(f"\033[97;46m Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} \033[0m")
print(f"\033[97;46m Python: {sys.version.split()[0]} | Host: {os.uname().nodename} \033[0m")
print(f"\033[97;46m{'='*80}\033[0m")


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from a JSON file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)


def setup_database(db_config: Dict[str, Any]) -> DatabaseManager:
    """Set up database connection.

    Args:
        db_config: Database configuration dictionary

    Returns:
        Database manager
    """
    try:
        db_manager = DatabaseManager(db_config)
        return db_manager
    except Exception as e:
        logger.error(f"Failed to set up database: {e}")
        sys.exit(1)


def monitor_website(
    website_id: int,
    url: str,
    regex_pattern: str,
    monitor: WebsiteMonitor,
    db_manager: DatabaseManager,
):
    """Monitor a website and store the results.

    Args:
        website_id: Website ID
        url: Website URL
        regex_pattern: Regex pattern to check for
        monitor: Website monitor
        db_manager: Database manager
    """
    try:
        result = monitor.check_website(url, regex_pattern)

        # Store result in database
        result_id = db_manager.store_monitoring_result(
            website_id=website_id,
            response_time_ms=result["response_time_ms"],
            http_status=result["http_status"],
            success=result["success"],
            regex_matched=result["regex_matched"],
            failure_reason=result["failure_reason"],
        )
        
        if result_id is None:
            logger.warning(f"Failed to store successful monitoring result for {url}")
    except Exception as e:
        logger.error(f"Error monitoring website {url}: {e}")
        # Try to store failure information
        try:
            result_id = db_manager.store_monitoring_result(
                website_id=website_id,
                response_time_ms=None,
                http_status=None,
                success=False,
                regex_matched=None,
                failure_reason=f"Internal error: {str(e)}",
            )
            
            if result_id is None:
                logger.warning(f"Failed to store failure information for {url}")
        except Exception as db_error:
            logger.error(f"Failed to store failure information for {url}: {db_error}")


def configure_websites(
    config: Dict[str, Any],
    db_manager: DatabaseManager,
    monitor: WebsiteMonitor,
    scheduler: Scheduler,
) -> int:
    """Configure websites from configuration.

    Args:
        config: Configuration dictionary
        db_manager: Database manager
        monitor: Website monitor
        scheduler: Scheduler

    Returns:
        Number of websites configured
    """
    websites = config.get("websites", [])
    configured_count = 0

    # First, validate all configurations
    for website_config in websites:
        errors = validate_website_config(website_config)
        if errors:
            logger.warning(
                f"Invalid website configuration: {website_config}\nErrors: {', '.join(errors)}"
            )
            continue

        try:
            # Add website to database
            website_id = db_manager.add_website_config(
                url=website_config["url"],
                check_interval_seconds=website_config["check_interval_seconds"],
                regex_pattern=website_config.get("regex_pattern"),
            )

            # Schedule monitoring
            scheduler.add_task(
                website_config["check_interval_seconds"],
                monitor_website,
                website_id,
                website_config["url"],
                website_config.get("regex_pattern"),
                monitor,
                db_manager,
            )

            configured_count += 1
            # Use bright green color ANSI escape sequence with white background and black text for better visibility
            print(f"\033[97;42m WEBSITE CONFIGURED \033[0m \033[1;92m{website_config['url']}\033[0m")
        except Exception as e:
            logger.error(f"Failed to configure website {website_config['url']}: {e}")

    return configured_count


def setup_signal_handlers(scheduler: Scheduler, db_manager: DatabaseManager):
    """Set up signal handlers for graceful shutdown.

    Args:
        scheduler: Scheduler to stop
        db_manager: Database manager to close
    """

    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        scheduler.stop()
        db_manager.close()
        logger.info("Graceful shutdown complete")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main entry point."""
    print("\033[97;44m SYSTEM STATUS \033[0m \033[1;96mStarting website monitor\033[0m")

    # Load configuration
    config = load_config()

    # Set up database
    db_manager = setup_database(config["database"])

    # Create monitor
    monitor = WebsiteMonitor(
        timeout=config.get("connection_timeout", 10),
        retry_limit=config.get("retry_limit", 3),
    )

    # Create scheduler
    scheduler = Scheduler(max_workers=config.get("max_workers", 10))

    # Set up signal handlers
    setup_signal_handlers(scheduler, db_manager)

    # Start scheduler
    scheduler.start()

    # Configure websites
    configured_count = configure_websites(config, db_manager, monitor, scheduler)
    print(f"\033[97;44m MONITOR STATUS \033[0m \033[1;96mConfigured {configured_count} websites\033[0m")

    # Keep the main thread alive
    try:
        while scheduler.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted")
        scheduler.stop()
        db_manager.close()

    logger.info("Website monitor stopped")


if __name__ == "__main__":
    main()
