import logging

from drehbert.drehbert_leds import DrehbertLEDs
from drehbert.stepper_motor import StepperMotor
from drehbert.usb_camera import UsbCamera

LOGGER = logging.getLogger(__name__)


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with DrehbertLEDs(), StepperMotor():
        camera = UsbCamera()
        camera.when_ready_changed = lambda ready: LOGGER.info(
            "USB camera remote ready: %s",
            ready,
        )
        async with camera:
            await camera.wait_until_ready()
            LOGGER.info("USB camera remote is ready")

            # LED and controller integration follows in DrehbertController.

    LOGGER.info("Revolution complete")

    return 0
