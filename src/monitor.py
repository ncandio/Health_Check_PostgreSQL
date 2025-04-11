"""
Website monitoring module that checks website availability
and content based on configured parameters.
"""

import json
import logging
import logging.handlers
import os
import re
import time
from typing import Any, Dict, Optional, Tuple

import requests
from requests.exceptions import RequestException

# Enhanced logging setup with file rotation and console output
log_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
)
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "website_monitor.log")

# Setup root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# File handler with rotation (10 MB per file, keep 5 backup files)
file_handler = logging.handlers.RotatingFileHandler(
    log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
root_logger.addHandler(file_handler)

# Console handler with colored output for better visibility
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter(
        "\033[92m%(asctime)s\033[0m - \033[94m%(name)s\033[0m - \033[93m%(levelname)s\033[0m - %(message)s"
    )
)
root_logger.addHandler(console_handler)

# Module logger with higher visibility for monitoring results
logger = logging.getLogger(__name__)
# Make sure all monitor messages are shown - these are the ones we care about!


class WebsiteMonitor:
    """Monitors websites for availability and content."""

    def __init__(self, timeout: int = 10, retry_limit: int = 3):
        """Initialize the website monitor.

        Args:
            timeout: Connection timeout in seconds
            retry_limit: Number of retries before giving up
        """
        self.timeout = timeout
        self.retry_limit = retry_limit

    def check_website(
        self, url: str, regex_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check a website's availability and content.

        Args:
            url: Website URL to check
            regex_pattern: Optional regex pattern to check for

        Returns:
            Dictionary containing check results
        """
        # Skip the starting check message - we only care about results

        result = {
            "url": url,
            "success": False,
            "response_time_ms": None,
            "http_status": None,
            "regex_matched": None,
            "failure_reason": None,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "check_details": {},
        }

        for attempt in range(self.retry_limit):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.retry_limit} for {url}")

                start_time = time.time()
                response = requests.get(url, timeout=self.timeout)
                end_time = time.time()

                response_time_ms = (end_time - start_time) * 1000
                result["response_time_ms"] = response_time_ms
                result["http_status"] = response.status_code
                result["success"] = 200 <= response.status_code < 400

                # Add detailed performance data
                result["check_details"]["dns_lookup_time_ms"] = (
                    response.elapsed.total_seconds() * 1000
                )
                result["check_details"]["total_network_time_ms"] = response_time_ms
                result["check_details"]["content_size_bytes"] = len(response.content)
                # Convert headers to dict and filter out any non-serializable values
                headers_dict = {}
                for k, v in response.headers.items():
                    try:
                        # Test if value is JSON serializable
                        json.dumps(v)
                        headers_dict[k] = v
                    except (TypeError, OverflowError):
                        # If not serializable, convert to string
                        headers_dict[k] = str(v)
                result["check_details"]["headers"] = headers_dict

                # Enhanced regex pattern logging with color coding
                if regex_pattern and result["success"]:
                    logger.info(
                        f"\033[95mApplying regex pattern: '{regex_pattern}' to response body\033[0m"
                    )
                    pattern = re.compile(regex_pattern, re.DOTALL)
                    match = pattern.search(response.text)
                    result["regex_matched"] = bool(match)

                    # Store regex match details
                    if match:
                        result["check_details"]["regex_match"] = {
                            "match_position": match.span(),
                            "matched_text": match.group(0)[:100]
                            + ("..." if len(match.group(0)) > 100 else ""),
                        }
                        logger.info(
                            f"\033[92mRegex pattern matched at position {match.span()}\033[0m"
                        )
                    else:
                        logger.info(
                            f"\033[93mRegex pattern '{regex_pattern}' not found in content\033[0m"
                        )
                        result["success"] = False
                        result["failure_reason"] = (
                            f"Regex pattern '{regex_pattern}' not found"
                        )

                break  # Exit retry loop on success

            except RequestException as e:
                logger.info(
                    f"\033[93mAttempt {attempt + 1}/{self.retry_limit} failed for {url}: {str(e)}\033[0m"
                )
                if attempt == self.retry_limit - 1:  # Last attempt
                    result["failure_reason"] = f"Request failed: {str(e)}"
                    result["check_details"]["exception_type"] = e.__class__.__name__
            except Exception as e:
                logger.error(
                    f"\033[91mUnexpected error checking {url}: {str(e)}\033[0m"
                )
                result["failure_reason"] = f"Unexpected error: {str(e)}"
                result["check_details"]["exception_type"] = e.__class__.__name__
                break

        # Only log successful results with enhanced color-coded output
        if result["success"]:
            print(
                f"\033[97;42m WEBSITE CHECK \033[0m \033[1;92m✓ SUCCESSFUL\033[0m \033[1;94m{url}\033[0m - "
                f"Status: \033[1;96m{result['http_status']}\033[0m, "
                f"Time: \033[1;93m{result['response_time_ms']:.2f}ms\033[0m, "
                f"Regex Match: \033[1;92m{result['regex_matched']}\033[0m"
            )

        # Log detailed result JSON for debugging and monitoring
        logger.debug(f"Detailed check result for {url}: {result}")

        return result
