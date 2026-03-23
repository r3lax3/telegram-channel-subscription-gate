import asyncio
import signal
import logging

from typing import Coroutine, Any


logger = logging.getLogger(__name__)


class AppRunner:
    def __init__(self):
        self._stop_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

    async def run(self, *coros: Coroutine[Any, Any, Any]) -> None:
        """Run coroutines and wait for shutdown signal."""
        loop = asyncio.get_running_loop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._stop_event.set)

        self._tasks = [asyncio.create_task(coro) for coro in coros]

        logger.info("Приложение запущено")
        await self._stop_event.wait()
        await self._shutdown()

    async def _shutdown(self) -> None:
        logger.info("Останавливаем приложение...")

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("Приложение остановлено")
