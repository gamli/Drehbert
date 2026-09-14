from collections.abc import Callable
from contextlib import AbstractContextManager, ExitStack
from typing import Any, Self

from gpiozero import GPIODevice


type GPIOResource = GPIODevice | Callable[[], Any]


class GPIOContextManager(AbstractContextManager):

    def __init__(self, *resources: GPIOResource):
        for resource in resources:
            if not isinstance(resource, GPIODevice) and not callable(resource):
                raise TypeError("GPIO resources must be GPIODevice instances or callables")

        self._resources = resources
        self._closed = False

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True

        # ExitStack invokes callbacks in reverse registration order and still
        # attempts the remaining cleanups if one of them raises.
        with ExitStack() as cleanup_stack:
            for resource in self._resources:
                cleanup = resource.close if isinstance(resource, GPIODevice) else resource
                cleanup_stack.callback(cleanup)

    def __enter__(self) -> Self:
        self.assert_not_closed()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def assert_not_closed(self) -> None:
        if self._closed:
            raise RuntimeError("Context manager is already closed")
