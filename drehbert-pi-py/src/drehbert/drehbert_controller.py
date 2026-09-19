from typing import Final

from drehbert.drehbert_buttons import DrehbertButtons
from drehbert.drehbert_leds import DrehbertLEDs
from drehbert.stepper_motor import StepperMotor
from drehbert.usb_camera import UsbCamera


class DrehbertController:
    def __init__(
            self,
            drehbert_buttons: DrehbertButtons,
            stepper_motor: StepperMotor,
            drehbert_leds: DrehbertLEDs,
            camera: UsbCamera,
    ):
        self._drehbert_buttons: Final[DrehbertButtons] = drehbert_buttons
        self._stepper_motor: Final[StepperMotor] = stepper_motor
        self._drehbert_leds: Final[DrehbertLEDs] = drehbert_leds
        self._camera: Final[UsbCamera] = camera
