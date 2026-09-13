from drehbert.gpio_pin import GpioPin
from gpiozero import OutputDevice
from drehbert.stepper_motor import StepperMotor


def create_stepper_motor_on_a4988_on_raspi_gpio() -> StepperMotor:
    step_pin = OutputDevice(20, active_high=True, initial_value=False)

    try:
        direction_pin = OutputDevice(16, active_high=True, initial_value=False)
    except BaseException:
        step_pin.close()
        raise

    try:
        enable_pin = OutputDevice(21, active_high=True, initial_value=False)
    except BaseException:
        direction_pin.close()
        step_pin.close()
        raise

    return StepperMotor(
        step_pin=step_pin,
        direction_pin=direction_pin,
        enable_pin=enable_pin
    )
