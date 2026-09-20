import asyncio
import logging
from asyncio import sleep

from drehbert.bluez_utils.bluetooth_camera import BluetoothCamera
# from drehbert.bluetooth_camera import BluetoothCamera
from drehbert.drehbert_leds import DrehbertLEDs, EDrehbertLEDPattern
from drehbert.stepper_motor import StepperMotor, EStepperMotorDirection

LOGGER = logging.getLogger(__name__)


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with DrehbertLEDs() as drehbert_leds:
        print("DrehbertLEDs opened")
        with StepperMotor() as motor:
            print("StepperMotor opened")
            async with BluetoothCamera() as bluetooth_camera:
                print("Entering pairing mode...")
                await bluetooth_camera.enter_pairing_mode()

                print("Waiting for connection...")
                loop = asyncio.get_running_loop()
                started_at = loop.time()
                while not await bluetooth_camera.is_connected():
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
            #     print(f"Letting Motor rotate for 32 steps")
            #     motor.rotate_steps(step_count=32, direction=EStepperMotorDirection.FORWARD)
            #     print(f"Sleeping for 2 seconds...")
            #     await sleep(2)
            #     print(f"\t...done")

    LOGGER.info("Revolution complete")

    return 0
