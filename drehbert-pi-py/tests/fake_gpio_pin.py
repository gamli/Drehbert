from dataclasses import field, dataclass


@dataclass
class FakeGpioPin:
    state: bool = False
    transitions: list[bool] = field(default_factory=list)
    closed: bool = False

    def on(self) -> None:
        self.state = True
        self.transitions.append(True)

    def off(self) -> None:
        self.state = False
        self.transitions.append(False)

    def close(self) -> None:
        self.closed = True

    @property
    def is_active(self) -> bool:
        return self.state
