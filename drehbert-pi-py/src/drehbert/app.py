import logging
from time import sleep

from drehbert.drehbert_leds import EDrehbertLEDPattern, DrehbertLEDs
from drehbert.stepper_motor import StepperMotorDirection, StepperMotor

LOGGER = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with DrehbertLEDs() as drehbert_leds:
        with StepperMotor() as motor:
            drehbert_leds.general(EDrehbertLEDPattern.ON)
            drehbert_leds.bluetooth(EDrehbertLEDPattern.BLINK)
            drehbert_leds.turntable(EDrehbertLEDPattern.OFF)
            drehbert_leds.error(EDrehbertLEDPattern.ON)
            for _ in range(100):
                motor.rotate_steps(step_count=32, direction=StepperMotorDirection.FORWARD)
                sleep(2)

    LOGGER.info("Revolution complete")

    return 0
