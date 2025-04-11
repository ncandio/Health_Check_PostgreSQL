"""
Tests for the scheduler module with 500 websites.
"""

import unittest
import time
import json
from unittest.mock import MagicMock
import threading
from src.scheduler import Scheduler


class Test500WebsitesScheduler(unittest.TestCase):
    """Test cases for the Scheduler class with 500 websites."""

    def setUp(self):
        """Set up test fixtures."""
        # Use more workers for high-load testing
        self.scheduler = Scheduler(max_workers=20)
        
        # Load website URLs from file
        with open('test/500_websites.txt', 'r') as f:
            content = f.read()
            
        # Extract domains from the file (strip numbers and other text)
        self.domains = []
        for line in content.split('\n'):
            if line.strip() and not line.startswith('#'):
                # Extract just the domain part, skipping numbering
                if '.' in line:
                    parts = line.strip().split(' ')
                    domain = next((part for part in parts if '.' in part), None)
                    if domain:
                        self.domains.append(domain)
        
        # Limit to 500 websites if more are present
        self.domains = self.domains[:500]
        
    def tearDown(self):
        """Tear down test fixtures."""
        if self.scheduler.is_running():
            self.scheduler.stop()
        time.sleep(1)  # Give time for clean shutdown
    
    def test_500_websites(self):
        """Test scheduler with 500 websites."""
        self.scheduler.start()
        
        # Create simple test functions that can be pickled
        def create_test_func(i):
            def func(domain):
                # Simple simulated website check
                return f"checked_{domain}"
            return func
        
        task_ids = []
        
        # Add 500 tasks
        for i, domain in enumerate(self.domains):
            task_id = self.scheduler.add_task(5, create_test_func(i), domain)
            task_ids.append(task_id)
        
        # Wait for some executions
        time.sleep(3)
        
        # Verify tasks were scheduled
        tasks = self.scheduler.list_tasks()
        self.assertEqual(len(tasks), 500, "Not all tasks were properly scheduled")
        
        # Verify the scheduler is still running
        self.assertTrue(self.scheduler.is_running())
        
        # Check dask status
        dask_status = self.scheduler.get_dask_status()
        self.assertEqual(dask_status["status"], "running")
        
        # Verify the number of workers
        self.assertLessEqual(dask_status["workers"], 20)
        
        # Check that we can get task info for each task
        for task_id in task_ids[:10]:  # Check first 10 tasks
            task_info = self.scheduler.get_task_info(task_id)
            self.assertIsNotNone(task_info)
            self.assertEqual(task_info['task_id'], task_id)
            
        # Test removing some tasks
        for task_id in task_ids[:50]:  # Remove first 50 tasks
            result = self.scheduler.remove_task(task_id)
            self.assertTrue(result)
            
        # Wait for tasks to be fully removed
        time.sleep(6)
        
        # Verify tasks were removed
        tasks = self.scheduler.list_tasks()
        self.assertEqual(len(tasks), 450, "Tasks were not properly removed")
        
        # Check scheduler performance metrics
        dask_status = self.scheduler.get_dask_status()
        self.assertEqual(dask_status["status"], "running")
        self.assertLessEqual(dask_status["tasks_pending"], 20)


if __name__ == "__main__":
    unittest.main()