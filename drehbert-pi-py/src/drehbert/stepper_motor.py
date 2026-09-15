from collections.abc import Callable
from enum import StrEnum
from math import isfinite
from time import sleep
from typing import Any, Final

from gpiozero import OutputDevice

from drehbert.gpio_constants import GPIO_MOTOR_DIR, GPIO_MOTOR_ENABLE, GPIO_MOTOR_STEP
from drehbert.drehbert_context_manager import DrehbertContextManager


class StepperMotorDirection(StrEnum):
    FORWARD = "forward"
    REVERSE = "reverse"


class StepperMotor(DrehbertContextManager):

    def __init__(
            self,
            *,
            steps_per_revolution: int = 3200,
            set_dir_delay_seconds: float = 0.001,
            steps_per_second: float = 400.0,
            step_pulse_seconds: float = 0.000_010,
            sleep_function: Callable[[float], None] = sleep,
            pin_factory: Any | None = None,
    ):
        super().__init__()

        self._require_positive_int("steps_per_revolution", steps_per_revolution)
        self._require_non_negative_finite_number(
            "set_dir_delay_seconds",
            set_dir_delay_seconds,
        )
        self._require_positive_finite_number("steps_per_second", steps_per_second)
        self._require_positive_finite_number("step_pulse_seconds", step_pulse_seconds)

        step_period_seconds = 1.0 / steps_per_second
        if step_pulse_seconds >= step_period_seconds:
            raise ValueError(
                "step_pulse_seconds must be shorter than one step period"
            )

        self._steps_per_revolution: Final[int] = steps_per_revolution
        self._set_dir_delay_seconds: Final[float] = set_dir_delay_seconds
        self._step_period_seconds: Final[float] = step_period_seconds
        self._step_pulse_seconds: Final[float] = step_pulse_seconds
        self._sleep: Final[Callable[[float], None]] = sleep_function

        self._motor_step: Final[OutputDevice] = OutputDevice(
            GPIO_MOTOR_STEP,
            pin_factory=pin_factory,
        )
        self._motor_dir: Final[OutputDevice] = OutputDevice(
            GPIO_MOTOR_DIR,
            pin_factory=pin_factory,
        )
        self._motor_enable: Final[OutputDevice] = OutputDevice(
            GPIO_MOTOR_ENABLE,
            initial_value=True,
            active_high=False,
            pin_factory=pin_factory,
        )

        self._current_step = 0

    def _close(self) -> None:
        self._motor_step.off()
        self._motor_step.close()

        self._motor_dir.off()
        self._motor_dir.close()

        self._motor_enable.off()
        self._motor_enable.close()

    def set_current_position_as_zero(self) -> None:
        self._assert_not_closed()
        self._current_step = 0

    def rotate_to_degrees(
            self,
            degrees: float,
            direction: StepperMotorDirection,
    ) -> None:
        self._assert_not_closed()
        self._require_direction(direction)

        if not isfinite(degrees):
            raise ValueError("degrees must be finite")

        target_step = round(
            degrees * self._steps_per_revolution / 360.0
        ) % self._steps_per_revolution

        if direction is StepperMotorDirection.FORWARD:
            step_count = (
                                 target_step - self._current_step
                         ) % self._steps_per_revolution
        else:
            step_count = (
                                 self._current_step - target_step
                         ) % self._steps_per_revolution

        self.rotate_steps(step_count, direction)

    def rotate_one_revolution(self, direction: StepperMotorDirection) -> None:
        self.rotate_steps(self._steps_per_revolution, direction)

    def rotate_steps(self, step_count: int, direction: StepperMotorDirection) -> None:
        self._assert_not_closed()
        self._require_direction(direction)
        self._require_int("step_count", step_count)

        if step_count == 0:
            return

        if step_count < 0:
            step_count = -step_count
            direction = self._reverse_direction(direction)

        self._set_dir(direction)

        for _ in range(step_count):
            self._advance_one_step_in_current_direction()

    def _advance_one_step_in_current_direction(self) -> None:
        try:
            self._motor_step.on()
            self._sleep(self._step_pulse_seconds)
            self._motor_step.off()

            # The A4988 advances on the STEP rising edge. Record the step before
            # waiting out the low part of the period.
            if self._motor_dir.is_active:
                self._current_step = (
                                             self._current_step + 1
                                     ) % self._steps_per_revolution
            else:
                self._current_step = (
                                             self._current_step - 1
                                     ) % self._steps_per_revolution

            self._sleep(self._step_period_seconds - self._step_pulse_seconds)
        finally:
            self._motor_step.off()

    def _set_dir(self, direction: StepperMotorDirection) -> None:
        requested_pin_state = direction is StepperMotorDirection.FORWARD
        if self._motor_dir.is_active != requested_pin_state:
            self._motor_dir.value = requested_pin_state
            self._sleep(self._set_dir_delay_seconds)

    @staticmethod
    def _reverse_direction(direction: StepperMotorDirection) -> StepperMotorDirection:
        if direction is StepperMotorDirection.FORWARD:
            return StepperMotorDirection.REVERSE
        return StepperMotorDirection.FORWARD

    @staticmethod
    def _require_direction(direction: StepperMotorDirection) -> None:
        if not isinstance(direction, StepperMotorDirection):
            raise TypeError("direction must be a StepperMotorDirection")

    @classmethod
    def _require_positive_int(cls, name: str, value: int) -> None:
        cls._require_int(name, value)
        if value <= 0:
            raise ValueError(f"{name} must be a positive integer")

    @staticmethod
    def _require_int(name: str, value: int) -> None:
        # bool is a subclass of int in Python, but is not a meaningful step count.
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")

    @staticmethod
    def _require_positive_finite_number(name: str, value: float) -> None:
        if not isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and greater than zero")

    @staticmethod
    def _require_non_negative_finite_number(name: str, value: float) -> None:
        if not isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and not negative")
