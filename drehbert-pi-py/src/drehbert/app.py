import logging

from drehbert.status_lights import EStatusLightPattern
from drehbert.status_lights_factory import create_status_lights_on_raspi_gpio
from drehbert.stepper_motor_factory import create_stepper_motor_on_a4988_on_raspi_gpio
from drehbert.stepper_motor import StepperMotorDirection

LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Rotate the turntable once and exit."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with create_status_lights_on_raspi_gpio() as status_lights:
        with create_stepper_motor_on_a4988_on_raspi_gpio() as motor:
            status_lights.set_general_pattern(EStatusLightPattern.ON)
            status_lights.set_bluetooth_pattern(EStatusLightPattern.BLINK)
            status_lights.set_turntable_pattern(EStatusLightPattern.OFF)
            status_lights.set_error_pattern(EStatusLightPattern.ON)
            motor.rotate_one_revolution(StepperMotorDirection.FORWARD)

    LOGGER.info("Revolution complete")

    return 0
