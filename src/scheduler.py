"""
Custom scheduler implementation for website monitoring.
Handles concurrent execution of monitoring tasks with different intervals.
"""

import heapq
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Task:
    """Represents a scheduled task with an execution time and callback."""

    def __init__(
        self,
        task_id: int,
        next_run: float,
        interval: float,
        callback: Callable,
        args: tuple,
    ):
        """Initialize a task.

        Args:
            task_id: Unique task identifier
            next_run: Next execution time (timestamp)
            interval: Execution interval in seconds
            callback: Function to call
            args: Arguments for the callback function
        """
        self.task_id = task_id
        self.next_run = next_run
        self.interval = interval
        self.callback = callback
        self.args = args
        self.last_run = None
        self.is_running = False
        self.error_count = 0

    def __lt__(self, other):
        """Compare tasks based on next execution time."""
        return self.next_run < other.next_run


class Scheduler:
    """Handles scheduling and execution of periodic tasks with different intervals."""

    def __init__(self, max_workers: int = 10):
        """Initialize the scheduler.

        Args:
            max_workers: Maximum number of concurrent worker threads
        """
        self.tasks = []  # Priority queue of tasks
        self.tasks_lock = threading.Lock()
        self.running = False
        self.scheduler_thread = None
        self.task_counter = 0
        self.workers_semaphore = threading.Semaphore(max_workers)
        self.task_map = {}  # Maps task_id to task for quick lookup
        self.stop_event = threading.Event()

    def add_task(self, interval: float, callback: Callable, *args) -> int:
        """Add a new task to the scheduler.

        Args:
            interval: Execution interval in seconds
            callback: Function to call
            args: Arguments for the callback function

        Returns:
            Task ID
        """
        with self.tasks_lock:
            self.task_counter += 1
            task_id = self.task_counter
            next_run = time.time()

            task = Task(task_id, next_run, interval, callback, args)
            self.task_map[task_id] = task
            heapq.heappush(self.tasks, task)
            logger.info(f"Added task {task_id} with interval {interval}s")

        return task_id

    def remove_task(self, task_id: int) -> bool:
        """Remove a task from the scheduler.

        Args:
            task_id: ID of the task to remove

        Returns:
            Whether the task was removed
        """
        with self.tasks_lock:
            if task_id in self.task_map:
                # Mark the task for removal by setting interval to -1
                # Actual removal will happen during next task processing
                self.task_map[task_id].interval = -1
                logger.info(f"Marked task {task_id} for removal")
                return True
            return False

    def _worker(self, task):
        """Worker thread that executes a task."""
        try:
            task.is_running = True
            task.last_run = time.time()
            task.callback(*task.args)
        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")
            task.error_count += 1
        finally:
            task.is_running = False
            self.workers_semaphore.release()

    def _scheduler_loop(self):
        """Main scheduler loop that dispatches tasks at their scheduled times."""
        while not self.stop_event.is_set() and self.running:
            now = time.time()
            next_task = None
            next_task_time = now + 60  # Default sleep time if no tasks

            with self.tasks_lock:
                if self.tasks and self.tasks[0].next_run <= now:
                    task = heapq.heappop(self.tasks)

                    # Check if task was marked for removal
                    if task.interval < 0:
                        if task.task_id in self.task_map:
                            del self.task_map[task.task_id]
                            logger.info(f"Removed task {task.task_id}")
                    else:
                        # Skip if the task is already running
                        if task.is_running:
                            # Re-schedule with a small delay to check again
                            task.next_run = now + 1
                            heapq.heappush(self.tasks, task)
                            continue

                        # Schedule next execution
                        task.next_run = now + task.interval
                        heapq.heappush(self.tasks, task)
                        next_task = task

                # Calculate time until next task
                if self.tasks:
                    next_task_time = self.tasks[0].next_run

            if next_task:
                # Acquire worker semaphore
                self.workers_semaphore.acquire()
                # Start worker thread
                threading.Thread(
                    target=self._worker, args=(next_task,), daemon=True
                ).start()
            else:
                # Sleep until next task or max 5 seconds
                sleep_time = min(max(0.1, next_task_time - time.time()), 5)
                if sleep_time > 0:
                    self.stop_event.wait(sleep_time)

    def start(self):
        """Start the scheduler."""
        if not self.running:
            self.running = True
            self.stop_event.clear()
            self.scheduler_thread = threading.Thread(
                target=self._scheduler_loop, daemon=True
            )
            self.scheduler_thread.start()
            logger.info("Scheduler started")

            # Give the scheduler a moment to fully initialize
            time.sleep(0.5)

    def stop(self):
        """Stop the scheduler."""
        if self.running:
            self.running = False
            self.stop_event.set()
            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=5.0)
            logger.info("Scheduler stopped")

    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self.running

    def get_task_info(self, task_id: int) -> Optional[Dict]:
        """Get information about a task.

        Args:
            task_id: ID of the task

        Returns:
            Dictionary with task information or None if task doesn't exist
        """
        with self.tasks_lock:
            if task_id in self.task_map:
                task = self.task_map[task_id]
                return {
                    "task_id": task.task_id,
                    "interval": task.interval,
                    "next_run": task.next_run,
                    "next_run_time": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(task.next_run)
                    ),
                    "last_run": task.last_run,
                    "last_run_time": (
                        time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime(task.last_run)
                        )
                        if task.last_run
                        else None
                    ),
                    "is_running": task.is_running,
                    "error_count": task.error_count,
                }
            return None

    def list_tasks(self) -> List[Dict]:
        """List all tasks and their status.

        Returns:
            List of dictionaries with task information
        """
        result = []
        with self.tasks_lock:
            for task_id, task in self.task_map.items():
                result.append(
                    {
                        "task_id": task.task_id,
                        "interval": task.interval,
                        "next_run": task.next_run,
                        "next_run_time": time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime(task.next_run)
                        ),
                        "last_run": task.last_run,
                        "last_run_time": (
                            time.strftime(
                                "%Y-%m-%d %H:%M:%S", time.localtime(task.last_run)
                            )
                            if task.last_run
                            else None
                        ),
                        "is_running": task.is_running,
                        "error_count": task.error_count,
                    }
                )
        return result

    def get_dask_status(self) -> Dict:
        """Get status information about the scheduler.

        Returns:
            Dictionary with status information
        """
        return {
            "status": "running" if self.running else "stopped",
            "workers": self.workers_semaphore._value,
            "tasks_pending": len([t for t in self.task_map.values() if t.is_running]),
            "tasks_total": len(self.task_map),
        }
