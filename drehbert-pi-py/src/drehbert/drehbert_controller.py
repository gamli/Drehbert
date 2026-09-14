from typing import Final

from drehbert.bluetooth_camera import BluetoothCameraManager
from drehbert.drehbert_buttons import DrehbertButtons
from drehbert.drehbert_leds import DrehbertLEDs
from drehbert.stepper_motor import StepperMotor


class DrehbertController:

    def __init__(
            self,
            drehbert_buttons: DrehbertButtons,
            stepper_motor: StepperMotor,
            drehbert_leds: DrehbertLEDs,
            bluetooth_camera_manager: BluetoothCameraManager,
    ):
        self._drehbert_buttons: Final[DrehbertButtons] = drehbert_buttons
        self._stepper_motor: Final[StepperMotor] = stepper_motor
        self._drehbert_leds: Final[DrehbertLEDs] = drehbert_leds
        self._bluetooth_camera_manager: Final[BluetoothCameraManager] = bluetooth_camera_manager
