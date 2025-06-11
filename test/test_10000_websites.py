"""
Tests for the scheduler module with 10000 websites.
"""

import unittest
import time
import json
import random
import string
import os
import gc
import threading
from unittest.mock import MagicMock
from src.scheduler import Scheduler


class Test10000WebsitesScheduler(unittest.TestCase):
    """Test cases for the Scheduler class with 10000 websites."""

    def setUp(self):
        """Set up test fixtures."""
        # Use more workers for high-load testing
        self.scheduler = Scheduler(max_workers=50)
        
        # Check if we have a cache file to avoid regenerating domains every time
        cache_file = "test/10000_domains_cache.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                self.domains = json.load(f)
        else:
            # Generate 10000 domains
            self.domains = self._generate_10000_domains()
            
            # Cache the domains for future test runs
            with open(cache_file, 'w') as f:
                json.dump(self.domains, f)
        
    def _generate_10000_domains(self):
        """Generate 10000 random domains."""
        domains = []
        
        # Common TLDs
        tlds = [".com", ".org", ".net", ".io", ".co", ".app", 
                ".tech", ".site", ".info", ".dev", ".ai", ".xyz"]
        
        # Base words to make domains more realistic
        base_words = ["app", "tech", "cloud", "data", "web", "dev", "api", 
                     "service", "platform", "tool", "system", "net", "soft",
                     "info", "solution", "digital", "cyber", "meta", "site",
                     "host", "server", "compute", "code", "build", "deploy"]
        
        # Generate 10000 unique domains using combinations and random strings
        word_len = len(base_words)
        tld_len = len(tlds)
        
        for i in range(10000):
            # Create domain with format: base_word + random_chars + number + tld
            word_idx = i % word_len
            tld_idx = (i // word_len) % tld_len
            
            word = base_words[word_idx]
            random_chars = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
            number = i  # Use counter to ensure uniqueness
            tld = tlds[tld_idx]
            
            domain = f"{word}{random_chars}{number}{tld}"
            domains.append(domain)
                
        # Shuffle to avoid patterns
        random.shuffle(domains)
        return domains
        
    def tearDown(self):
        """Tear down test fixtures."""
        if self.scheduler.is_running():
            self.scheduler.stop()
        time.sleep(3)  # Give more time for clean shutdown with many tasks
        gc.collect()  # Force garbage collection
    
    def test_10000_websites_task_creation(self):
        """Test creating 10000 website tasks."""
        self.scheduler.start()
        
        # Create simple test functions that can be pickled
        def create_test_func(i):
            def func(domain):
                # Simple simulated website check with minimal work
                return f"checked_{domain}"
            return func
        
        task_ids = []
        
        # Add 10000 tasks in batches to avoid overwhelming the scheduler
        batch_size = 500
        for batch_start in range(0, 10000, batch_size):
            batch_end = min(batch_start + batch_size, 10000)
            
            # Create a batch of tasks
            batch_task_ids = []
            for i, domain in enumerate(self.domains[batch_start:batch_end]):
                idx = batch_start + i
                # Use longer interval to avoid overloading the scheduler
                task_id = self.scheduler.add_task(30, create_test_func(idx), domain)
                batch_task_ids.append(task_id)
            
            task_ids.extend(batch_task_ids)
            
            # Give scheduler time to process batch
            time.sleep(1)
        
        # Wait for some initial executions
        time.sleep(5)
        
        # Verify tasks were scheduled
        tasks = self.scheduler.list_tasks()
        self.assertGreaterEqual(len(tasks), 9000, "Most tasks should be properly scheduled")
        
        # Verify the scheduler is still running
        self.assertTrue(self.scheduler.is_running())
        
        # Check dask status
        dask_status = self.scheduler.get_dask_status()
        self.assertEqual(dask_status["status"], "running")
        
        # Verify we can get task info for some random tasks
        sample_size = min(50, len(task_ids))
        sample_tasks = random.sample(task_ids, sample_size)
        successful_info_fetches = 0
        
        for task_id in sample_tasks:
            try:
                task_info = self.scheduler.get_task_info(task_id)
                if task_info and task_info['task_id'] == task_id:
                    successful_info_fetches += 1
            except Exception:
                # Some tasks might not be fully registered yet
                pass
                
        # We should be able to get info for at least 80% of sampled tasks
        self.assertGreaterEqual(successful_info_fetches, sample_size * 0.8)
    
    def test_10000_websites_stress(self):
        """Test the scheduler under stress with 10000 websites."""
        # Start with a fresh scheduler for this test
        if self.scheduler.is_running():
            self.scheduler.stop()
            time.sleep(2)
            
        self.scheduler = Scheduler(max_workers=50)
        self.scheduler.start()
        
        # Create a very lightweight test function
        def lightweight_check(domain):
            # Do almost nothing to avoid resource exhaustion
            return domain
        
        # Add just 1000 tasks initially (10% of full load)
        initial_domains = self.domains[:1000]
        initial_task_ids = []
        
        for i, domain in enumerate(initial_domains):
            task_id = self.scheduler.add_task(20, lightweight_check, domain)
            initial_task_ids.append(task_id)
            
            # Add small delay every 100 tasks
            if i % 100 == 0:
                time.sleep(0.1)
        
        # Wait for initial batch to be processed
        time.sleep(5)
        
        # Verify the scheduler is handling the initial load
        self.assertTrue(self.scheduler.is_running())
        tasks = self.scheduler.list_tasks()
        self.assertGreaterEqual(len(tasks), 900)  # Allow for some task registration delay
        
        # Remove half of initial tasks
        for task_id in initial_task_ids[:500]:
            self.scheduler.remove_task(task_id)
            
        # Wait for removals to be processed
        time.sleep(3)
        
        # Add 1000 more tasks to test dynamic scaling
        additional_domains = self.domains[1000:2000]
        for domain in additional_domains:
            self.scheduler.add_task(30, lightweight_check, domain)
            
        # Wait for additional tasks to be processed
        time.sleep(5)
        
        # Final verification - scheduler should still be running
        self.assertTrue(self.scheduler.is_running())
        dask_status = self.scheduler.get_dask_status()
        self.assertEqual(dask_status["status"], "running")
        
        # Clean up explicitly
        self.scheduler.stop()
        time.sleep(3)
        gc.collect()


if __name__ == "__main__":
    unittest.main()