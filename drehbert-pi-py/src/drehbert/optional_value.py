from typing import overload


class OptionalValue[T]:

    def __init__(self, name: str = "value") -> None:
        self._name = name
        self._value: T | None = None

    @overload
    def __call__(self) -> T:
        ...

    @overload
    def __call__(self, value: T) -> None:
        ...

    def __call__(self, value: T | None = None) -> T | None:
        if value is not None:
            self.set(value)
        return self.get()

    def set(self, value: T) -> None:
        self._value = value

    def get(self) -> T:
        if self._value is None:
            raise RuntimeError(f"{self._name} is not set")

        return self._value

    def is_set(self) -> bool:
        return self._value is not None

    def reset(self) -> None:
        self._value = None
