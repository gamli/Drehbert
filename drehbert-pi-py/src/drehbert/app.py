import asyncio
import logging

from drehbert.bluetooth_camera import BluetoothCamera
from drehbert.drehbert_leds import DrehbertLEDs
from drehbert.stepper_motor import StepperMotor

LOGGER = logging.getLogger(__name__)


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with DrehbertLEDs() as drehbert_leds:
        with StepperMotor() as motor:
            async with BluetoothCamera() as bluetooth:
                print("Entering pairing mode...")
                await bluetooth.enter_pairing_mode()

                print("Waiting for connection...")
                loop = asyncio.get_running_loop()
                started_at = loop.time()
                while not await bluetooth.is_connected():
                    elapsed = loop.time() - started_at
                    print(f"\rWaiting for connection... {elapsed:.1f} seconds", end="", flush=True)
                    await asyncio.sleep(5)

                print("\nConnected.")

                # drehbert_leds.general(EDrehbertLEDPattern.ON)
                # drehbert_leds.bluetooth(EDrehbertLEDPattern.BLINK)
                # drehbert_leds.turntable(EDrehbertLEDPattern.OFF)
                # drehbert_leds.error(EDrehbertLEDPattern.ON)
                #
                # for _ in range(100):
                #     motor.rotate_steps(step_count=32, direction=StepperMotorDirection.FORWARD)
                #     sleep(20000)

    LOGGER.info("Revolution complete")

    return 0
