from collections.abc import Callable
from enum import StrEnum
from math import isfinite
from time import sleep
from typing import Any, Final

from gpiozero import OutputDevice

from drehbert.gpio_constants import GPIO_MOTOR_DIR, GPIO_MOTOR_ENABLE, GPIO_MOTOR_STEP
from drehbert.gpio_context_manager import GPIOContextManager


class StepperMotorDirection(StrEnum):
    FORWARD = "forward"
    REVERSE = "reverse"


class StepperMotor(GPIOContextManager):

    def __init__(
            self,
            *,
            full_steps_per_revolution: int = 200,
            configured_microsteps_per_full_step: int = 16,
            set_dir_delay_seconds: float = 0.001,
            microsteps_per_second: int = 400,
            step_pulse_seconds: float = 0.000_010,
            sleep_function: Callable[[float], None] = sleep,
            pin_factory: Any | None = None,
    ):
        self._require_positive_int("full_steps_per_revolution", full_steps_per_revolution)
        self._require_positive_int(
            "configured_microsteps_per_full_step",
            configured_microsteps_per_full_step,
        )
        self._require_positive_int("microsteps_per_second", microsteps_per_second)

        if set_dir_delay_seconds < 0:
            raise ValueError("set_dir_delay_seconds must not be negative")
        if step_pulse_seconds <= 0:
            raise ValueError("step_pulse_seconds must be greater than zero")

        step_period_seconds = 1.0 / microsteps_per_second
        if step_pulse_seconds >= step_period_seconds:
            raise ValueError(
                "step_pulse_seconds must be shorter than one microstep period"
            )

        self._steps_per_revolution: Final[int] = (
            full_steps_per_revolution * configured_microsteps_per_full_step
        )
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

        def make_off_close(device: OutputDevice) -> Callable[[], None]:
            def off_close() -> None:
                device.off()
                device.close()

            return off_close

        # Cleanup runs in reverse order, disabling the driver before releasing
        # the direction and step pins.
        super().__init__(
            make_off_close(self._motor_step),
            make_off_close(self._motor_dir),
            make_off_close(self._motor_enable),
        )

        self._current_step = 0

    def set_current_position_as_zero(self) -> None:
        self.assert_not_closed()
        self._current_step = 0

    def rotate_to_degrees(
            self,
            degrees: float,
            direction: StepperMotorDirection,
    ) -> None:
        self.assert_not_closed()
        self._validate_direction(direction)

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
        self.assert_not_closed()
        self._validate_direction(direction)

        if isinstance(step_count, bool) or not isinstance(step_count, int):
            raise TypeError("step_count must be an integer")

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
    def _validate_direction(direction: StepperMotorDirection) -> None:
        if not isinstance(direction, StepperMotorDirection):
            raise TypeError("direction must be a StepperMotorDirection")

    @staticmethod
    def _require_positive_int(name: str, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
