class OptionalValue[T]:

    def __init__(self, name: str = "value") -> None:
        self._name = name
        self._value: T | None = None

    def set(self, value: T) -> None:
        self._value = value

    def get(self) -> T:
        if self._value is None:
            raise RuntimeError(f"{self._name} is not set")

        return self._value
