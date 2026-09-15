from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Self


class DrehbertContextManager(AbstractContextManager, ABC):

    def __init__(self):
        self._closed = False

    def __enter__(self) -> Self:
        self._assert_not_closed()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._close()

    @abstractmethod
    def _close(self) -> None: ...

    def _assert_not_closed(self) -> None:
        if self._closed:
            raise RuntimeError("Context manager is already closed")
