import logging
from collections.abc import Callable
from enum import Enum
from time import sleep
from types import TracebackType
from typing import Self, Final

from drehbert.gpio_pin import GpioOutputPin


class StepperMotorDirection(str, Enum):
    FORWARD = "forward"
    REVERSE = "reverse"


class StepperMotor:

    FULL_STEPS_PER_REVOLUTION: Final[int] = 200
    MICROSTEPS_PER_FULL_STEP: Final[int] = 16
    STEPS_PER_REVOLUTION: Final[int] = FULL_STEPS_PER_REVOLUTION * MICROSTEPS_PER_FULL_STEP
    STEPS_PER_SECOND: Final[float] = 400.0
    DIRECTION_SETUP_DELAY_SECONDS: Final[float] = 0.001

    def __init__(
            self,
            step_pin: GpioOutputPin,
            direction_pin: GpioOutputPin,
            enable_pin: GpioOutputPin,
            sleep_function: Callable[[float], None] = sleep,
    ) -> None:
        self._step_pin = step_pin
        self._direction_pin = direction_pin
        self._enable_pin = enable_pin
        self._sleep = sleep_function
        self._closed = False

        self._step_pin.off()
        self._direction_pin.on()
        self._enable_pin.off()  # enable the motor

    def rotate_one_revolution(self, direction: StepperMotorDirection) -> None:
        self.rotate_steps(self.STEPS_PER_REVOLUTION, direction)

    def rotate_steps(self, count: int, direction: StepperMotorDirection) -> None:
        if self._closed:
            raise RuntimeError("Motor is already closed")
        if count < 0:
            raise ValueError("Microstep count must not be negative")
        if count == 0:
            return

        if direction is StepperMotorDirection.FORWARD:
            self._direction_pin.on()
        else:
            self._direction_pin.off()

        self._sleep(self.DIRECTION_SETUP_DELAY_SECONDS)
        half_period_seconds = 0.5 / self.STEPS_PER_SECOND

        try:
            for step_idx in range(count):
                self._step_pin.on()
                self._sleep(half_period_seconds)
                self._step_pin.off()
                self._sleep(half_period_seconds)
        finally:
            self._step_pin.off()

    def close(self) -> None:
        if self._closed:
            return

        self._step_pin.off()
        self._step_pin.close()
        self._direction_pin.on()
        self._direction_pin.close()
        self._enable_pin.on()  # disables the motor
        self._enable_pin.close()

        self._closed = True

    def __enter__(self) -> Self:
        if self._closed:
            raise RuntimeError("Motor is already closed")
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
    ) -> None:
        self.close()
