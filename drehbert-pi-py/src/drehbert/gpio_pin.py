from typing import Protocol


class GpioPin(Protocol):
    """Small GPIO protocol that fakes can implement in unit tests."""

    def on(self) -> None: ...

    def off(self) -> None: ...

    def close(self) -> None: ...
