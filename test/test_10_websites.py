"""
Tests for the scheduler module with 10 websites.
"""

import unittest
import time
import json
from unittest.mock import MagicMock
import threading
from src.scheduler import Scheduler


class Test10WebsitesScheduler(unittest.TestCase):
    """Test cases for the Scheduler class with 10 websites."""

    def setUp(self):
        """Set up test fixtures."""
        # Use fewer workers for small-scale testing
        self.scheduler = Scheduler(max_workers=4)
        
        # Define 10 popular websites
        self.domains = [
            "google.com",
            "youtube.com",
            "facebook.com",
            "twitter.com",
            "instagram.com",
            "amazon.com",
            "wikipedia.org",
            "reddit.com",
            "linkedin.com",
            "github.com"
        ]
        
    def tearDown(self):
        """Tear down test fixtures."""
        if self.scheduler.is_running():
            self.scheduler.stop()
        time.sleep(1)  # Give time for clean shutdown
    
    def test_10_websites(self):
        """Test scheduler with 10 websites."""
        self.scheduler.start()
        
        # Create simple test functions that can be pickled
        def create_test_func(i):
            def func(domain):
                # Simple simulated website check
                return f"checked_{domain}"
            return func
        
        task_ids = []
        
        # Add 10 tasks
        for i, domain in enumerate(self.domains):
            task_id = self.scheduler.add_task(2, create_test_func(i), domain)
            task_ids.append(task_id)
        
        # Wait for some executions
        time.sleep(3)
        
        # Verify tasks were scheduled
        tasks = self.scheduler.list_tasks()
        self.assertEqual(len(tasks), 10, "Not all tasks were properly scheduled")
        
        # Verify the scheduler is still running
        self.assertTrue(self.scheduler.is_running())
        
        # Check dask status
        dask_status = self.scheduler.get_dask_status()
        self.assertEqual(dask_status["status"], "running")
        
        # Verify the number of workers
        self.assertLessEqual(dask_status["workers"], 4)
        
        # Check that we can get task info for each task
        for task_id in task_ids:
            task_info = self.scheduler.get_task_info(task_id)
            self.assertIsNotNone(task_info)
            self.assertEqual(task_info['task_id'], task_id)
            
        # Test removing some tasks
        for task_id in task_ids[:3]:  # Remove first 3 tasks
            result = self.scheduler.remove_task(task_id)
            self.assertTrue(result)
            
        # Wait for tasks to be fully removed
        time.sleep(3)
        
        # Verify tasks were removed
        tasks = self.scheduler.list_tasks()
        self.assertEqual(len(tasks), 7, "Tasks were not properly removed")
        
        # Check scheduler performance metrics
        dask_status = self.scheduler.get_dask_status()
        self.assertEqual(dask_status["status"], "running")
        self.assertLessEqual(dask_status["tasks_pending"], 5)


if __name__ == "__main__":
    unittest.main()