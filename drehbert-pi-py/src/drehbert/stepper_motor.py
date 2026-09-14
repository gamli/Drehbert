import logging
from collections.abc import Callable
from enum import Enum
from time import sleep
from typing import Any, Final

from gpiozero import OutputDevice

from drehbert.gpio_constants import GPIO_MOTOR_STEP, GPIO_MOTOR_DIR, GPIO_MOTOR_ENABLE
from drehbert.gpio_context_manager import GPIOContextManager


class StepperMotorDirection(str, Enum):
    FORWARD = "forward"
    REVERSE = "reverse"


LOGGER = logging.getLogger(__name__)


class StepperMotor(GPIOContextManager):

    def __init__(
            self,
            *,
            full_steps_per_revolution=200,
            microsteps_per_full_step=16,
            set_dir_delay_seconds=0.001,
            max_steps_per_second=100,
            sleep_function: Callable[[float], None] = sleep,
            pin_factory: Any | None = None,
    ):
        self._full_steps_per_revolution: Final[int] = full_steps_per_revolution
        self._microsteps_per_full_step: Final[int] = microsteps_per_full_step
        self._steps_per_revolution: Final[int] = full_steps_per_revolution * microsteps_per_full_step
        self._set_dir_delay_seconds: Final[float] = set_dir_delay_seconds
        self._max_steps_per_second: Final[int] = max_steps_per_second

        self._sleep: Final[Callable[[float], None]] = sleep_function

        self._motor_step: Final[OutputDevice] = OutputDevice(GPIO_MOTOR_STEP, pin_factory=pin_factory)
        self._motor_dir: Final[OutputDevice] = OutputDevice(GPIO_MOTOR_DIR, pin_factory=pin_factory)
        self._motor_enable: Final[OutputDevice] = (
            OutputDevice(GPIO_MOTOR_ENABLE, initial_value=True, active_high=False, pin_factory=pin_factory)
        )

        # noinspection unused-parameter (it is only to convert any lambda return value to none)
        def to_none(*args): return None

        super().__init__(
            lambda: to_none(self._motor_step.off()),
            lambda: to_none(self._motor_dir.off()),
            lambda: to_none(self._motor_enable.off()),
        )

        self._current_step: int = 0

    def reset(self) -> None:
        self._current_step = 0

    def rotate_to_degrees(self, degrees: float) -> None:
        target_degrees_steps = round((degrees * self._steps_per_revolution) / 360.0)
        step_diff = target_degrees_steps - self._current_step
        self.rotate_steps(step_diff, StepperMotorDirection.FORWARD)

    def rotate_one_revolution(self, direction: StepperMotorDirection) -> None:
        self.rotate_steps(self._steps_per_revolution, direction)

    def rotate_steps(self, step_count: int, direction: StepperMotorDirection) -> None:
        self.assert_not_closed()

        # not really needed, but saves a bit of time on zero steps
        if step_count == 0:
            return

        # we support negative steps by reversing the direction
        if step_count < 0:
            step_count = -step_count
            if direction is StepperMotorDirection.FORWARD:
                direction = StepperMotorDirection.REVERSE
            else:
                direction = StepperMotorDirection.FORWARD

        self._set_dir(direction)

        # LOGGER.info(f"Start revolution ENABLE={self._motor_enable.is_active} ; DIR={self._motor_dir.value}/{direction}")

        for step_idx in range(step_count):
            # LOGGER.info(f"Step {step_idx} ENABLE={self._motor_enable.is_active} ; DIR={self._motor_dir.value}/{direction}")
            self._advance_one_step_in_current_direction()

    def _advance_one_step_in_current_direction(self):
        try:

            half_step_duration_seconds = 0.5 / self._max_steps_per_second
            # turn the pin on for MOTOR_HALF_PERIOD_SECONDS
            self._motor_step.on()
            self._sleep(half_step_duration_seconds)
            # and turn the pin off again
            self._motor_step.off()
            # wait for the other half of the period for an even pattern
            self._sleep(half_step_duration_seconds)

            if self._motor_dir.is_active:
                self._current_step = (self._current_step + 1) % self._steps_per_revolution
            else:
                self._current_step = (self._current_step - 1) % self._steps_per_revolution

        finally:
            # if anything happens, we try to turn the pin off
            self._motor_step.off()

    def _set_dir(self, direction: StepperMotorDirection):
        # we only change the pin and wait if the direction actually changed
        if direction is StepperMotorDirection.FORWARD:
            if not self._motor_dir.is_active:
                self._motor_dir.on()
                self._sleep(self._set_dir_delay_seconds)
        else:
            if self._motor_dir.is_active:
                self._motor_dir.off()
                self._sleep(self._set_dir_delay_seconds)
