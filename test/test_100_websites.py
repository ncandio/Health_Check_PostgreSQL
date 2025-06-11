"""
Tests for the scheduler module with 100 websites.
"""

import unittest
import time
import json
from unittest.mock import MagicMock
import threading
from src.scheduler import Scheduler


class Test100WebsitesScheduler(unittest.TestCase):
    """Test cases for the Scheduler class with 100 websites."""

    def setUp(self):
        """Set up test fixtures."""
        # Use more workers for medium-scale testing
        self.scheduler = Scheduler(max_workers=10)
        
        # Generate 100 domains (base domains with suffixes)
        base_domains = [
            "example", "test", "sample", "demo", "site", 
            "web", "cloud", "app", "dev", "data"
        ]
        
        tlds = [
            ".com", ".org", ".net", ".io", ".co", 
            ".app", ".tech", ".site", ".info", ".dev"
        ]
        
        # Generate 100 domains using combinations of base domains and TLDs
        self.domains = []
        for i in range(10):
            for j in range(10):
                # Create variations like example1.com, test2.org, etc.
                domain = f"{base_domains[i]}{j+1}{tlds[j]}"
                self.domains.append(domain)
        
        # Ensure we have exactly 100 domains
        self.domains = self.domains[:100]
        
    def tearDown(self):
        """Tear down test fixtures."""
        if self.scheduler.is_running():
            self.scheduler.stop()
        time.sleep(1)  # Give time for clean shutdown
    
    def test_100_websites(self):
        """Test scheduler with 100 websites."""
        self.scheduler.start()
        
        # Create simple test functions that can be pickled
        def create_test_func(i):
            def func(domain):
                # Simple simulated website check
                return f"checked_{domain}"
            return func
        
        task_ids = []
        
        # Add 100 tasks
        for i, domain in enumerate(self.domains):
            task_id = self.scheduler.add_task(3, create_test_func(i), domain)
            task_ids.append(task_id)
        
        # Wait for some executions
        time.sleep(3)
        
        # Verify tasks were scheduled
        tasks = self.scheduler.list_tasks()
        self.assertEqual(len(tasks), 100, "Not all tasks were properly scheduled")
        
        # Verify the scheduler is still running
        self.assertTrue(self.scheduler.is_running())
        
        # Check dask status
        dask_status = self.scheduler.get_dask_status()
        self.assertEqual(dask_status["status"], "running")
        
        # Verify the number of workers
        self.assertLessEqual(dask_status["workers"], 10)
        
        # Check that we can get task info for each task
        for task_id in task_ids[:10]:  # Check first 10 tasks
            task_info = self.scheduler.get_task_info(task_id)
            self.assertIsNotNone(task_info)
            self.assertEqual(task_info['task_id'], task_id)
            
        # Test removing some tasks
        for task_id in task_ids[:20]:  # Remove first 20 tasks
            result = self.scheduler.remove_task(task_id)
            self.assertTrue(result)
            
        # Wait for tasks to be fully removed
        time.sleep(4)
        
        # Verify tasks were removed
        tasks = self.scheduler.list_tasks()
        self.assertEqual(len(tasks), 80, "Tasks were not properly removed")
        
        # Check scheduler performance metrics
        dask_status = self.scheduler.get_dask_status()
        self.assertEqual(dask_status["status"], "running")
        self.assertLessEqual(dask_status["tasks_pending"], 10)


if __name__ == "__main__":
    unittest.main()