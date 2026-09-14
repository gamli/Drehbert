from enum import Enum
from typing import Any, Final

from gpiozero import LED

from drehbert.gpio_constants import GPIO_LED_ERROR, GPIO_LED_TURNTABLE, GPIO_LED_BLUETOOTH, GPIO_LED_GENERAL
from drehbert.gpio_context_manager import GPIOContextManager


class EDrehbertLEDPattern(str, Enum):
    OFF = "off"
    ON = "on"
    BLINK = "blink"


class DrehbertLEDs(GPIOContextManager):

    def __init__(self, pin_factory: Any | None = None):

        self._led_general: Final[LED] = LED(GPIO_LED_GENERAL, pin_factory=pin_factory)
        self._led_bluetooth: Final[LED] = LED(GPIO_LED_BLUETOOTH, pin_factory=pin_factory)
        self._led_turntable: Final[LED] = LED(GPIO_LED_TURNTABLE, pin_factory=pin_factory)
        self._led_error: Final[LED] = LED(GPIO_LED_ERROR, pin_factory=pin_factory)

        def make_off_close(led: LED):
            def off_close():
                led.off()
                led.close()

            return off_close

        super().__init__(
            make_off_close(self._led_general),
            make_off_close(self._led_bluetooth),
            make_off_close(self._led_turntable),
            make_off_close(self._led_error),
        )

    def general(self, pattern: EDrehbertLEDPattern) -> None:
        self._set_pattern(self._led_general, pattern)

    def bluetooth(self, pattern: EDrehbertLEDPattern) -> None:
        self._set_pattern(self._led_bluetooth, pattern)

    def turntable(self, pattern: EDrehbertLEDPattern) -> None:
        self._set_pattern(self._led_turntable, pattern)

    def error(self, pattern: EDrehbertLEDPattern) -> None:
        self._set_pattern(self._led_error, pattern)

    def _set_pattern(self, led: LED, pattern: EDrehbertLEDPattern) -> None:
        self.assert_not_closed()

        if pattern == EDrehbertLEDPattern.OFF:
            led.off()
        elif pattern == EDrehbertLEDPattern.ON:
            led.on()
        elif pattern == EDrehbertLEDPattern.BLINK:
            led.blink()
        else:
            raise ValueError(f"Invalid pattern: {pattern}")
