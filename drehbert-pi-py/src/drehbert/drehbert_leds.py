from enum import Enum
from typing import Any, override

from gpiozero import LED

from drehbert.drehbert_context_manager import DrehbertContextManager
from drehbert.gpio_constants import GPIO_LED_ERROR, GPIO_LED_TURNTABLE, GPIO_LED_BLUETOOTH, GPIO_LED_GENERAL
from drehbert.optional_value import OptionalValue


class EDrehbertLEDPattern(str, Enum):
    OFF = "off"
    ON = "on"
    BLINK = "blink"


class DrehbertLEDs(DrehbertContextManager):

    def __init__(self, pin_factory: Any | None = None):
        super().__init__()

        self._pin_factory = pin_factory

        self._led_general = OptionalValue[LED]("_led_general")
        self._led_bluetooth = OptionalValue[LED]("_led_bluetooth")
        self._led_scan = OptionalValue[LED]("_led_scan")
        self._led_error = OptionalValue[LED]("_led_error")

    def _open(self) -> None:
        self._led_general: OptionalValue[LED] = LED(GPIO_LED_GENERAL, pin_factory=self._pin_factory)
        self._led_bluetooth: OptionalValue[LED] = LED(GPIO_LED_BLUETOOTH, pin_factory=self._pin_factory)
        self._led_scan: OptionalValue[LED] = LED(GPIO_LED_TURNTABLE, pin_factory=self._pin_factory)
        self._led_error: OptionalValue[LED] = LED(GPIO_LED_ERROR, pin_factory=self._pin_factory)

    @override
    def _close(self) -> None:

        self._led_general().off()
        self._led_general().close()

        self._led_bluetooth().off()
        self._led_bluetooth().close()

        self._led_scan().off()
        self._led_scan().close()

        self._led_error().off()
        self._led_error().close()

    def general(self, pattern: EDrehbertLEDPattern) -> None:
        self._set_pattern(self._led_general(), pattern)

    def bluetooth(self, pattern: EDrehbertLEDPattern) -> None:
        self._set_pattern(self._led_bluetooth(), pattern)

    def turntable(self, pattern: EDrehbertLEDPattern) -> None:
        self._set_pattern(self._led_scan(), pattern)

    def error(self, pattern: EDrehbertLEDPattern) -> None:
        self._set_pattern(self._led_error(), pattern)

    def _set_pattern(self, led: LED, pattern: EDrehbertLEDPattern) -> None:
        self._assert_open()

        if pattern == EDrehbertLEDPattern.OFF:
            led.off()
        elif pattern == EDrehbertLEDPattern.ON:
            led.on()
        elif pattern == EDrehbertLEDPattern.BLINK:
            led.blink()
        else:
            raise ValueError(f"Invalid pattern: {pattern}")
