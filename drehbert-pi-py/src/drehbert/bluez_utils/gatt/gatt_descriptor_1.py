from dbus_next import PropertyAccess
from dbus_next.service import ServiceInterface, dbus_property, method

from drehbert.dbus_utils import DBUS_STRING, DBUS_OBJECT_PATH, DBUS_BYTE_ARRAY, DBUS_STRING_ARRAY, DBUS_OPTIONS
from ..binary_utils import read_at_offset


# noinspection PyPep8Naming
class BluezGattDescriptor1(ServiceInterface):

    def __init__(self, uuid: str, characteristic_path: str, flags: list[str], value: bytes) -> None:
        super().__init__("org.bluez.GattDescriptor1")
        self._uuid = uuid
        self._characteristic_path = characteristic_path
        self._flags = flags
        self._value = value

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> DBUS_STRING:
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Characteristic(self) -> DBUS_OBJECT_PATH:
        return self._characteristic_path

    @dbus_property(access=PropertyAccess.READ)
    def Value(self) -> DBUS_BYTE_ARRAY:
        return self._value

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> DBUS_STRING_ARRAY:
        return self._flags

    @method()
    def ReadValue(self, options: DBUS_OPTIONS) -> DBUS_BYTE_ARRAY:
        return read_at_offset(self._value, options)
