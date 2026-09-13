from typing import Protocol


class GpioOutputPin(Protocol):

    def on(self) -> None: ...

    def off(self) -> None: ...

    def close(self) -> None: ...

    @property
    def is_active(self) -> bool: ...


class GpioDigitalOutputPin(GpioOutputPin, Protocol):

    def blink(self, on_time=1, off_time=1, n=None, background=True) -> None: ...