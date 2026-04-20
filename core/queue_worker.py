import asyncio
from loguru import logger
from typing import Callable, Any, Coroutine

class QueueWorker:
    def __init__(self, max_concurrent: int = 2):
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._running = False
        self.active_tasks = {} # {chat_id: task_object}

    async def add_task(self, chat_id: int, task_func: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs):
        """Add a task to the queue with chat_id tracking."""
        await self.queue.put((chat_id, task_func, args, kwargs))
        logger.info(f"Task added to queue for {chat_id}. Current size: {self.queue.qsize()}")

    async def _worker(self):
        while self._running:
            chat_id, task_func, args, kwargs = await self.queue.get()
            try:
                # Create the task but don't await yet if we want to track it
                # However, semaphore needs to be respected.
                async with self.semaphore:
                    # Current task being executed
                    task = asyncio.current_task()
                    self.active_tasks[chat_id] = task
                    logger.info(f"Executing task for {chat_id} with {task_func.__name__}")
                    try:
                        await task_func(*args, **kwargs)
                    finally:
                        self.active_tasks.pop(chat_id, None)
            except asyncio.CancelledError:
                logger.warning(f"Task for {chat_id} was cancelled.")
            except Exception as e:
                logger.exception(f"Error executing task for {chat_id}: {e}")
            finally:
                self.queue.task_done()

    async def cancel_task(self, chat_id: int):
        if chat_id in self.active_tasks:
            task = self.active_tasks[chat_id]
            task.cancel()
            return True
        return False

    def start(self):
        if not self._running:
            self._running = True
            asyncio.create_task(self._worker())
            logger.info("Queue worker started")

    def stop(self):
        self._running = False
        logger.info("Queue worker stopping")

    @property
    def pending_count(self) -> int:
        return self.queue.qsize()
