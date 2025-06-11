"""
Tests for the scheduler module with 1000 websites.
"""

import unittest
import time
import json
import random
import string
from unittest.mock import MagicMock
import threading
from src.scheduler import Scheduler


class Test1000WebsitesScheduler(unittest.TestCase):
    """Test cases for the Scheduler class with 1000 websites."""

    def setUp(self):
        """Set up test fixtures."""
        # Use more workers for high-load testing
        self.scheduler = Scheduler(max_workers=30)
        
        # Generate 1000 domains
        self.domains = self._generate_1000_domains()
        
    def _generate_1000_domains(self):
        """Generate 1000 random domains."""
        domains = []
        
        # Common TLDs
        tlds = [".com", ".org", ".net", ".io", ".co", ".app", 
                ".tech", ".site", ".info", ".dev", ".ai", ".xyz"]
        
        # Base words to make domains more realistic
        base_words = ["app", "tech", "cloud", "data", "web", "dev", "api", 
                     "service", "platform", "tool", "system", "net", "soft",
                     "info", "solution", "digital", "cyber", "meta", "site",
                     "host", "server", "compute", "code", "build", "deploy"]
        
        # Generate 1000 unique domains
        while len(domains) < 1000:
            # Create domain with format: random_word + number + tld
            word = random.choice(base_words)
            random_chars = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 7)))
            number = random.randint(1, 999)
            tld = random.choice(tlds)
            
            domain = f"{word}{random_chars}{number}{tld}"
            if domain not in domains:
                domains.append(domain)
                
        return domains
        
    def tearDown(self):
        """Tear down test fixtures."""
        if self.scheduler.is_running():
            self.scheduler.stop()
        time.sleep(2)  # Give time for clean shutdown
    
    def test_1000_websites(self):
        """Test scheduler with 1000 websites."""
        self.scheduler.start()
        
        # Create simple test functions that can be pickled
        def create_test_func(i):
            def func(domain):
                # Simple simulated website check
                return f"checked_{domain}"
            return func
        
        task_ids = []
        
        # Add 1000 tasks in batches to avoid overwhelming the scheduler
        batch_size = 200
        for batch_start in range(0, 1000, batch_size):
            batch_end = min(batch_start + batch_size, 1000)
            for i, domain in enumerate(self.domains[batch_start:batch_end]):
                idx = batch_start + i
                task_id = self.scheduler.add_task(10, create_test_func(idx), domain)
                task_ids.append(task_id)
            
            # Small delay between batches
            time.sleep(0.5)
        
        # Wait for some executions
        time.sleep(5)
        
        # Verify tasks were scheduled
        tasks = self.scheduler.list_tasks()
        self.assertEqual(len(tasks), 1000, "Not all tasks were properly scheduled")
        
        # Verify the scheduler is still running
        self.assertTrue(self.scheduler.is_running())
        
        # Check dask status
        dask_status = self.scheduler.get_dask_status()
        self.assertEqual(dask_status["status"], "running")
        
        # Verify the number of workers
        self.assertLessEqual(dask_status["workers"], 30)
        
        # Check that we can get task info for a sample of tasks
        sample_tasks = random.sample(task_ids, 20)  # Check 20 random tasks
        for task_id in sample_tasks:
            task_info = self.scheduler.get_task_info(task_id)
            self.assertIsNotNone(task_info)
            self.assertEqual(task_info['task_id'], task_id)
            
        # Test removing some tasks
        tasks_to_remove = random.sample(task_ids, 200)  # Remove 200 random tasks
        for task_id in tasks_to_remove:
            result = self.scheduler.remove_task(task_id)
            self.assertTrue(result)
            
        # Wait for tasks to be fully removed
        time.sleep(5)
        
        # Verify tasks were removed
        tasks = self.scheduler.list_tasks()
        self.assertEqual(len(tasks), 800, "Tasks were not properly removed")
        
        # Check scheduler performance metrics
        dask_status = self.scheduler.get_dask_status()
        self.assertEqual(dask_status["status"], "running")
        
        # Check memory usage (this might not be available in all environments)
        if "memory_usage_percent" in dask_status:
            self.assertLessEqual(dask_status["memory_usage_percent"], 90, 
                                "Memory usage is too high")


if __name__ == "__main__":
    unittest.main()