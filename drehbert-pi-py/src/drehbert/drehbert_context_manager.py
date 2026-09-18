from abc import ABC, abstractmethod
from contextlib import AbstractContextManager, AbstractAsyncContextManager
from enum import StrEnum
from typing import Self


class EDrehbertContextManagerState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class DrehbertContextManager(AbstractContextManager, ABC):

    def __init__(self):
        self._state = EDrehbertContextManagerState.CLOSED

    def __enter__(self) -> Self:
        self.open()
        return self

    def open(self) -> None:
        self._assert_closed()
        self._state = EDrehbertContextManagerState.OPEN
        self._open()

    @abstractmethod
    def _open(self) -> None:
        pass

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        if self._state != EDrehbertContextManagerState.OPEN:
            return
        self._state = EDrehbertContextManagerState.CLOSED
        self._close()

    @abstractmethod
    def _close(self) -> None:
        pass

    def _assert_open(self) -> None:
        if self._state != EDrehbertContextManagerState.OPEN:
            raise RuntimeError("Context manager is not open")

    def _assert_closed(self) -> None:
        if self._state != EDrehbertContextManagerState.CLOSED:
            raise RuntimeError("Context manager is not closed")


class DrehbertAsyncContextManager(AbstractAsyncContextManager, ABC):

    def __init__(self):
        self._state = EDrehbertContextManagerState.CLOSED

    async def __aenter__(self) -> Self:
        await self.open()
        return self

    async def open(self) -> None:
        self._assert_closed()
        self._state = EDrehbertContextManagerState.OPEN
        await self._open()

    @abstractmethod
    async def _open(self) -> None:
        pass

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    async def close(self) -> None:
        if self._state != EDrehbertContextManagerState.OPEN:
            return
        self._state = EDrehbertContextManagerState.CLOSED
        await self._close()

    @abstractmethod
    async def _close(self) -> None:
        pass

    def _assert_open(self) -> None:
        if self._state != EDrehbertContextManagerState.OPEN:
            raise RuntimeError("Context manager is not open")

    def _assert_closed(self) -> None:
        if self._state != EDrehbertContextManagerState.CLOSED:
            raise RuntimeError("Context manager is not closed")
