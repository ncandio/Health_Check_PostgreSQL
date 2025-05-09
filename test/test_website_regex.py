"""
Tests for regex pattern matching on real websites.
"""

import unittest
import os
import sys
import time
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the project modules
from src.monitor import WebsiteMonitor


class TestWebsiteRegex(unittest.TestCase):
    """Test cases for regex pattern matching on real websites."""

    def setUp(self):
        """Set up test environment."""
        # Create a WebsiteMonitor instance with a shorter timeout and fewer retries for testing
        self.monitor = WebsiteMonitor(timeout=5, retry_limit=2)
        
        # Define test websites and regex patterns
        self.instagram_url = "https://www.instagram.com/"
        self.reddit_url = "https://www.reddit.com/"
        
        # Define patterns that should match
        self.instagram_match_pattern = r"Instagram"
        self.reddit_match_pattern = r"Reddit"
        
        # Define patterns that should not match
        self.instagram_no_match_pattern = r"ThisShouldNeverAppearOnInstagramHomepage123456789"
        self.reddit_no_match_pattern = r"ThisShouldNeverAppearOnRedditHomepage987654321"

    def tearDown(self):
        """Clean up after each test."""
        pass

    def test_instagram_availability(self):
        """Test basic availability of Instagram."""
        result = self.monitor.check_website(self.instagram_url)
        
        self.assertTrue(result["success"], 
                       f"Instagram should be available but got failure: {result.get('failure_reason')}")
        self.assertIsNotNone(result["http_status"], "HTTP status code should be present")
        self.assertIsNotNone(result["response_time_ms"], "Response time should be present")
    
    def test_reddit_availability(self):
        """Test basic availability of Reddit."""
        result = self.monitor.check_website(self.reddit_url)
        
        self.assertTrue(result["success"], 
                       f"Reddit should be available but got failure: {result.get('failure_reason')}")
        self.assertIsNotNone(result["http_status"], "HTTP status code should be present")
        self.assertIsNotNone(result["response_time_ms"], "Response time should be present")

    def test_instagram_match_pattern(self):
        """Test a regex pattern that should match on Instagram."""
        try:
            result = self.monitor.check_website(self.instagram_url, self.instagram_match_pattern)
            
            self.assertTrue(result["success"], 
                          f"Instagram check with matching pattern should succeed but got: {result.get('failure_reason')}")
            self.assertTrue(result["regex_matched"], 
                          "The pattern should match Instagram content")
            self.assertIn("regex_match", result["check_details"], 
                         "Match details should be present")
        except Exception as e:
            self.fail(f"Test failed with exception: {str(e)}")

    def test_reddit_match_pattern(self):
        """Test a regex pattern that should match on Reddit."""
        try:
            result = self.monitor.check_website(self.reddit_url, self.reddit_match_pattern)
            
            self.assertTrue(result["success"], 
                          f"Reddit check with matching pattern should succeed but got: {result.get('failure_reason')}")
            self.assertTrue(result["regex_matched"], 
                          "The pattern should match Reddit content")
            self.assertIn("regex_match", result["check_details"], 
                         "Match details should be present")
        except Exception as e:
            self.fail(f"Test failed with exception: {str(e)}")

    def test_instagram_no_match_pattern(self):
        """Test a regex pattern that should not match on Instagram."""
        result = self.monitor.check_website(self.instagram_url, self.instagram_no_match_pattern)
        
        self.assertFalse(result["success"], 
                        "Check should fail when pattern doesn't match")
        self.assertFalse(result["regex_matched"], 
                        "The pattern should not match Instagram content")
        self.assertIsNotNone(result["failure_reason"], 
                            "A failure reason should be provided")
        self.assertIn("Regex pattern", result["failure_reason"], 
                     "Failure reason should mention regex pattern")

    def test_reddit_no_match_pattern(self):
        """Test a regex pattern that should not match on Reddit."""
        result = self.monitor.check_website(self.reddit_url, self.reddit_no_match_pattern)
        
        self.assertFalse(result["success"], 
                        "Check should fail when pattern doesn't match")
        self.assertFalse(result["regex_matched"], 
                        "The pattern should not match Reddit content")
        self.assertIsNotNone(result["failure_reason"], 
                            "A failure reason should be provided")
        self.assertIn("Regex pattern", result["failure_reason"], 
                     "Failure reason should mention regex pattern")

    def test_error_handling_invalid_url(self):
        """Test error handling with an invalid URL."""
        invalid_url = "https://thisurldoesnotexist123456789.com/"
        result = self.monitor.check_website(invalid_url)
        
        self.assertFalse(result["success"], 
                        "Check should fail for invalid URL")
        self.assertIsNotNone(result["failure_reason"], 
                            "A failure reason should be provided")
        self.assertIn("exception_type", result["check_details"], 
                     "Exception details should be present")

    def test_error_handling_invalid_regex(self):
        """Test error handling with an invalid regex pattern."""
        # This regex pattern has an unclosed group which should cause an error
        invalid_regex = r"Instagram(unclosed.group"
        
        result = self.monitor.check_website(self.instagram_url, invalid_regex)
        
        # Based on the monitor implementation, the success may still be True
        # but we should have a failure_reason and exception_type
        self.assertIsNotNone(result["failure_reason"], "A failure reason should be provided")
        self.assertIn("exception_type", result["check_details"], "Exception details should be present")
        self.assertTrue("error" in result["failure_reason"].lower(), 
                       "Failure reason should mention an error")


if __name__ == "__main__":
    unittest.main()