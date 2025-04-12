"""
Custom scheduler implementation for website monitoring using uvloop event loop.
Handles concurrent execution of monitoring tasks with different intervals.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional
import uvloop
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Task:
    """Represents a scheduled task with an execution time and callback."""

    def __init__(
        self,
        task_id: int,
        interval: float,
        callback: Callable,
        args: tuple,
    ):
        """Initialize a task.

        Args:
            task_id: Unique task identifier
            interval: Execution interval in seconds
            callback: Function to call
            args: Arguments for the callback function
        """
        if asyncio.iscoroutinefunction(callback):
            raise ValueError("Async functions are not supported. Please provide a synchronous function.")
            
        self.task_id = task_id
        self.interval = interval
        self.callback = callback
        self.args = args
        self.last_run = None
        self.is_running = False
        self.error_count = 0
        self.task = None
        self._stop = False
        self._timeout = 300  # 5 minutes timeout for task execution

    async def run(self, scheduler):
        """Run the task periodically."""
        while not self._stop:
            try:
                await scheduler._execute_task(self)
                # Use wait_for to ensure sleep doesn't block indefinitely
                await asyncio.wait_for(asyncio.sleep(self.interval), timeout=self.interval + 1)
            except asyncio.TimeoutError:
                logger.warning(f"Task {self.task_id} sleep timeout, continuing...")
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task {self.task_id} loop: {e}")
                # Use wait_for to ensure sleep doesn't block indefinitely
                try:
                    await asyncio.wait_for(asyncio.sleep(self.interval), timeout=self.interval + 1)
                except asyncio.TimeoutError:
                    logger.warning(f"Task {self.task_id} error recovery sleep timeout, continuing...")
                    continue

    def stop(self):
        """Stop the task."""
        self._stop = True
        if self.task and not self.task.done():
            self.task.cancel()


class Scheduler:
    """Handles scheduling and execution of periodic tasks with different intervals using uvloop."""

    def __init__(self, max_workers: int = 10):
        """Initialize the scheduler.

        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.loop = uvloop.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.tasks: Dict[int, Task] = {}
        self.task_counter = 0
        self.running = False
        self.max_workers = max_workers
        self.active_workers = 0
        self.worker_semaphore = asyncio.Semaphore(max_workers)
        self._stop_event = asyncio.Event()
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._timeout = 300  # 5 minutes timeout for task execution

    async def _execute_task(self, task: Task):
        """Execute a task asynchronously."""
        try:
            task.is_running = True
            task.last_run = time.time()
            
            # Use wait_for to ensure semaphore doesn't block indefinitely
            await asyncio.wait_for(
                self.worker_semaphore.acquire(),
                timeout=task._timeout
            )
            
            self.active_workers += 1
            
            # Run task with timeout
            await asyncio.wait_for(
                self.loop.run_in_executor(
                    self._thread_pool,
                    task.callback,
                    *task.args
                ),
                timeout=task._timeout
            )
                
        except asyncio.TimeoutError:
            logger.error(f"Task {task.task_id} execution timed out after {task._timeout} seconds")
            task.error_count += 1
        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")
            task.error_count += 1
        finally:
            task.is_running = False
            self.active_workers -= 1
            try:
                self.worker_semaphore.release()
            except ValueError:
                # Ignore if semaphore was already released
                pass

    def add_task(self, interval: float, callback: Callable, *args) -> int:
        """Add a new task to the scheduler.

        Args:
            interval: Execution interval in seconds
            callback: Function to call (must be synchronous)
            args: Arguments for the callback function

        Returns:
            Task ID

        Raises:
            ValueError: If callback is an async function
        """
        if asyncio.iscoroutinefunction(callback):
            raise ValueError("Async functions are not supported. Please provide a synchronous function.")

        self.task_counter += 1
        task_id = self.task_counter

        task = Task(task_id, interval, callback, args)
        self.tasks[task_id] = task
        
        if self.running:
            task.task = self.loop.create_task(task.run(self))
        
        logger.info(f"Added task {task_id} with interval {interval}s")
        return task_id

    def remove_task(self, task_id: int) -> bool:
        """Remove a task from the scheduler.

        Args:
            task_id: ID of the task to remove

        Returns:
            Whether the task was removed
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.stop()
            del self.tasks[task_id]
            logger.info(f"Removed task {task_id}")
            return True
        return False

    async def _run(self):
        """Run the scheduler."""
        self.running = True
        self._stop_event.clear()
        
        # Start all existing tasks
        for task in self.tasks.values():
            task.task = self.loop.create_task(task.run(self))
        
        try:
            # Wait for stop signal with timeout
            while not self._stop_event.is_set():
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=1.0  # Check every second
                    )
                except asyncio.TimeoutError:
                    # Check if any tasks are stuck
                    for task_id, task in list(self.tasks.items()):
                        if task.is_running and time.time() - task.last_run > task._timeout:
                            logger.warning(f"Task {task_id} appears stuck, removing...")
                            self.remove_task(task_id)
                    continue
        finally:
            # Stop all tasks
            for task in self.tasks.values():
                task.stop()
            
            self.running = False

    def start(self):
        """Start the scheduler."""
        if not self.running:
            try:
                self.loop.run_until_complete(self._run())
            except KeyboardInterrupt:
                self.stop()
            except Exception as e:
                logger.error(f"Unexpected error in scheduler: {e}")
                self.stop()
            finally:
                self._thread_pool.shutdown(wait=True)
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self.running:
            self._stop_event.set()
            self.loop.stop()
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
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return {
                "task_id": task.task_id,
                "interval": task.interval,
                "last_run": task.last_run,
                "last_run_time": (
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(task.last_run))
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
        return [
            {
                "task_id": task.task_id,
                "interval": task.interval,
                "last_run": task.last_run,
                "last_run_time": (
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(task.last_run))
                    if task.last_run
                    else None
                ),
                "is_running": task.is_running,
                "error_count": task.error_count,
            }
            for task in self.tasks.values()
        ]

    def get_dask_status(self) -> Dict:
        """Get status information about the scheduler.

        Returns:
            Dictionary with status information
        """
        return {
            "status": "running" if self.running else "stopped",
            "workers": self.max_workers - self.active_workers,
            "tasks_pending": len([t for t in self.tasks.values() if t.is_running]),
            "tasks_total": len(self.tasks),
        }
