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
                # Limit concurrency using semaphore
                await self.semaphore.acquire()
                
                # Create a NEW task for the actual work so it can be cancelled
                # without killing this worker loop.
                task = asyncio.create_task(self._run_task(chat_id, task_func, *args, **kwargs))
                self.active_tasks[chat_id] = task
                
            except Exception as e:
                logger.exception(f"Error preparing task for {chat_id}: {e}")
                self.queue.task_done()
                if self.semaphore.locked():
                    self.semaphore.release()

    async def _run_task(self, chat_id: int, task_func: Callable, *args, **kwargs):
        try:
            logger.info(f"Executing task for {chat_id} with {task_func.__name__}")
            await task_func(*args, **kwargs)
        except asyncio.CancelledError:
            logger.warning(f"Task for {chat_id} was successfully cancelled.")
        except Exception as e:
            logger.exception(f"Error executing task for {chat_id}: {e}")
        finally:
            self.active_tasks.pop(chat_id, None)
            self.semaphore.release()
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
