from typing import Callable
from drehbert.stepper_motor import StepperMotor
from tests.fake_gpio_pin import FakeGpioPin


def create_fake_stepper_motor(
        sleep_function: Callable[[float], None] | None = None
) -> tuple[StepperMotor, FakeGpioPin, FakeGpioPin, FakeGpioPin, list[float]]:
    step_pin = FakeGpioPin()
    direction_pin = FakeGpioPin()
    enable_pin = FakeGpioPin()
    sleeps: list[float] = []

    def combined_sleep_function(timestamp: float):
        sleeps.append(timestamp)
        if sleep_function is not None:
            sleep_function(timestamp)

    motor = StepperMotor(
        step_pin=step_pin,
        direction_pin=direction_pin,
        enable_pin=enable_pin,
        sleep_function=combined_sleep_function,
    )
    return motor, step_pin, direction_pin, enable_pin, sleeps
