import logging
from time import sleep

from drehbert.status_leds import EStatusLEDPattern, StatusLEDs
from drehbert.stepper_motor import StepperMotorDirection, StepperMotor

LOGGER = logging.getLogger(__name__)


def main() -> int:

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with StatusLEDs() as status_leds:
        with StepperMotor() as motor:
            status_leds.general(EStatusLEDPattern.ON)
            status_leds.bluetooth(EStatusLEDPattern.BLINK)
            status_leds.turntable(EStatusLEDPattern.OFF)
            status_leds.error(EStatusLEDPattern.ON)
            for _ in range(100):
                motor.rotate_steps(step_count=32, direction=StepperMotorDirection.FORWARD)
                sleep(2)

    LOGGER.info("Revolution complete")

    return 0
