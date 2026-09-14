from enum import StrEnum
from typing import Any, Callable

from gpiozero import Button

from drehbert.gpio_constants import GPIO_BUTTON_SCAN, GPIO_BUTTON_BLUETOOTH
from drehbert.gpio_context_manager import GPIOContextManager


class EButtonGesture(StrEnum):
    SHORT_PRESS = "short_press"
    LONG_PRESS = "long_press"


type ButtonGestureHandler = Callable[[EButtonGesture], None]


class DrehbertButtons(GPIOContextManager):

    def __init__(self, long_press_threshold: float = 3, pin_factory: Any | None = None):
        self._long_press_threshold = long_press_threshold

        self.when_scan_button_gesture: ButtonGestureHandler | None = None
        self.when_bluetooth_button_gesture: ButtonGestureHandler | None = None

        self._scan_button = Button(GPIO_BUTTON_SCAN, pin_factory=pin_factory)
        self._register_gpiozero_button_when_released(self._scan_button, lambda: self.when_scan_button_gesture)

        self._bluetooth_button = Button(GPIO_BUTTON_BLUETOOTH, pin_factory=pin_factory)
        self._register_gpiozero_button_when_released(self._bluetooth_button, lambda: self.when_bluetooth_button_gesture)

        def clear_gestures():
            self.when_scan_button_gesture = None
            self.when_bluetooth_button_gesture = None

        super().__init__(
            self._scan_button,
            self._bluetooth_button,
            clear_gestures,
        )

    def _register_gpiozero_button_when_released(
            self,
            button: Button,
            get_handler: Callable[[], ButtonGestureHandler | None],
    ):
        def when_released():
            gesture_handler = get_handler()
            if gesture_handler is None:
                return
            is_short_press = button.active_time < self._long_press_threshold
            gesture_handler(EButtonGesture.SHORT_PRESS if is_short_press else EButtonGesture.LONG_PRESS)

        button.when_released = when_released
