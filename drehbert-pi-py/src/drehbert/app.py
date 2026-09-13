import logging


from drehbert.stepper_motor_factory import create_stepper_motor_on_a4988_on_raspi_gpio
from drehbert.stepper_motor import StepperMotorDirection

LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Rotate the turntable once and exit."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with create_stepper_motor_on_a4988_on_raspi_gpio() as motor:
        motor.rotate_one_revolution(StepperMotorDirection.FORWARD)

    LOGGER.info("Revolution complete")

    return 0
