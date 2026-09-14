from contextlib import AbstractContextManager
from inspect import isfunction
from typing import Self, Callable, Any

from gpiozero import GPIODevice


class GPIOContextManager(AbstractContextManager):

    def __init__(self, *devices: GPIODevice | Callable[[], Any]):
        self._devices = devices
        self._closed = False

    def close(self) -> None:
        if self._closed:
            return

        for device in self._devices:
            if isfunction(device):
                device()
            elif isinstance(device, GPIODevice):
                device.close()

        self._closed = True

    def __enter__(self) -> Self:
        self.assert_not_closed()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def assert_not_closed(self):
        if self._closed:
            raise RuntimeError("Context manager is already closed")
