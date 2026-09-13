from gpiozero import DigitalOutputDevice

from drehbert.status_lights import StatusLights


def create_status_lights_on_raspi_gpio() -> StatusLights:
    general_status_pin = DigitalOutputDevice(1)

    try:
        bluetooth_status_pin = DigitalOutputDevice(7)
    except BaseException:
        general_status_pin.close()
        raise

    try:
        turntable_status_pin = DigitalOutputDevice(8)
    except BaseException:
        bluetooth_status_pin.close()
        general_status_pin.close()
        raise

    try:
        error_status_pin = DigitalOutputDevice(25)
    except BaseException:
        turntable_status_pin.close()
        bluetooth_status_pin.close()
        general_status_pin.close()
        raise

    return StatusLights(
        general_status_pin=general_status_pin,
        bluetooth_status_pin=bluetooth_status_pin,
        turntable_status_pin=turntable_status_pin,
        error_status_pin=error_status_pin
    )
