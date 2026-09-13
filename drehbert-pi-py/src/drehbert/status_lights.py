from enum import Enum
from types import TracebackType
from typing import Self

from drehbert.gpio_pin import GpioDigitalOutputPin


class EStatusLightPattern(str, Enum):
    OFF = "off"
    ON = "on"
    BLINK = "blink"

class StatusLights:

    def __init__(
            self,
            general_status_pin: GpioDigitalOutputPin,
            bluetooth_status_pin: GpioDigitalOutputPin,
            turntable_status_pin: GpioDigitalOutputPin,
            error_status_pin: GpioDigitalOutputPin,
    ) -> None:
        self._general_status_pin = general_status_pin
        self._bluetooth_status_pin = bluetooth_status_pin
        self._turntable_status_pin = turntable_status_pin
        self._error_status_pin = error_status_pin
        self._closed = False

        self._general_status_pin.off()
        self._bluetooth_status_pin.off()
        self._turntable_status_pin.off()
        self._error_status_pin.off()

    def set_general_pattern(self, pattern: EStatusLightPattern) -> None:
        self._set_pattern(self._general_status_pin, pattern)

    def set_bluetooth_pattern(self, pattern: EStatusLightPattern) -> None:
        self._set_pattern(self._bluetooth_status_pin, pattern)

    def set_turntable_pattern(self, pattern: EStatusLightPattern) -> None:
        self._set_pattern(self._turntable_status_pin, pattern)

    def set_error_pattern(self, pattern: EStatusLightPattern) -> None:
        self._set_pattern(self._error_status_pin, pattern)

    def _set_pattern(self, status_pin: GpioDigitalOutputPin, pattern: EStatusLightPattern) -> None:
        if self._closed:
            raise RuntimeError("Status lights is already closed")

        if pattern == EStatusLightPattern.OFF:
            status_pin.off()
        elif pattern == EStatusLightPattern.ON:
            status_pin.on()
        elif pattern == EStatusLightPattern.BLINK:
            status_pin.blink()
        else:
            raise ValueError(f"Invalid pattern: {pattern}")

    def close(self) -> None:
        if not self._closed:
            self._general_status_pin.off()
            self._general_status_pin.close()
            self._bluetooth_status_pin.off()
            self._bluetooth_status_pin.close()
            self._turntable_status_pin.off()
            self._turntable_status_pin.close()
            self._error_status_pin.off()
            self._error_status_pin.close()
            self._closed = True

    def __enter__(self) -> Self:
        if self._closed:
            raise RuntimeError("Status lights is already closed")
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
    ) -> None:
        self.close()
