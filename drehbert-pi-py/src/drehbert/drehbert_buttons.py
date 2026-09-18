from collections.abc import Callable
from enum import StrEnum
from typing import Any, override

from gpiozero import Button

from drehbert.drehbert_context_manager import DrehbertContextManager
from drehbert.gpio_constants import GPIO_BUTTON_BLUETOOTH, GPIO_BUTTON_SCAN
from drehbert.optional_value import OptionalValue


class EButtonGesture(StrEnum):
    SHORT_PRESS = "short_press"
    LONG_PRESS = "long_press"


type ButtonGestureHandler = Callable[[EButtonGesture], None]


class DrehbertButtons(DrehbertContextManager):

    def __init__(self, long_press_threshold: float = 3.0, pin_factory: Any | None = None):
        super().__init__()

        if long_press_threshold <= 0:
            raise ValueError("long_press_threshold must be greater than zero")

        self._long_press_threshold = long_press_threshold
        self._pin_factory = pin_factory

        self.when_bluetooth_button_gesture: ButtonGestureHandler | None = None
        self._bluetooth_button = OptionalValue[Button]("_bluetooth_button")

        self.when_scan_button_gesture: ButtonGestureHandler | None = None
        self._scan_button = OptionalValue[Button]("_bluetooth_button")

    def _open(self) -> None:

        self.when_bluetooth_button_gesture: ButtonGestureHandler | None = None
        self._bluetooth_button.set(Button(
            GPIO_BUTTON_BLUETOOTH,
            hold_time=self._long_press_threshold,
            pin_factory=self._pin_factory,
        ))
        self._register_gpiozero_button_gestures(
            self._bluetooth_button.get(),
            lambda: self.when_bluetooth_button_gesture,
        )

        self.when_scan_button_gesture: ButtonGestureHandler | None = None
        self._scan_button.set(Button(
            GPIO_BUTTON_SCAN,
            hold_time=self._long_press_threshold,
            pin_factory=self._pin_factory,
        ))
        self._register_gpiozero_button_gestures(
            self._scan_button.get(),
            lambda: self.when_scan_button_gesture,
        )

    @override
    def _close(self) -> None:

        self.when_bluetooth_button_gesture = None
        self._bluetooth_button.get().close()

        self.when_scan_button_gesture = None
        self._scan_button.get().close()

    @staticmethod
    def _register_gpiozero_button_gestures(
            button: Button,
            get_handler: Callable[[], ButtonGestureHandler | None],
    ) -> None:

        was_held = False

        def when_pressed() -> None:
            nonlocal was_held
            was_held = False

        def when_held() -> None:
            nonlocal was_held
            was_held = True

            gesture_handler = get_handler()
            if gesture_handler is not None:
                gesture_handler(EButtonGesture.LONG_PRESS)

        def when_released() -> None:
            if was_held:
                return

            gesture_handler = get_handler()
            if gesture_handler is not None:
                gesture_handler(EButtonGesture.SHORT_PRESS)

        button.when_pressed = when_pressed
        button.when_held = when_held
        button.when_released = when_released
