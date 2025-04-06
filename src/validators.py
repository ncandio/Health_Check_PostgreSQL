"""
Validation functions for website monitor configuration.
"""

import re
import logging
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """Validate a URL.

    Args:
        url: URL to validate

    Returns:
        Whether the URL is valid
    """
    # Basic URL validation pattern
    pattern = re.compile(
        r"^(https?://)"  # http:// or https://
        r"([a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)"  # domain
        r"(:\d+)?"  # optional port
        r"(/[-a-zA-Z0-9_%/.~]*)?"  # optional path
        r"(\?[-a-zA-Z0-9_%&=]*)?"  # optional query
        r"(#[-a-zA-Z0-9_]*)?$"  # optional fragment
    )
    return bool(pattern.match(url))


def validate_check_interval(interval: int) -> bool:
    """Validate a check interval.

    Args:
        interval: Check interval in seconds

    Returns:
        Whether the interval is valid (5-300 seconds)
    """
    return 5 <= interval <= 300


def validate_regex_pattern(pattern: Optional[str]) -> bool:
    """Validate a regex pattern.

    Args:
        pattern: Regex pattern to validate

    Returns:
        Whether the pattern is valid
    """
    if pattern is None:
        return True

    try:
        re.compile(pattern)
        return True
    except re.error:
        return False


def validate_website_config(config: Dict[str, Any]) -> List[str]:
    """Validate a website configuration.

    Args:
        config: Website configuration dictionary

    Returns:
        List of validation errors, empty if valid
    """
    errors = []

    # Check URL
    url = config.get("url")
    if not url:
        errors.append("URL is required")
    elif not validate_url(url):
        errors.append(f"Invalid URL: {url}")

    # Check interval
    interval = config.get("check_interval_seconds")
    if interval is None:
        errors.append("Check interval is required")
    elif not isinstance(interval, int):
        errors.append("Check interval must be an integer")
    elif not validate_check_interval(interval):
        errors.append(
            f"Check interval must be between 5 and 300 seconds, got {interval}"
        )

    # Check regex pattern
    pattern = config.get("regex_pattern")
    if pattern is not None and not validate_regex_pattern(pattern):
        errors.append(f"Invalid regex pattern: {pattern}")

    return errors
